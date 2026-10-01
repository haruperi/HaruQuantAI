# Darwinex source

Feature: `FEAT-DM-DARWINEX_ACQUISITION`; requirements `FR-DARWINEX-DECODE`,
`FR-DARWINEX-ACQUIRE`, `FR-DARWINEX-PUBLISH`. Status: candidate, not qualified.

Source DAT 4.1/4.2 decoding, bid/ask log synchronization, volume scaling,
resampling, canonical types and archive preference are retained in one module.
The host streams archives into temporary custody and bounds member expansion.
Add/download/import/status/cancel operations use real host jobs and persistence.
Catalog metadata is the owner script's embedded input; it does not certify
current live provider availability. Imported sides retain source zero/carry rules.

Focused checks cover absolute DAT fields, bid/ask carry, volume scaling and an
actual isolated HTTP-format archive job followed by retained storage reads.
Bounded original/adapted DAT, log and resampling comparisons passed. Live download
published 93,356 real EURUSD ticks. Complete custom catalogs, broker timezone
conversion, large log streaming and complete browser/release qualification remain
pending. Higher bars aggregate the complete bounded request window before
publication; missing-only publication retains existing timestamps. UI source files
are bounded to 6 MiB per symbol.

Malformed later DAT block markers fail closed. The source decoder breaks from
its loop while retaining an uninitialized allocated tail in that case; the
integration rejects that corrupt input rather than publishing unspecified values.
Valid-input decoding formulas are unchanged. This is a bounded input-integrity
adaptation under the approved host safety policy, not a parity assertion.
