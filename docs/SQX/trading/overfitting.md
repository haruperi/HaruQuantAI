# Overfitting: the central problem of generated strategies

Every strategy in a databank was **selected because it looked good on the same history it was
tested on**. That selection step is where fake edges come from, and it is the single risk that
dominates all others in automated strategy generation. Everything the workflow does after
Step 1 exists to attack it. Vocabulary:
[concepts → Overfitting](../overview/concepts.md#overfitting--curve-fitting).

## Two different failures with the same symptom

- **Curve fitting (per strategy)** — one strategy has so many tunable parts (indicator periods,
  levels, session filters, stop multiples) that it can memorise the noise in the data. Symptom:
  the result collapses if any parameter moves slightly.
- **Data-mining bias / selection luck (per search)** — even if no single strategy is fitted,
  testing 100 000 candidates on the same history guarantees that some are profitable **by
  chance alone**. Symptom: the winner looks great, its parameter neighbours look like noise,
  and it dies out-of-sample.

The second is the one people underestimate. If a strategy has a genuine 0 % edge, roughly 1 in
20 random variants will still pass a 5 % significance bar. Generate enough and you will always
find "profitable" systems — the search itself produces them.

## The tells

| Signal | What it usually means |
|---|---|
| OOS performance far below IS ([OOS/IS ratio](../overview/robustness-tests/oos-is-ratios.md)) | fitted to the in-sample period |
| Equity curve driven by a handful of trades | not an edge, an outlier — check with [What-if](../overview/robustness-tests/what-if.md) |
| Neighbouring parameter values perform badly | a lucky spike, not a plateau (sequential optimization / SPP) |
| Result changes a lot at higher [test precision](crosscheck-funnel.md) | the "edge" was a simulation artifact |
| Very few trades (< ~100) | statistically meaningless whatever the metrics say |
| Works on exactly one symbol and one timeframe | fitted to that series' idiosyncrasies |

## What actually defends against it

Roughly in order of how much protection they buy:

1. **Hold-out data you never look at.** IS/OOS (and the three-way IST/ISV/OOS split) only works
   while the OOS segment stays untouched. Every time you rebuild after seeing OOS results, the
   OOS becomes part of the fitting — its value degrades with each look.
2. **Out-of-sample in other dimensions** — other symbols, other timeframes, other brokers'
   data. A real edge is a property of market behaviour, not of one price series
   ([multi-market retest](../overview/robustness-tests/multi-market.md)).
3. **Fewer degrees of freedom.** Fewer conditions and fewer optimizable parameters mean less
   room to memorise noise. A simple rule that works on five markets beats a nine-condition rule
   that works on one.
4. **Perturbation tests.** [Monte Carlo retest methods](../overview/robustness-tests/monte-carlo-retest-methods.md)
   randomise parameters, start bar, spread and history; a real edge degrades gracefully, a
   fitted one falls apart.
5. **Parameter-space shape.** Optimize and look at the *surface*, not the peak: you want a broad
   plateau. Walk-forward and the WF Matrix answer the related question of whether periodic
   reoptimization helps at all.
6. **Expect a brutal survival rate.** Passing the funnel is supposed to be rare — throwing away
   99 %+ of candidates is the system working, not a misconfiguration.

## The honest accounting

Two habits keep the numbers meaningful:

- **Count your attempts.** A strategy that survived a 10-candidate search and one that survived
  a 500 000-candidate search have very different evidence behind the same metrics. The more you
  searched, the higher the bar the survivor must clear.
- **Never re-test on data you have already burned.** When the OOS is used up, the only clean
  data left is data that has not happened yet — which is what
  [forward testing](going-live.md) is for.

Random generation is somewhat less prone to this than genetic evolution (evolution actively
optimizes toward the sample it can see), which is why the vendor pattern of *random build →
survivors seed a genetic build* is a reasonable compromise
([concepts → Build mode](../overview/concepts.md#build-mode-random-vs-genetic)).

## Related

- [The elimination method](elimination-method.md) — the defenses applied as a step-by-step procedure
- [The cross-check funnel](crosscheck-funnel.md) — how the defenses are ordered by cost
- [Robustness tests](../overview/robustness-tests/README.md) — each test in detail
- [The trader's workflow](workflow.md) — where each defense sits in the process
