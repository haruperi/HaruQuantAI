# File import source

`FEAT-DM-FILE_IMPORT` owns `FR-FILE-PARSE` and `FR-FILE-PUBLISH`.
Status: integration candidate; complete UI and removal qualification pending.

The cohesive file preserves the owner script's predefined formats, candidate
ordering, numeric/date parsing, MT5 sparse-tick correction, descending reversal,
timeframe recognition, rounding and canonical conversion. The host owns jobs,
registered datasets and yearly bar/monthly tick partitions. On existing partitions,
incoming timestamps take precedence, as in the supplied source script.

Uploaded text replaces standalone filesystem reads. Source SQL and import-time
configuration are excluded. The original parser's timezone arguments do not
convert timestamps; parsed timestamps are UTC. Custom formats persist through
scoped host settings. Stock groups publish after successful data imports through
revision-checked workspace catalogs. QDM, large-file streaming and end-of-bar
conversion remain unsupported; unsupported timezone and end-bar choices fail
explicitly. Tick imports also publish the script-derived M1 resource.

Evidence: `tests/plugin/DataSource/test_file_import.py` and five exact original vs
adapted parser comparisons under the approved task evidence directory. These do
not prove all format combinations or independent SQX parity.
