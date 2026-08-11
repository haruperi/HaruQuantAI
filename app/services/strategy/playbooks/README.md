# playbooks/ — Strategy Playbooks

Feature `FEAT-STR-16` (operational planning).

## Responsibility

Hold human-readable and machine-evaluable setup definitions for planning,
evaluation, and debrief. A playbook references a strategy profile version and
carries setup rules and debrief prompts.

## Public API

- `build_strategy_playbook`, `parse_strategy_playbook`

## Boundaries

- Playbooks never decide eligibility or evaluate live setups; evaluation is
  delegated to `setup_evaluation/`.

## Persistence

Versioned playbook definitions (`playbook versions`). See the owning package
README for the authoritative schema.
