# Yahoo Data Source

Owner: `workspace.data_manager`. Package: `plugin.data_manager.yahoo`.
Status: integration candidate; live provider and complete UI qualification pending.

`app/plugin/DataSource/yahoo.py` owns `FEAT-DM-YAHOO_ACQUISITION` and its
`FR-YAHOO-CHART-QUERY`, `FR-YAHOO-RESAMPLE`, and `FR-YAHOO-PUBLISH` requirements.
The local manifest owns exact package paths and the acquisition-slot attachment.

The implementation reuses the owner's script interval normalization, chart
decoding, date windows and resampling routines. HTTP sessions and finite jobs are
bound through host capabilities. No source SQL or operational paths are exposed
to the plugin. Parameters are described by the module's Pydantic models; catalog
responses include their schema. Cookie state is private to the prepared source.

Definitions persist source parameters and returned metadata. Acquisition publishes
immutable, digest-checked Parquet partitions and only then updates inventory.
Missing data, failed chunks and failed publication cannot report success. Source
catalog provisioning is explicit; this candidate never migrates an existing store
at startup. Old browser fixtures are not imported as dataset truth.

Focused evidence: `tests/plugin/DataSource/test_yahoo.py` covers recorded-format
responses, null and adjusted-close handling, timeframe aggregation and the real
job-to-custody flow against isolated storage. These tests do not establish current
Yahoo service availability or independent SQX parity.

Removal retains published partitions and catalog records, which host custody can
read without this plugin. The full removal/restart matrix is still pending.
