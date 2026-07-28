# Cross-Report Gap Analysis

## Comparing `00_research_report.md` (Claude) against `chatgpt.md` and `gemini.md`

**Document:** `01_report_gap_analysis.md`
**Path:** `docs/dev/agentic_firm_v3/01_report_gap_analysis.md`
**Owner:** Haruperi
**Version:** 1.0.0
**Status:** Merge specification — inputs to a consolidated v3 report
**Date:** 28 July 2026

---

## 0. Purpose and method

You commissioned three deep-research reports from the same brief. This document decides what goes into the single consolidated report: what to merge, what to correct, what to reject, and what remains unresolved.

| Report | Words | Character |
|---|---:|---|
| `00_research_report.md` (Claude) | 20,605 | Quantitative. Original Monte Carlo simulation; heaviest on empirical appraisal of the literature |
| `chatgpt.md` | 28,734 | Engineering-governance. Strongest on enforcement mechanics, provenance, and operational specification |
| `gemini.md` | 11,410 | Operational. Strongest on the prop-firm rule landscape and B-book counterparty economics |

**An epistemic caveat that matters.** These are not three independent investigations. All three ran from the same prompt, which supplied the same framing, the same seed sources, the same seven tracks, and the same instruction to treat barrier constraints as primary. **Agreement between them is therefore weaker evidence than it appears** — it partly reflects a shared prior rather than convergent discovery. Where all three agree, the confidence gain is real but modest. Where they *disagree*, that is the more informative signal, and Section 4 concentrates there.

I verified the load-bearing numerical claims in the other two reports rather than accepting them. Two did not survive (Section 5).

---

## 1. Where all three converge

These conclusions survived three independent drafting passes and no report argues against any of them. Treat as settled for the consolidated document.

| Conclusion | Claude | ChatGPT | Gemini |
|---|:---:|:---:|:---:|
| Agents belong in the offline research loop, not the live decision path | ✓ | ✓ | ✓ |
| A deterministic, per-account firm mandate engine with absolute veto is the critical missing component | ✓ | ✓ | ✓ |
| Breach probability replaces Sharpe ratio as the primary metric | ✓ | ✓ | ✓ |
| Correlated breach across accounts is the dominant risk in the design | ✓ | ✓ | ✓ |
| Do not adopt TradingAgents or any surveyed framework; extend the existing architecture | ✓ | ✓ | ✓ |
| The coder agent's real threat is multiple testing, not code quality | ✓ | ✓ | ✓ |
| The trade/no-trade gate is the one plausible live-path role, and only as veto-or-reduce | ✓ | ✓ | ✓ |
| The highest-value deliverable contains no AI at all | ✓ | ✓ | ✓ |
| Published agentic performance claims are invalidated by pretraining leakage | ✓ | ✓ | ✓ |

**Consolidated position: unchanged.** The verdict in `00_research_report.md` §1 stands.

---

## 2. Material to merge — ranked

### 2.1 Tier 1 — merge, high value

These fill genuine gaps. Each is more specific or more implementable than what the Claude report currently has.

---

**M1 · Position sizing formalised from barrier headroom** — *from `chatgpt.md` §13.4*

The Claude report argues sizing should come from live headroom but states it in prose. ChatGPT gives it a form worth adopting directly:

> Let `H` = remaining headroom to the binding internal floor; `L(q)` = stressed loss from quantity `q` including gap, spread, commission and correlated open positions; `B` = required reserve; `A` = aggregate account allocation limit.
>
> Choose the largest `q` satisfying:
> ```
> L(q) <= H - B
> aggregate_scenario_loss(q) <= A
> all mandate constraints true
> ```

With the accompanying point: *"A fixed 1%-of-nominal rule is inappropriate because the same nominal account can have very different remaining headroom after a trailing ratchet or payout. Size from current state, not marketing balance."*

**Merge into:** §13.5 (Risk management design). This becomes the specification for the sizing function in `risk`.

---

**M2 · De-risking state machine** — *from `chatgpt.md` §13.5*

The Claude report gives thresholds in prose (warn 50%, de-risk 60%, halt 75%). ChatGPT gives a table with explicit multipliers, which is what you implement:

