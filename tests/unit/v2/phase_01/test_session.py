"""Unit and integration test suite for host sessions and security authority.

Tests FR-HOST-SESS-* requirements:
- FR-HOST-SESS-LOOPBACK-ORIGIN: Loopback origin checks and DNS rebinding rejection.
- FR-HOST-SESS-LIFECYCLE: Ephemeral session lifecycle, TTL, and restart invalidation.
- FR-HOST-SESS-SCOPE-AUTHORIZATION: Granular scoped action authorization.
- FR-HOST-SESS-DISTINCT-AUTHORITY: Dangerous action elevation gates.
- FR-HOST-SESS-SECRET-SANITIZATION: Credential masking and input redaction.
- FR-HOST-SESS-DISTRIBUTION-QUALIFICATION: Clean installation and domain removal.
- FR-HOST-SESS-REST-PROJECTION: FastAPI endpoints and Bearer dependency.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from app.host.session import (
    AuthenticationError,
    DistinctAuthorityCoordinator,
    DistinctAuthorityRequiredError,
    DistinctAuthorityType,
    ElevationExpiredError,
    ElevationRequest,
    HostAuthentication,
    LoginCooldownError,
    LoginRequest,
    LoopbackOriginError,
    LoopbackSecurityMiddleware,
    LoopbackValidator,
    MaskedSecret,
    PermissionDeniedError,
    RoleType,
    ScopeAuthorizer,
    SecurityError,
    SessionContext,
    SessionExpiredError,
    SessionManager,
    StandardScope,
    create_auth_router,
    create_sessions_router,
    extract_bearer_token,
    get_current_session,
    get_tls_remote_deployment_proposal,
    hash_password,
    main,
    reset_global_security_state,
    sanitize_operational_inputs,
    validate_user_code_ast,
    verify_clean_installation,
    verify_domain_removal,
    verify_password,
)
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clean_security_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[None]:
    """Reset global security singletons before and after each test."""
    from app.host import persistence

    monkeypatch.setattr(persistence, "DEFAULT_DATABASE_PATH", tmp_path / "sessions.db")
    reset_global_security_state()
    yield
    reset_global_security_state()


# -----------------------------------------------------------------------------
# 1. Loopback Origin & DNS Rebinding Tests
# -----------------------------------------------------------------------------


def test_loopback_validator_valid_hosts() -> None:
    """Validate accepted local loopback host addresses."""
    val = LoopbackValidator()
    assert val.is_loopback_host("localhost")
    assert val.is_loopback_host("localhost:8000")
    assert val.is_loopback_host("127.0.0.1")
    assert val.is_loopback_host("127.0.0.1:5173")
    assert val.is_loopback_host("127.0.0.2")
    assert val.is_loopback_host("::1")
    assert val.is_loopback_host("[::1]:8000")
    assert val.is_loopback_host("testserver")
    assert not val.is_loopback_host("")


def test_loopback_validator_foreign_hosts_rejected() -> None:
    """Verify non-loopback host names and IP addresses are rejected."""
    val = LoopbackValidator()
    assert not val.is_loopback_host("attacker.com")
    assert not val.is_loopback_host("evil.example.org:8000")
    assert not val.is_loopback_host("192.168.1.100")
    assert not val.is_loopback_host("10.0.0.1")
    assert not val.is_loopback_host("8.8.8.8")


def test_loopback_validator_origin_and_referer() -> None:
    """Verify loopback origin and referer parsing."""
    val = LoopbackValidator()
    assert val.is_loopback_url("http://localhost:5173")
    assert val.is_loopback_url("http://127.0.0.1:8000/app")
    assert val.is_loopback_url("http://[::1]:8080/shell")
    assert val.is_loopback_url("")  # Empty referer allowed
    assert not val.is_loopback_url("https://malicious.site/attack")
    assert not val.is_loopback_url("http://192.168.1.50:8000")


def test_loopback_validator_headers_validation_exceptions() -> None:
    """Verify header validation raises LoopbackOriginError on unauthorized origins."""
    val = LoopbackValidator()

    # Valid loopback headers
    val.validate_request_headers(
        {
            "host": "localhost:8000",
            "origin": "http://localhost:5173",
            "referer": "http://localhost:5173/",
        }
    )

    # Invalid host
    with pytest.raises(LoopbackOriginError, match="Unauthorized host"):
        val.validate_request_headers({"host": "evil.com"})

    # Invalid origin
    with pytest.raises(LoopbackOriginError, match="Unauthorized origin"):
        val.validate_request_headers(
            {"host": "localhost:8000", "origin": "https://evil.com"}
        )

    # Invalid referer
    with pytest.raises(LoopbackOriginError, match="Unauthorized referer"):
        val.validate_request_headers(
            {"host": "localhost:8000", "referer": "https://phishing.site/leak"}
        )


def test_loopback_middleware_asgi_rejection() -> None:
    """Test ASGI middleware intercepting foreign requests and returning 403 Forbidden."""
    app = FastAPI()
    app.add_middleware(LoopbackSecurityMiddleware)

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"ping": "pong"}

    client = TestClient(app)

    # Loopback request passes
    resp = client.get("/ping", headers={"Host": "localhost:8000"})
    assert resp.status_code == 200

    # Foreign Host rejected with 403
    resp_foreign = client.get("/ping", headers={"Host": "attacker.com"})
    assert resp_foreign.status_code == 403
    data = resp_foreign.json()
    assert data["status"] == "error"
    assert data["error"]["code"] == "LOOPBACK_ORIGIN_DENIED"


# -----------------------------------------------------------------------------
# 2. Ephemeral Session Lifecycle & Guaranteed Restart Invalidation
# -----------------------------------------------------------------------------


def test_session_creation_and_verification() -> None:
    """Verify ephemeral session token creation and verification."""
    mgr = SessionManager(host_instance_id="host-run-1", default_ttl_sec=3600)
    session = mgr.create_session(username="trader_alice", role=RoleType.OPERATOR)

    assert session.username == "trader_alice"
    assert session.role == RoleType.OPERATOR
    assert session.host_instance_id == "host-run-1"
    assert len(session.token) == 64  # secrets.token_hex(32)
    assert not session.is_expired()
    assert mgr.active_session_count() == 1

    # Verify session retrieves identical context
    verified = mgr.verify_session(session.token)
    assert verified.username == "trader_alice"
    assert verified.token == session.token


def test_session_verification_errors() -> None:
    """Verify missing, unknown, and expired token error cases."""
    mgr = SessionManager(default_ttl_sec=3600)

    # Missing token
    with pytest.raises(AuthenticationError, match="Missing session token"):
        mgr.verify_session("")

    # Unknown token
    with pytest.raises(AuthenticationError, match="Invalid or unknown session token"):
        mgr.verify_session("non-existent-token-12345")


def test_session_ttl_expiration() -> None:
    """Verify expired session token raises SessionExpiredError and is purged."""
    mgr = SessionManager(default_ttl_sec=1)
    session = mgr.create_session(username="temp_user", ttl_sec=1)
    assert not session.is_expired()

    time.sleep(1.1)
    assert session.is_expired()

    with pytest.raises(SessionExpiredError, match="Session token has expired"):
        mgr.verify_session(session.token)

    # Token should be pruned from store
    assert mgr.active_session_count() == 0


def test_session_explicit_revocation() -> None:
    """Verify single and user-wide token revocations."""
    mgr = SessionManager()
    s1 = mgr.create_session("trader_bob")
    _s2 = mgr.create_session("trader_bob")
    s3 = mgr.create_session("trader_carol")
    assert mgr.active_session_count() == 3

    # Revoke single token
    assert mgr.revoke_session(s1.token)
    assert not mgr.revoke_session("unknown")
    assert mgr.active_session_count() == 2

    # Revoke user tokens
    revoked_count = mgr.revoke_user("trader_bob")
    assert revoked_count == 1
    assert mgr.active_session_count() == 1

    # Carol remains active
    assert mgr.verify_session(s3.token).username == "trader_carol"


def test_guaranteed_restart_invalidation() -> None:
    """Verify that host restart immediately invalidates all active sessions."""
    mgr = SessionManager(host_instance_id="host-boot-001")
    s1 = mgr.create_session("operator_1")
    _s2 = mgr.create_session("operator_2")
    assert mgr.active_session_count() == 2

    # Host restarts -> reset() is invoked
    mgr.reset(new_host_instance_id="host-boot-002")
    assert mgr.active_session_count() == 0

    # Old tokens fail verification
    with pytest.raises(AuthenticationError, match="Invalid or unknown session token"):
        mgr.verify_session(s1.token)

    # Even if an old session object is retained, host mismatch raises restart error
    old_session = SessionContext(
        token="orphan-token",
        username="operator_old",
        role=RoleType.OPERATOR,
        scopes={"system:read"},
        created_at="2026-01-01T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
        last_active_at="2026-01-01T00:00:00Z",
        host_instance_id="host-boot-001",  # previous host instance
    )
    with mgr._lock:
        mgr._sessions["orphan-token"] = old_session

    with pytest.raises(
        AuthenticationError, match="Session invalidated: host runtime restarted"
    ):
        mgr.verify_session("orphan-token")


# -----------------------------------------------------------------------------
# 3. Scoped Authorization & Wildcard Permissions
# -----------------------------------------------------------------------------


def test_scope_authorization_operator_role() -> None:
    """Verify standard operator principal scopes."""
    mgr = SessionManager()
    authorizer = ScopeAuthorizer()
    session = mgr.create_session(role=RoleType.OPERATOR)

    # Standard operational scopes allowed
    authorizer.authorize(session, StandardScope.JOBS_READ)
    authorizer.authorize(session, StandardScope.RESOURCES_WRITE)
    authorizer.authorize(session, StandardScope.SETTINGS_READ)
    authorizer.authorize(session, StandardScope.BACKTEST_RUN)


def test_scope_authorization_readonly_role_denials() -> None:
    """Verify readonly principal cannot execute mutating actions."""
    mgr = SessionManager()
    authorizer = ScopeAuthorizer()
    readonly_session = mgr.create_session(role=RoleType.READONLY)

    # Read actions permitted
    authorizer.authorize(readonly_session, StandardScope.JOBS_READ)
    authorizer.authorize(readonly_session, StandardScope.RESOURCES_READ)

    # Write actions denied
    with pytest.raises(PermissionDeniedError, match="lacks scope 'jobs:write'"):
        authorizer.authorize(readonly_session, StandardScope.JOBS_WRITE)

    with pytest.raises(PermissionDeniedError, match="lacks scope 'resources:delete'"):
        authorizer.authorize(readonly_session, StandardScope.RESOURCES_DELETE)


def test_scope_authorization_wildcards() -> None:
    """Verify wildcard scope evaluation."""
    authorizer = ScopeAuthorizer()

    # Domain wildcard: "jobs:*"
    session_jobs = SessionContext(
        token="tok1",
        username="worker",
        role=RoleType.OPERATOR,
        scopes={"jobs:*", "data:read"},
        created_at="2026-01-01T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
        last_active_at="2026-01-01T00:00:00Z",
        host_instance_id="h1",
    )
    authorizer.authorize(session_jobs, "jobs:read")
    authorizer.authorize(session_jobs, "jobs:write")
    authorizer.authorize(session_jobs, "jobs:cancel")
    with pytest.raises(PermissionDeniedError):
        authorizer.authorize(session_jobs, "data:write")

    # Global wildcard: "*"
    session_super = SessionContext(
        token="tok2",
        username="system",
        role=RoleType.SYSTEM,
        scopes={"*"},
        created_at="2026-01-01T00:00:00Z",
        expires_at="2099-01-01T00:00:00Z",
        last_active_at="2026-01-01T00:00:00Z",
        host_instance_id="h1",
    )
    authorizer.authorize(session_super, "anything:action")


def test_scope_evaluation_non_throwing() -> None:
    """Verify evaluate_scope provides structured non-throwing responses."""
    mgr = SessionManager()
    authorizer = ScopeAuthorizer()
    session = mgr.create_session(role=RoleType.READONLY)

    res_allowed = authorizer.evaluate_scope(session, StandardScope.JOBS_READ)
    assert res_allowed.allowed
    assert not res_allowed.requires_distinct_authority

    res_denied = authorizer.evaluate_scope(session, StandardScope.JOBS_WRITE)
    assert not res_denied.allowed
    assert res_denied.reason is not None

    res_distinct = authorizer.evaluate_scope(
        session, DistinctAuthorityType.LIVE_TRADING
    )
    assert not res_distinct.allowed
    assert res_distinct.requires_distinct_authority


# -----------------------------------------------------------------------------
# 4. Distinct Authority Elevation for Dangerous Operations
# -----------------------------------------------------------------------------


def test_distinct_authority_denial_by_default() -> None:
    """Verify dangerous operations require elevation even for operator sessions."""
    mgr = SessionManager()
    authorizer = ScopeAuthorizer()
    session = mgr.create_session(role=RoleType.OPERATOR)

    # Standard operator cannot execute live trading without elevation
    with pytest.raises(
        DistinctAuthorityRequiredError, match="dangerous operation requiring explicit"
    ):
        authorizer.authorize(session, DistinctAuthorityType.LIVE_TRADING)

    with pytest.raises(DistinctAuthorityRequiredError):
        authorizer.authorize(session, DistinctAuthorityType.SYSTEM_DESTRUCTIVE)

    with pytest.raises(DistinctAuthorityRequiredError):
        authorizer.authorize(session, DistinctAuthorityType.SCRIPTS_EXECUTE)


def test_distinct_authority_elevation_flow() -> None:
    """Verify end-to-end elevation, assertion, and revocation."""
    mgr = SessionManager()
    authorizer = ScopeAuthorizer()
    coord = DistinctAuthorityCoordinator()
    session = mgr.create_session(role=RoleType.OPERATOR)

    # Invalid confirmation phrase rejected
    with pytest.raises(SecurityError, match="Invalid confirmation phrase"):
        coord.elevate(
            session,
            ElevationRequest(
                scope=DistinctAuthorityType.LIVE_TRADING,
                reason="Arming live terminal",
                confirmation_phrase="wrong-phrase",
            ),
        )

    # Valid elevation
    grant = coord.elevate(
        session,
        ElevationRequest(
            scope=DistinctAuthorityType.LIVE_TRADING,
            reason="Arming live terminal for execution",
            confirmation_phrase="CONFIRM:live_trading:execute",
            ttl_seconds=300,
        ),
    )
    assert grant.scope == DistinctAuthorityType.LIVE_TRADING
    assert not grant.is_expired()
    assert session.has_distinct_grant(DistinctAuthorityType.LIVE_TRADING)

    # Scope authorization now succeeds
    authorizer.authorize(session, DistinctAuthorityType.LIVE_TRADING)
    coord.require_distinct_authority(session, DistinctAuthorityType.LIVE_TRADING)

    # Revoke elevation
    assert coord.revoke_elevation(session, DistinctAuthorityType.LIVE_TRADING)
    assert not session.has_distinct_grant(DistinctAuthorityType.LIVE_TRADING)

    with pytest.raises(DistinctAuthorityRequiredError):
        coord.require_distinct_authority(session, DistinctAuthorityType.LIVE_TRADING)


def test_distinct_authority_expiration() -> None:
    """Verify expired elevation grant raises ElevationExpiredError."""
    mgr = SessionManager()
    authorizer = ScopeAuthorizer()
    coord = DistinctAuthorityCoordinator()
    session = mgr.create_session(role=RoleType.OPERATOR)

    # Elevate with minimum TTL
    grant = coord.elevate(
        session,
        ElevationRequest(
            scope=DistinctAuthorityType.SYSTEM_DESTRUCTIVE,
            reason="Pruning old database tables",
            confirmation_phrase="CONFIRM:system:destructive",
            ttl_seconds=10,
        ),
    )

    # Artificially expire the grant
    expired_grant = grant.model_copy(update={"expires_at": "2020-01-01T00:00:00+00:00"})
    session.distinct_grants[DistinctAuthorityType.SYSTEM_DESTRUCTIVE.value] = (
        expired_grant
    )

    with pytest.raises(ElevationExpiredError, match="has expired"):
        authorizer.authorize(session, DistinctAuthorityType.SYSTEM_DESTRUCTIVE)

    session.distinct_grants[DistinctAuthorityType.SYSTEM_DESTRUCTIVE.value] = (
        expired_grant
    )
    with pytest.raises(ElevationExpiredError):
        coord.require_distinct_authority(
            session, DistinctAuthorityType.SYSTEM_DESTRUCTIVE
        )


# -----------------------------------------------------------------------------
# 5. Masked Secrets & Operational Input Sanitization
# -----------------------------------------------------------------------------


def test_masked_secret_representation() -> None:
    """Verify MaskedSecret masks plaintext in repr and str."""
    secret = MaskedSecret("super_sensitive_api_token_12345")
    assert "super_sensitive" not in str(secret)
    assert "[REDACTED:" in str(secret)
    assert "super_sensitive" not in repr(secret)
    assert secret.get_secret_value() == "super_sensitive_api_token_12345"

    # Equality and hashing
    same_secret = MaskedSecret("super_sensitive_api_token_12345")
    assert secret == same_secret
    assert secret == "super_sensitive_api_token_12345"
    assert hash(secret) == hash(same_secret)


def test_sanitize_operational_inputs_nested() -> None:
    """Verify recursive redaction of sensitive dictionary fields."""
    raw_payload: dict[str, Any] = {
        "workspace": "strategy_builder",
        "api_key": "live-broker-key-xyz",
        "password": "db_password_123",
        "parameters": {
            "token": "bearer-token-abc",
            "symbol": "EURUSD",
            "nested_list": [
                {"auth_bearer": "secret-jwt"},
                {"safe_param": 42},
                MaskedSecret("masked_value"),
            ],
        },
    }

    sanitized = sanitize_operational_inputs(raw_payload)

    assert sanitized["workspace"] == "strategy_builder"
    assert sanitized["api_key"].startswith("[REDACTED:")
    assert sanitized["password"].startswith("[REDACTED:")
    assert sanitized["parameters"]["token"].startswith("[REDACTED:")
    assert sanitized["parameters"]["symbol"] == "EURUSD"
    assert sanitized["parameters"]["nested_list"][0]["auth_bearer"].startswith(
        "[REDACTED:"
    )
    assert sanitized["parameters"]["nested_list"][1]["safe_param"] == 42
    assert sanitized["parameters"]["nested_list"][2].startswith("[REDACTED:")


# -----------------------------------------------------------------------------
# 6. User Code Execution Bounds & AST Validation
# -----------------------------------------------------------------------------


def test_validate_user_code_ast_valid() -> None:
    """Verify compliant user script passes AST validation."""
    code = """
