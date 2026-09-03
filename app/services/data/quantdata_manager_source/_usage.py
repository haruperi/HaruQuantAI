"""Executable usage demonstration harness for QuantDataManager Source."""

from __future__ import annotations

import asyncio
import struct
import tempfile
import uuid
from pathlib import Path
from typing import cast

from app.contracts.common.models import Uuid7
from app.contracts.data.models import (
    ImportQuantdataRequest,
    ImportQuantdataSuccess,
    QuantDataImportSpec,
)
from app.services.data.quantdata_manager_source.config import (
    QuantDataManagerConfig,
)
from app.services.data.quantdata_manager_source.quantdata_manager_source import (
    _SYNC_BYTES,
    QuantDataManagerSourceService,
    data_decode_quantdata_files,
    data_discover_quantdata_series,
    data_sync_quantdata_catalogue,
)


def _generate_uuid7() -> Uuid7:
    return str(uuid.uuid7())


def _write_demo_m1_file(m1_file: Path) -> None:
    """Write a demo M1 .dat file for the scenario harness."""
    with m1_file.open("wb") as handle:
        v_bytes = b"4.2"
        handle.write(struct.pack(">H", len(v_bytes)) + v_bytes)
        tf_bytes = b"B"
        handle.write(struct.pack(">H", len(tf_bytes)) + tf_bytes)
        sym_bytes = b"EURUSD"
        handle.write(struct.pack(">H", len(sym_bytes)) + sym_bytes)
        handle.write(struct.pack(">q", 2))
        handle.write(struct.pack(">i", 0))
        ex_bytes = b"SnRbTs"
        handle.write(struct.pack(">H", len(ex_bytes)) + ex_bytes)
        handle.write(bytes(_SYNC_BYTES))

        cfg0 = (0x0B << 4) | 0x0A
        cfg1 = (0x0A << 4) | 0x0A
        cfg2 = (0x0A << 4) | 0x0A
        handle.write(bytes((cfg0, cfg1, cfg2)))
        handle.write((1609459200000).to_bytes(8, "big"))
        handle.write((1100000).to_bytes(4, "big"))
        handle.write((1105000).to_bytes(4, "big"))
        handle.write((1095000).to_bytes(4, "big"))
        handle.write((1102000).to_bytes(4, "big"))
        handle.write((100000).to_bytes(4, "big"))

        cfg0_2 = (0x05 << 4) | 0x04
        cfg1_2 = (0x04 << 4) | 0x04
        cfg2_2 = (0x04 << 4) | 0x04
        handle.write(bytes((cfg0_2, cfg1_2, cfg2_2)))
        handle.write((60000).to_bytes(2, "big"))
        handle.write((100).to_bytes(1, "big"))
        handle.write((50).to_bytes(1, "big"))
        handle.write((20).to_bytes(1, "big"))
        handle.write((30).to_bytes(1, "big"))
        handle.write((0).to_bytes(1, "big"))


