# Simulation Checklists, Modes, and Missions

`FEAT-SIM-10` owns deterministic checklist definitions and runtime state,
simulation-mode assistance policy, actual-state evidence binding, and mission
completion. It never lets a presentation caller directly assert that a step is
satisfied and every mode remains restricted to the simulation route.
