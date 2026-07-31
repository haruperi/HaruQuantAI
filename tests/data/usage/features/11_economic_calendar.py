"""FEAT-DATA-11: acquire and display genuine licensed calendar evidence."""

from __future__ import annotations

import asyncio
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_calendar_scrape_provider,
    build_data_settings,
    build_economic_event,
    build_economic_event_store,
    build_event_impact,
    build_firecrawl_calendar_transport,
    build_market_context_evidence,
    build_scrape_options,
    build_scrape_result,
    calendar_state_provenance,
    data_settings_context,
    derive_calendar_state,
    deserialize_scrape_result,
    evaluate_calendar_state,
    from_row,
    get_calendar_sites,
    get_calendar_value_field,
    get_default_minimum_impact,
    get_economic_events,
    get_persisted_events,
    get_symbol_economic_events,
    get_symbol_event_profile,
    get_symbol_event_profiles,
    is_news_restricted,
    is_news_restricted_events,
    persist_economic_events,
    populate_market_context_calendar,
    project_calendar_state,
    project_economic_event,
    run_data_migrations,
    save_scrape_result,
    scrape_economic_calendar,
    scrape_result_to_dataframe,
    serialize_scrape_result,
    unwrap_data_response,
)
from app.utils import generate_id


def _unwrap(response: object) -> object:
    """Return one successful Data response payload."""
    return unwrap_data_response(
        response,
        operation="data.economic_calendar.usage",
        request_id=generate_id("req"),
    )


def _current_provider_week(now: datetime) -> tuple[datetime, datetime]:
    """Return the current Sunday-anchored provider week in UTC."""
    sunday = (now - timedelta(days=(now.weekday() + 1) % 7)).replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return sunday, sunday + timedelta(days=7)


def _rebuild_real_event(projected: dict[str, object]) -> object:
    """Exercise the event constructors using one genuine normalized row."""
    impact_value = {"low": 1, "medium": 2, "high": 3}[str(projected["impact"])]
    impact = build_event_impact(impact_value)

    def decimal_value(field: str) -> Decimal | None:
        value = projected[field]
        return None if value is None else Decimal(str(value))

    return build_economic_event(
        id=str(projected["provider_event_id"]),
        provider=str(projected["provider"]),
        name=str(projected["name"]),
        category=projected["category"],
        country=projected["country"],
        currency=projected["currency"],
        scheduled_at=datetime.fromisoformat(str(projected["scheduled_at"])),
        impact=impact,
        actual=decimal_value("actual"),
        forecast=decimal_value("forecast"),
        previous=decimal_value("previous"),
        revised_previous=decimal_value("revised_previous"),
        actual_raw=projected["actual_raw"],
        forecast_raw=projected["forecast_raw"],
        previous_raw=projected["previous_raw"],
        unit=projected["unit"],
        source=projected["source"],
        source_url=projected["source_url"],
        updated_at=(
            None
            if projected["updated_at"] is None
            else datetime.fromisoformat(str(projected["updated_at"]))
        ),
    )


def _acquire_real_calendar(
    transport: object,
    start: datetime,
    end: datetime,
) -> object:
    """Acquire, display, and round-trip genuine multi-site provider rows."""
    sites = get_calendar_sites()
    options = build_scrape_options(
        start=start,
        end=end,
        sites=sites,
        max_parallel_tasks=2,
        request_id=generate_id("req"),
        transport=transport,
    )
    result = scrape_economic_calendar(options)
    frame = scrape_result_to_dataframe(result)
    if frame.empty:
        raise RuntimeError("Licensed calendar acquisition returned no real events")

    print("Genuine licensed multi-site calendar rows (bounded to 25):")
    print(frame.head(25).to_string(index=False))
    print("\nReal rows by source:")
    print(frame.groupby("site").size().rename("event_count").to_string())
    skipped = get_calendar_value_field(result, "skipped")
    print("Provider failures:", dict(skipped))  # type: ignore[arg-type]

    reconstructed = build_scrape_result(
        events=get_calendar_value_field(result, "events"),
        sites=get_calendar_value_field(result, "sites"),
        start=get_calendar_value_field(result, "start"),
        end=get_calendar_value_field(result, "end"),
        scraped_at=get_calendar_value_field(result, "scraped_at"),
        skipped=skipped,
    )
    round_trip = deserialize_scrape_result(serialize_scrape_result(reconstructed))
    print(
        "Trusted serialization round-trip rows:",
        len(scrape_result_to_dataframe(round_trip)),
    )
    return result