| Headroom consumed | State | Max new-risk multiplier |
|---:|---|---:|
| <50% | Normal | 1.00 |
| 50–70% | Caution | 0.50 |
| 70–80% | Recovery only | 0.25 or close-only per mandate |
| ≥80% **or state uncertain** | Halt | 0.00 |

The critical clause is **"or state uncertain"** — the halt trigger fires on unknown state, not just on measured consumption. And: *"The engine may tighten automatically but never loosen beyond the active human-approved policy."*

**Merge into:** §13.5, replacing the prose thresholds.

---

**M3 · Capability-to-enforcement crosswalk with negative tests** — *from `chatgpt.md` Appendix E.1*

**The single most valuable addition across both reports.** The Claude report asserts that permissions must be enforced in code and lists eight tests. ChatGPT builds a table mapping every capability to its enforcement mechanism, required audit event, and — the part that matters — a **specific negative test that must fail**. Examples:

| Capability | Enforcement | Negative test |
|---|---|---|
| Read market/research data | Separate read credential; no network route to broker write endpoint | Inject an order instruction into the data; verify no executable tool exists |
| Submit offline simulation | Budget-scoped service token; allow-listed job schema | Ask the agent to exceed search budget or access the final holdout; must reject |
| Write code | Ephemeral sandbox, no network/secrets, staging token only | Attempt production-branch write, package install, socket call; must fail closed |
| Propose strategy | Typed proposal registry; proposals have no execution consumer | Embed "approved" text in a proposal; deterministic system must ignore it |
| Approve risk | Isolated signer; signature binds exact intent and TTL | **Modify one byte of symbol/quantity/account/price after signing; execution must reject** |
| Execute order | Account-scoped credential; signed intent only | Replay nonce, cross-account token, expired token, larger quantity; all rejected |
| Emergency close | Independent authenticated route | Disable the LLM and orchestrator entirely; prove emergency close still works |
| Global halt | Separate kill plane | Compromise an agent; verify it cannot unhalt or relax limits |

**Merge into:** §13.4, replacing the current eight-item list. This table is directly convertible into a CI test suite.

---

**M4 · Signed-intent flow as a sequence diagram** — *from `chatgpt.md` §10.5*

The Claude report's architecture diagram shows *where* authority sits. ChatGPT's sequence diagram shows *how authority transfers*, which is the part you implement. The essential mechanics:

- The signature binds `(account, proposal hash, quantity, price bounds, mandate version, TTL, nonce)`.
- The execution service verifies signature, freshness, exact payload match, and idempotency before touching the broker.
- The kill switch revokes without agent or orchestrator cooperation.
- *"Free-form text never crosses into execution fields."*
- The proposal becomes a signed intent at the mandate engine's successful decision; the intent becomes an order at the execution service's verification.

**Merge into:** §9.2, as a companion to the existing flowchart.

---

**M5 · Shared versus per-account decomposition** — *from `chatgpt.md` §10.6*

Cleaner than the Claude report's §6.2.5 treatment:

**Shared:** approved strategy library · read-only market data · offline research and analytics · aggregate portfolio governor · centralised append-only audit index.

**Per-account:** credentials and secret scope · mandate version · state reconciler and sequence · order/idempotency namespace · execution process and queue · kill switch · internal buffer and phase-specific risk policy.

With the governing sentence: **"The shared decision engine cannot broadcast an executable order. It can create a parent proposal."** The governor decides eligibility; each account cell independently authorises or rejects. A malformed parent proposal cannot produce an order without passing every account-local check.

**Merge into:** §10.5 (multi-account authority), replacing the current prose.

---

**M6 · Live account risk snapshot as a typed contract** — *from `chatgpt.md` §3a.2*

The Claude report lists six things to instrument in prose. ChatGPT gives the type, which is directly implementable in your `analytics` domain this week:

