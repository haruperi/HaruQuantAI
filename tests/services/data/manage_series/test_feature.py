"""Lifecycle tests for FEAT-DATA-MANAGE_SERIES."""

from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.manage_series.feature import create_feature


class _Context:
    def __init__(self) -> None:
        self.provided: dict[object, object] = {}

    def provide(self, key: object, value: object) -> None:
        self.provided[key] = value


async def test_feature_mount_publishes_declared_capability() -> None:
    feature = create_feature()
    context = _Context()

    await feature.mount(context, {})  # type: ignore[arg-type]

    assert feature.spec.feature_id == "FEAT-DATA-MANAGE_SERIES"
    assert DATA_SERIES_STORE_CAPABILITY in context.provided