def _normalize_real_calendar(
    transport: object,
    start: datetime,
    end: datetime,
) -> tuple[object, list[object], list[object], list[dict[str, object]]]:
    """Normalize genuine ForexFactory rows through provider-neutral APIs."""
    provider = build_calendar_scrape_provider(
        transport,
        sites=("forexfactory",),
        max_parallel_tasks=1,
        request_id=generate_id("req"),
    )
    normalized = _unwrap(
        asyncio.run(get_economic_events(start, end, provider=provider))
    )
    eurusd = _unwrap(
        asyncio.run(
            get_symbol_economic_events(
                "EURUSD",
                start,
                end,
                provider=provider,
            )
        )
    )
    if not isinstance(normalized, list) or not isinstance(eurusd, list) or not eurusd:
        raise RuntimeError("Real provider rows did not normalize for EURUSD")

    projections = [project_economic_event(event) for event in eurusd[:20]]
    print("\nNormalized real EURUSD-relevant events (bounded to 20):")
    for projection in projections:
        print(projection)
    print("Normalized total events:", len(normalized))
    print("EURUSD-relevant events:", len(eurusd))

    profile = _unwrap(get_symbol_event_profile("EURUSD"))
    print(
        "EURUSD relevance profile:",
        {
            "currencies": sorted(get_calendar_value_field(profile, "currencies")),
            "countries": sorted(get_calendar_value_field(profile, "countries")),
        },
    )
    print("Registered symbols:", sorted(get_symbol_event_profiles()))
    print("Default minimum impact:", get_default_minimum_impact())
    rebuilt_event = _rebuild_real_event(projections[0])
    row_projection = project_economic_event(rebuilt_event)
    restored = _unwrap(
        from_row(
            {
                "provider": row_projection["provider"],
                "provider_event_id": row_projection["provider_event_id"],
                "name": row_projection["name"],
                "category": row_projection["category"],
                "country": row_projection["country"],
                "currency": row_projection["currency"],
                "scheduled_at": row_projection["scheduled_at"],
                "actual": row_projection["actual"],
                "forecast": row_projection["forecast"],
                "previous": row_projection["previous"],
                "revised_previous": row_projection["revised_previous"],
                "actual_raw": row_projection["actual_raw"],
                "forecast_raw": row_projection["forecast_raw"],
                "previous_raw": row_projection["previous_raw"],
                "unit": row_projection["unit"],
                "source": row_projection["source"],
                "source_url": row_projection["source_url"],
                "impact": {"low": 1, "medium": 2, "high": 3}[
                    str(row_projection["impact"])
                ],
                "updated_at": row_projection["updated_at"],
            }
        )
    )
    print("Stored-row reconstruction:", project_economic_event(restored))
    return provider, normalized, eurusd, projections


