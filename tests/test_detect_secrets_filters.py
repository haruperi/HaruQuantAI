"""Behavioral checks for the evidence secret-scan false-positive filters.

Test values are constructed at runtime so this file itself contains no
high-entropy literals or scan-triggering keywords for the scanner it tests.
"""

from scripts.detect_secrets_filters import (
    is_valid_repository_artifact_path_evidence,
    is_valid_repository_evidence,
)

LEDGER = "docs/dev/evidence/reimplementation.json"
# Assembled at runtime: the joined donor path is itself high-entropy enough
# to trip the scanner this file tests, so no single literal may contain it.
_DONOR_ROOT = "SQX_REFERENCE_ROOT"
_DONOR_TAIL = "/internal/plugins/ResultsDatabankActions"
_DONOR_ACTIONS_PATH = f"{_DONOR_ROOT}{_DONOR_TAIL}"
# Alternating-case alphabet plus digits: high entropy, not a logical-root path.
_HIGH_ENTROPY_NON_PATH = (
    "".join(c.upper() if i % 2 else c for i, c in enumerate("abcdefghijklmnopqrstuvw"))
    + "0123456789+/xz"
)


def test_logical_root_artifact_path_is_filtered() -> None:
    line = f'          "{_DONOR_ACTIONS_PATH}/",'
    assert is_valid_repository_artifact_path_evidence(LEDGER, line, _DONOR_ACTIONS_PATH)
    assert is_valid_repository_evidence(LEDGER, line, _DONOR_ACTIONS_PATH)


def test_artifact_locator_keyed_line_is_filtered() -> None:
    path = "HARUQUANTAI_ROOT/app/ui/app/host/App.tsx"
    line = f'"artifact_locator": "{path}",'
    assert is_valid_repository_artifact_path_evidence(LEDGER, line, path)


def test_trailing_slash_mismatch_is_tolerated() -> None:
    path = "SQX_REFERENCE_ROOT/internal/web/BUILDER"
    line = f'  "{path}/",'
    assert is_valid_repository_artifact_path_evidence(LEDGER, line, path)


def test_path_without_logical_root_is_not_filtered() -> None:
    path = "internal/plugins/ProjectDatabanks/views/databanks.html"
    line = f'          "{path}",'
    assert not is_valid_repository_artifact_path_evidence(LEDGER, line, path)


def test_non_path_high_entropy_string_is_not_filtered() -> None:
    line = f'          "{_HIGH_ENTROPY_NON_PATH}",'
    assert not is_valid_repository_artifact_path_evidence(
        LEDGER, line, _HIGH_ENTROPY_NON_PATH
    )


def test_artifact_path_rule_is_scoped_to_the_ledger() -> None:
    line = f'          "{_DONOR_ACTIONS_PATH}/",'
    assert not is_valid_repository_artifact_path_evidence(
        "docs/other.json", line, _DONOR_ACTIONS_PATH
    )


def test_fingerprint_rule_still_applies() -> None:
    digest = "b" * 64
    line = f'        "value": "{digest}",'
    assert is_valid_repository_evidence(LEDGER, line, digest)
