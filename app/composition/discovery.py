"""Feature discovery via entry points and explicit factory registration."""

from __future__ import annotations

import importlib.metadata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from app.kernel.feature import Feature


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Categorized result of one feature-discovery pass."""

    discovered: dict[str, Feature] = field(default_factory=dict)
    missing_targets: dict[str, str] = field(default_factory=dict)
    failed_imports: dict[str, str] = field(default_factory=dict)
    failed_specs: dict[str, str] = field(default_factory=dict)


class FeatureDiscoverer:
    """Discover composable feature factories without crashing the application shell."""

    def __init__(self, entry_point_group: str = "haruquantai.features") -> None:
        """Initialize a discoverer for an entry-point group."""
        self._group = entry_point_group
        self._manual_features: dict[str, Feature | Callable[[], Feature]] = {}

    def register_feature(
        self,
        feature_or_factory: Feature | Callable[[], Feature],
        feature_id: str | None = None,
    ) -> None:
        """Register a feature instance or factory for discovery."""
        if isinstance(feature_or_factory, Feature):
            key = feature_id or feature_or_factory.spec.feature_id
        elif callable(feature_or_factory):
            key = feature_id or getattr(
                feature_or_factory,
                "__name__",
                f"manual_factory_{id(feature_or_factory)}",
            )
        else:
            raise TypeError("Manual feature must satisfy Feature or be callable")
        self._manual_features[str(key)] = feature_or_factory

    def discover(self) -> DiscoveryResult:
        """Discover manual features and installed entry-point features."""
        discovered: dict[str, Feature] = {}
        missing_targets: dict[str, str] = {}
        failed_imports: dict[str, str] = {}
        failed_specs: dict[str, str] = {}

        self._load_manual(discovered, failed_imports, failed_specs)
        self._load_entry_points(
            discovered,
            missing_targets,
            failed_imports,
            failed_specs,
        )
        return DiscoveryResult(
            discovered=discovered,
            missing_targets=missing_targets,
            failed_imports=failed_imports,
            failed_specs=failed_specs,
        )

    def _record_feature(
        self,
        feature: Feature,
        diagnostic_name: str,
        discovered: dict[str, Feature],
        failed_specs: dict[str, str],
    ) -> None:
        feature.spec.validate()
        feature_id = feature.spec.feature_id
        if feature_id in discovered:
            failed_specs[diagnostic_name] = (
                f"Duplicate feature ID '{feature_id}' discovered; the existing "
                "feature was retained and the duplicate was rejected"
            )
            return
        discovered[feature_id] = feature

    def _load_manual(
        self,
        discovered: dict[str, Feature],
        failed_imports: dict[str, str],
        failed_specs: dict[str, str],
    ) -> None:
        for diagnostic_name, item in self._manual_features.items():
            try:
                feature = item() if callable(item) and not isinstance(item, Feature) else item
                if not isinstance(feature, Feature):
                    failed_specs[diagnostic_name] = (
                        "Manual target does not satisfy the Feature protocol"
                    )
                    continue
                self._record_feature(
                    feature,
                    diagnostic_name,
                    discovered,
                    failed_specs,
                )
            except ValueError as error:
                failed_specs[diagnostic_name] = str(error)
            except Exception as error:  # noqa: BLE001
                failed_imports[diagnostic_name] = str(error)

    def _load_entry_points(
        self,
        discovered: dict[str, Feature],
        missing_targets: dict[str, str],
        failed_imports: dict[str, str],
        failed_specs: dict[str, str],
    ) -> None:
        entry_points: Sequence[importlib.metadata.EntryPoint]
        try:
            entry_points = tuple(
                importlib.metadata.entry_points(group=self._group)
            )
        except Exception as error:  # noqa: BLE001
            failed_imports["__entry_points__"] = str(error)
            return

        for entry_point in entry_points:
            diagnostic_name = entry_point.name
            try:
                target = entry_point.load()
                feature = target() if callable(target) else target
                if not isinstance(feature, Feature):
                    failed_specs[diagnostic_name] = (
                        f"Target '{diagnostic_name}' does not satisfy Feature protocol"
                    )
                    continue
                self._record_feature(
                    feature,
                    diagnostic_name,
                    discovered,
                    failed_specs,
                )
            except ModuleNotFoundError as error:
                target_module = entry_point.value.split(":", maxsplit=1)[0]
                if error.name and (
                    error.name == target_module
                    or target_module.startswith(f"{error.name}.")
                ):
                    missing_targets[diagnostic_name] = (
                        f"Entry point module '{target_module}' is missing"
                    )
                else:
                    failed_imports[diagnostic_name] = (
                        f"Feature dependency '{error.name}' missing: {error}"
                    )
            except ValueError as error:
                failed_specs[diagnostic_name] = str(error)
            except Exception as error:  # noqa: BLE001
                failed_imports[diagnostic_name] = str(error)
