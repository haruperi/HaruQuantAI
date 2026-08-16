# Scenario Engine

`FEAT-SIM-11` owns immutable mission definitions, deterministic trigger
evaluation, emergency and abnormal-operation templates, injected-event ordering,
and Simulator-owned evidence providers for Research and Optimization.

The scenario engine is the sole owner of seeded transport, response, delivery,
and connection-lifecycle faults. Every triggered fault carries its calibration
checksum, stream identity/counter, deterministic draw, and journal event type.
