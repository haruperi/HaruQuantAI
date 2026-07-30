"""FEAT-DATA-16 point-in-time research-source evidence."""

from app.services.data.research_sources.contracts import (
    ResearchSourceDocument,
    ResearchSourceEligibility,
    ResearchSourceIngestRequest,
    ResearchSourcePage,
    ResearchSourcePolicy,
    ResearchSourceQuery,
    VerifiedResearchSource,
)
from app.services.data.research_sources.ingestion import ingest_research_source
from app.services.data.research_sources.migrations import (
    RESEARCH_PROVIDER_MIGRATION_STEP,
    RESEARCH_SOURCE_MIGRATION_STEP,
)
from app.services.data.research_sources.normalization import (
    normalize_research_provider_payload,
)
from app.services.data.research_sources.observations import (
    persist_research_source_observations,
    project_research_source_observation,
    query_research_source_observations,
)
from app.services.data.research_sources.policy import (
    assess_research_source_eligibility,
    validate_research_source_policy,
)
from app.services.data.research_sources.providers import (
    persist_research_provider_records,
)
from app.services.data.research_sources.queries import (
    project_research_source_evidence,
    query_research_sources,
)
from app.services.data.research_sources.transport import (
    retrieve_research_provider_payload,
)
from app.services.data.research_sources.verified_sources import (
    persist_verified_research_source,
)

__all__ = (
    "RESEARCH_PROVIDER_MIGRATION_STEP",
    "RESEARCH_SOURCE_MIGRATION_STEP",
    "ResearchSourceDocument",
    "ResearchSourceEligibility",
    "ResearchSourceIngestRequest",
    "ResearchSourcePage",
    "ResearchSourcePolicy",
    "ResearchSourceQuery",
    "VerifiedResearchSource",
    "assess_research_source_eligibility",
    "ingest_research_source",
    "normalize_research_provider_payload",
    "persist_research_provider_records",
    "persist_research_source_observations",
    "persist_verified_research_source",
    "project_research_source_evidence",
    "project_research_source_observation",
    "query_research_source_observations",
    "query_research_sources",
    "retrieve_research_provider_payload",
    "validate_research_source_policy",
)