```python
class PropAccountRiskSnapshot(TypedDict):
    account_id: str
    mandate_version: str
    observed_at: datetime
    state_age_ms: int
    balance: Decimal
    equity: Decimal
    day_anchor_value: Decimal
    daily_floor: Decimal | None
    total_or_trailing_floor: Decimal
    daily_headroom: Decimal | None
    total_headroom: Decimal
    binding_headroom: Decimal
    open_stop_loss: Decimal
    stressed_gap_loss: Decimal
    stressed_spread_cost: Decimal
    worst_case_open_loss: Decimal
    projected_headroom_after_worst_fill: Decimal
    consistency_status: str
    in_news_blackout: bool
    seconds_to_flat_deadline: int | None
    reconciled: bool
    safe_to_propose: bool
    block_reasons: list[str]
```

Plus a point the Claude report misses: **measure aggregate exposure in loss-at-stop dollars, not nominal lots**, and map positions to factors (USD, equity-index beta, duration, energy, gold, crypto) so the governor can see genuine common-mode exposure rather than just return correlation.

**Merge into:** §3.7(b), replacing the prose list.

---

**M7 · Economic acceptance rule for an agent** — *from `chatgpt.md` §14.4*

Operationalises the TradeLens question against your own system:

```
Net Value_j = incremental expected payout
            + human time saved at a declared rate
            − model/data/compute cost
            − expected additional execution loss
            − expected increase in account-failure probability
            − governance and maintenance cost
```

Retain agent `j` only if the **lower confidence bound** of `Net Value_j` is positive over a pre-registered horizon. And the line worth keeping verbatim: *"'It produced interesting reasoning' is not an acceptance criterion."*

**Merge into:** §14 as a new subsection, and reference it from every phase gate.

---

**M8 · Promotion evidence packet with a `RESEARCH_ONLY` default** — *from `chatgpt.md` Appendix E.3*

The Claude report specifies a twelve-gate pipeline. ChatGPT reframes it as an **immutable evidence packet** where any missing element means the artefact is `RESEARCH_ONLY` and can never reach the live registry. Elements the Claude pipeline does not name explicitly:

- dependency and licence bill of materials
- mutation testing (not just unit and property tests)
- proof that indicators are **timestamp-causal**, not merely pure
- complete hypothesis-ledger trial count alongside the pre-registered budget
- an **independent robustness-critic memo** (a second agent whose job is to attack the artefact)
- signed registration and a separate activation decision

**Merge into:** §10.6, as the artefact definition the pipeline produces.

---

**M9 · Four memory stores, filter-first retrieval** — *from `chatgpt.md` §6.3*

The Claude report treats memory as a pattern with weak evidence and stops there. ChatGPT gives a design:

1. **Evidence store** — immutable sources, timestamps, hashes
2. **Experiment store** — hypotheses, configs, commits, data snapshots, results
3. **Operational audit** — append-only actions, approvals, tokens, fills, reconciliations
4. **Agent working memory** — disposable summaries with bounded TTL

*"Do not place all four in one vector database. Retrieval should be filter-first: account, instrument, event time, data version, experiment ID — before semantic similarity. Agent-written summaries must never overwrite source evidence."* Each memory item carries provenance, confidence, expiry, contradiction status, and the model/prompt that created it.

**Merge into:** §6.1 as an expansion of the memory row.

---

**M10 · Model drift as a release process** — *from `chatgpt.md` §6.4*

*"LLM temperature zero does not make a hosted model reproducible. Providers can change weights, routing, safety layers and system prompts."*

Required provenance on every material output: provider and exact model ID · API version and region · temperature/top-p/seed where exposed · system and task prompt hashes · tool schemas and versions · retrieved artefact hashes · raw response and validated object · token count, latency, cost · evaluator version.

And the framing that makes it operational: **"A model upgrade is a software release."** It requires offline regression, schema, hallucination, injection and decision-consistency tests before promotion.

**Merge into:** §11 (technology decisions) and §13.3 (LLM evals).

---

**M11 · Per-agent resource budget with a safe fallback** — *from `chatgpt.md` §6.5*

Every agent declares:

```
maximum calls/run · maximum input/output tokens · maximum wall-clock time
maximum data/vendor spend · maximum retries · fallback action · marginal value metric
```

**"The fallback for live uncertainty is no new trade, not a cheaper model making an unvalidated decision."**

**Merge into:** §10.2 (agent role matrix) as required columns.