import math

def calculate(x, y):
    return math.sqrt(x ** 2 + y ** 2)
"""
    validate_user_code_ast(code)


def test_validate_user_code_ast_forbidden_imports() -> None:
    """Verify dangerous module imports raise SecurityError."""
    forbidden_codes = [
        "import subprocess\nsubprocess.run(['dir'])",
        "import socket\ns = socket.socket()",
        "from ctypes import c_int",
        "import urllib.request",
        "from http.server import HTTPServer",
    ]

    for snippet in forbidden_codes:
        with pytest.raises(SecurityError, match="prohibited without distinct"):
            validate_user_code_ast(snippet)


def test_validate_user_code_syntax_error() -> None:
    """Verify syntax error in user code raises SecurityError."""
    with pytest.raises(SecurityError, match="User code syntax error"):
        validate_user_code_ast("def broken_syntax(")


# -----------------------------------------------------------------------------
# 7. Distribution Qualification & TLS Remote Proposal
# -----------------------------------------------------------------------------


def test_clean_installation_verification(tmp_path: Path) -> None:
    """Verify clean installation detector checks directory baseline and leaks."""
    base = tmp_path / "haru_install"
    base.mkdir()

    # Missing directories initially
    res1 = verify_clean_installation(base)
    assert not res1.is_clean
    assert "data" in res1.missing_paths

    # Create expected directories
    for d in ["data", "logs", "config"]:
        (base / d).mkdir()

    res2 = verify_clean_installation(base)
    assert res2.is_clean
    assert len(res2.verified_paths) == 3

    # Introduce leaked test file
    leak_file = base / "data" / "leaked_test.db"
    leak_file.write_text("corrupted", encoding="utf-8")

    res3 = verify_clean_installation(base)
    assert not res3.is_clean
    assert len(res3.leaked_artifacts) == 1


def test_domain_removal_verification(tmp_path: Path) -> None:
    """Verify domain removal checks session revocation and CAS artifact retention."""
    base = tmp_path / "workspace"
    cas_dir = base / "data" / "resources"
    cas_dir.mkdir(parents=True)

    # Create simulated immutable CAS artifact
    art = cas_dir / "art1.bin"
    art.write_bytes(b"retained immutable data")

    mgr = SessionManager()
    mgr.create_session("plugin:indicator_pack")
    assert mgr.active_session_count() == 1

    result = verify_domain_removal(
        domain_id="indicator_pack",
        base_dir=base,
        session_manager=mgr,
    )
    assert result.domain_id == "indicator_pack"
    assert result.sessions_revoked == 1
    assert result.cas_artifacts_preserved == 1
    assert result.unrelated_data_intact
    assert mgr.active_session_count() == 0


def test_tls_remote_deployment_proposal() -> None:
    """Verify TLS remote deployment specification attributes."""
    proposal = get_tls_remote_deployment_proposal()
    assert proposal.local_binding == "127.0.0.1:8000"
    assert "Reverse-Proxy" in proposal.recommended_topology
    assert "TLS v1.3" in proposal.tls_termination
    assert len(proposal.network_isolation_notes) >= 4


# -----------------------------------------------------------------------------
# 8. FastAPI REST Endpoints & Bearer Token Dependency
# -----------------------------------------------------------------------------


def test_sessions_router_endpoints(tmp_path: Path) -> None:
    """Verify REST endpoints for sessions, elevation, scope checks, and distribution."""
    mgr = SessionManager(host_instance_id="host-test")
    auth = ScopeAuthorizer()
    coord = DistinctAuthorityCoordinator()

    app = FastAPI()
    from app.host.settings import HostSettings

    settings = HostSettings(tmp_path / "session-login.db")
    settings.update(
        {
            "user_access": {
                "username": "trader_1",
                "password_hash": hash_password("test-password"),
            }
        }
    )
    router = create_sessions_router(mgr, auth, coord, HostAuthentication(settings, mgr))
    app.include_router(router)
    client = TestClient(app)

    # 1. Login
    resp_login = client.post("/sessions/login", json={"password": "test-password"})
    assert resp_login.status_code == 200
    login_data = resp_login.json()["data"]
    token = login_data["token"]
    assert login_data["username"] == "trader_1"

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Me
    resp_me = client.get("/sessions/me", headers=headers)
    assert resp_me.status_code == 200
    assert resp_me.json()["data"]["username"] == "trader_1"

    # 3. Verify standard scope
    resp_scope = client.post(
        "/sessions/verify-scope",
        headers=headers,
        json={"scope": "jobs:read"},
    )
    assert resp_scope.status_code == 200
    assert resp_scope.json()["data"]["allowed"]

    # 4. Elevate dangerous scope
    resp_elev = client.post(
        "/sessions/elevate",
        headers=headers,
        json={
            "scope": "live_trading:execute",
            "reason": "Live session authorization",
            "confirmation_phrase": "CONFIRM:live_trading:execute",
            "ttl_seconds": 600,
        },
    )
    assert resp_elev.status_code == 200
    assert resp_elev.json()["data"]["scope"] == "live_trading:execute"

    # 5. Clean install check
    resp_clean = client.get("/sessions/distribution/clean-install-check")
    assert resp_clean.status_code == 200

    # 6. Domain removal check
    resp_removal = client.post(
        "/sessions/distribution/domain-removal-check?domain_id=test_pack"
    )
    assert resp_removal.status_code == 200
    assert resp_removal.json()["data"]["domain_id"] == "test_pack"

    # 7. TLS proposal
    resp_tls = client.get("/sessions/tls-proposal")
    assert resp_tls.status_code == 200
    assert resp_tls.json()["data"]["local_binding"] == "127.0.0.1:8000"

    # 8. Revoke
    resp_rev = client.post("/sessions/revoke", headers=headers)
    assert resp_rev.status_code == 200
    assert resp_rev.json()["data"]["revoked"]

    # Subsequent /me call fails
    resp_me_revoked = client.get("/sessions/me", headers=headers)
    assert resp_me_revoked.status_code == 401


def test_bearer_token_dependency_extraction() -> None:
    """Verify extract_bearer_token header validation."""
    with pytest.raises(HTTPException) as exc1:
        extract_bearer_token(None)
    assert exc1.value.status_code == 401

    with pytest.raises(HTTPException) as exc2:
        extract_bearer_token("Basic dXNlcjpwYXNz")
    assert exc2.value.status_code == 401

    assert extract_bearer_token("Bearer secret_tok") == "secret_tok"


def test_get_current_session_dependency() -> None:
    """Verify get_current_session dependency behavior."""
    mgr = SessionManager()
    session = mgr.create_session("alice")

    resolved = get_current_session(token=session.token, mgr=mgr)
    assert resolved.username == "alice"

    with pytest.raises(HTTPException) as exc:
        get_current_session(token="invalid", mgr=mgr)
    assert exc.value.status_code == 401


# -----------------------------------------------------------------------------
# 10. CLI Entrypoint
# -----------------------------------------------------------------------------


def test_cli_entrypoint() -> None:
    """Verify sessions CLI tool executes requested commands cleanly."""
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0

    assert main([]) == 0
    assert main(["--audit-scopes"]) == 0
    assert main(["--tls-proposal"]) == 0
    # Clean install on repository root
    rc = main(["--check-install"])
    assert rc in (0, 1)


@pytest.fixture
def configured_auth(tmp_path: Path) -> HostAuthentication:
    """One isolated configured host user, with no plaintext storage."""
    from app.host.settings import HostSettings

    settings = HostSettings(tmp_path / "auth.db")
    settings.update(
        {
            "user_access": {
                "username": "configured-user",
                "password_hash": hash_password("test-password"),
            }
        }
    )
    return HostAuthentication(settings, SessionManager(host_instance_id="test-host"))


def test_password_verifier_and_secret_representation() -> None:
    """Verifier is salted, bounded and rejects wrong/malformed credentials."""
    encoded = hash_password("test-password")
    assert encoded != hash_password("test-password")
    assert "test-password" not in encoded
    assert verify_password("test-password", encoded)
    assert not verify_password("wrong", encoded)
    assert not verify_password("", encoded)
    assert not verify_password("x" * 1025, encoded)
    for malformed in [
        "plaintext",
        encoded.replace("600000", "999999999"),
        "pbkdf2-sha256$600000$" + "z" * 32 + "$" + "z" * 64,
    ]:
        assert not verify_password("test-password", malformed)
    assert "test-password" not in repr(LoginRequest(password="test-password"))
    with pytest.raises(ValueError):
        hash_password("")


def test_authentication_identity_changes_and_cooldown(
    configured_auth: HostAuthentication, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only configured operator credentials mint tokens; changes revoke authority."""
    auth = configured_auth
    issued = auth.authenticate(LoginRequest(password="test-password"))
    assert issued.username == "configured-user"
    assert issued.host_instance_id == "test-host"
    assert auth.verify_session(issued.token).role == RoleType.OPERATOR
    for request in [
        LoginRequest(password="wrong"),
        LoginRequest(password="test-password", username="other-user"),
        LoginRequest(password="test-password", role=RoleType.SYSTEM),
    ]:
        with pytest.raises(AuthenticationError):
            auth.authenticate(request)
    auth.settings.update(
        {"user_access": {"password_hash": hash_password("replacement-password")}}
    )
    with pytest.raises(AuthenticationError):
        auth.verify_session(issued.token)
    for _ in range(2):
        with pytest.raises(AuthenticationError):
            auth.authenticate(LoginRequest(password="wrong"))
    with pytest.raises(LoginCooldownError):
        auth.authenticate(LoginRequest(password="replacement-password"))
    monkeypatch.setattr(
        "app.host.session.time.monotonic", lambda: auth._window_start + 61
    )
    new_session = auth.authenticate(LoginRequest(password="replacement-password"))
    assert auth.verify_session(new_session.token).username == "configured-user"


