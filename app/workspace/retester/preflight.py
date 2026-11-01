"""Retester preflight validation and execution mode policy.

Description:
    Provides preflight policy methods to resolve candidate strategy record keys
    and determine the execution mode (0 for subjob-creating cross-checks,
    1 for standalone sequential runs).

Purpose:
    FEAT-RETESTER-PREFLIGHT: Deterministic record key selection and mode resolution.

Key Capabilities:
    - FR-retest-preflight-keys: Resolve explicit selection vs databank keys without
      accidental fallback to all records when explicit selection is empty.
    - FR-retest-preflight-mode: Determine mode 0 vs 1 based on enabled subjob checks.

Python API Usage:
    from app.workspace.retester.preflight import RetestPreflight
    keys = RetestPreflight.record_keys(databank_keys=("k1",), selected_keys=None)
    mode = RetestPreflight.mode(cross_checks_enabled=True, creates_subjobs=(True,))

CLI Usage:
    python -m app.cli retest preflight-mode --cross-checks true
"""

from __future__ import annotations

from app.core.host.logging import get_logger

logger = get_logger(__name__)


class RetestPreflight:
    """Preflight policy helper for Retester jobs."""

    @staticmethod
    def record_keys(
        *,
        databank_keys: tuple[str, ...],
        selected_keys: tuple[str, ...] | None,
    ) -> tuple[str, ...]:
        """Resolve effective record keys for retesting.

        Args:
            databank_keys: All strategy keys present in the source databank.
            selected_keys: User-selected strategy keys, or None for all.

        Returns:
            Effective tuple of record keys to retest.

        Raises:
            TypeError: If databank_keys is not a tuple of strings, or selected_keys
                is not None and not a tuple of strings.
        """
        if not isinstance(databank_keys, tuple) or not all(
            type(k) is str for k in databank_keys
        ):
            raise TypeError("record keys must be tuples of strings")

        if selected_keys is not None:
            if not isinstance(selected_keys, tuple) or not all(
                type(k) is str for k in selected_keys
            ):
                raise TypeError("record keys must be tuples of strings")
            logger.info(
                "FR-retest-preflight-keys: resolved %d explicit selected keys",
                len(selected_keys),
            )
            return selected_keys

        logger.info(
            "FR-retest-preflight-keys: resolved all %d databank keys",
            len(databank_keys),
        )
        return databank_keys

    @staticmethod
    def mode(
        *,
        cross_checks_enabled: bool,
        creates_subjobs: tuple[bool, ...],
    ) -> int:
        """Determine backtest execution mode based on cross-check configuration.

        Mode 0 is used when cross-checks are enabled and at least one enabled check
        creates subjobs (e.g. Monte Carlo Retest, Walk Forward). Mode 1 is used
        otherwise.

        Args:
            cross_checks_enabled: Master flag indicating whether cross-checks
                are enabled.
            creates_subjobs: Tuple of boolean flags for enabled checks creating subjobs.

        Returns:
            0 if cross_checks_enabled is True and any creates_subjobs item is True,
            otherwise 1.

        Raises:
            TypeError: If cross_checks_enabled is not bool, or creates_subjobs is not
                a tuple of exact booleans.
        """
        if type(cross_checks_enabled) is not bool:
            raise TypeError("cross-check mode requires booleans")

        if not isinstance(creates_subjobs, tuple) or not all(
            type(b) is bool for b in creates_subjobs
        ):
            raise TypeError("cross-check mode requires booleans")

        if cross_checks_enabled and any(creates_subjobs):
            logger.info("FR-retest-preflight-mode: mode 0 (subjob execution enabled)")
            return 0

        logger.info("FR-retest-preflight-mode: mode 1 (standard sequential execution)")
        return 1
