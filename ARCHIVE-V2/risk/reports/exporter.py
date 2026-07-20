"""Risk report exporter module.

Enforces explicit write authorizations, directory traversal checks, overwrite
policies, and builds write receipt evidence upon export completion.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from app.services.risk.errors import RiskValidationError as ValidationError
from app.services.risk.models import RiskContract
from app.services.risk.validations import ValidationResult, _fail, _ok
from app.utils.logger import logger
from app.utils.normalization import utc_now
from pydantic import Field

if TYPE_CHECKING:
    from app.services.risk.reports.builder import RiskReport


class AuthorizedReportPath(RiskContract):
    """Authorized destination path schema for report writes.

    Args:
        root: The authorized base directory.
        relative_path: Relative path under the base directory.
        overwrite: Allow overwriting existing file if True.
        request_id: Optional association trace ID.
    """

    root: str = Field(..., description="Authorized root directory path.")
    relative_path: str = Field(..., description="Relative file path from the root.")
    overwrite: bool = Field(default=False, description="True to allow overwriting.")
    request_id: str | None = Field(
        default=None, description="Request ID associated with the write."
    )


class ReportWriteReceipt(RiskContract):
    """receipt containing structural verification details of a file write.

    Args:
        report_id: Associated report identifier.
        destination_path: Absolute target path of the written file.
        checksum: Cryptographic SHA256 checksum of file content.
        written_at: UTC timestamp.
    """

    report_id: str = Field(..., description="Unique report ID.")
    destination_path: str = Field(..., description="Absolute destination path.")
    checksum: str = Field(..., description="SHA256 checksum of written report.")
    written_at: datetime = Field(..., description="Timestamp of write operation.")


def validate_report_export_destination(
    destination: AuthorizedReportPath,
) -> ValidationResult:
    """Validate report destination path against traversal and overwrites.

    Args:
        destination: Bounded path parameters.

    Returns:
        ValidationResult: The validation outcome.
    """
    logger.debug(
        f"Validating export destination relative path: {destination.relative_path}"
    )
    import tempfile

    try:
        root_path = Path(destination.root).resolve()
        target_path = (root_path / destination.relative_path).resolve()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Path resolution failed: {e}")
        return _fail(
            message=f"Invalid path configuration: {e}",
            code="INVALID_INPUT",
            details={"error": str(e)},
        )

    workspace_root = Path.cwd().resolve()
    temp_dir = Path(tempfile.gettempdir()).resolve()

    in_workspace = str(target_path).startswith(str(workspace_root))
    in_temp = str(target_path).startswith(str(temp_dir))
    in_root = str(target_path).startswith(str(root_path))

    if not (in_workspace or in_temp or in_root):
        logger.warning(
            f"Path traversal check failed. Target: {target_path}, "
            f"Workspace: {workspace_root}, Temp: {temp_dir}"
        )
        return _fail(
            message=(
                "Path traversal detected: path is outside the authorized directories."
            ),
            code="PERMISSION_DENIED",
            details={"target_path": str(target_path)},
        )

    if target_path.suffix.lower() not in {".json", ".txt", ".md"}:
        logger.warning(f"Unsafe extension blocked: {target_path.suffix}")
        return _fail(
            message="Unsafe file extension. Only .json, .txt, .md are permitted.",
            code="PERMISSION_DENIED",
            details={"suffix": target_path.suffix},
        )

    if target_path.exists() and not destination.overwrite:
        logger.warning(f"File exists overwrite blocked: {target_path}")
        return _fail(
            message=f"File already exists and overwrite is disabled: {target_path}",
            code="VALIDATION_FAILED",
            details={"path": str(target_path)},
        )

    return _ok()


def build_report_write_receipt(
    report: RiskReport,
    destination: AuthorizedReportPath,
    checksum: str,
) -> ReportWriteReceipt:
    """Create deterministic export receipt.

    Args:
        report: The compiled risk report.
        destination: Bounded export path.
        checksum: SHA256 checksum.

    Returns:
        ReportWriteReceipt: Bounded receipt.
    """
    logger.debug(f"Building report write receipt for report: {report.report_id}")
    root_path = Path(destination.root).resolve()
    target_path = (root_path / destination.relative_path).resolve()
    return ReportWriteReceipt(
        report_id=report.report_id,
        destination_path=str(target_path),
        checksum=checksum,
        written_at=utc_now(),
    )


def write_risk_report(
    report: RiskReport,
    destination: AuthorizedReportPath,
) -> ReportWriteReceipt:
    """Write the report safely to the destination and return a receipt.

    Args:
        report: The risk report to export.
        destination: Authorized export path parameter.

    Returns:
        ReportWriteReceipt: Export receipt.
    """
    logger.info(f"Writing risk report: {report.report_id}")
    val_res = validate_report_export_destination(destination)
    if not val_res["valid"]:
        logger.error(f"Export validation failed: {val_res['message']}")
        raise ValidationError(val_res["message"])

    root_path = Path(destination.root).resolve()
    target_path = (root_path / destination.relative_path).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    report_json = report.to_json()
    checksum = hashlib.sha256(report_json.encode("utf-8")).hexdigest()

    try:
        with target_path.open("w", encoding="utf-8") as f:
            f.write(report_json)
        logger.info(f"Successfully wrote risk report to: {target_path}")
    except OSError as e:
        logger.error(f"Failed to write risk report file: {e}")
        err_msg = f"Failed to write risk report file: {e}"
        raise ValidationError(err_msg) from e

    return build_report_write_receipt(report, destination, checksum)
