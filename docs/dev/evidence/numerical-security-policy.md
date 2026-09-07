# HaruQuantAI V3 — Numerical and Security Policy

## 1. Numerical Arithmetic & Precision Policy

1. **Integer & Scaled Representation:** All monetary quantities, prices, and account balances must use either:
   - Fixed-point integer scaled units (e.g. basis points, cents, pips * 10^5), OR
   - High-precision `Decimal` objects where performance permits, OR
   - Double-precision IEEE 754 float strictly bounded by epsilon equality checks:
     `abs(a - b) < 1e-9`.
2. **Deterministic Computations:**
   - Numerical calculations (drawdown, Sharpe ratio, profit factor, margins) must be causal and reproduce identical results across runs given identical inputs.
   - Any pseudo-random generator (Monte Carlo simulations, genetic builder) must accept an explicit `seed` parameter and default to deterministic behavior.
3. **No Lookahead Bias:**
   - Bar and indicator calculations must strictly consume data with timestamps `<= current_bar_timestamp`.
   - Event handling in simulators must preserve strict causal order (Tick -> Fill -> State Update).

## 2. Security and Isolation Policy

1. **Credential Redaction:**
   - Secrets, broker API keys, and session tokens must NEVER be logged or included in trace outputs.
   - User passwords must use versioned scrypt hashing; only SHA-256 session digests are persisted.
2. **Code Execution Sandboxing:**
   - Custom Python strategies and indicators must run in bounded worker processes with memory limits, restricted import whitelists, and execution timeouts.
3. **SQL & Path Safety:**
   - SQLite queries must use parameterized placeholders (`?`) exclusively. Dynamic table or field names must be strictly validated against static allowlists.
   - File paths must be strictly checked to prevent path traversal attacks outside the designated workspace directories.
