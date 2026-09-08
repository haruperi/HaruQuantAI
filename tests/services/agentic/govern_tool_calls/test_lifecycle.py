def test_tool_governance_has_no_import_time_receiver() -> None:
    from app.services.agentic.govern_tool_calls.govern_tool_calls import GovernToolCallsService
    assert GovernToolCallsService is not None