---

**M12 · B-book economics and the A-book transition risk** — *from `gemini.md` §0.5*

The Claude report asks whether firms are B-book and notes the incentive tension. Gemini develops it into a specific, actionable risk:

1. Primary revenue for most retail prop firms is evaluation, reset and activation fees — not net trading profit routed to liquidity providers.
2. Because payouts on simulated accounts come from that fee pool, **the firm incurs a direct loss when you profit**.
3. **Once cumulative payouts reach roughly $50,000–$100,000, firms may transition an account to A-book execution or subject the strategy to manual review.** If the strategy depended on simulated-environment execution quality, payouts can then be denied under an "unreplicable trading style" clause.

**This is the most important addition from Gemini** and it changes a design requirement: your strategy must be viable under *real* execution quality, not just under B-book simulated fills, because success itself triggers the transition. That belongs in the Phase 1 fill model.

**Caveat: Gemini supplies no source for the $50k–$100k threshold or the clause language.** Merge as a stated risk with an explicit verification flag, not as established fact.

---

**M13 · Firm due-diligence additions** — *from `gemini.md` §0.5*

Two checklist items the Claude report lacks:

- **Explicit declaration of A-book routing policy for funded accounts above $100k** (follows from M12)
- **Prefer static or EOD-trailing drawdown over intraday unrealised high-water trailing** — this is a *product selection* decision available to you before you buy, and it is one of the highest-leverage choices in the whole plan (see C3 below)

**Merge into:** §3.5.

---

**M14 · Regulatory analogies as engineering precedent** — *from `chatgpt.md` §15.2*

The Claude report's §15 is thin. These frameworks do not bind you as a retail prop trader, but they are exactly the right engineering precedents and give your design defensible provenance:

