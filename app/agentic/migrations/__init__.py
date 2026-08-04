"""Agentic-owned immutable schema definitions.

Migrations are schema evolution, not CRUD, so they live outside
``app/agentic/persistence/`` per the canonical migration-definition location
recorded in ``docs/ARCHITECTURE.md``. One submodule per feature area keeps
schema locality with the capability that owns it.

Sequence numbers are unique across the domain: ``001`` workflow, ``002``
context memory, ``003`` lifecycle, ``004`` operations, ``005`` experimentation.
"""

from app.agentic.migrations.experiment import (
    AGENTIC_EXPERIMENT_MIGRATION_STEPS as AGENTIC_EXPERIMENT_MIGRATION_STEPS,
)
from app.agentic.migrations.experiment import (
    build_experiment_migration_request,
    get_experiment_migration_statements,
)
from app.agentic.migrations.lifecycle import (
    AGENTIC_LIFECYCLE_MIGRATION_STEPS as AGENTIC_LIFECYCLE_MIGRATION_STEPS,
)
from app.agentic.migrations.lifecycle import (
    build_lifecycle_migration_request,
    get_lifecycle_migration_statements,
)
from app.agentic.migrations.memory import (
    AGENTIC_MEMORY_MIGRATION_STEPS as AGENTIC_MEMORY_MIGRATION_STEPS,
)
from app.agentic.migrations.memory import (
    build_agentic_memory_migration_request,
    get_agentic_memory_migration_statements,
)
from app.agentic.migrations.operations import (
    AGENTIC_OPERATIONS_MIGRATION_STEPS as AGENTIC_OPERATIONS_MIGRATION_STEPS,
)
from app.agentic.migrations.operations import (
    build_operations_migration_request,
    get_operations_migration_statements,
)
from app.agentic.migrations.workflow import (
    AGENTIC_MIGRATION_STEPS as AGENTIC_MIGRATION_STEPS,
)
from app.agentic.migrations.workflow import (
    build_agentic_migration_request,
    get_agentic_migration_statements,
)

__all__ = [
    "AGENTIC_EXPERIMENT_MIGRATION_STEPS",
    "AGENTIC_LIFECYCLE_MIGRATION_STEPS",
    "AGENTIC_MEMORY_MIGRATION_STEPS",
    "AGENTIC_MIGRATION_STEPS",
    "AGENTIC_OPERATIONS_MIGRATION_STEPS",
    "build_agentic_memory_migration_request",
    "build_agentic_migration_request",
    "build_experiment_migration_request",
    "build_lifecycle_migration_request",
    "build_operations_migration_request",
    "get_agentic_memory_migration_statements",
    "get_agentic_migration_statements",
    "get_experiment_migration_statements",
    "get_lifecycle_migration_statements",
    "get_operations_migration_statements",
]
