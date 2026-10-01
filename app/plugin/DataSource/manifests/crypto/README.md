# Crypto source

`FEAT-DM-CRYPTO_ACQUISITION` owns `FR-CRYPTO-ACQUIRE` and `FR-CRYPTO-PUBLISH`.
Status: candidate under development, not qualified.

Six source exchange drivers retain endpoint selection, symbol normalization,
timeframe conversion, pagination and candle field ordering. Runtime sessions and
jobs are injected; source singleton, SQL and SQX synchronization are excluded.
Floating crypto volume is preserved in yearly partitions. Explicit request failures
are counted so a partial publication is not reported as complete acquisition.

Focused tests cover six exchange candle mappings, notation, fractional-volume
custody, nested retries and Retry-After. Six exact source-driver fixture
comparisons passed. Frontend tests require actual job results and cover cancel
races. All six exchanges returned live symbol catalogs and one real daily candle
each in isolated custody. Broader differential/retry edge cases and complete
browser/removal qualification remain outstanding. Metadata fallback defaults remain source defaults,
not evidence that an exchange returned those values.