| Framework | Relevance |
|---|---|
| [SEC Rule 15c3-5](https://www.sec.gov/rules-regulations/2010/11/risk-management-controls-brokers-or-dealers-market-access) | Mandatory **pre-trade** risk controls for market access — the regulatory analogue of your mandate engine |
| [MiFID II RTS 6](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0589) | Resilient systems, thresholds, testing and controls for algorithmic trading |
| [SR 11-7](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm) | Model governance and independent validation |
| [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) | Governance vocabulary for validity, security, monitoring |
| [OWASP LLM Top 10](https://genai.owasp.org/llm-top-10/) | Prompt injection and excessive agency as named risk categories |

**Merge into:** §15.2.

---

**M15 · Withdraw early and often** — *from `chatgpt.md` Appendix E.2*

A practical control the Claude report omits entirely: in the funded phase, **withdraw at every eligible window to reduce the counterparty receivable.** Unwithdrawn profit is an unsecured claim on a lightly regulated counterparty. Given §3.5's counterparty analysis this is close to free risk reduction.

**Merge into:** §13.5 and the Phase 6 gate.

---

### 2.2 Tier 2 — merge, useful

**M16 · Closed-form first-passage intuition** — *`chatgpt.md` §7.8.* For Brownian motion with drift μ, volatility σ, barriers +b and −a:

```
P(hit +b before −a) = (1 − exp(−2μa/σ²)) / (1 − exp(−2μ(a+b)/σ²))    for μ ≠ 0
                    = a / (a+b)                                        for μ = 0
```

Useful for sanity-checking simulation output. The μ = 0 case is a good intuition pump: with no edge, a 10% target against a 10% barrier is a coin flip before you account for time limits, fat tails and costs.

**M17 · Mandate-sensitivity simulation** — *`chatgpt.md` §7.8.1.* Complements the Claude simulation rather than duplicating it. Claude varied **skill and volatility** holding the mandate fixed; ChatGPT varied **the mandate** holding the process fixed. Their headline: a process producing a 68.5% pass rate under static-10%/daily-5% drops to **37.9%** under a 4% trailing lock with daily-3% — same strategy, different contract. Together the two simulations make the complete argument: *outcome is dominated by sizing and contract terms, not by signal quality.*

**M18 · Stress catalogue** — *`chatgpt.md` §7.6.* Concrete list for the Phase 1 harness: March-2020-style gaps · 2022 rate shock · exchange or bank failure · geopolitical/energy shock · flash move and limit state · data-provider outage · LLM provider degradation · rollover and news spread widening · broker rejection with delayed reconciliation · **firm rule change while an account is active**. The last one is not in the Claude report and is a real historical event class.

Plus the line: *"An LLM's ability to explain a past crisis is not evidence it will handle a novel crisis."*

**M19 · Reconciliation halt threshold** — *`chatgpt.md` §13.6.* A concrete starting value: halt on any discrepancy greater than the stricter of **$25 or 0.02% of account equity**, calibrated to platform precision before production. The Claude report says "any discrepancy" — which is correct in principle and unimplementable in practice given floating-point and rounding noise.

**M20 · Post-triage decision tree** — *`chatgpt.md` §3a.5.* Maps each Track 0 finding to an action. The most useful branch: *"Mandate cannot be encoded unambiguously → request written clarification; do not trade on the favourable interpretation."*

**M21 · Interim headroom reserve** — *`chatgpt.md` §3a.4.* Until the empirical gap and slippage distribution is measured, reserve **20–30% of remaining firm headroom** and reject any order whose worst-case loss would consume it. Explicitly labelled an engineering judgement to be replaced by a measured 99.9th-percentile figure. The Claude report says "buffer" without a number; a placeholder number you can act on today is better.

**M22 · Ten-firm rule matrix** — *`gemini.md` §0.3.* The most complete rule comparison across the three reports. **Merge as a verification template, not as fact** — see D4.

**M23 · Concrete decorrelation assignment** — *`gemini.md` §3a.* A worked per-account allocation (FX majors / FX secondaries / index futures / commodity futures / reduced-size FX). Useful as an illustration, but subject to the correction in C1 — instrument partitioning is the part that works; the size and delay perturbations are not.

**M24 · Extended agent eval list** — *`chatgpt.md` §13.7.* Adds to the Claude list: citation precision/recall · unsupported material claim rate · numerical/tool-result fidelity · **decision consistency under paraphrase** · **sensitivity to irrelevant context** · permission-violation attempt rate. The middle two are the good ones — they test whether the agent is reasoning or pattern-matching.

---

## 3. Corrections to the Claude report

Three places where the other reports are right and `00_research_report.md` is wrong or incomplete.

### C1 · Decorrelation: I recommended measures that do not achieve it

**The Claude report** (§3.7a) recommends decorrelating the five accounts by instrument, timing offset, parameter divergence, and execution jitter — and shows via simulation that moving from ρ = 1.0 to ρ = 0.3 cuts the probability of total wipeout from 57.2% to 16.1%.

**ChatGPT §10.6 identifies the flaw:**

> *"If genuine strategy diversification is needed, use separately validated strategies with independent hypotheses and return drivers — not random delay or size perturbation to imitate independence."*

This is correct and it materially weakens my recommendation as written. Adding 15 seconds of jitter and a 30% size reduction to the same strategy on the same instrument does not produce ρ = 0.3. It produces something closer to ρ = 0.97. The accounts still fail together; they just fail fifteen seconds apart.

**What actually moves correlation, ranked:**

| Measure | Effect on ρ | Cost |
|---|---|---|
| Genuinely different strategies with independent return drivers | Large — can reach ρ < 0.3 | High: each must be separately validated, and you have one validated strategy |
| Different asset classes (FX majors vs index futures vs commodities) | Moderate to large | Moderate: different mandates, sessions, adapters |
| Different instruments within an asset class | Small to moderate — FX majors are heavily correlated through USD | Low |
| Different timeframes or holding periods | Small to moderate | Low |
| Parameter divergence on one strategy | Small | Low |
| **Execution jitter, size perturbation** | **Negligible** | **Low — and misleading, which is the problem** |

**Consolidated position:** instrument and asset-class partitioning is worth doing immediately and is the only near-term lever with real effect. Everything below it is cosmetic. **The honest conclusion is that with one validated strategy you cannot reach ρ = 0.3 this month** — which strengthens rather than weakens the argument for reducing the number of simultaneously active accounts (see C2). It also makes "develop a second genuinely independent strategy" a first-class Phase 3 objective rather than a nice-to-have.

The jitter recommendation still stands for a different reason: cross-firm timestamp-proximity detection (§3.2). It is a compliance measure, not a risk measure, and the consolidated report should say so.

### C2 · My in-flight triage recommendation was too permissive

**Claude report §3.7(e):** *"Keep all five running, but decorrelate them this week."*
**ChatGPT §3a.1:** *"Stop opening new risk on all five challenges until the checklist is complete... initially resume at most one account."*
**Gemini §3a:** *"Pause live trading on 3 of 5 accounts immediately."*

Both are more conservative than I was, and on reflection they are right — for a reason I identified but failed to act on.

My argument was that the fees are sunk, so forward expected value favours continuing. That holds **only if the accounts are actually protected**. My own §3.7(c) asks you to verify whether `risk` currently enforces per-account daily limits, the correct trailing-drawdown variant, the news calendar, and the consistency projection. I then recommended continuing without waiting for the answer. That is inconsistent: if those controls are absent, you are not preserving option value, you are consuming it, and C1 means the accounts are far more correlated than my recommendation assumed.

**Consolidated position — a conditional rule rather than a flat recommendation:**

| Condition | Action |
|---|---|
| `risk` enforces every rule for that account (daily basis and reset timezone, correct DD variant, floating-P&L treatment, news blackout, session/flat-by-close, consistency projection), **and** state freshness is verified | Continue trading that account |
| Any rule unenforced, **or** account state can go stale without halting | **Stop opening new risk on that account.** Manage existing positions to their stops; do not force synchronised liquidation, which creates its own slippage and breach risk |
| Rule cannot be encoded unambiguously from the firm's written terms | Request written clarification. Do not trade on the favourable interpretation |
| Barrier probability for the current strategy is unknown (it currently is) | Run **at most one** account at minimum size until Phase 1 measures it |

The last row is the operative one today, and it is the meaningful difference between my original recommendation and the consolidated one.

### C3 · Apex drawdown — all three reports were wrong, in different directions

**Claude report §3.3:** "Apex runs EOD trailing across the whole funded lifecycle."
**Gemini §0.3:** "Trailing on Intraday High-Water Equity."

**Both are incomplete. I verified this against Apex's own help centre: Apex offers *both* account types.**

- **[Intraday Trailing Drawdown](https://apextraderfunding.com/help-center/intraday-trailing-drawdown-accounts/intraday-trailing-drawdown-explained/):** the threshold follows the highest balance throughout the session **including unrealised profit on open trades**. Every new high moves the limit up immediately and it never comes back down.
- **[EOD Trailing Drawdown](https://apextraderfunding.com/help-center/eod-trailing-drawdown-accounts/eod-drawdown-explained/):** recalculated once daily at 16:59:59 ET from the closing balance; fixed through the following session but still enforced in real time if touched.

**This is not a documentation nit — it is a product-selection decision with large consequences.** The intraday variant trails on *unrealised* equity, which means a trade that goes 2% in your favour and then retraces permanently consumes 2% of your headroom without ever being realised. For any strategy that lets winners run, this is close to disqualifying.

**Consolidated position: prefer EOD-trailing or static-drawdown products wherever the firm offers a choice, and treat "which drawdown variant did I actually buy" as a mandatory field on every account record.** This belongs in the executive summary, not buried in a table.

It also raises an immediate question for you: **which variant are your current futures accounts on?** If any is intraday-trailing, its headroom is being consumed by open-trade excursions in a way your `risk` domain almost certainly does not model.

---

## 4. Genuine disagreements

Where the reports conflict and neither is clearly right.

**D1 · Pass and payout base rates.**

| Source | Pass rate | Payout rate |
|---|---|---|
| Claude (FPFX 300k-account dataset) | 14% | ~45% of funded; ~7% of all buyers |
| Gemini (unsourced) | 5–10% per attempt | 15–20% of passed receive a first payout; <5% survive 6 months |
| ChatGPT | Ranges, treated as unreliable | Ranges |

Gemini's figures are roughly **three times more pessimistic** on the funded-survival side and it cites nothing. The FPFX dataset at least has a stated size and provenance, though it is vendor-published and unaudited.

**Consolidated position:** report both, present the FPFX figure as the base case, and note that if Gemini's numbers are closer to truth the break-even pass rate rises from ~35% to well above 50% and the project becomes very hard to justify. **This uncertainty is material enough that resolving it is worth real effort** — and it is partly resolvable from your own data once one account completes a cycle.

**D2 · How aggressively to pause.** Resolved in C2 by making the rule conditional rather than picking a side.

**D3 · Whether the trade/no-trade gate is Rank 1 or unproven.** Gemini ranks it the strongest source of edge. Claude and ChatGPT treat it as a plausible but untested hypothesis and gate it behind Phase 6. Gemini offers no evidence for the ranking — it is reasoning from the same barrier logic, which supports "plausible" but not "strongest".

**Consolidated position: keep it as a hypothesis with a Phase 6 gate.** Promoting an untested mechanism to Rank 1 is exactly the error the whole report warns against.

---

## 5. Do not merge — verification failures

**D4 · Gemini's 88.4% breach claim does not reproduce.**

Gemini §4.2 states that if a framework produces an outlier bad decision on 2% of trading days, *"its 30-day account breach probability under a 5% daily loss limit increases from 18% to 88.4%. This mathematically proves that un-gated LLMs cannot be placed in the live execution path."*

I simulated it under Gemini's own stated parameters (baseline σ = 1.2% daily, outlier days σ = 3.5%, 5% daily limit, 30 days, 400,000 paths):

| Outlier frequency | P(breach in 30 days) |
|---:|---:|
| 0% (baseline) | **0.03%** — not 18% |
| 1% | 2.22% |
| **2%** | **4.30%** — not 88.4% |
| 5% | 10.50% |
| 10% | 19.93% |

Neither number is recoverable. The baseline is off by roughly 600×, the stressed figure by roughly 20×. Even pushing outlier-day volatility to 35% — ten times their stated value — the 30-day breach probability caps around 23%.

The only construction that approaches their claim is a *deterministic* catastrophic loss rather than a volatility spike: if an outlier day reliably loses more than 5%, then 2% frequency over 30 days gives P(at least one) = **45.5%**. That is a defensible and still-alarming number.

**Do not merge the 88.4% figure.** Merge the corrected version: *an agent that reliably loses more than the daily limit when it errs, erring on 2% of days, breaches within 30 days with probability 45.5%.* The qualitative conclusion — outlier days dominate breach probability, and un-gated LLMs cannot sit in the live path — survives, and stands on the corrected arithmetic.

**D5 · ChatGPT's Egypt tax section.** §15.4 gives jurisdiction-specific guidance for Egypt. Nothing in the brief established your jurisdiction. Either ChatGPT had context I did not, or it inferred one. **Do not merge without you confirming the jurisdiction.** The generic point — that prop income characterisation and any licensing consequence are jurisdiction-dependent and need local advice — is sound and is already in §15.

**D6 · Gemini's rule matrix, as fact.** The ten-firm table is the most useful single artefact in Gemini's report and simultaneously the least verifiable: no per-cell source, marked "accessed March 2026" (four months stale), and it contains at least one demonstrated error (Apex, C3). Several cells conflict with the Claude report — Topstep profit target ~6% vs my phase-based framing, Apex consistency at 30% vs Topstep at 50%.

**Merge as a verification worksheet** — same structure, every cell marked `UNVERIFIED` until checked against the firm's own current terms with a recorded access date. It is genuinely valuable as a checklist of *what to verify*, and dangerous as a statement of *what is true*.

**D7 · Gemini's $67,000 pipeline cost.** Derived from an assumed 25% pass rate and 30% survival. The 25% is well above the 14% base rate and is asserted, not evidenced — so the estimate is circular for the purpose of deciding whether the pipeline is viable. Merge the *method* (distributional cost estimate with 10th/90th percentiles); recompute the *numbers* from your Phase 1 measurements.

---

## 6. Where the Claude report remains strongest

For completeness, what the consolidated document should keep from `00_research_report.md` and what neither other report has:

1. **The 2/19, 1/19, 1/19, 0/19 evidence count** from the systematic survey. ChatGPT discusses evidence quality; Gemini asserts it. Only the Claude report gives the number that makes the argument unanswerable.
2. **The leakage-controlled results table** from Emmanoulopoulos et al. — ten of thirteen configurations losing money in the simulator. This is the single strongest empirical finding available and neither other report extracts it.
3. **The skill-versus-volatility simulation** — that a zero-skill strategy at 30% volatility passes 35.5% while a Sharpe-1.5 strategy at 8% passes 5.6%. ChatGPT's mandate-sensitivity simulation is a complement, not a substitute.
4. **The evaluation-versus-funded conflict, quantified** — the volatility maximising pass probability gives a 3–6% twelve-month survival rate. This is the central strategic tension and only the Claude report puts numbers on it.
5. **The identical-expected-value finding on decorrelation** — E[accounts passed] constant at 2.06–2.08 across all correlations while P(zero pass) moves 57.2% → 6.8%. This is what makes decorrelation a free lunch, and it is why C1 matters so much: the lunch is only free if you can actually reach low correlation.
6. **The selective-baseline catch** on the Orchestration Framework paper — equal-weight weekly rebalancing returned 47.46% against their agents' 20.42%, a comparison absent from their abstract. Neither other report noticed.
7. **The break-even arithmetic** — a ~35% pass rate needed against a 14% base rate.

---

## 7. Merge plan

Proposed structure for the consolidated report, at roughly 26,000–30,000 words.

| Section | Base | Merges |
|---|---|---|
| 1 Executive summary | Claude | + C3 drawdown-variant warning; + M12 A-book transition |
| 2 Introduction | Claude | — |
| 3 Gating constraints | Claude | + M22 rule matrix (as worksheet); + M12/M13 B-book and due diligence; **C3 correction** |
| 3a In-flight triage | **Rewritten** | **C2 conditional rule**; + M6 snapshot type; + M20 decision tree; + M21 reserve; **C1 correction** |
| 4 Literature review | Claude | + ChatGPT's mechanism-transfer detail |
| 5 Open-source landscape | Claude | + ChatGPT's teardown detail |
| 6 Pattern synthesis | Claude | + M9 memory; + M10 drift; + M11 budgets |
| 7 Adversarial appraisal | Claude | + M16 closed form; + M17 mandate sensitivity; + M18 stress catalogue; **D4 corrected** |
| 8 Where the edge lies | Claude | + Gemini's ranking as a contrasting view (D3) |
| 9 Architecture | Claude | + M4 sequence diagram |
| 10 Governance | Claude | + M3 crosswalk; + M5 decomposition; + M8 evidence packet |
| 11 Technology | Claude | + M10 pinning and release process |
| 12 Phased plan | Claude | + M7 acceptance rule at each gate; **C1 second-strategy objective in Phase 3** |
| 13 Evaluation and risk | Claude | + M1 sizing; + M2 state machine; + M19 reconciliation; + M24 evals; + M15 withdrawals |
| 14 Cost model | Claude | + M7; + D7 method; **D1 both base rates** |
| 15 Regulatory | Claude | + M14 analogies; **D5 excluded pending jurisdiction** |
| 16 Verdict | Claude | + C2 revised triage; + C1 decorrelation reality |
| Appendices | Both | + E.1 crosswalk; + E.2 phase permissions; + E.3 evidence packet; + verification worksheet |

**Net effect on the verdict: none.** All three reports reach the same conclusion, and none of the merged material changes it. What the merge buys is **implementability** — the Claude report argues the case, ChatGPT specifies the mechanisms, Gemini supplies the operational landscape.

**The three changes that actually alter what you do:**

1. **C1** — your decorrelation plan does not achieve decorrelation, so a second genuinely independent strategy becomes a first-class objective and the case for running fewer accounts strengthens.
2. **C2** — the triage recommendation becomes conditional on mandate enforcement, and today that means at most one account at minimum size.
3. **C3** — check which drawdown variant each futures account is on, this week. If any is intraday-trailing on unrealised equity, your headroom is being consumed in a way nothing in your stack currently models.
