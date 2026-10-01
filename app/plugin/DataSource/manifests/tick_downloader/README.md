# Tick Downloader source

Owner: `plugin.data_manager.tick_downloader`; Data Manager acquisition slot 1.0.0.
Feature: `FEAT-DM-TICK_DOWNLOADER`; requirements: `FR-TD-DECODE`, `FR-TD-PUBLISH`.

Candidate. Uploaded BI5 hours use the owner script's big-endian fields, decimal
scaling, float32 side-volume rounding, canonical tick/M1 conversion and
incoming-first partition merge. Catalog decimal metadata is local to this plugin.
The backend inspects logical uploaded paths; it never opens arbitrary server paths.

UI uploads actual bytes, one bounded hour per host job, and reads actual catalog
and job state. Files are capped at 6 MiB, backend batches at 8 MiB base64 and 128
hours, expansion at 128 MiB. Corrupt/truncated files fail explicitly. Published
rows survive provider removal. No simulated progress or browser-owned datasets.

Zero-based month paths are supported. One-based fallback directory semantics,
higher-timeframe import UI, missing-mode optimization, large-file streaming,
durable job recovery, differential/live/removal qualification remain pending.
This candidate is not a release or independently certified SQX parity.
