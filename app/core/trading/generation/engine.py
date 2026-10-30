"""Strategy generation primitives supporting Random and Genetic Programming engines."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from itertools import count

from app.core.enums import OrderType, Timeframe
from app.core.generators import RandomGenerator
from app.core.trading.blocks.registry import block_registry
from app.core.trading.strategy.contracts import (
    ActionKind,
    ConditionDefinition,
    ParameterDefinition,
    RuleAction,
    RuleDefinition,
    RuleTriggerKind,
    StrategyDocument,
    TradingSetupConfig,
)

_DEFAULT_COMPARATORS = (">", "<", ">=", "<=")
_DEFAULT_PRICE_FIELDS = ("close", "open", "high", "low")
_HALF_PROB = 0.5
_MIN_RULES_FOR_SWAP = 2
_MUTATION_DELTA_SCALE = 0.2


@dataclass(frozen=True, slots=True)
class GenerationSpec:
    """Configuration specification for strategy generation engines."""

    symbol: str = "EURUSD"
    timeframe: Timeframe = Timeframe.PERIOD_H1
    allowed_blocks: tuple[str, ...] = ()
    max_rule_depth: int = 3
    target_databank: str = "default"
    population_size: int = 50
    island_count: int = 2
    crossover_prob: float = 0.7
    mutation_prob: float = 0.2
    tournament_size: int = 3
    tournament_prob: float = 0.8
    seed: int | None = None


@dataclass(slots=True)
class Individual:
    """Candidate individual in a genetic programming population."""

    strategy: StrategyDocument
    fitness: float = 0.0
    island_id: int = 0
    generation: int = 0


class GenerationEngine:
    """Strategy generation engine implementing Random and Genetic Programming (GP)."""

    def __init__(self, spec: GenerationSpec | None = None) -> None:
        self.spec = spec or GenerationSpec()
        self.rng = RandomGenerator(self.spec.seed)
        self._strategy_id_gen = count(1)

        # Island populations: list of populations per island
        self.islands: list[list[Individual]] = [
            [] for _ in range(max(1, self.spec.island_count))
        ]
        self.current_generation: int = 0

    def generate_random_strategy(
        self, strategy_id: str | None = None
    ) -> StrategyDocument:
        """Construct a valid StrategyDocument with randomized conditions and actions."""
        sid = strategy_id or f"strat-gen-{next(self._strategy_id_gen)}"

        entry_conditions = self._generate_conditions(
            count=self.rng.next_int(1, max(1, self.spec.max_rule_depth))
        )
        exit_conditions = self._generate_conditions(count=1)

        direction = 1 if self.rng.next_double() >= _HALF_PROB else -1
        order_type = OrderType.BUY if direction == 1 else OrderType.SELL

        entry_rule = RuleDefinition(
            rule_id=f"{sid}-entry",
            name="Entry Rule",
            trigger=RuleTriggerKind.ON_BAR_CLOSE,
            conditions=tuple(entry_conditions),
            actions=(
                RuleAction(
                    kind=ActionKind.ENTER,
                    direction=direction,
                    order_type=order_type,
                    volume=1.0,
                    sl_pips=float(self.rng.next_int(10, 100)),
                    tp_pips=float(self.rng.next_int(20, 200)),
                ),
            ),
        )

        exit_rule = RuleDefinition(
            rule_id=f"{sid}-exit",
            name="Exit Rule",
            trigger=RuleTriggerKind.ON_BAR_CLOSE,
            conditions=tuple(exit_conditions),
            actions=(RuleAction(kind=ActionKind.EXIT),),
        )

        params: list[ParameterDefinition] = []
        for i, cond in enumerate(entry_conditions + exit_conditions):
            if isinstance(cond.right, (int, float)):
                params.append(
                    ParameterDefinition(
                        name=f"param_threshold_{i}",
                        param_type="float",
                        value=float(cond.right),
                    )
                )

        return StrategyDocument(
            strategy_id=sid,
            rules=(entry_rule, exit_rule),
            params=tuple(params),
            trading_setup=TradingSetupConfig(),
        )

    def _generate_conditions(self, count: int) -> list[ConditionDefinition]:
        conditions: list[ConditionDefinition] = []
        registered_blocks = list(self.spec.allowed_blocks) or [
            d.spec.id for d in block_registry.snapshot()
        ]

        for _ in range(count):
            comp = _DEFAULT_COMPARATORS[
                self.rng.next_int(0, len(_DEFAULT_COMPARATORS) - 1)
            ]

            use_block = (
                len(registered_blocks) > 0 and self.rng.next_double() < _HALF_PROB
            )

            if use_block:
                block_id = registered_blocks[
                    self.rng.next_int(0, len(registered_blocks) - 1)
                ]
                conditions.append(
                    ConditionDefinition(
                        left="close",
                        comparator=comp,
                        right=0.0,
                        composition_block_id=block_id,
                    )
                )
            else:
                left_field = _DEFAULT_PRICE_FIELDS[
                    self.rng.next_int(0, len(_DEFAULT_PRICE_FIELDS) - 1)
                ]
                # Right side operand
                if self.rng.next_double() < _HALF_PROB:
                    right_val: str | float = _DEFAULT_PRICE_FIELDS[
                        self.rng.next_int(0, len(_DEFAULT_PRICE_FIELDS) - 1)
                    ]
                else:
                    right_val = round(self.rng.next_double() * 2.0, 4)

                conditions.append(
                    ConditionDefinition(
                        left=left_field,
                        comparator=comp,
                        right=right_val,
                    )
                )

        return conditions

    def tournament_select(self, population: Sequence[Individual]) -> Individual:
        """Select an individual using probabilistic tournament selection.

        Samples `tournament_size` (3) candidates, ranks by fitness descending,
        and selects with rank probability `tournament_prob` (0.8).
        """
        if not population:
            msg = "Population must not be empty for tournament selection"
            raise ValueError(msg)

        k = min(len(population), self.spec.tournament_size)
        indices: list[int] = []
        for _ in range(k):
            idx = self.rng.next_int(0, len(population) - 1)
            indices.append(idx)

        # Sort candidates descending by fitness
        candidates = sorted(
            [population[i] for i in indices],
            key=lambda ind: ind.fitness,
            reverse=True,
        )

        prob = self.spec.tournament_prob
        for i in range(len(candidates) - 1):
            if self.rng.next_double() < prob:
                return candidates[i]

        return candidates[-1]

    def crossover(
        self, parent1: StrategyDocument, parent2: StrategyDocument
    ) -> tuple[StrategyDocument, StrategyDocument]:
        """Perform rule subtree crossover between two parent strategy documents."""
        sid1 = f"strat-cx-{next(self._strategy_id_gen)}"
        sid2 = f"strat-cx-{next(self._strategy_id_gen)}"

        r1 = list(parent1.rules)
        r2 = list(parent2.rules)

        child1_rules: tuple[RuleDefinition, ...]
        child2_rules: tuple[RuleDefinition, ...]
        if len(r1) >= _MIN_RULES_FOR_SWAP and len(r2) >= _MIN_RULES_FOR_SWAP:
            # Swap exit rules
            child1_rules = (r1[0], r2[1])
            child2_rules = (r2[0], r1[1])
        elif r1 and r2:
            # Swap condition sets within the first rule
            rule1 = r1[0]
            rule2 = r2[0]
            new_r1 = RuleDefinition(
                rule_id=rule1.rule_id,
                name=rule1.name,
                trigger=rule1.trigger,
                conditions=rule2.conditions,
                actions=rule1.actions,
            )
            new_r2 = RuleDefinition(
                rule_id=rule2.rule_id,
                name=rule2.name,
                trigger=rule2.trigger,
                conditions=rule1.conditions,
                actions=rule2.actions,
            )
            child1_rules = (new_r1, *tuple(r1[1:]))
            child2_rules = (new_r2, *tuple(r2[1:]))
        else:
            child1_rules = tuple(r1)
            child2_rules = tuple(r2)

        c1 = StrategyDocument(
            strategy_id=sid1,
            rules=child1_rules,
            params=parent1.params,
            trading_setup=parent1.trading_setup,
        )
        c2 = StrategyDocument(
            strategy_id=sid2,
            rules=child2_rules,
            params=parent2.params,
            trading_setup=parent2.trading_setup,
        )
        return c1, c2

    def mutate(self, strategy: StrategyDocument) -> StrategyDocument:
        """Apply point mutations to strategy conditions and parameter thresholds."""
        mutated_rules: list[RuleDefinition] = []

        for rule in strategy.rules:
            new_conditions: list[ConditionDefinition] = []
            for cond in rule.conditions:
                # Probabilistic comparator mutation
                if self.rng.next_double() < self.spec.mutation_prob:
                    new_comp = _DEFAULT_COMPARATORS[
                        self.rng.next_int(0, len(_DEFAULT_COMPARATORS) - 1)
                    ]
                else:
                    new_comp = cond.comparator

                # Probabilistic right-hand threshold mutation
                if isinstance(cond.right, (int, float)):
                    if self.rng.next_double() < self.spec.mutation_prob:
                        delta = (
                            self.rng.next_double() - _HALF_PROB
                        ) * _MUTATION_DELTA_SCALE
                        new_right: str | float = round(
                            float(cond.right) * (1.0 + delta), 4
                        )
                    else:
                        new_right = cond.right
                else:
                    new_right = cond.right

                new_conditions.append(
                    ConditionDefinition(
                        left=cond.left,
                        comparator=new_comp,
                        right=new_right,
                        composition_block_id=cond.composition_block_id,
                        composition_params=cond.composition_params,
                    )
                )

            mutated_rules.append(
                RuleDefinition(
                    rule_id=rule.rule_id,
                    name=rule.name,
                    trigger=rule.trigger,
                    conditions=tuple(new_conditions),
                    actions=rule.actions,
                    is_enabled=rule.is_enabled,
                )
            )

        # Mutate parameter definitions
        new_params: list[ParameterDefinition] = []
        for p in strategy.params:
            if (
                isinstance(p.value, (int, float))
                and self.rng.next_double() < self.spec.mutation_prob
            ):
                perturbed = float(p.value) * (
                    1.0 + (self.rng.next_double() - _HALF_PROB) * _MUTATION_DELTA_SCALE
                )
                new_params.append(
                    ParameterDefinition(
                        name=p.name,
                        param_type=p.param_type,
                        value=round(perturbed, 4),
                    )
                )
            else:
                new_params.append(p)

        sid = f"strat-mut-{next(self._strategy_id_gen)}"
        return StrategyDocument(
            strategy_id=sid,
            rules=tuple(mutated_rules),
            params=tuple(new_params),
            trading_setup=strategy.trading_setup,
        )

    def initialize_population(self) -> None:
        """Seed island populations with randomly generated strategies."""
        num_islands = max(1, self.spec.island_count)
        pop_per_island = max(2, self.spec.population_size // num_islands)

        self.islands = []
        for island_id in range(num_islands):
            island: list[Individual] = []
            for _ in range(pop_per_island):
                strat = self.generate_random_strategy()
                island.append(
                    Individual(
                        strategy=strat,
                        fitness=0.0,
                        island_id=island_id,
                        generation=0,
                    )
                )
            self.islands.append(island)

    def _reproduce_island(
        self, island: list[Individual], island_id: int
    ) -> list[Individual]:
        """Perform reproduction steps (elitism, CX, mutation) for an island."""
        pop_size = len(island)
        best = max(island, key=lambda x: x.fitness)
        new_island: list[Individual] = [
            Individual(
                strategy=best.strategy,
                fitness=best.fitness,
                island_id=island_id,
                generation=self.current_generation,
            )
        ]

        while len(new_island) < pop_size:
            p1 = self.tournament_select(island)
            p2 = self.tournament_select(island)

            if self.rng.next_double() < self.spec.crossover_prob:
                c1, c2 = self.crossover(p1.strategy, p2.strategy)
            else:
                c1, c2 = p1.strategy, p2.strategy

            if self.rng.next_double() < self.spec.mutation_prob:
                c1 = self.mutate(c1)
            if self.rng.next_double() < self.spec.mutation_prob:
                c2 = self.mutate(c2)

            new_island.append(
                Individual(
                    strategy=c1,
                    fitness=0.0,
                    island_id=island_id,
                    generation=self.current_generation,
                )
            )
            if len(new_island) < pop_size:
                new_island.append(
                    Individual(
                        strategy=c2,
                        fitness=0.0,
                        island_id=island_id,
                        generation=self.current_generation,
                    )
                )

        return new_island

    def _migrate_ring(self, next_islands: list[list[Individual]]) -> None:
        """Migrate the best individual to the next island in ring topology."""
        num_islands = len(self.islands)
        for i in range(num_islands):
            target_island = (i + 1) % num_islands
            best_ind = max(self.islands[i], key=lambda x: x.fitness)
            worst_idx = min(
                range(len(next_islands[target_island])),
                key=lambda idx: next_islands[target_island][idx].fitness,
            )
            next_islands[target_island][worst_idx] = Individual(
                strategy=best_ind.strategy,
                fitness=best_ind.fitness,
                island_id=target_island,
                generation=self.current_generation,
            )

    def step_generation(
        self, fitness_evaluator: Callable[[StrategyDocument], float]
    ) -> list[Individual]:
        """Advance genetic programming island populations by one generation."""
        if not self.islands or not self.islands[0]:
            self.initialize_population()

        self.current_generation += 1

        # 1. Evaluate fitness on all islands
        for island in self.islands:
            for ind in island:
                ind.fitness = float(fitness_evaluator(ind.strategy))

        # 2. Reproduction within each island
        next_islands = [
            self._reproduce_island(island, island_id)
            for island_id, island in enumerate(self.islands)
        ]

        # 3. Migration between neighboring islands (ring topology)
        if len(self.islands) > 1:
            self._migrate_ring(next_islands)

        self.islands = next_islands
        all_individuals: list[Individual] = []
        for isl in self.islands:
            all_individuals.extend(isl)
        return all_individuals


__all__ = ["GenerationEngine", "GenerationSpec", "Individual"]
