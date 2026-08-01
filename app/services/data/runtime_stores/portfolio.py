"""Portfolio namespace construction for durable runtime records."""

from collections.abc import Callable, Mapping

from app.services.data.runtime_stores.codecs import build_runtime_store

type _Codec = tuple[Callable[[object], str], Callable[[str], object]]


def build_portfolio_runtime_store(codecs: Mapping[str, _Codec]) -> object:
    """Build an opaque Portfolio runtime-record handle.

    Returns:
        Namespaced Data-owned handle.
    """
    return build_runtime_store("portfolio", codecs)


__all__ = ("build_portfolio_runtime_store",)