def test_missing_account_fails_closed(tmp_path: Path) -> None:
    """Missing credential setup issues no HTTP-capable session."""
    from app.host.settings import HostSettings

    auth = HostAuthentication(HostSettings(tmp_path / "missing.db"), SessionManager())
    with pytest.raises(AuthenticationError):
        auth.authenticate(LoginRequest(password="any-password"))
    assert not auth.manager._sessions


def test_local_account_setup_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Local setup stores hashes only and requires confirmation for replacement."""
    from app.host.settings import HostSettings

    path = tmp_path / "account.db"
    answers = iter(["test-password", "test-password"])
    monkeypatch.setattr("app.host.session.getpass.getpass", lambda _: next(answers))
    assert (
        main(["--configure-user", "--username", "configured-user", "--db", str(path)])
        == 0
    )
    account = HostSettings(path).get_snapshot().values["application"]["user_access"]
    assert account["username"] == "configured-user"
    assert "password" not in account
    assert verify_password("test-password", account["password_hash"])
    monkeypatch.setattr("builtins.input", lambda _: "CANCEL")
    assert (
        main(["--configure-user", "--username", "replacement", "--db", str(path)]) == 1
    )
    assert (
        HostSettings(path).get_snapshot().values["application"]["user_access"]
        == account
    )
    monkeypatch.setattr("builtins.input", lambda _: "REPLACE")
    answers = iter(["replacement-password", "does-not-match"])
    assert (
        main(["--configure-user", "--username", "replacement", "--db", str(path)]) == 2
    )
    assert (
        HostSettings(path).get_snapshot().values["application"]["user_access"]
        == account
    )


def test_credential_logging_has_no_payload(
    configured_auth: HostAuthentication, caplog: pytest.LogCaptureFixture
) -> None:
    """Credential capability logs outcomes without passwords, hashes or tokens."""
    import logging

    caplog.set_level(logging.DEBUG)
    issued = configured_auth.authenticate(LoginRequest(password="test-password"))
    with pytest.raises(AuthenticationError):
        configured_auth.authenticate(LoginRequest(password="wrong-password"))
    text = caplog.text
    assert "Login authenticated" in text and "Login rejected" in text
    assert "test-password" not in text and "wrong-password" not in text
    assert issued.token not in text
    assert (
        configured_auth.settings.get_snapshot().values["application"]["user_access"][
            "password_hash"
        ]
        not in text
    )


def test_default_session_remains_valid_for_24_hours_without_extending_expiry() -> None:
    """Verification retains the issued expiry and rejects the token after 24 hours."""
    from datetime import UTC, datetime, timedelta
    from unittest.mock import patch

    start = datetime(2026, 10, 9, tzinfo=UTC)
    with patch("app.host.session.datetime", wraps=datetime) as clock:
        clock.now.return_value = start
        manager = SessionManager()
        session = manager.create_session(username="ttl-test")
        expiry = session.expires_at
        assert datetime.fromisoformat(expiry) - start == timedelta(hours=24)
        clock.now.return_value = start + timedelta(hours=23, minutes=59, seconds=59)
        assert manager.verify_session(session.token).expires_at == expiry
        clock.now.return_value = start + timedelta(hours=24, seconds=1)
        with pytest.raises(SessionExpiredError):
            manager.verify_session(session.token)


def test_account_change_verifies_password_and_revokes_sessions(tmp_path: Path) -> None:
    """Account UI changes preserve verifier privacy and require a fresh login."""
    from app.host.settings import HostSettings

    target = HostSettings(tmp_path / "account.db")
    target.update(
        {
            "user_access": {
                "username": "original",
                "password_hash": hash_password("old-synthetic-password"),
            }
        }
    )
    manager = SessionManager()
    authentication = HostAuthentication(target, manager)
    session = authentication.authenticate(
        LoginRequest(password="old-synthetic-password")
    )
    app = FastAPI()
    app.include_router(create_auth_router(authentication))
    headers = {"authorization": f"Bearer {session.token}"}
    with TestClient(app) as client:
        assert client.get("/auth/account").status_code == 401
        account = client.get("/auth/account", headers=headers).json()["data"]
        assert account["username"] == "original"
        assert account["session_timeout_mins"] == 1440
        request = {
            "expected_revision": account["revision"],
            "username": "replacement",
            "session_timeout_mins": 2880,
            "current_password": "wrong-synthetic-password",
            "new_password": "new-synthetic-password",
        }
        before = target.get_snapshot()
        assert (
            client.put("/auth/account", headers=headers, json=request).status_code
            == 403
        )
        assert target.get_snapshot() == before
        authentication.verify_session(session.token)
        request["current_password"] = "old-synthetic-password"
        saved = client.put("/auth/account", headers=headers, json=request)
        assert saved.status_code == 200
        assert "synthetic-password" not in saved.text
        assert saved.json()["data"]["reauthenticate"] is True
        assert client.get("/auth/account", headers=headers).status_code == 401
        new_session = authentication.authenticate(
            LoginRequest(password="new-synthetic-password")
        )
        assert new_session.username == "replacement"
        from datetime import datetime

        assert (
            datetime.fromisoformat(new_session.expires_at)
            - datetime.fromisoformat(new_session.created_at)
        ).total_seconds() >= 172800
        with pytest.raises(AuthenticationError):
            authentication.authenticate(LoginRequest(password="old-synthetic-password"))


@pytest.mark.parametrize("channel", ["ui", "cli"])
def test_session_channels_record_hashed_tokens(tmp_path: Path, channel: str) -> None:
    """HTTP login and trusted CLI/Python issuance use the same singular store."""
    import hashlib

    from app.host.persistence import DatabaseManager, HostSessionStore
    from app.host.session import SessionTokenManager
    from app.host.settings import HostSettings

    path = tmp_path / "recorded.db"
    settings = HostSettings(path)
    settings.update(
        {
            "user_access": {
                "username": "test",
                "password_hash": hash_password("synthetic-password"),
            }
        }
    )
    store = HostSessionStore(DatabaseManager(path))
    mgr = SessionManager(host_instance_id="issuer", store=store)
    if channel == "ui":
        authentication = HostAuthentication(settings, mgr)
        app = FastAPI()
        app.include_router(create_auth_router(authentication))
        with TestClient(app) as client:
            assert (
                client.post("/auth/login", json={"password": "invalid"}).status_code
                == 401
            )
            assert store.list_records(peer_id="issuer") == []
            response = client.post(
                "/auth/login", json={"password": "synthetic-password"}
            )
            assert response.status_code == 200
            token = response.json()["data"]["token"]
            assert (
                client.get(
                    "/auth/status", headers={"Authorization": "Bearer " + token}
                ).status_code
                == 200
            )
            assert (
                client.get(
                    "/auth/status", headers={"Authorization": "Bearer " + token}
                ).status_code
                == 200
            )
    else:
        token = SessionTokenManager(manager=mgr).create_token("test").token
    rows = store.list_records(peer_id="issuer")
    assert len(rows) == 1
    assert rows[0].token_hash == hashlib.sha256(token.encode()).hexdigest()
    assert token not in str(rows[0].model_dump())
    assert rows[0].status == "ACTIVE"
    assert rows[0].revoked_at_utc is None
    assert rows[0].username == "test"
    assert rows[0].expires_at_utc == mgr.verify_session(token).expires_at
    mgr.revoke_session(token)
    revoked = store.list_records(peer_id="issuer")[0]
    assert revoked.status == "REVOKED" and revoked.revoked_at_utc is not None


def test_session_records_expiry_and_issuer_isolation(tmp_path: Path) -> None:
    from app.host.persistence import DatabaseManager, HostSessionStore

    store = HostSessionStore(DatabaseManager(tmp_path / "lifecycle.db"))
    first = SessionManager(host_instance_id="one", store=store)
    second = SessionManager(host_instance_id="two", store=store)
    expired = first.create_session("test", ttl_sec=-1)
    with pytest.raises(SessionExpiredError):
        first.verify_session(expired.token)
    assert store.list_records(peer_id="one")[0].status == "EXPIRED"
    first.create_session("test")
    active = second.create_session("test")
    assert first.revoke_user("test") == 1
    assert second.verify_session(active.token)
    assert store.list_records(peer_id="two")[0].status == "ACTIVE"
    second.reset(new_host_instance_id="three")
    assert store.list_records(peer_id="two")[0].status == "REVOKED"
    assert len(store.list_records(peer_id="one")) == 2
    fresh = SessionManager(host_instance_id="two", store=store)
    with pytest.raises(AuthenticationError):
        fresh.verify_session(active.token)


def test_session_persistence_failure_does_not_issue_or_retain_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.host.persistence import DatabaseManager, HostSessionStore, PersistenceError

    store = HostSessionStore(DatabaseManager(tmp_path / "failure.db"))
    mgr = SessionManager(host_instance_id="failure", store=store)

    def fail(*args: Any, **kwargs: Any) -> None:
        raise PersistenceError("synthetic storage failure")

    with monkeypatch.context() as patcher:
        patcher.setattr(store, "create", fail)
        with pytest.raises(PersistenceError):
            mgr.create_session("test")
    assert mgr.active_session_count() == 0
    assert store.list_records(peer_id="failure") == []
    active = mgr.create_session("test")
    with monkeypatch.context() as patcher:
        patcher.setattr(store, "update_status", fail)
        with pytest.raises(PersistenceError):
            mgr.revoke_session(active.token)
    with pytest.raises(AuthenticationError):
        mgr.verify_session(active.token)
    mgr.reset()
    assert store.list_records(peer_id="failure")[0].status == "REVOKED"


def test_login_storage_failure_returns_safe_unavailable(
    configured_auth: HostAuthentication, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.host.persistence import PersistenceError

    app = FastAPI()
    app.include_router(create_auth_router(configured_auth))

    def fail(*args: Any, **kwargs: Any) -> None:
        raise PersistenceError("private database details")

    monkeypatch.setattr(configured_auth.manager, "create_session", fail)
    with TestClient(app) as client:
        response = client.post("/auth/login", json={"password": "test-password"})
        assert response.status_code == 503
        assert "private database details" not in response.text
        assert "token" not in (response.json().get("data") or {})
