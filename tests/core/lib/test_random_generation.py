"""Exercise shared donor RNG through the actual strategy generation consumer."""

from app.core.lib.random import RandomGenerator
from app.core.trading.generation.engine import GenerationEngine, GenerationSpec


def test_generation_uses_shared_donor_stream() -> None:
    first = GenerationEngine(GenerationSpec(seed=42))
    second = GenerationEngine(GenerationSpec(seed=42))
    assert isinstance(first.rng, RandomGenerator)
    assert first.rng.next_double() == 0.3745401173314896
    first.rng.seed(42)
    for index in range(3):
        strategy_id = f"donor-rng-{index}"
        assert first.generate_random_strategy(strategy_id) == (
            second.generate_random_strategy(strategy_id)
        )
