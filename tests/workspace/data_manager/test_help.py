"""Unit tests for the Data Manager Help service."""

import pytest
from app.workspace.data_manager.help import Help


@pytest.fixture
def help_service():
    return Help()


def test_get_topic_overview(help_service):
    res = help_service.get_topic("overview")
    assert res["success"] is True
    data = res["data"]
    assert data["topic"] == "overview"
    assert data["title"] == "Data Manager Overview"
    assert data["tab"] == "Home"
    assert len(data["available_topics"]) == 11
    assert "data" in data["available_topics"]
    assert "custom-data" in data["available_topics"]
    assert len(data["tutorials"]) >= 3
    assert len(data["links"]) == 3
    # Check SQX donor test IDs are present
    donor_test_ids = {a["test_id"] for a in data["links"]}
    assert "dm-help-openlink-btn" in donor_test_ids
    assert "dm-help-openlink-btn-2" in donor_test_ids
    assert "dm-help-openlink-btn-3" in donor_test_ids


def test_get_topic_fallback(help_service):
    res = help_service.get_topic("unknown_topic")
    assert res["success"] is True
    assert res["data"]["topic"] == "overview"


def test_get_topic_specific(help_service):
    res = help_service.get_topic("custom-data")
    assert res["success"] is True
    data = res["data"]
    assert data["topic"] == "custom-data"
    assert data["title"] == "External Indicators & COT Data"
    assert data["tab"] == "External indicators"
    assert any("COT" in cap for cap in data["key_capabilities"])


def test_list_topics(help_service):
    res = help_service.list_topics()
    assert res["success"] is True
    topics = res["data"]["topics"]
    assert len(topics) == 11
    assert res["data"]["count"] == 11
    keys = {t["topic"] for t in topics}
    expected = {
        "overview",
        "data",
        "import",
        "export",
        "symbols",
        "sessions",
        "brokers",
        "custom-data",
        "stock-groups",
        "log",
        "chart",
    }
    assert keys == expected


def test_list_articles(help_service):
    res = help_service.list_articles()
    assert res["success"] is True
    articles = res["data"]["articles"]
    assert len(articles) == 3

    # Filter by topic
    res_export = help_service.list_articles("export")
    assert res_export["success"] is True
    assert len(res_export["data"]["articles"]) == 2

    res_import = help_service.list_articles("import")
    assert res_import["success"] is True
    assert len(res_import["data"]["articles"]) == 1
    assert res_import["data"]["articles"][0]["id"] == "historical-data-import"


def test_list_tutorials(help_service):
    res = help_service.list_tutorials()
    assert res["success"] is True
    tutorials = res["data"]["tutorials"]
    assert len(tutorials) >= 6

    res_symbols = help_service.list_tutorials("symbols")
    assert res_symbols["success"] is True
    assert len(res_symbols["data"]["tutorials"]) == 1
    assert res_symbols["data"]["tutorials"][0]["id"] == "symbol-setup"


def test_get_tutorial(help_service):
    res = help_service.get_tutorial("tick-precision-testing")
    assert res["success"] is True
    tut = res["data"]
    assert tut["id"] == "tick-precision-testing"
    assert tut["test_id"] == "dm-help-openlink-btn"
    assert len(tut["steps"]) == 3

    res_missing = help_service.get_tutorial("non-existent")
    assert res_missing["success"] is False
    assert "not found" in res_missing["message"].lower()


def test_search(help_service):
    res = help_service.search("MetaTrader")
    assert res["success"] is True
    data = res["data"]
    assert data["total_matches"] > 0
    assert len(data["articles"]) > 0

    res_empty = help_service.search("")
    assert res_empty["success"] is False


def test_user_notes(help_service):
    # Initially no note
    res_get = help_service.get_topic_note("export")
    assert res_get["success"] is True
    assert res_get["data"]["note"] is None

    # Set note
    res_set = help_service.set_topic_note("export", "Remember to check tick precision.")
    assert res_set["success"] is True
    assert res_set["data"]["note"] == "Remember to check tick precision."

    # Now get_topic reflects note
    res_topic = help_service.get_topic("export")
    assert res_topic["data"]["user_note"] == "Remember to check tick precision."

    # Reset single note
    res_reset = help_service.reset_defaults("export")
    assert res_reset["success"] is True
    assert help_service.get_topic_note("export")["data"]["note"] is None

    # Invalid topic
    res_invalid = help_service.set_topic_note("invalid", "Test note")
    assert res_invalid["success"] is False

    # Oversized note
    res_oversized = help_service.set_topic_note("export", "x" * 10_001)
    assert res_oversized["success"] is False
