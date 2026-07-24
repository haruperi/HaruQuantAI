# FEAT-BRK-12 cTrader Market Data

This folder is the sole production owner of this focused Brokers feature. Current
status is `Partial` until the validation gates in the package README complete.
`operations.py` owns cTrader market-data operations; `sessions.py` maps full-symbol
weekly intervals and broker holiday closures into `BrokerTradingSession` without
generating or guessing venue hours. Public API, contracts, requirements, and usage
evidence are registered only in `app/services/brokers/README.md`.
