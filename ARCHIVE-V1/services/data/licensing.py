"""Data source licensing registration and validation rules.

Provides the default license registry plus database-backed registration and
validation of redistribution constraints per source and symbol.
"""

from datetime import UTC, datetime
from typing import Any

from app.services.data.storage import db_helper
from app.services.utils.errors import ValidationError
from app.services.utils.logger import logger

# --- Licensing Constraints ---
DEFAULT_LICENSE_REGISTRY: dict[str, dict[str, Any]] = {
    "csv": {
        "license_type": "Open",
        "redistribution_restricted": False,
        "attribution": "Local CSV Ingestion",
    },
    "parquet": {
        "license_type": "Open",
        "redistribution_restricted": False,
        "attribution": "Local Parquet Ingestion",
    },
    "synthetic": {
        "license_type": "Permissive",
        "redistribution_restricted": False,
        "attribution": "HaruQuant Synthetic Bar/Tick Generator",
    },
    "mt5": {
        "license_type": "Proprietary",
        "redistribution_restricted": True,
        "attribution": "MetaTrader 5 Terminal Gateway Data",
    },
    "ctrader": {
        "license_type": "Proprietary",
        "redistribution_restricted": True,
        "attribution": "cTrader OpenAPI Client Feed",
    },
    "dukascopy": {
        "license_type": "Restricted",
        "redistribution_restricted": True,
        "attribution": "Dukascopy Community Feed",
    },
    "binance": {
        "license_type": "Restricted",
        "redistribution_restricted": True,
        "attribution": "Binance Public API Data",
    },
    "ccxt": {
        "license_type": "Restricted",
        "redistribution_restricted": True,
        "attribution": "CCXT Exchange API Data",
    },
    "yahoo": {
        "license_type": "Restricted",
        "redistribution_restricted": True,
        "attribution": "Yahoo Finance Public Feed",
    },
}


def _ensure_licensing_table() -> None:
    """Description.
        Ensure data_licenses table exists in database.
    
    Args:
        None.
    
    Returns:
        None.
    """
    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS data_licenses (
                    source TEXT,
                    symbol TEXT,
                    license_type TEXT NOT NULL,
                    redistribution_restricted INTEGER DEFAULT 0,
                    attribution TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (source, symbol)
                );
                """
            )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Could not initialize data_licenses table: {e}")


# Initialize table on load
_ensure_licensing_table()


def register_license(
    source: str,
    symbol: str,
    license_type: str,
    *,
    redistribution_restricted: bool,
    attribution: str | None = None,
    request_id: str | None = None,
) -> None:
    """Description.
        Register or update license metadata for a source and symbol.
    
    Args:
        source: str.
        symbol: str.
        license_type: str.
        redistribution_restricted: bool.
        attribution: str | None.
        request_id: str | None.
    
    Returns:
        None.
    """
    logger.info(
        f"Registering license: source={source}, symbol={symbol}",
        extra={"request_id": request_id},
    )

    try:
        with db_helper.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO data_licenses (
                    source, symbol, license_type, redistribution_restricted,
                    attribution, created_at
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    source,
                    symbol,
                    license_type,
                    1 if redistribution_restricted else 0,
                    attribution,
                    datetime.now(UTC).isoformat(),
                ),
            )
    except Exception as e:
        logger.error(
            f"Failed to save license for {source}:{symbol} to DB: {e}",
            extra={"request_id": request_id},
        )
        msg = f"Failed to register license: {e}"
        raise ValidationError(msg) from e


def validate_license(
    source: str,
    symbol: str,
    workflow_context: str,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Description.
        Validate licensing constraints for a given workflow context.
    
    Args:
        source: str.
        symbol: str.
        workflow_context: str.
        request_id: str | None.
    
    Returns:
        dict[str, Any].
    """
    logger.debug(
        f"Validating license: source={source}, symbol={symbol}, "
        f"context={workflow_context}",
        extra={"request_id": request_id},
    )

    license_info = None
    try:
        with db_helper.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM data_licenses
                WHERE source = ? AND (symbol = ? OR symbol = '*');
                """,
                (source, symbol),
            )
            row = cursor.fetchone()
            if row:
                license_info = {
                    "license_type": row["license_type"],
                    "redistribution_restricted": bool(row["redistribution_restricted"]),
                    "attribution": row["attribution"],
                }
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Database query error during license check: {e}")

    if not license_info and source in DEFAULT_LICENSE_REGISTRY:
        license_info = DEFAULT_LICENSE_REGISTRY[source]
        logger.debug(f"Resolved default license for source={source}")

    if not license_info:
        err_msg = (
            f"Missing license metadata for source={source}, symbol={symbol}. "
            f"Operation rejected (LICENSE_RESTRICTION)."
        )
        logger.error(err_msg, extra={"request_id": request_id})
        raise ValidationError("LICENSE_RESTRICTION: Metadata missing.")

    if license_info["redistribution_restricted"] and workflow_context in (
        "risk",
        "execution_bound",
    ):
        err_restrict = (
            f"Workflow {workflow_context} rejected due to redistribution "
            f"restrictions on source={source}, symbol={symbol} "
            f"(LICENSE_RESTRICTION)."
        )
        logger.error(err_restrict, extra={"request_id": request_id})
        raise ValidationError("LICENSE_RESTRICTION: Redistribution limits.")

    return license_info


__all__ = [
    "register_license",
    "validate_license",
]
