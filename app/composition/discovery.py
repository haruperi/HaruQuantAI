"""Feature discovery via entry points and factory registration."""

import importlib.metadata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from app.kernel.feature import Feature


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Outcome of a feature discovery pass."""

    discovered: dict[str, Feature] = field(default_factory=dict)
    missing_targets: dict[str, str] = field(default_factory=dict)
    failed_imports: dict[str, str] = field(default_factory=dict)
    failed_specs: dict[str, str] = field(default_factory=dict)


class FeatureDiscoverer:
    """Discover and instantiate composable feature factories."""

    def __init__(self, entry_point_group: str = "haruquantai.features") -> None:
        self._group = entry_point_group
        self._manual_features: dict[str, Feature | Callable[[], Feature]] = {}

    def register_feature(
        self,
        feature_or_factory: Feature | Callable[[], Feature],
        feature_id: str | None = None,
    ) -> None:
        """Register a feature instance or factory for discovery."""
        if isinstance(feature_or_factory, Feature):
            key = feature_or_factory.spec.feature_id
        elif callable(feature_or_factory):
            key = feature_id or getattr(
                feature_or_factory,
                "__name__",
                f"manual_factory_{id(feature_or_factory)}",
            )
        else:
            msg = "feature_or_factory must satisfy Feature or be callable"
            raise TypeError(msg)
        self._manual_features[str(key)] = feature_or_factory

    def discover(self) -> DiscoveryResult:
        """Discover all manual and installed entry-point features."""
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

    def _add_discovered(
        self,
        discovered: dict[str, Feature],
        feature: Feature,
        source_name: str,
        failed_specs: dict[str, str],
    ) -> None:
        feature.spec.validate()
        feature_id = feature.spec.feature_id
        if feature_id in discovered:
            failed_specs[source_name] = (
                f"Duplicate feature ID '{feature_id}' discovered from '{source_name}'"
            )
            return
        discovered[feature_id] = feature

    def _load_manual(
        self,
        discovered: dict[str, Feature],
        failed_imports: dict[str, str],
        failed_specs: dict[str, str],
    ) -> None:
        for registration_key, item in self._manual_features.items():
            try:
                feature = item if isinstance(item, Feature) else item()
                self._add_discovered(
                    discovered,
                    feature,
                    registration_key,
                    failed_specs,
                )
            except ValueError as err:
                failed_specs[registration_key] = str(err)
            except Exception as err:  # noqa: BLE001
                failed_imports[registration_key] = str(err)

    def _load_entry_points(
        self,
        discovered: dict[str, Feature],
        missing_targets: dict[str, str],
        failed_imports: dict[str, str],
        failed_specs: dict[str, str],
    ) -> None:
        entry_points: Sequence[importlib.metadata.EntryPoint]
        try:
            entry_points = tuple(importlib.metadata.entry_points(group=self._group))
        except Exception as err:  # noqa: BLE001
            failed_imports[self._group] = f"Entry-point discovery failed: {err}"
            return

        for entry_point in entry_points:
            source_name = entry_point.name
            try:
                factory = entry_point.load()
                feature = factory() if callable(factory) else factory
                if not isinstance(feature, Feature):
                    failed_specs[source_name] = (
                        f"Target object '{source_name}' does not satisfy Feature protocol"
                    )
                    continue
                self._add_discovered(
                    discovered,
                    feature,
                    source_name,
                    failed_specs,
                )
            except ModuleNotFoundError as err:
                target_module = entry_point.value.split(":")[0]
                missing_name = err.name or ""
                if target_module == missing_name or target_module.startswith(
                    f"{missing_name}."
                ):
                    missing_targets[source_name] = (
                        f"Entry point module '{target_module}' is missing"
                    )
                else:
                    failed_imports[source_name] = (
                        f"Feature dependency '{missing_name}' missing: {err}"
                    )
            except ValueError as err:
                failed_specs[source_name] = str(err)
            except Exception as err:  # noqa: BLE001
                failed_imports[source_name] = str(err)
