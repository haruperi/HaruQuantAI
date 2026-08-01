"""Agentic namespace construction for durable runtime records."""

from collections.abc import Callable, Mapping

from app.services.data.runtime_stores.codecs import build_runtime_store

type _Codec = tuple[Callable[[object], str], Callable[[str], object]]


def build_agentic_runtime_store(codecs: Mapping[str, _Codec]) -> object:
    """Build an opaque Agentic runtime-record handle.

    Returns:
        Namespaced Data-owned handle.
    """
    return build_runtime_store("agentic", codecs)


__all__ = ("build_agentic_runtime_store",)
