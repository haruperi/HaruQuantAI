# FEAT-BRK-CONNECT_CTRADER — cTrader Provider

Own one removable cTrader application/account integration. The feature verifies the
configured provider environment/account at the session boundary, performs genuine
provider reads, and transports already-authorized orders without provider fallback.

It provides only `broker.provider.ctrader@1`; the dispatcher republishes the public
Broker capabilities. Instrument identity/mappings remain Catalogue-owned and
risk/release admission remains outside Brokers.
