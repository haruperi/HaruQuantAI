"""Unit tests for the Analytics migration manifest boundary."""

from types import SimpleNamespace

from app.services.analytics.migrations import definitions


def test_runner_submits_complete_manifest_once(monkeypatch) -> None:
    """Delegate the exact complete manifest once through Data."""
    captured = []

    def run(request):
        captured.append(request)
        return SimpleNamespace(status="success", data=object())

    monkeypatch.setattr(definitions, "run_domain_migrations", run)
    response = definitions.run_analytics_migrations(
        "req-00000000-0000-4000-8000-000000000060"
    )
    assert response.status == "success"
    assert len(captured) == 1
    request = captured[0]
    assert request.domain == "analytics"
    assert request.complete_manifest is True
    assert tuple(request.steps) == definitions.ANALYTICS_MIGRATIONS
    assert [step.migration_id for step in request.steps] == [
        "001_analytics_schema_v1",
        "002_retire_unused_analytics_derived_store",
        "003_player_evidence_schema",
    ]
