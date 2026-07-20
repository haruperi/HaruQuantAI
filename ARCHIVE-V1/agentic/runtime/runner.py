"""Reusable Google ADK runner helper."""

from __future__ import annotations

import importlib
from collections.abc import AsyncIterator

APP_NAME = "haruquant"
USER_ID = "haruperi"


async def run_agent(agent, prompt: str, session_id: str = "default") -> str:
    """Run an ADK agent and return the final text response."""
    runner_module = importlib.import_module("google.adk.runners")
    sessions_module = importlib.import_module("google.adk.sessions")
    types = importlib.import_module("google.genai.types")

    session_service = sessions_module.InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    runner = runner_module.Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)],
    )

    final_parts: list[str] = []
    events: AsyncIterator = runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    )

    async for event in events:
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                text = getattr(part, "text", None)
                if text:
                    final_parts.append(text)

    return "\n".join(final_parts)
