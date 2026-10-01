# Data source plugin registry

Dukascopy's Python user API exports only `add_symbol`, `download_data`, and
`show_disclaimer`, matching its three UI dropdown actions and the reference script.
Other module-defined functions are internal. The host-only `prepare` lifecycle
alias is excluded from `__all__`; CLI commands continue through internal helpers.

Status: integration candidate, 2026-09-30. The prior README's Qualified assertions
are historical and do not qualify the current candidate. Source code was absent
at the audited baseline; this integration is being independently verified.

The owner-written implementations under `SQX_REFERENCE_ROOT/scripts/` take
precedence for provider behavior. Host capabilities own transport, jobs and data
custody; one cohesive Python file owns each source. No independent SQX parity
claim is made.

| Feature | Owning module | Current implementation |
| --- | --- | --- |
| `FEAT-DM-DUKASCOPY_ACQUISITION` / `FR-DATA-001` | `dukascopy.py` | Direct acquisition, script numeric decoding/header repair, annual CDN decode, partial hourly publication; candidate |
| `FEAT-DM-YAHOO_ACQUISITION` | `yahoo.py` | Real chart/session acquisition and custody; see [Yahoo registry](manifests/yahoo/README.md) |
| `FEAT-DM-FILE_IMPORT` | `file_import.py` | Real parser/import jobs; [registry](manifests/file_import/README.md) |
| `FEAT-DM-CRYPTO_ACQUISITION` | `crypto.py` | Six exchanges and real jobs; [registry](manifests/crypto/README.md) |
| `FEAT-DM-MT5_ACQUISITION` | `mt5.py` | Historical terminal worker and custody; [registry](manifests/mt5/README.md) |
| `FEAT-DM-TICK_DOWNLOADER` | `tick_downloader_import.py` | Actual BI5 upload/import; [registry](manifests/tick_downloader/README.md) |
| `FEAT-DM-SQ_EQUITY` | `sq_equity.py` | Actual authenticated acquisition and custody; [registry](manifests/sq_equity/README.md) |
| `FEAT-DM-SQ_FUTURES` | `sq_futures.py` | Actual authenticated acquisition and Open Interest; [registry](manifests/sq_futures/README.md) |
| `FEAT-DM-EXTERNAL_INDICATORS` | `external_indicators.py` | Real uploaded values, immutable revisions and durable definitions; candidate |
| `FEAT-DM-DARWINEX_ACQUISITION` | `darwinex.py` | DAT/CDN and bid/ask log jobs; [registry](manifests/darwinex/README.md) |

Paired provider manifests remain beside their UI contributions and own their
backend files. SQ headless manifests remain under `manifests/`.
Tick decoding preserves the source NumPy price scaling and float32 side-volume
rounding; canonical storage combines both side volumes. All Sunday hours are
requested. Missing hours do not discard received rows or acquire false coverage.
Subsequent missing-mode runs request unreceived chunks. CDN members are decoded
from bounded host-spooled ZIPs; individual absent chunks fall back to direct retrieval.

The module retains legacy host-facing acquisition glue and its complete source
catalog. Bounded original/adapted numerical comparisons and live acquisition passed;
these do not certify every retry, catalog or format combination. Cohort removal,
fresh backend reads and UI rebuilds passed in isolated installations. Complete
per-case browser evidence and final source-bound release qualification remain
outstanding. Parameters live in the module, not in a duplicated table here.

Focused commands:

```sh
uv run pytest tests/plugin/DataSource/test_dukascopy.py tests/plugin/DataSource/test_yahoo.py --no-cov
uv run python -m tests.examples.dukascopy_offline
```

Dukascopy now also has a host-backed provider CLI, idempotent definition addition,
HTTP fallback after HTTPS failure, and bounded multi-year/concurrent acquisition.
Its [registry](manifests/dukascopy/README.md) records explicit raw result resources,
canonical compatibility, and the host-backed general Data Manager CLI.
The new work does not qualify the other providers or assert complete source parity.

Historical repository versions and task evidence remain in Git and
`.agents/logs/`. Current execution evidence is maintained under
`.agents/logs/20260930_datamanager_script_integration/`.
