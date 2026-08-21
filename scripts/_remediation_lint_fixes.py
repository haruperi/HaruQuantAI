"""Apply deterministic one-time lint fixes to the remediation branch."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "app/api/http.py": [
        (
            '    """Route one system control-plane request."""',
            '    """Route one system control-plane request.\n\n    Returns:\n        HTTP status, response headers, and JSON-compatible response body.\n    """',
        ),
    ],
    "app/api/system.py": [
        (
            '        """Resolve the active storage engine."""',
            '        """Resolve the active storage engine.\n\n        Returns:\n            Active storage-engine provider.\n        """',
        ),
        (
            '        """Resolve the active system clock."""',
            '        """Resolve the active system clock.\n\n        Returns:\n            Active system-clock provider.\n        """',
        ),
        (
            '        """Resolve the active metrics collector."""',
            '        """Resolve the active metrics collector.\n\n        Returns:\n            Active metrics-collector provider.\n        """',
        ),
        (
            '        """Inspect one capability and its active provider generation."""',
            '        """Inspect one capability and its active provider generation.\n\n        Returns:\n            Capability availability and provider metadata.\n        """',
        ),
        (
            '        """Inspect package, capability, runtime, and replacement health."""',
            '        """Inspect package, capability, runtime, and replacement health.\n\n        Returns:\n            Consolidated diagnostic information for the feature.\n        """',
        ),
    ],
    "app/composition/config.py": [
        (
            "    def __post_init__(self) -> None:\n        normalized = self.profile.strip().lower()",
            '    def __post_init__(self) -> None:\n        """Normalize and validate direct AppConfig construction."""\n        normalized = self.profile.strip().lower()',
        ),
        (
            "    for capability, feature_id in providers_raw.items():\n        if not isinstance(capability, str) or not isinstance(feature_id, str):",
            "    for raw_capability, raw_feature_id in providers_raw.items():\n        if not isinstance(raw_capability, str) or not isinstance(raw_feature_id, str):",
        ),
        (
            "        capability = capability.strip()\n        feature_id = feature_id.strip()",
            "        capability = raw_capability.strip()\n        feature_id = raw_feature_id.strip()",
        ),
        (
            '    """Parse and validate application configuration from TOML text."""',
            '    """Parse and validate application configuration from TOML text.\n\n    Returns:\n        Validated application configuration.\n\n    Raises:\n        ConfigurationError: If TOML syntax or configuration semantics are invalid.\n    """',
        ),
        (
            '    """Load and validate application configuration from a TOML file."""',
            '    """Load and validate application configuration from a TOML file.\n\n    Returns:\n        Validated application configuration.\n\n    Raises:\n        FileNotFoundError: If the configuration file does not exist.\n        ConfigurationError: If the file content is invalid.\n    """',
        ),
    ],
    "app/composition/discovery.py": [
        (
            '        """Register a feature instance or factory for discovery."""',
            '        """Register a feature instance or factory for discovery.\n\n        Raises:\n            TypeError: If the supplied object is neither a feature nor a factory.\n        """',
        ),
        (
            '        """Discover manual features and installed entry-point features."""',
            '        """Discover manual features and installed entry-point features.\n\n        Returns:\n            Successfully discovered features and categorized failures.\n        """',
        ),
    ],
    "app/composition/engine.py": [
        (
            '        """Parse TOML and reconcile it atomically."""',
            '        """Parse TOML and reconcile it atomically.\n\n        Returns:\n            Report describing lifecycle transitions.\n        """',
        ),
        (
            '        """Load a TOML file and reconcile it atomically."""',
            '        """Load a TOML file and reconcile it atomically.\n\n        Returns:\n            Report describing lifecycle transitions.\n        """',
        ),
        (
            '        """Serialize and commit one configuration reconciliation."""',
            '        """Serialize and commit one configuration reconciliation.\n\n        Returns:\n            Report describing lifecycle transitions.\n        """',
        ),
        (
            '        """Reconcile a new configuration and emit a reload event."""',
            '        """Reconcile a new configuration and emit a reload event.\n\n        Returns:\n            Report describing lifecycle transitions.\n        """',
        ),
        (
            '        """Replace a feature and return a compatibility success tuple."""',
            '        """Replace a feature and return a compatibility success tuple.\n\n        Returns:\n            Commit status and optional diagnostic message.\n        """',
        ),
        (
            '        """Serialize a staged feature replacement and return full diagnostics."""',
            '        """Serialize a staged feature replacement and return full diagnostics.\n\n        Returns:\n            Detailed replacement and cleanup report.\n        """',
        ),
    ],
    "app/kernel/events.py": [
        (
            '        """Register one handler and return an idempotent exact disposer."""',
            '        """Register one handler and return an idempotent exact disposer.\n\n        Returns:\n            Disposer for this exact subscription.\n        """',
        ),
        (
            '        """Remove only the subscription identified by the exact token."""',
            '        """Remove only the subscription identified by the exact token.\n\n        Returns:\n            Whether an active subscription was removed.\n        """',
        ),
        (
            '        """Remove the first matching registration for compatibility."""',
            '        """Remove the first matching registration for compatibility.\n\n        Returns:\n            Whether a matching registration was removed.\n        """',
        ),
        (
            '        """Transform an event through ordered pipeline handlers."""',
            '        """Transform an event through ordered pipeline handlers.\n\n        Returns:\n            Final transformed value, or None when short-circuited.\n        """',
        ),
        (
            '        """Register an item and return an idempotent disposer."""',
            '        """Register an item and return an idempotent disposer.\n\n        Returns:\n            Disposer for the registered contributor.\n\n        Raises:\n            ValueError: If the key is already registered.\n        """',
        ),
        (
            '        """Return an item or raise KeyError."""',
            '        """Return an item or raise KeyError.\n\n        Raises:\n            KeyError: If the contributor is unavailable.\n        """',
        ),
    ],
    "app/kernel/feature.py": [
        (
            '        """Validate feature identity and declaration consistency."""',
            '        """Validate feature identity and declaration consistency.\n\n        Raises:\n            ValueError: If identity, dependencies, or configuration keys are invalid.\n        """',
        ),
    ],
    "app/kernel/graph.py": [
        (
            '        """Resolve providers, eligibility, and deterministic lifecycle order."""',
            '        """Resolve providers, eligibility, and deterministic lifecycle order.\n\n        Returns:\n            Resolved providers, lifecycle order, and dependency maps.\n        """',
        ),
    ],
    "app/kernel/reconciler.py": [
        (
            '        """Reconcile active features against a desired configuration."""',
            '        """Reconcile active features against a desired configuration.\n\n        Returns:\n            Report describing started, stopped, blocked, and failed features.\n        """',
        ),
        (
            "    async def swap_feature_transactional(\n",
            "    async def swap_feature_transactional(  # noqa: PLR0915\n",
        ),
        (
            '        """Stage, atomically publish, and reconcile a feature replacement."""',
            '        """Stage, atomically publish, and reconcile a feature replacement.\n\n        Returns:\n            Detailed commit, rollback, consumer, and cleanup result.\n        """',
        ),
    ],
    "app/kernel/registry.py": [
        (
            '        """Register one capability without overwriting an active binding."""',
            '        """Register one capability without overwriting an active binding.\n\n        Returns:\n            Ownership token for the new binding.\n        """',
        ),
        (
            '        """Atomically register a new capability bundle."""',
            '        """Atomically register a new capability bundle.\n\n        Returns:\n            Ownership tokens in bundle order.\n\n        Raises:\n            CapabilityAlreadyBoundError: If a capability is duplicated or active.\n        """',
        ),
        (
            '        """Atomically replace one capability through the explicit swap path."""',
            '        """Atomically replace one capability through the explicit swap path.\n\n        Returns:\n            Ownership token for the replacement binding.\n        """',
        ),
        (
            '        """Atomically replace every capability in a provider bundle."""',
            '        """Atomically replace every capability in a provider bundle.\n\n        Returns:\n            Ownership tokens in bundle order.\n        """',
        ),
        (
            '        """Revoke a binding only when its exact generation is still active."""',
            '        """Revoke a binding only when its exact generation is still active.\n\n        Returns:\n            Whether the active generation was removed.\n        """',
        ),
        (
            '        """Resolve an active provider for a capability."""',
            '        """Resolve an active provider for a capability.\n\n        Returns:\n            Active provider, or None when unavailable.\n        """',
        ),
        (
            '        """Resolve a mandatory capability or raise when unavailable."""',
            '        """Resolve a mandatory capability or raise when unavailable.\n\n        Returns:\n            Active capability provider.\n\n        Raises:\n            CapabilityUnavailableError: If no provider is active.\n        """',
        ),
    ],
    "app/kernel/scope.py": [
        (
            '        """Raise ScopeClosedError when the scope is already closed."""',
            '        """Raise ScopeClosedError when the scope is already closed.\n\n        Raises:\n            ScopeClosedError: If the scope is closed.\n        """',
        ),
        (
            '        """Spawn and supervise a background task owned by this scope."""',
            '        """Spawn and supervise a background task owned by this scope.\n\n        Returns:\n            Managed asyncio task.\n\n        Raises:\n            ScopeClosedError: If the scope is closed.\n        """',
        ),
        (
            '        """Enter a synchronous context manager owned by this scope."""',
            '        """Enter a synchronous context manager owned by this scope.\n\n        Returns:\n            Resource returned by the context manager.\n        """',
        ),
        (
            '        """Enter an asynchronous context manager owned by this scope."""',
            '        """Enter an asynchronous context manager owned by this scope.\n\n        Returns:\n            Resource returned by the context manager.\n        """',
        ),
    ],
    "app/main.py": [
        (
            '    """Run the composition runtime and return a process exit code."""',
            '    """Run the composition runtime and return a process exit code.\n\n    Returns:\n        Process exit code.\n    """',
        ),
        (
            '    """Synchronous project script entry point."""',
            '    """Synchronous project script entry point.\n\n    Raises:\n        SystemExit: Always, with the asynchronous runtime exit code.\n    """',
        ),
    ],
    "app/services/broker/mock_feed/config.py": [
        (
            '        """Parse and validate a strict mock-feed configuration mapping."""',
            '        """Parse and validate a strict mock-feed configuration mapping.\n\n        Returns:\n            Validated mock-feed configuration.\n\n        Raises:\n            ValueError: If a field is unknown or invalid.\n        """',
        ),
    ],
    "app/services/data/historical_bars/config.py": [
        (
            '        """Parse and validate a strict historical-bars configuration mapping."""',
            '        """Parse and validate a strict historical-bars configuration mapping.\n\n        Returns:\n            Validated historical-bars configuration.\n\n        Raises:\n            ValueError: If a field is unknown or invalid.\n        """',
        ),
    ],
    "app/services/data/historical_bars/feature.py": [
        (
            '    """Create a HistoricalBarsFeature instance."""',
            '    """Create a HistoricalBarsFeature instance.\n\n    Returns:\n        New feature instance.\n    """',
        ),
    ],
    "app/services/data/historical_bars/retrieve.py": [
        (
            '        """Retrieve normalized bars, applying the configured blank-timeframe fallback."""',
            '        """Retrieve normalized bars with the configured timeframe fallback.\n\n        Returns:\n            Canonical normalized bars.\n        """',
        ),
    ],
    "app/services/system/storage/config.py": [
        (
            '        """Parse and validate a strict storage configuration mapping."""',
            '        """Parse and validate a strict storage configuration mapping.\n\n        Returns:\n            Validated storage configuration.\n\n        Raises:\n            ValueError: If a field is unknown or invalid.\n        """',
        ),
    ],
    "scripts/validate_feature_docs.py": [
        (
            '    """Load registered feature factories from pyproject.toml."""',
            '    """Load registered feature factories from pyproject.toml.\n\n    Returns:\n        Entry-point name-to-target mapping.\n\n    Raises:\n        TypeError: If the entry-point table is not a mapping.\n    """',
        ),
        (
            '        raise ValueError("Feature entry-point table is invalid")',
            '        raise TypeError("Feature entry-point table is invalid")',
        ),
        (
            "def validate_feature_readme(\n",
            "def validate_feature_readme(  # noqa: C901, PLR0912\n",
        ),
        (
            'def main() -> int:\n    """Validate every registered feature README."""',
            'def main() -> int:  # noqa: C901\n    """Validate every registered feature README.\n\n    Returns:\n        Zero when all documents match runtime truth; otherwise one.\n    """',
        ),
        (
            "    except (OSError, ValueError, tomllib.TOMLDecodeError) as error:",
            "    except (OSError, TypeError, tomllib.TOMLDecodeError) as error:",
        ),
    ],
    "scripts/verify_feature_removal.py": [
        (
            "        raise RuntimeError(\"[project.entry-points.'haruquantai.features'] is invalid\")",
            "        raise TypeError(\"[project.entry-points.'haruquantai.features'] is invalid\")",
        ),
        (
            '    """Discover every registered feature or fail on incomplete metadata."""',
            '    """Discover every registered feature or fail on incomplete metadata.\n\n    Returns:\n        Complete feature-removal target mapping.\n\n    Raises:\n        RuntimeError: If an entry point cannot be resolved or is duplicated.\n        TypeError: If entry-point metadata has an invalid type.\n    """',
        ),
        (
            '    """Run one verification step and capture its output on failure."""',
            '    """Run one verification step and capture its output on failure.\n\n    Returns:\n        Captured verification-step result.\n    """',
        ),
        (
            '    """Remove one exact feature entry-point declaration."""',
            '    """Remove one exact feature entry-point declaration.\n\n    Raises:\n        RuntimeError: If exactly one matching declaration is not removed.\n    """',
        ),
        (
            '    """Verify one feature deletion inside an isolated temporary workspace."""',
            '    """Verify one feature deletion inside an isolated temporary workspace.\n\n    Returns:\n        Complete target verification report.\n\n    Raises:\n        RuntimeError: If target source or metadata is inconsistent.\n    """',
        ),
        (
            '    """Run one target or the complete registered-feature removal matrix."""',
            '    """Run one target or the complete registered-feature removal matrix.\n\n    Returns:\n        Zero when every selected target passes; otherwise one.\n    """',
        ),
        (
            "    except RuntimeError as error:",
            "    except (RuntimeError, TypeError) as error:",
        ),
    ],
    "tests/composition/test_config.py": [
        (
            'match="mixes a .config table"',
            'match=r"mixes a \\.config table"',
        ),
    ],
}


def main() -> None:
    """Apply every expected replacement exactly once."""
    for relative_path, replacements in REPLACEMENTS.items():
        path = ROOT / relative_path
        content = path.read_text(encoding="utf-8")
        for old, new in replacements:
            if old not in content:
                raise RuntimeError(
                    f"Expected text not found in {relative_path}: {old!r}"
                )
            content = content.replace(old, new, 1)
        path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
