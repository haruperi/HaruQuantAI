"""Public `FEAT-AGT-06` evidence context and governed memory API."""

from app.agentic.context_memory.context import assemble_context, get_exclusion_reasons
from app.agentic.context_memory.models import (
    ContextBundle,
    EvidenceClaim,
    MemoryRecord,
    build_evidence_claim,
    build_memory_record,
    classify_injection,
    derive_content_hash,
)
from app.agentic.context_memory.repository import (
    AgenticMemoryStore,
    build_in_memory_memory_store,
    retrieve_memory,
    store_memory,
)
from app.agentic.migrations.memory import (
    build_agentic_memory_migration_request,
    get_agentic_memory_migration_statements,
)

__all__: tuple[str, ...] = (
    "AgenticMemoryStore",
    "ContextBundle",
    "EvidenceClaim",
    "MemoryRecord",
    "assemble_context",
    "build_agentic_memory_migration_request",
    "build_evidence_claim",
    "build_in_memory_memory_store",
    "build_memory_record",
    "classify_injection",
    "derive_content_hash",
    "get_agentic_memory_migration_statements",
    "get_exclusion_reasons",
    "retrieve_memory",
    "store_memory",
)
