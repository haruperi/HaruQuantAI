"""Feature discovery via entry points and explicit factory registration."""

from __future__ import annotations

import importlib.metadata
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from app.kernel.feature import Feature

logger = logging.getLogger(__name__)


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
        """Register a feature instance or factory for discovery.

        Raises:
            TypeError: If the supplied object is neither a feature nor a factory.
        """
        if isinstance(feature_or_factory, Feature):
            key = (
                feature_id
                if feature_id is not None
                else feature_or_factory.spec.feature_id
            )
        elif feature_id is not None:
            key = feature_id
        else:
            factory_name = getattr(feature_or_factory, "__name__", None)
            key = (
                factory_name
                if isinstance(factory_name, str)
                else f"manual_factory_{id(feature_or_factory)}"
            )
        self._manual_features[key] = feature_or_factory

    def discover(self) -> DiscoveryResult:
        """Discover manual features and installed entry-point features.

        Returns:
            Successfully discovered features and categorized failures.
        """
        logger.debug(
            "Starting feature discovery pass",
            extra={
                "event": "DISCOVERY_START",
                "fields": {"group": self._group},
            },
        )
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

        has_warnings = bool(missing_targets or failed_imports or failed_specs)
        if has_warnings:
            logger.warning(
                "Feature discovery pass completed with diagnostic errors",
                extra={
                    "event": "DISCOVERY_COMPLETED_WITH_WARNINGS",
                    "fields": {
                        "discovered_count": len(discovered),
                        "missing_targets_count": len(missing_targets),
                        "failed_imports_count": len(failed_imports),
                        "failed_specs_count": len(failed_specs),
                    },
                },
            )
        else:
            logger.info(
                "Feature discovery pass completed successfully",
                extra={
                    "event": "DISCOVERY_COMPLETED",
                    "fields": {"discovered_count": len(discovered)},
                },
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
            msg = (
                f"Duplicate feature ID '{feature_id}' discovered; the existing "
                "feature was retained and the duplicate was rejected"
            )
            logger.warning(
                "Duplicate feature ID rejected during discovery",
                extra={
                    "event": "DISCOVERY_DUPLICATE_REJECTED",
                    "fields": {
                        "feature_id": feature_id,
                        "diagnostic_name": diagnostic_name,
                    },
                },
            )
            failed_specs[diagnostic_name] = msg
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
                feature = item if isinstance(item, Feature) else item()
                self._record_feature(
                    feature,
                    diagnostic_name,
                    discovered,
                    failed_specs,
                )
            except ValueError as error:
                logger.warning(
                    "Invalid feature specification in manual registration",
                    extra={
                        "event": "DISCOVERY_MANUAL_SPEC_FAILED",
                        "fields": {
                            "diagnostic_name": diagnostic_name,
                            "error": str(error),
                        },
                    },
                )
                failed_specs[diagnostic_name] = str(error)
            except Exception as error:  # noqa: BLE001
                logger.warning(
                    "Manual feature factory instantiation failure",
                    extra={
                        "event": "DISCOVERY_MANUAL_FACTORY_FAILED",
                        "fields": {
                            "diagnostic_name": diagnostic_name,
                            "error_type": type(error).__name__,
                            "error": str(error),
                        },
                    },
                )
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
            entry_points = tuple(importlib.metadata.entry_points(group=self._group))
        except Exception as error:
            logger.exception(
                "Failed to query entry points group",
                extra={
                    "event": "DISCOVERY_ENTRY_POINTS_QUERY_FAILED",
                    "fields": {"group": self._group, "error": str(error)},
                },
            )
            failed_imports["__entry_points__"] = str(error)
            return

        for entry_point in entry_points:
            diagnostic_name = entry_point.name
            try:
                target = entry_point.load()
                feature = target() if callable(target) else target
                if not isinstance(feature, Feature):
                    msg = (
                        f"Target '{diagnostic_name}' does not satisfy Feature protocol"
                    )
                    logger.warning(
                        "Entry point target does not satisfy Feature protocol",
                        extra={
                            "event": "DISCOVERY_PROTOCOL_MISMATCH",
                            "fields": {"entry_point": diagnostic_name},
                        },
                    )
                    failed_specs[diagnostic_name] = msg
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
                    msg = f"Entry point module '{target_module}' is missing"
                    logger.warning(
                        "Entry point target module is missing",
                        extra={
                            "event": "DISCOVERY_TARGET_MODULE_MISSING",
                            "fields": {
                                "entry_point": diagnostic_name,
                                "target_module": target_module,
                            },
                        },
                    )
                    missing_targets[diagnostic_name] = msg
                else:
                    msg = f"Feature dependency '{error.name}' missing: {error}"
                    logger.warning(
                        "Entry point feature dependency missing",
                        extra={
                            "event": "DISCOVERY_DEPENDENCY_MISSING",
                            "fields": {
                                "entry_point": diagnostic_name,
                                "missing_module": error.name,
                            },
                        },
                    )
                    failed_imports[diagnostic_name] = msg
            except ValueError as error:
                logger.warning(
                    "Invalid feature spec from entry point",
                    extra={
                        "event": "DISCOVERY_ENTRY_POINT_SPEC_FAILED",
                        "fields": {
                            "entry_point": diagnostic_name,
                            "error": str(error),
                        },
                    },
                )
                failed_specs[diagnostic_name] = str(error)
            except Exception as error:  # noqa: BLE001
                logger.warning(
                    "Entry point load failure",
                    extra={
                        "event": "DISCOVERY_ENTRY_POINT_FAILED",
                        "fields": {
                            "entry_point": diagnostic_name,
                            "error_type": type(error).__name__,
                            "error": str(error),
                        },
                    },
                )
                failed_imports[diagnostic_name] = str(error)
