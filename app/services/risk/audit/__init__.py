"""Audit and decision-token package exports.

Exposes cryptographic chain hashing, traversal, verification, token signatures,
and validation logic, retaining compatibility namespaces.
"""

from __future__ import annotations

from app.services.risk.audit.events import (
    AuditContext,
    AuditRedactionPolicy,
    build_canonical_audit_payload,
    create_risk_audit_event,
    redact_audit_payload,
)
from app.services.risk.audit.hash_chain import (
    AuditChainVerification,
    append_audit_hash,
    build_genesis_hash,
    require_valid_audit_chain,
    verify_risk_audit_chain,
)
from app.services.risk.audit.tokens import (
    DefaultTokenSigner,
    RequiredActionScope,
    RiskDecisionTokenSigner,
    TokenValidationContext,
    TokenValidationResult,
    create_risk_decision_token,
    revoke_risk_approval_token,
    validate_risk_approval_token,
    validate_token_expiry,
    validate_token_scope,
)

__all__ = [
    # Hash Chain & Sequence
    "AuditChainVerification",
    # Events & Redaction
    "AuditContext",
    "AuditRedactionPolicy",
    # Tokens & Verification
    "DefaultTokenSigner",
    "RequiredActionScope",
    "RiskDecisionTokenSigner",
    "TokenValidationContext",
    "TokenValidationResult",
    "append_audit_hash",
    "build_canonical_audit_payload",
    "build_genesis_hash",
    "create_risk_audit_event",
    "create_risk_decision_token",
    "redact_audit_payload",
    "require_valid_audit_chain",
    "revoke_risk_approval_token",
    "validate_risk_approval_token",
    "validate_token_expiry",
    "validate_token_scope",
    "verify_risk_audit_chain",
]
