"""Feature discovery via entry points and factory registration."""

import importlib.metadata
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from app.kernel.feature import Feature


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Outcome of a feature discovery pass.

    Attributes:
        discovered: Successfully loaded features keyed by feature_id.
        missing_targets: Features whose entry point module/target does not exist.
        failed_imports: Features whose third-party dependency import failed.
        failed_specs: Features with invalid or malformed specifications.
    """

    discovered: dict[str, Feature] = field(default_factory=dict)
    missing_targets: dict[str, str] = field(default_factory=dict)
    failed_imports: dict[str, str] = field(default_factory=dict)
    failed_specs: dict[str, str] = field(default_factory=dict)


class FeatureDiscoverer:
    """Discovers and instantiates composable feature factories."""

    def __init__(self, entry_point_group: str = "haruquantai.features") -> None:
        """Initialize the discoverer.

        Args:
            entry_point_group: Entry point group name in package metadata.
        """
        self._group = entry_point_group
        self._manual_features: dict[str, Feature | Callable[[], Feature]] = {}

    def register_feature(
        self,
        feature_or_factory: Feature | Callable[[], Feature],
        feature_id: str | None = None,
    ) -> None:
        """Manually register a feature instance or factory for discovery.

        Args:
            feature_or_factory: Feature instance or factory callable returning Feature.
            feature_id: Optional explicit feature ID key for diagnostic tracking.
        """
        if isinstance(feature_or_factory, Feature):
            self._manual_features[feature_or_factory.spec.feature_id] = (
                feature_or_factory
            )
        elif callable(feature_or_factory):
            key = feature_id or getattr(
                feature_or_factory,
                "__name__",
                f"manual_factory_{id(feature_or_factory)}",
            )
            self._manual_features[str(key)] = feature_or_factory

    def discover(self) -> DiscoveryResult:
        """Discover and load all registered entry points and manual features.

        Returns:
            DiscoveryResult containing loaded features and categorized errors.
        """
        discovered: dict[str, Feature] = {}
        missing_targets: dict[str, str] = {}
        failed_imports: dict[str, str] = {}
        failed_specs: dict[str, str] = {}

        self._load_manual(discovered, missing_targets, failed_imports, failed_specs)
        self._load_entry_points(
            discovered, missing_targets, failed_imports, failed_specs
        )

        return DiscoveryResult(
            discovered=discovered,
            missing_targets=missing_targets,
            failed_imports=failed_imports,
            failed_specs=failed_specs,
        )

    def _load_manual(
        self,
        discovered: dict[str, Feature],
        _missing: dict[str, str],
        failed_imports: dict[str, str],
        failed_specs: dict[str, str],
    ) -> None:
        """Load manually registered feature instances and factories.

        Args:
            discovered: Output dict for discovered features.
            _missing: Output dict for missing targets.
            failed_imports: Output dict for failed imports.
            failed_specs: Output dict for failed specs.
        """
        for f_id, item in self._manual_features.items():
            if isinstance(item, Feature):
                try:
                    item.spec.validate()
                    discovered[f_id] = item
                except ValueError as err:
                    failed_specs[f_id] = str(err)
            elif callable(item):
                try:
                    feat = item()
                    feat.spec.validate()
                    discovered[f_id] = feat
                except ValueError as err:
                    failed_specs[f_id] = str(err)
                except Exception as err:  # noqa: BLE001
                    failed_imports[f_id] = str(err)

    def _load_entry_points(
        self,
        discovered: dict[str, Feature],
        missing_targets: dict[str, str],
        failed_imports: dict[str, str],
        failed_specs: dict[str, str],
    ) -> None:
        """Load entry points registered in package metadata.

        Args:
            discovered: Output dict for discovered features.
            missing_targets: Output dict for missing targets.
            failed_imports: Output dict for failed imports.
            failed_specs: Output dict for failed specs.
        """
        entry_points: Sequence[importlib.metadata.EntryPoint]
        try:
            entry_points = tuple(importlib.metadata.entry_points(group=self._group))
        except Exception:  # noqa: BLE001
            entry_points = ()

        for ep in entry_points:
            f_name = ep.name
            try:
                factory = ep.load()
                feat = factory() if callable(factory) else factory
                if not hasattr(feat, "spec") or not hasattr(feat, "mount"):
                    failed_specs[f_name] = (
                        f"Target object '{f_name}' does not satisfy Feature protocol"
                    )
                    continue

                feat.spec.validate()
                discovered[feat.spec.feature_id] = feat
            except ModuleNotFoundError as err:
                target_module = ep.value.split(":")[0]
                if err.name and err.name in target_module:
                    missing_targets[f_name] = (
                        f"Entry point module '{target_module}' is missing"
                    )
                else:
                    failed_imports[f_name] = (
                        f"Feature dependency '{err.name}' missing: {err}"
                    )
            except ValueError as err:
                failed_specs[f_name] = str(err)
            except Exception as err:  # noqa: BLE001
                failed_imports[f_name] = str(err)
