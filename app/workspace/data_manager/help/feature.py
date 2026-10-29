"""Data Manager contextual help, tutorials, and documentation articles."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from app.core.host.persistence import HostPersistence
from app.core.lib.responses import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)

from ._helpers import (
    _DONOR_ARTICLES,
    _MAX_NOTE_LENGTH,
    _TOPIC_OVERVIEW,
    _TOPICS,
    _TUTORIALS,
)

__all__ = ["Help"]


class Help:
    """Contextual guidance, donor links, and tutorials for Data Manager."""

    def __init__(
        self,
        persistence: HostPersistence | None = None,
        *,
        logs: Any | None = None,
    ) -> None:
        self.gateway = persistence
        self.logs = logs
        self._user_notes: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    @staticmethod
    def _result(
        operation: str,
        started: float,
        data: Any = None,
        *,
        error: str = "",
        code: ErrorCode = ErrorCode.VALIDATION,
    ) -> dict[str, Any]:
        duration_ms = (time.perf_counter() - started) * 1000
        metadata = ResponseMetadata(
            operation=f"help.{operation}",
            duration_ms=duration_ms,
        )
        if error:
            return StandardResponse.failure(
                message=error,
                metadata=metadata,
                error=StandardError(code=code, message=error),
            )
        return StandardResponse.success(
            message="Data Manager help operation completed",
            metadata=metadata,
            data=data,
        )

    def get_topic(self, topic: str = _TOPIC_OVERVIEW) -> dict[str, Any]:
        """Return the contextual HelpGuidePayload for a given topic."""
        started = time.perf_counter()
        normalized = (topic or _TOPIC_OVERVIEW).strip().lower()
        if normalized not in _TOPICS:
            normalized = _TOPIC_OVERVIEW

        definition = _TOPICS[normalized]
        available_topics = list(_TOPICS.keys())

        tutorials = [
            t
            for t in _TUTORIALS
            if t.get("topic") == normalized or normalized == "overview"
        ]
        if not tutorials:
            tutorials = [t for t in _TUTORIALS if t.get("test_id")]

        articles = [
            a
            for a in _DONOR_ARTICLES
            if a.get("topic") == normalized or normalized == "overview"
        ]
        if not articles:
            articles = _DONOR_ARTICLES

        with self._lock:
            note_entry = self._user_notes.get(normalized)
            note = note_entry.get("note") if note_entry else None

        payload = {
            "topic": normalized,
            "title": definition["title"],
            "summary": definition["summary"],
            "tab": definition["tab"],
            "available_topics": available_topics,
            "key_capabilities": definition.get("key_capabilities", []),
            "tutorials": tutorials,
            "links": articles,
            "user_note": note,
        }
        return self._result("get_topic", started, data=payload)

    def list_topics(self) -> dict[str, Any]:
        """Return a catalog of all supported Data Manager topics."""
        started = time.perf_counter()
        items = [
            {
                "topic": key,
                "title": value["title"],
                "tab": value["tab"],
                "summary": value["summary"],
                "key_capabilities": value.get("key_capabilities", []),
            }
            for key, value in _TOPICS.items()
        ]
        return self._result(
            "list_topics", started, data={"topics": items, "count": len(items)}
        )

    def list_articles(self, topic: str | None = None) -> dict[str, Any]:
        """Return StrategyQuant X donor help articles, optionally filtered."""
        started = time.perf_counter()
        norm = topic.strip().lower() if topic else None
        articles = [
            a for a in _DONOR_ARTICLES if norm is None or a.get("topic") == norm
        ]
        return self._result(
            "list_articles",
            started,
            data={"articles": articles, "count": len(articles)},
        )

    def list_tutorials(self, topic: str | None = None) -> dict[str, Any]:
        """Return interactive tutorials, optionally filtered by topic."""
        started = time.perf_counter()
        norm = topic.strip().lower() if topic else None
        tutorials = [t for t in _TUTORIALS if norm is None or t.get("topic") == norm]
        return self._result(
            "list_tutorials",
            started,
            data={"tutorials": tutorials, "count": len(tutorials)},
        )

    def get_tutorial(self, tutorial_id: str) -> dict[str, Any]:
        """Return a single tutorial by ID."""
        started = time.perf_counter()
        clean_id = (tutorial_id or "").strip().lower()
        found = next((t for t in _TUTORIALS if t["id"].lower() == clean_id), None)
        if not found:
            return self._result(
                "get_tutorial",
                started,
                error=f"Tutorial '{tutorial_id}' not found.",
                code=ErrorCode.NOT_FOUND,
            )
        return self._result("get_tutorial", started, data=found)

    def search(self, query: str) -> dict[str, Any]:
        """Search across topics, summaries, tutorials, and articles."""
        started = time.perf_counter()
        clean = (query or "").strip().lower()
        if not clean:
            return self._result(
                "search",
                started,
                error="Search query cannot be empty.",
                code=ErrorCode.VALIDATION,
            )

        matched_topics = [
            {"topic": k, "title": v["title"], "summary": v["summary"]}
            for k, v in _TOPICS.items()
            if clean in k
            or clean in v["title"].lower()
            or clean in v["summary"].lower()
        ]

        matched_tutorials = [
            t
            for t in _TUTORIALS
            if clean in t["id"].lower()
            or clean in t["title"].lower()
            or clean in t["summary"].lower()
            or any(clean in step.lower() for step in t.get("steps", []))
        ]

        matched_articles = [
            a
            for a in _DONOR_ARTICLES
            if clean in a["title"].lower()
            or clean in a["summary"].lower()
            or clean in a["url"].lower()
        ]

        data = {
            "query": query,
            "topics": matched_topics,
            "tutorials": matched_tutorials,
            "articles": matched_articles,
            "total_matches": (
                len(matched_topics) + len(matched_tutorials) + len(matched_articles)
            ),
        }
        return self._result("search", started, data=data)

    def set_topic_note(self, topic: str, note: str) -> dict[str, Any]:
        """Persist a custom user note for a topic."""
        started = time.perf_counter()
        normalized = (topic or "").strip().lower()
        if normalized not in _TOPICS:
            return self._result(
                "set_topic_note",
                started,
                error=f"Topic '{topic}' is not a valid Data Manager topic.",
                code=ErrorCode.NOT_FOUND,
            )
        if len(note) > _MAX_NOTE_LENGTH:
            return self._result(
                "set_topic_note",
                started,
                error="Note cannot exceed 10,000 characters.",
                code=ErrorCode.VALIDATION,
            )

        now = datetime.now(UTC).isoformat()
        with self._lock:
            self._user_notes[normalized] = {"note": note, "updated_at": now}

        return self._result(
            "set_topic_note",
            started,
            data={"topic": normalized, "note": note, "updated_at": now},
        )

    def get_topic_note(self, topic: str) -> dict[str, Any]:
        """Retrieve the persisted user note for a topic."""
        started = time.perf_counter()
        normalized = (topic or "").strip().lower()
        with self._lock:
            entry = self._user_notes.get(normalized)
            note = entry.get("note") if entry else None

        return self._result(
            "get_topic_note", started, data={"topic": normalized, "note": note}
        )

    def reset_defaults(self, topic: str | None = None) -> dict[str, Any]:
        """Clear user notes and reset to built-in guidance."""
        started = time.perf_counter()
        norm = topic.strip().lower() if topic else None
        with self._lock:
            if norm:
                self._user_notes.pop(norm, None)
            else:
                self._user_notes.clear()

        return self._result(
            "reset_defaults",
            started,
            data={"topic": topic or "all", "status": "defaults_restored"},
        )