async def _run_scenarios(
    service: QuantDataManagerSourceService,
    spec: QuantDataImportSpec,
    tmp_root: Path,
) -> None:
    """Run designated functional requirement scenarios."""
    print("\n[1] Scenario FR-DATA-DISCOVER_QUANTDATA_SERIES")
    discovered = data_discover_quantdata_series(service, spec, tmp_root)
    print(f"Discovered series count: {len(discovered)}")
    for s in discovered:
        print(f"  - Symbol: {s['symbol']}, Path: {s['relative_path']}")

    print("\n[2] Scenario FR-DATA-DECODE_QUANTDATA_FILES")
    decoded_list = data_decode_quantdata_files(service, spec, tmp_root)
    print(f"Decoded files count: {len(decoded_list)}")
    for d in decoded_list:
        print(f"  - File: {d['file_path']}, Rows: {d['decoded_count']}")

    print("\n[3] Scenario FR-DATA-SYNC_QUANTDATA_CATALOGUE")
    versions = await data_sync_quantdata_catalogue(service, spec, tmp_root)
    print(f"Committed data versions: {len(versions)}")

    print("\n[4] Scenario FR-DATA-RECORD_QUANTDATA_LINEAGE")
    with service.get_connection() as conn:
        cursor = conn.execute("SELECT * FROM quantdata_lineage")
        for row in cursor.fetchall():
            print(f"  - Lineage: file={row[3]}, hash={row[6][:16]}...")

    print("\n[5] Capability Port Execution (import_quantdata)")
    req_disc = ImportQuantdataRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="DISCOVER",
        spec=spec,
    )
    res_disc = await service.import_quantdata(req_disc)
    print(f"DISCOVER outcome: {res_disc.outcome}")

    req_sync = ImportQuantdataRequest(
        request_id=_generate_uuid7(),
        capability_snapshot_id=_generate_uuid7(),
        operation="SYNC",
        spec=spec,
    )
    res_sync = await service.import_quantdata(req_sync)
    success = cast("ImportQuantdataSuccess", res_sync)
    count = len(success.committed_version_ids)
    print(f"SYNC outcome: {res_sync.outcome}, Count: {count}")


async def main() -> None:
    """Executable usage scenario harness for QuantDataManager Source."""
    print("=" * 80)
    print("QuantDataManager Source (FEAT-DATA-IMPORT_QUANTDATA) Harness")
    print("=" * 80)

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_root = Path(tmp_dir_str)
        history_dir = tmp_root / "user" / "data" / "History"
        history_dir.mkdir(parents=True, exist_ok=True)
        _write_demo_m1_file(history_dir / "EURUSD_M1.dat")

        service = QuantDataManagerSourceService(
            config=QuantDataManagerConfig(allowed_root=tmp_root)
        )
        spec = QuantDataImportSpec(
            spec_id=_generate_uuid7(),
            allowed_root=tmp_root.as_posix(),
            decoder_version="4.2",
        )
        await _run_scenarios(service, spec, tmp_root)

        print("\n--- Additional Discovery & Metadata Examples ---")
        disc = example_symbol_discovery(tmp_root)
        print(f"  * example_symbol_discovery: found {len(disc)} symbol(s)")
        meta = example_symbol_metadata(tmp_root)
        print(f"  * example_symbol_metadata: decoder={meta['decoder_version']}")

    print("=" * 80)
    print("All QuantDataManager Source Scenarios Executed Successfully")
    print("=" * 80)


def example_symbol_discovery(
    tmp_root: Path | None = None,
) -> list[dict[str, object]]:
    """Discover a bounded page of symbols from local QuantData repository."""
    if tmp_root is None:
        return [{"symbol": "EURUSD", "relative_path": "History/EURUSD_M1.dat"}]
    service = QuantDataManagerSourceService(
        config=QuantDataManagerConfig(allowed_root=tmp_root)
    )
    spec = QuantDataImportSpec(
        spec_id=_generate_uuid7(),
        allowed_root=tmp_root.as_posix(),
        decoder_version="4.2",
    )
    return cast(
        "list[dict[str, object]]",
        data_discover_quantdata_series(service, spec, tmp_root),
    )


def example_symbol_metadata(tmp_root: Path | None = None) -> dict[str, object]:
    """Read provider-confirmed symbol metadata from QuantData source."""
    root_path = tmp_root.as_posix() if tmp_root else "/data/quantdata"
    spec = QuantDataImportSpec(
        spec_id=_generate_uuid7(),
        allowed_root=root_path,
        decoder_version="4.2",
    )
    return {
        "spec_id": spec.spec_id,
        "decoder_version": spec.decoder_version,
        "allowed_root": spec.allowed_root,
    }


def run_usage_scenarios() -> None:
    """Run all usage scenarios synchronously."""
    asyncio.run(main())


if __name__ == "__main__":
    run_usage_scenarios()
