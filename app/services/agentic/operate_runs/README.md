# FEAT-AGT-OPERATE_RUNS

Provides `agentic.operations@1`. Operation payloads are bounded and redacted before durable persistence. Containment/readiness is durable state, while notifications are only hints; every consequential Agentic consumer must re-check current readiness. Replay validation compares exact immutable references and rejects any side-effectful replay request.
