# SQ Futures source

Status: integration candidate; bounded authenticated live acquisition passed.
Complete UI and removal qualification remains pending.
Feature: `FEAT-DM-SQ_FUTURES`. Requirements:
`FR-SQ-FUTURES-CATALOG`, `FR-SQ-FUTURES-DECODE`,
`FR-SQ-FUTURES-PUBLISH`.

One source file owns script-derived DAT decoding, canonical numeric schema,
symbol routing, parameter schemas and acquisition jobs. It attaches exclusively
to Data Manager; the SQData presentation package routes to this capability.
The embedded public catalog is a 70,131-row metadata snapshot from the
owner-script database. No database connection, donor path, or credential is
embedded. Credentials are configured in an ephemeral host network session.

Source DAT behavior supports versions 4.1/4.2, delta reconstruction and volume
scaling. The host bounds records and archive sizes. Daily futures retain Open
Interest; minute futures preserve the script's six-column canonical schema.
No independent SQX parity is claimed. Bounded DAT and resampling comparisons
against the original source passed. Complete browser qualification remains pending.

Actual script authentication acquired four daily rows for 2024-01-02 through
2024-01-05 into isolated custody. A fresh producer-independent reader returned
equal rows after source shutdown. Timestamps, source fingerprints and partition
hashes are in the task's `sq-authenticated-acquisition.json`. No credentials were
stored in repository files. The universal loader accepts bounded contribution
sources up to 4 MiB so the complete metadata catalog can remain cohesive.