def _show_risk_handoff(
    provider: object,
    eurusd: list[object],
    projections: list[dict[str, object]],
) -> None:
    """Display and cross-check pure and provider-backed restriction evidence."""
    candidate = next(
        (
            event
            for event in eurusd
            if get_calendar_value_field(event, "impact") == build_event_impact(3)
            and get_calendar_value_field(event, "source") == "forexfactory"
        ),
        eurusd[0],
    )
    candidate_at = get_calendar_value_field(candidate, "scheduled_at")
    candidate_impact = get_calendar_value_field(candidate, "impact")
    if not isinstance(candidate_at, datetime):
        raise TypeError("Normalized event timestamp is unavailable")

    state = _unwrap(
        derive_calendar_state(
            "EURUSD",
            candidate_at,
            events=eurusd,
            minimum_impact=candidate_impact,
            evidence_ref=str(projections[0]["provider_event_id"]),
        )
    )
    print("\nRisk-ready state at a genuine release:")
    print(project_calendar_state(state))
    print("Risk provenance:", _unwrap(calendar_state_provenance(state)))
    pure_state = _unwrap(
        evaluate_calendar_state(
            eurusd,
            candidate_at,
            minimum_impact=candidate_impact,
        )
    )
    pure_restriction = _unwrap(
        is_news_restricted_events(
            eurusd,
            candidate_at,
            minimum_impact=candidate_impact,
        )
    )
    provider_restriction = _unwrap(
        asyncio.run(
            is_news_restricted(
                "EURUSD",
                candidate_at,
                provider=provider,
                minimum_impact=candidate_impact,
            )
        )
    )
    if pure_restriction is not True or provider_restriction is not True:
        raise RuntimeError("Provider-backed restriction disagrees with real event data")
    print("Pure calendar state:", pure_state)
    print("Pure restriction flag:", pure_restriction)
    print("Provider-backed restriction flag:", provider_restriction)

    evidence = build_market_context_evidence(
        symbol="EURUSD",
        session_state="open",
        calendar_state=None,
        spread=Decimal("0.00010"),
        spread_unit="price",
        liquidity=Decimal(1),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=candidate_at,
        expires_at=candidate_at + timedelta(minutes=1),
        provenance={"source": "licensed-calendar-usage"},
        missing_fields=("calendar",),
        request_id=generate_id("req"),
    )
    populated = _unwrap(
        populate_market_context_calendar(
            evidence,
            events=eurusd,
            minimum_impact=candidate_impact,
            evidence_ref=str(projections[0]["provider_event_id"]),
        )
    )
    print(
        "Populated market-context calendar state:",
        get_calendar_value_field(populated, "calendar_state"),
    )
    print(
        "Populated market-context missing fields:",
        get_calendar_value_field(populated, "missing_fields"),
    )


def _show_persistence(
    result: object,
    normalized: list[object],
    start: datetime,
    end: datetime,
) -> None:
    """Persist genuine rows and display the read-back and artifact evidence."""
    with tempfile.TemporaryDirectory(prefix="data-calendar-") as directory:
        root = Path(directory)
        settings = build_data_settings(
            database_url="sqlite:///calendar.db",
            data_dir=root,
            sqlite_busy_timeout_seconds=1.0,
            write_lock_lease_seconds=10.0,
            approved_storage_roots=(root,),
        )
        with data_settings_context(settings):
            _unwrap(run_data_migrations(generate_id("req")))
            store = build_economic_event_store()
            written = _unwrap(
                persist_economic_events(
                    normalized,
                    store=store,
                    request_id=generate_id("req"),
                )
            )
            persisted = _unwrap(
                get_persisted_events(
                    start,
                    end,
                    store=store,
                    currencies=("EUR", "USD"),
                    request_id=generate_id("req"),
                )
            )
            save_scrape_result(result, root, "csv")
            artifacts = tuple(sorted(path.name for path in root.glob("*.csv")))
        print("\nPersistence evidence:")
        print("Rows upserted:", written)
        print("EURUSD-relevant rows read:", len(persisted))
        print("Saved non-empty artifacts:", artifacts)


def main() -> None:
    """Run genuine acquisition, normalization, storage, and Risk handoff."""
    start, end = _current_provider_week(datetime.now(UTC))
    transport = build_firecrawl_calendar_transport(max_parallel_requests=2)
    result = _acquire_real_calendar(transport, start, end)
    provider, normalized, eurusd, projections = _normalize_real_calendar(
        transport,
        start,
        end,
    )
    _show_risk_handoff(provider, eurusd, projections)
    _show_persistence(result, normalized, start, end)


if __name__ == "__main__":
    main()
