# Deep Research Prompt — "AI Trading Agents Firm"

**How to use this file**

- **Section A** is the prompt. Copy from `=== BEGIN PROMPT ===` to `=== END PROMPT ===` and paste it into Claude/Cowork, ChatGPT Deep Research, or Gemini Deep Research.
- **Section B** is a per-tool appendix — paste the relevant block underneath the prompt depending on where you run it.
- **Section C** is a seed source list to paste into the `<user_provided_sources>` slot alongside your own links.
- Before running: fill in every `[[...]]` placeholder. If you leave one blank, the researcher will assume the default noted in brackets.

---

## SECTION A — THE PROMPT

```
=== BEGIN PROMPT ===

<role>
You are a research lead with a dual background: (1) a quantitative researcher who has
built and killed production trading systems, and (2) an ML systems architect who has
shipped multi-agent LLM applications. You are sceptical by disposition. You treat a
claimed backtest Sharpe ratio as an accusation to be investigated, not a result to be
reported. You are writing for a technically competent principal who will spend real
money and real months acting on your conclusions.
</role>

<objective>
Produce a single, self-contained professional research report that answers one question:

  "Given everything that is currently known — academically and in practice — about
   LLM-powered multi-agent trading systems, what is the best course of action for
   building my own AI Trading Agents Firm to be deployed on proprietary trading firm
   funded accounts, and what is the honest expected outcome?"

The prop-firm deployment is not a variation on the question; it is the question. A
recommendation that would be sound for a system trading own capital may be actively
wrong under a hard drawdown barrier, a consistency rule, and a counterparty that
profits when I fail.

The report must be usable as (a) a literature review I could defend in front of
quantitative researchers, and (b) an engineering and business blueprint I can start
executing from on Monday.
</objective>

<system_being_designed>
An "AI Trading Agents Firm": a multi-agent framework that mirrors the division of
labour of a real trading desk or hedge fund. Specialised LLM-powered agents —
fundamental analyst, sentiment/news analyst, technical analyst, macro analyst,
bull/bear researchers, trader, risk management committee, portfolio manager, and a
compliance/audit function — collaborate, debate, and escalate to reach a trading
decision. Agents engage in structured adversarial discussion to converge on a strategy,
and the system learns from realised outcomes over time.
</system_being_designed>

<my_context>
THIS IS A BROWNFIELD PROJECT, NOT A GREENFIELD ONE. I already have a working,
deterministic, modular Python trading system in production. I am not asking how to
build a trading system. I am asking how to add an agentic AI layer to a system that
already exists, without breaking the properties that make it safe.

EXISTING SYSTEM — domain modules, all built and running:
  utils         Business-neutral shared infrastructure for all other domains.
  brokers       Thin passthrough over external broker/market-data APIs (MT5, cTrader,
                Binance Spot/Futures; read-only Dukascopy, Yahoo Finance) behind one
                canonical `BrokerAdapter` interface, with zero business logic. Every
                live connection in the system routes exclusively through this domain.
  data          Acquire, normalize, store and serve market data and read-only broker/
                account state. All broker access here is read-only via BrokerAdapter
                read capability traits.
  indicators    Deterministic pure-function indicator computation over normalized data.
  strategy      Turn market state + indicators into canonical signals and trade intents,
                only when invoked by an approved runtime workflow.
  risk          Intercept every trading proposal and approve or reject against safety
                limits, exposure and governance policy. THE MASTER GATE.
  trading       Orchestrate live/demo workflows, convert approved risk decisions into
                deterministic order intents, execute on route (`sim`/`demo`/`live`)
                with reconciliation, monitoring and emergency controls.
  simulator     Historical backtest loop; deterministic strategy replay through the core
                trading path; simulated fills, journals, execution reports.
  analytics     Performance metrics and reports from trades, returns, benchmarks.
                Read-only, advisory only.
  optimization  Repeated simulation runs to search strategy parameter spaces and
                validate robustness. Never places trades.
  research      Sandboxed, LEAKAGE-GATED environment for data exploration and hypothesis
                evaluation. Advisory reports only.
  portfolio     Construct, simulation-validate, version, activate and monitor
                deterministic multi-strategy allocations. Does not approve risk or
                execute trades.
  ui/api        FastAPI gateway (`app/services/api`) + Next.js frontend (`ui/`).

  NOTE FOR THE RESEARCHER: this architecture already enforces much of the separation of
  duties that Track 6.2 demands — signals cannot self-execute, risk is a hard gate, and
  the research/analytics/optimization/portfolio domains are advisory by construction.
  Treat these boundaries as CONSTRAINTS TO PRESERVE, not as suggestions to redesign.
  Your job in Track 6 is to determine where agents attach to this topology, which
  domains must remain entirely deterministic and LLM-free, and what new components are
  genuinely missing. Recommending a rewrite would be a failure of the assignment; if
  some boundary is genuinely wrong for agentic use, argue it specifically.

WHAT I WANT THE AGENTS TO DO — in my own words, to be critically assessed, not accepted:
  Automate what I currently do by hand: run strategy research, generate and test
  hypotheses, run simulations/backtests, run optimizations, interpret analytics, and
  propose portfolio changes. I also want a CODER AGENT that writes new indicators and
  strategies as actual code in the existing `indicators` and `strategy` domains.
  Assess honestly whether the agentic layer belongs primarily in this offline research
  loop, primarily in the live decision path, or both — and in what order.

CAPITAL AND DEPLOYMENT:
  - 5 prop firm challenges ALREADY PURCHASED AND CURRENTLY BEING TRADED by the existing
    deterministic system. None passed yet; all are early. Target $200,000 per funded
    account, five-plus firms, across both FX/CFD (FTMO-style, MT5) and futures
    (Topstep-style) models.
  - The evaluation phase is live right now. The report must therefore include immediate,
    actionable triage for the five in-flight challenges alongside the longer-term build.
  - This is a hard barrier problem: reach a bounded profit target without ever touching
    a daily loss limit or trailing drawdown, under consistency rules, with a
    counterparty that profits when I fail. It is NOT long-run risk-adjusted growth.

TEAM AND TIME — deliberately de-emphasised:
  Solo. Strong software engineering, light on quant — assume I can implement anything
  you specify precisely, including with AI coding assistance, but do NOT assume I can
  independently derive quantitative methodology. Where the report relies on quant
  reasoning, explain it fully rather than gesturing at it.
  DO NOT compress or expand the plan to fit a schedule. Produce the complete, correct
  plan. Sequence it by dependency and risk, not by calendar. The only contextual factor
  that should genuinely shape your recommendations is the existing codebase above.
</my_context>

<research_scope>
Work through all eight tracks. Do not skip a track because it is less interesting; the
value of this report is in Tracks 0, 4 and 7 as much as Track 1.

TRACK 0 — GATING CONSTRAINTS: prop firm rules and automation policy
  DO THIS TRACK FIRST AND REPORT IT FIRST. If 0.1 resolves unfavourably, it invalidates
  or radically reshapes everything downstream, and I need to know that on page one
  rather than page ninety. Do not proceed to the architecture tracks assuming the
  deployment is permitted; establish whether it is.

  0.1 AUTOMATION PERMISSIBILITY — the existential question.
      Determine, firm by firm, the actual written policy on fully automated and
      AI-driven trading. Distinguish carefully between: outright prohibition of EAs and
      bots; permission with mandatory disclosure or approval; permission for
      "trade-assist" automation but not autonomous execution; and silence in the terms
      combined with discretionary enforcement in practice. Quote the relevant clauses
      verbatim with a link and an access date, because these terms change frequently
      and are often revised after a firm has to pay out.
      Then examine ENFORCEMENT, which is where the real risk sits: what behavioural
      signatures do firms use to detect algorithmic trading, what have they retroactively
      voided payouts for, and what does the documented record of trader disputes show?
      A rule that is permissive on paper and enforced arbitrarily at payout time is
      worse than a clear prohibition, because the loss arrives after the work is done.

  0.2 THE MULTI-ACCOUNT / COPY-TRADING PROBLEM — the second existential question.
      I intend to run one decision engine across five or more firms. Most prop firm
      terms contain clauses on copy trading, group trading, account management by third
      parties, and identical or highly correlated positions across accounts. Establish:
      how broadly each firm drafts these clauses; whether they apply only within a firm
      or across firms; whether firms share data or use common risk-monitoring vendors
      to detect correlated activity across the industry; and what the documented
      consequences have been. Determine whether "one strategy, five firms" is
      permissible, permissible-if-decorrelated, or prohibited. If decorrelation is the
      answer, specify what degree of decorrelation would be required and what that costs
      in expected return — because deliberately degrading five instances of one strategy
      to look independent is a real and underappreciated cost.

  0.3 RULE TAXONOMY. Build a comparative rule matrix across a representative sample of
      at least 8-10 firms spanning both FX/CFD and futures models, covering at minimum:
        | Firm | Model (FX-CFD / futures) | Account sizes offered | Eval structure
        (1-phase / 2-phase / instant) | Profit target per phase | Daily loss limit
        (and whether calculated on balance or equity, and at what reset time) |
        Max drawdown (static vs trailing; trailing on balance, equity, or high-water
        mark) | Min/max trading days | Consistency rule | News-trading restriction |
        Weekend/overnight holding | Flat-by-close | Prohibited strategies |
        EA/automation policy | Profit split | Payout frequency & minimum |
        Scaling plan | Challenge fee | Reset fee | Jurisdiction & entity |
      Flag every place where the rule is ambiguous as written, because ambiguity is
      resolved by the firm, not by me.

  0.4 TRANSLATE RULES INTO A MACHINE-READABLE CONSTRAINT SPECIFICATION. The deliverable
      is a proposed schema — a firm-mandate object — expressive enough to encode every
      rule above declaratively, so that one core engine can serve five different rule
      sets without any rule being hard-coded into strategy logic. Include worked
      examples for two firms, one from each model. Pay particular attention to the rules
      that are hard to express: trailing drawdown that ratchets on unrealised equity,
      consistency rules that depend on the final profit distribution and are therefore
      only evaluable retrospectively, and news restrictions that require an economic
      calendar dependency at decision time.

  0.5 FIRM COUNTERPARTY RISK. Prop firms are unregulated or lightly regulated
      counterparties that have failed, changed terms retroactively, and refused payouts.
      Establish the base rate: document the notable firm failures, regulatory actions,
      and payout disputes, and derive a due-diligence checklist for selecting five
      firms. Assess whether the firms are B-book simulated environments or route to real
      liquidity, and what that implies about their incentive to pay a consistently
      profitable algorithmic trader. Address directly: is the business model of the
      counterparty compatible with my succeeding at scale?

  0.6 THE ECONOMICS OF THE FUNDING PIPELINE. Model the expected value of the evaluation
      process itself: challenge fees per firm, pass probability per attempt, expected
      number of attempts, resets, time to funding, published-vs-realistic payout rates,
      and profit split. State the all-in expected cost of reaching five funded $200k
      accounts, with a distribution and not just a point estimate. Include the industry
      base rates for evaluation pass and payout where they can be sourced, and note
      where firms' self-reported figures are unaudited.
      Note that five challenge fees are already sunk. Model forward expected value from
      the current position, and separately model the marginal decision I actually face
      each time an account fails: reset, re-buy, switch firm, or stop.

  0.8 IN-FLIGHT TRIAGE — five challenges are being traded RIGHT NOW by the existing
      deterministic system, none passed, all early. This is not a hypothetical.
      Address, concretely and near the front of the report:
        (a) Whether the five accounts are effectively one correlated position, and what
            can be done about that immediately without a rewrite. If one system trades
            all five on the same signals, a single bad session ends the entire
            allocation, and every dollar of challenge fee with it.
        (b) The cheapest instrumentation I can add THIS WEEK to know my true live
            breach exposure: distance to each barrier per account, worst-case open-
            position loss, and correlation of open exposure across accounts.
        (c) Whether the existing `risk` domain already enforces the specific prop rules
            of each firm (per-account daily loss, trailing drawdown on unrealised
            equity, consistency, news windows, flat-by-close) or whether those are
            currently unenforced — and what the minimum viable firm mandate engine
            looks like as an addition to `risk` rather than a replacement of it.
        (d) Given Track 0.1 and 0.2, whether the current live setup already exposes me
            to an automation-policy or correlated-account violation, and what to do
            about that immediately.
        (e) A blunt answer on whether to keep trading all five concurrently, reduce to
            fewer, or pause — with the reasoning shown. Do not soften this.

  0.7 VERDICT FOR THIS TRACK. State plainly whether the intended deployment — an
      autonomous multi-agent system running across five-plus firms at $200k each — is
      permissible, permissible with modification, or in conflict with the terms of the
      firms most likely to be selected. If it is the latter, propose the compliant
      alternatives (disclosed automation, semi-autonomous human-approved execution,
      firm selection filtered on automation policy, fewer firms, own capital) and carry
      the chosen framing through the rest of the report.

TRACK 1 — Academic foundations of multi-agent LLM trading
  1.1 Locate and read the primary literature on LLM agents applied to trading and
      investment decisions. Cover, at minimum: multi-agent trading frameworks that
      assign analyst/trader/risk roles; memory-augmented financial agents; LLM agents
      for portfolio construction; agent-based market simulation using LLMs.
  1.2 Cover the enabling multi-agent literature that these systems borrow from:
      multi-agent debate and self-consistency, role-play and society-of-mind agent
      frameworks, reflection / verbal reinforcement learning, tool use and planning,
      and hierarchical agent orchestration. Explain precisely WHICH mechanism each
      trading framework imported and whether the original paper's claimed benefit
      survived the transfer to finance.
  1.3 Cover the pre-LLM baseline this must beat: classical statistical arbitrage,
      factor models, deep RL for trading, and supervised return prediction. State
      plainly what the pre-LLM literature says about achievable out-of-sample edge.
  1.4 Cover the LLM-for-finance primitives: financial sentiment extraction from news
      and social media, earnings-call and filings analysis, financial domain LLMs and
      their benchmarks, numerical reasoning limits of LLMs.
  For each significant paper: full citation, venue and peer-review status, dataset and
  date range, universe, baseline compared against, headline claim, and — mandatory —
  your assessment of the strongest methodological objection to it.

TRACK 2 — Open-source landscape (read the code, not just the README)
  2.1 Multi-agent trading frameworks. For each: architecture (agent roster,
      communication topology, orchestration library, memory design, prompt structure),
      how signals become orders, what backtesting engine is used, licence, maintenance
      health (commits, contributors, open issues, last release), and community
      reception including credible criticism found in issues, forks, HN/Reddit threads
      or blog teardowns.
  2.2 Financial ML / RL platforms and agent toolkits.
  2.3 Backtesting and execution infrastructure — event-driven vs vectorised engines,
      which ones correctly model slippage, spread, commission, funding, borrow, partial
      fills, and latency; which ones silently permit look-ahead.
  2.4 Data infrastructure — market data, fundamentals, news, alternative data;
      for each: coverage across equities/FX/crypto, licence terms for algorithmic use,
      point-in-time correctness, cost at my scale, and API ergonomics.
  2.5 Agent orchestration frameworks (graph-based, conversational, and hand-rolled)
      with a recommendation and the reasoning behind it.
  2.6 For every framework surveyed, extract its de facto permission model: which agents
      can touch the broker, whether any separation exists between research and
      execution, whether that separation is enforced in code or merely instructed in a
      prompt, and what the audit trail records. Most open frameworks are demos and will
      fail this test — document exactly how they fail, because those gaps are the
      specification for what I must build.
  For the 3-5 most important repositories, produce a genuine teardown: how a single
  decision flows end-to-end through the code, and the specific design choices you would
  keep, change, or reject.

TRACK 3 — Architecture synthesis
  3.1 Extract the recurring architectural patterns across all systems surveyed
      (role decomposition, debate/critique loops, hierarchical escalation, memory and
      retrieval, reflection on realised P&L, tool/function calling, structured output
      contracts, human-in-the-loop gates).
  3.2 For each pattern: what problem it solves, what evidence exists that it improves
      decision quality, its failure modes, and its token/latency/dollar cost.
  3.3 Comparative architecture table across all systems surveyed.
  3.4 Explicitly address the hard design questions:
      - Which decisions genuinely need an LLM, and which are better served by
        deterministic code or a small classical model? Where is the LLM decorative?
      - Does adversarial debate improve decisions, or does it manufacture confident
        consensus? What does the evidence actually show?
      - How is state and memory persisted across sessions without unbounded context
        growth or contaminated retrieval?
      - How are agent outputs made machine-parseable and schema-validated?
      - Determinism, reproducibility, seeding, and model-version drift.
      - Cost and latency budget per decision at realistic decision frequency.
      - Where do humans sit in the loop, and what can never be automated?
      - How is authority partitioned? Survey how the field handles — or ignores —
        separation of duties between agents that research and agents that execute,
        least-privilege tool access, signed/validated intents between components, and
        auditability of an autonomous decision after the fact. Note that this is where
        the practitioner and regulatory literature is far ahead of the ML literature.

TRACK 4 — Adversarial due diligence (this track carries the most weight)
  Interrogate the entire field. Address each of the following explicitly and at length:
  4.1 LOOK-AHEAD LEAKAGE VIA PRETRAINING. An LLM asked to analyse a 2021 stock may
      already know what happened next. This is the single most serious threat to every
      backtest of an LLM trading agent. Establish: which papers acknowledge it, which
      mitigate it and how (date-masked prompts, entity anonymisation, post-cutoff
      holdout periods, synthetic markets), and whether any published result survives
      strict scrutiny on this point. State your conclusion bluntly.
  4.2 Standard backtest pathologies: survivorship bias, point-in-time fundamentals,
      restatement, delisting returns, timestamp alignment, weekend/session handling,
      and the difference between decision time and data-availability time.
  4.3 Backtest overfitting and multiple testing — deflated performance metrics,
      probability of backtest overfitting, the effect of the researcher's own
      iteration count. How many strategies were tried before the reported one?
  4.4 Transaction cost realism: spread, slippage, market impact, commission, financing,
      FX swap/rollover, crypto funding rates, and taxes. Recompute or sanity-check
      headline results under realistic costs wherever you have enough information to
      do so, and show your arithmetic.
  4.5 Capacity and decay: at what AUM does each claimed edge disappear? What is the
      evidence on alpha decay after publication?
  4.6 Non-stationarity and regime change: how do these systems behave in regimes absent
      from their evaluation window? What happened to LLM trading agents through
      documented stress episodes?
  4.7 LLM-specific failure modes: hallucinated facts and figures, sycophancy and
      agreement cascades in multi-agent debate, prompt injection via ingested news or
      social content (a live attack surface when agents read the open internet),
      position/recency bias, numerical reasoning errors, non-determinism, silent
      degradation on model updates, and provider outages mid-session.
  4.8 Publication and incentive bias: negative results are not published; profitable
      systems are not open-sourced. What should be inferred from the fact that these
      frameworks are public?
  4.9 Steelman the opposing case in full: "LLM multi-agent trading firms are an
      expensive re-derivation of signals obtainable more cheaply and more reliably by
      classical means, and the multi-agent layer adds cost, latency and variance
      without adding edge." Give this argument its strongest form, then respond to it.
  4.10 EVERY PERFORMANCE CLAIM MUST BE RE-EXAMINED UNDER A BARRIER CONSTRAINT.
      This is the single most important adaptation of the literature to my situation.
      Published results report Sharpe, cumulative return, and maximum drawdown over a
      full evaluation window. None of those tell me what I need to know, which is:
      what is the probability that this system touches a 5% daily loss or a 10% total
      drawdown before it reaches a 10% profit target? A strategy's survival under a
      hard barrier is governed by the left tail of its DAILY return distribution and by
      the serial correlation of its losses — not by its mean or its Sharpe ratio.
      Wherever a surveyed system reports enough information, estimate or bound its
      breach probability under representative prop rules, and show the working. Where
      the paper does not report daily return distributions or intraday equity paths,
      say so explicitly — that omission alone makes most of the literature unusable for
      my purpose, and that finding is itself a headline result of this report.
      Note specifically: LLM agents exhibit non-determinism and occasional catastrophic
      reasoning failures. In an unconstrained account that is a bad day. Under a
      trailing drawdown it is terminal. Quantify how often surveyed systems produce
      outlier-bad single decisions.
  4.11 CORRELATED BREACH ACROSS ACCOUNTS. Any evaluation of my design must model five
      or more accounts simultaneously, not one. Establish how correlated account
      failure should be modelled, why per-account risk limits do not aggregate to
      portfolio-level safety when the accounts share a decision engine, and what the
      literature on correlated failure in replicated systems has to say. Treat "five
      accounts" as one position with five times the leverage unless decorrelation is
      designed in deliberately and verified empirically.

TRACK 5 — Where the real edge plausibly is
  5.1 Separate the sources of potential edge and rank them by evidence strength:
      unstructured-text alpha (news, filings, transcripts, social); speed of synthesis;
      breadth of coverage across many instruments; reduction of human behavioural
      error; superior risk management and position sizing; research productivity
      (LLM as strategy generator rather than signal generator); execution quality.
  5.2 Identify the niches where a solo/small operator has a structural advantage over
      institutions — capacity-constrained instruments, unloved markets, longer holding
      periods, willingness to hold uncomfortable positions.
  5.3 Identify where a small operator cannot compete and should not try.
  5.4 THE TWO DEPLOYMENT SURFACES — treat this as a central question of the report,
      because it is the decision I am actually making.
      Surface A, the OFFLINE RESEARCH LOOP: agents generate and screen hypotheses, run
      and interpret simulations, drive optimization sweeps, read analytics, and write
      candidate indicator/strategy code. No live capital is ever at risk from an agent's
      output until a human promotes it. Failures are cheap, slow and reversible, and the
      LLM is doing something it is demonstrably good at — synthesis, code, and
      exploration of a large hypothesis space.
      Surface B, the LIVE DECISION PATH: agents participate in or determine what is
      traded, when, and at what size, in real time. Failures are expensive, fast and
      irreversible, non-determinism becomes a live risk, and every barrier-breach
      scenario in Track 4.10 applies.
      Assess both on evidence, cost, latency, and failure severity. Give a clear
      recommendation on which to build first and whether Surface B is worth building at
      all given prop constraints. My stated intent is mostly Surface A — automating
      research, backtesting and optimization that I currently do by hand — and my
      instinct is that this is where the value is. Test that instinct rather than
      confirming it, and if the evidence says Surface B adds real edge under barrier
      constraints, say so.
  5.5 THE PROP-SPECIFIC EDGE HYPOTHESIS — evaluate it seriously rather than assuming it.
      Under a barrier constraint, the highest-value decision a system makes may be the
      decision NOT to trade: staying flat through a high-impact news release, detecting
      a regime in which the strategy's edge has degraded, recognising that the account
      is close enough to its drawdown limit that expected value is negative regardless
      of signal quality, and enforcing that discipline without the behavioural failures
      that end most human-run funded accounts. Synthesising heterogeneous unstructured
      context (calendar, news, positioning, regime) into a trade/no-trade gate is
      plausibly what LLMs are genuinely better at than classical models, and it is
      exactly what prop constraints reward. Assess the evidence for and against this
      hypothesis. If it holds, it implies an architecture in which the LLM layer is a
      risk and context filter over a classical signal generator, rather than the signal
      generator itself — which is close to the opposite of how the surveyed frameworks
      are built. Take that implication seriously and say so if the evidence supports it.
  5.6 TWO OBJECTIVE FUNCTIONS. Analyse the evaluation phase and the funded phase
      separately. Passing an evaluation is a first-passage problem with an absorbing
      barrier and a time constraint, and the optimal risk profile for it is provably
      different from the optimal profile for compounding funded capital under the same
      drawdown limit (where the objective becomes indefinite survival plus payout
      timing). Establish what the optimal-stopping and barrier-option literature implies
      about position sizing in each phase, including whether the standard prop-trading
      folk wisdom (risk 0.5-1% per trade, target the profit goal slowly) is actually
      optimal or merely conventional. Address the consistency rule as a binding
      constraint that explicitly forbids the fat-right-tail outcome most systems seek.

TRACK 6 — Build blueprint

  6.0 BROWNFIELD ATTACHMENT MAP — do this before proposing any architecture.
      Produce a table with one row per existing domain (utils, brokers, data,
      indicators, strategy, risk, trading, simulator, analytics, optimization, research,
      portfolio, ui/api) and these columns:
        | Domain | Current responsibility | Agent attaches here? (No / Advisory /
          Proposing / Orchestrating) | What the agent would do | Why an LLM is
          justified here rather than deterministic code | New interface required |
          Risk introduced | Must remain LLM-free? (Y/N) and why |
      Rules for filling it in:
        - Default to "No". Every "Yes" must be argued for. The burden of proof is on
          adding the agent, not on leaving the domain alone.
        - `brokers`, `risk` and the execution path of `trading` should almost certainly
          be LLM-free. If you disagree with that, argue it explicitly; if you agree,
          say so and explain the reasoning so I can defend the decision later.
        - `research`, `optimization`, `simulator` and `analytics` are the natural
          agent surfaces: offline, advisory by construction, no live capital at risk,
          and already leakage-gated in the case of `research`. Assess whether the
          highest-value agentic layer is entirely offline.
        - Identify what is genuinely MISSING from the current architecture for prop
          deployment — my current guess is a per-account firm mandate engine and an
          account-portfolio governor above the existing `portfolio` domain, but verify
          that rather than accepting it.
      Then state the SMALLEST viable first integration: the single agent, attached at a
      single domain, that would deliver the most value at the least risk. Name it
      specifically.

  6.1 A concrete reference architecture for MY system, with a component diagram
      (Mermaid), the agent roster with each agent's precise responsibility, inputs,
      output schema, escalation rules, and the orchestration topology. Justify every
      agent's existence; delete any agent that is present only for narrative symmetry.

  6.2 GOVERNANCE MATRICES — separation of duties between research and execution.
      This subsection is a hard requirement, not an optional extra. The governing
      principle is least privilege enforced at the tool layer, not at the prompt layer:
      an agent must be structurally incapable of taking an action it is not authorised
      to take. A prompt instruction saying "do not place orders" is not a control; an
      agent process that has no order-placement credential is a control. Every matrix
      below must be accompanied by a statement of how the constraint is ENFORCED IN
      CODE (credential scoping, separate service accounts, tool-registry allow-lists,
      signed intents, a broker adapter that only accepts payloads carrying a valid risk
      approval token, etc.).

      Non-negotiable invariants the design must satisfy, each stated and justified:
        (i)   No agent that proposes a trade may also execute it.
        (ii)  No agent that analyses market data holds live execution credentials.
        (iii) Risk approval is a separate process boundary from strategy generation,
              and cannot be overridden by any research agent.
        (iv)  Deterministic, non-LLM code performs the final pre-trade checks
              (limits, sizing, sanity bounds, duplicate detection). The LLM never has
              the last word before the venue.
        (v)   Every state-changing action is logged to an append-only audit trail
              identifying the proposing agent, the approving component, the inputs
              that produced it, and the model version and prompt hash used.
        (vi)  A named human principal is accountable for each decisional layer
              ("accountability anchoring"), and the design records who that is.
        (vii) Kill-switch authority sits outside the agent graph entirely and can be
              exercised without agent cooperation.
        (viii) A FIRM MANDATE ENGINE — deterministic, non-LLM, per-account — holds an
              absolute veto over every order. It evaluates the account's live distance
              to its daily loss limit and its trailing drawdown, the consistency-rule
              implications of the proposed trade, session and news-window restrictions,
              instrument and lot-size permissions, and flat-by-close requirements, and
              it rejects anything that could breach. No agent may see its rules as
              advisory, override it, or reason its way past it. It fails closed: if it
              cannot verify current account state, it refuses to authorise trades.
              This component is the most important thing in the system. Design it first
              and treat the agent layer as the part that must earn its place around it.
        (ix)  Per-account isolation: each funded account has its own mandate engine,
              its own credentials, and its own kill-switch. A fault in one account's
              execution path cannot propagate to another. A portfolio-level governor
              sits above them with authority to halt all accounts but never to relax an
              individual account's limits.

      6.2.1 AGENT ROLE MATRIX — one row per agent.
        | Agent | Purpose (one sentence) | Inputs | Tools granted | Output schema |
          Decision rights | Prohibited actions | Escalates to | Model tier & why |
          Est. cost/latency per invocation | MVP or Later |
        Notes: "Decision rights" must be phrased as what the agent may unilaterally
        cause to happen. "Prohibited actions" must be specific and testable. "Model
        tier" should justify where a small/cheap/local model is sufficient — do not
        default every role to a frontier model.

      6.2.2 AGENT PERMISSION MATRIX — one row per agent, one column per capability.
        | Agent | Account scope (which accounts it can affect) | Market Data Read |
          News/Web Read | Research Tools | Fundamentals Read | Portfolio/Position Read |
          Account/Balance & Drawdown-Headroom Read | Strategy Propose | Risk Approve |
          Order Propose | Order Modify | Order Execute | Position Close | Kill-Switch |
          Policy Veto | Firm-Mandate Override | Memory Write | Config/Param Write |
        The "Firm-Mandate Override" column must read N for every single row without
        exception, including any human-facing agent. If any row is not N, the design is
        wrong. State this and show it.
        Use a four-value scale, not a binary: N (no access) / R (read-only) /
        P (may propose, cannot effect) / X (may effect). Add a footnote column for
        scope limits (e.g. "X, capped at 0.25% NAV, instruments on allow-list only,
        during session hours only"). The matrix must make it visually obvious that the
        research half of the org chart contains no X in any execution column.
        Follow the matrix with: (a) the enforcement mechanism for each X and P,
        (b) what an attacker or a malfunctioning agent could achieve if it fully
        controlled each row, and (c) an explicit prompt-injection analysis — any agent
        with web/news read access is attacker-reachable, so trace what an injected
        instruction in a news article could reach through that agent's permission set.

      6.2.3 RISK-CONTROL MATRIX — one row per identified risk.
        | Risk ID | Category | Failure scenario (concrete) | Likelihood | Impact |
          Preventive control | Detective control (+ alert threshold) |
          Recovery control (+ RTO) | Responsible component | Human owner |
          Residual risk | How this control is tested |
        Categories must span at least: market risk, model risk, LLM behavioural risk
        (hallucination, sycophancy/consensus cascade, injection), data risk (stale,
        wrong, revised, leaked), execution risk (duplicate orders, partial fills,
        rejects, disconnects, clock skew), infrastructure risk (provider outage, rate
        limits, cost blowout), governance risk (permission escalation, audit gap),
        and regulatory/counterparty risk. Every X in the permission matrix must have
        at least one corresponding row here.
        MANDATORY prop-specific rows, at minimum: daily loss limit breach; trailing
        drawdown breach on unrealised equity while a position is open; simultaneous
        breach across multiple accounts from one correlated decision; consistency-rule
        violation discovered only at payout; trading during a restricted news window;
        failure to flatten before session close on a futures account; stale or
        desynchronised account state causing the mandate engine to size against a wrong
        equity figure; detection of prohibited automation or correlated multi-account
        activity leading to account termination or voided payout; firm insolvency or
        refusal to pay; and loss of an account through pure software fault (duplicate
        order, disconnect mid-position, clock skew, failed reconciliation) rather than
        through any trading decision at all.
        For each, the Impact column should be denominated in accounts lost, not in
        percent — the natural unit of loss in this system is a whole $200k account.

      6.2.4 State the trust boundaries explicitly (Mermaid diagram): which components
        run in which process/credential domain, what crosses each boundary, and in
        what serialised, schema-validated form. Show where the "proposal" becomes a
        "signed intent", where the firm mandate engine authorises or rejects it, and
        where the authorised intent becomes an order at a specific venue.

      6.2.5 MULTI-ACCOUNT AUTHORITY MODEL. Extend the matrices to the five-plus-account
        reality. Specify: which components are per-account and which are shared; how a
        shared decision engine is prevented from becoming a single point of correlated
        failure; how the allocator decides which accounts act on a given signal, and on
        what authority; what limits exist on aggregate exposure across firms; and what
        the portfolio governor may and may not do. Add to the permission matrix a
        column for account scope (which accounts each component may affect) and, if
        Track 0.2 concluded that decorrelation is required for compliance, specify the
        mechanism that produces it — deliberate parameter, timing, or instrument
        divergence per account — together with its cost in expected return and how
        compliance with it is evidenced.

      6.2.6 CODE-GENERATING AGENT GOVERNANCE. I want an agent that writes new
        indicators and strategies as real code into the existing `indicators` and
        `strategy` domains. This is the highest-leverage and highest-risk agent in the
        design, because its output outlives the conversation that produced it and will
        eventually run against live accounts. Specify in full:
        - The promotion pipeline from generated code to live use, as a series of gates
          that cannot be skipped: generation in an isolated sandbox with no network and
          no broker credentials; static analysis and dependency allow-listing; unit
          tests including property-based tests that indicators are pure and
          deterministic; replay against a frozen reference dataset; simulator run under
          full prop constraints; out-of-sample and walk-forward validation; human review
          and explicit sign-off; versioned registration; then and only then, activation.
        - Why NO generated code may ever be hot-loaded into a running live process, and
          what mechanism enforces that.
        - How generated strategies are protected from the leakage the `research` domain
          already gates against — note that a coder agent can reintroduce look-ahead
          bias in a single line, and that an LLM with pretraining knowledge of market
          history is a uniquely dangerous author of a trading rule.
        - THE MULTIPLE-TESTING PROBLEM, which an automated strategy generator makes
          catastrophically worse: an agent that can propose a thousand strategies will
          find spurious winners at a rate that guarantees self-deception. Specify the
          statistical correction regime up front — a pre-registered search budget,
          deflated performance metrics, tracking of the total number of hypotheses
          tested across the system's entire lifetime, and a hard rule that the
          out-of-sample set is consumed and retired once used. This single issue may
          be the strongest argument against the strategy-generating agent; assess it
          honestly and say so if it is.
        - Provenance and audit: every artefact traceable to the prompt, model version,
          input data and validation results that produced it.
        - The permission row for this agent in 6.2.2 — write access to a staging
          repository only, never to the live strategy registry.

      6.2.7 EVALUATION-PHASE vs FUNDED-PHASE PERMISSIONS. Permissions and limits should
        differ between an account in evaluation and the same account once funded, since
        the objective function changes. Show both configurations and the promotion
        procedure between them.

  6.3 Technology decisions with reasoning and rejected alternatives: orchestration
      framework, model selection per agent role (including where a small/cheap or
      local model suffices), data vendors per asset class, backtesting engine,
      execution layer (including the MT5 path and its specific constraints), storage,
      observability and evaluation tooling.
  6.4 A phased plan. For each phase: objective, scope, duration, deliverables, cost
      estimate, and — most importantly — a pre-registered GO/NO-GO criterion with a
      numeric threshold that must be met before the next phase or before any increase
      in capital. Sequence by dependency and risk, NOT by calendar — do not compress or
      pad the plan to fit a schedule. Note that this is a brownfield plan: most phases
      are additions to existing domains, and each phase must state what it changes in
      the current codebase. Suggested spine, revise if you have a better sequence but
      keep the gates:
        Phase 0 — IMMEDIATE, runs in parallel with everything else and before any agent
                  work. Firm mandate engine added inside the existing `risk` domain:
                  per-account, deterministic, encoding every rule of each of the five
                  firms currently being traded. Live breach-exposure instrumentation and
                  cross-account correlation monitoring. This protects capital already at
                  risk today.
                  GATE: the mandate engine rejects every rule-violating order in an
                  adversarial test suite, including under stale-state conditions, before
                  it is trusted.
        Phase 1 — Barrier-aware evaluation harness in `simulator` and `analytics`:
                  Monte Carlo over the full evaluation process, five-account joint
                  simulation, breach probability as the primary reported metric
                  alongside existing performance statistics.
                  GATE: the existing deterministic strategy's breach probability and
                  simulated pass rate are measured and known. This number is the
                  baseline everything later must beat, and it may well be the most
                  valuable single output of the entire project.
        Phase 2 — FIRST AGENT, offline only, attached at the smallest viable surface
                  identified in 6.0 — most likely an analytics or research
                  interpretation agent with no write access to anything.
                  GATE: it produces conclusions a competent human would agree with, on
                  a held-out set of past runs where the answer is already known.
        Phase 3 — Research and optimization agents: hypothesis generation, sweep
                  orchestration, robustness interpretation, all advisory, all inside the
                  existing leakage-gated `research` and `optimization` domains.
                  GATE: measurable improvement in research throughput AND no degradation
                  in out-of-sample quality of what the process produces.
        Phase 4 — Coder agent, sandboxed, writing to a staging registry only, behind the
                  full promotion pipeline of 6.2.6 with the multiple-testing budget
                  enforced from day one.
                  GATE: a generated indicator or strategy survives the complete
                  promotion pipeline and beats the Phase 1 baseline out of sample.
        Phase 5 — Multi-agent structure, only if Phases 2-4 showed single agents earning
                  their cost. Ablate every agent; delete any that does not pay for
                  itself.
        Phase 6 — Only if Track 5.4 concluded Surface B is worthwhile: agent influence
                  on the live decision path, introduced as an advisory filter that can
                  veto or reduce a deterministic signal but never originate or enlarge
                  one. Demo route first, then a single account.
                  GATE: demonstrated reduction in breach probability on live data.
        Phase 7 — Extension across accounts, sequentially, with decorrelation measures
                  from 6.2.5 in place and empirically verified.
      State at which phase each permission in 6.2.2 is first granted; execution
      permissions must be introduced as late as the plan allows. State explicitly which
      phases could safely run concurrently for a solo builder and which must not.
  6.5 Evaluation methodology I should adopt: walk-forward and purged/embargoed
      cross-validation, out-of-sample discipline, the statistics used to decide whether
      an edge is real, ablation protocol for agent contribution, and the LLM-specific
      evals (determinism, schema compliance, hallucination rate, injection resistance,
      cost per decision). Include a permission-enforcement test suite: adversarial
      tests that attempt to make a research agent execute a trade, and which must fail
      closed.
      PROP-SPECIFIC EVALUATION — this is the primary metric set, and it replaces Sharpe
      ratio as the headline:
        - Monte Carlo simulation of the full evaluation process across thousands of
          paths, reporting: probability of passing, probability of breaching each limit,
          expected days to pass, and the distribution of worst-case daily loss.
        - Simultaneous simulation of five-plus correlated accounts, reporting the
          distribution of accounts surviving after 6 and 12 months. Report the joint
          distribution, not five marginals.
        - Consistency-rule compliance under the realised profit distribution.
        - Sensitivity of all the above to the rule variant (static vs trailing
          drawdown, balance vs equity calculation, reset timing) — the same strategy can
          pass comfortably under one variant and fail reliably under another.
        - Stress tests on the specific events that kill funded accounts: a gap through a
          stop, a widened spread at a news release or session open, a broker requote or
          rejection, a feed outage mid-position, and a flash move.
      Report expected value in units of funded accounts retained and dollars paid out
      after profit split, not in percentage return.
  6.6 Risk management design: position sizing, exposure and correlation limits,
      drawdown-triggered de-risking, kill-switches, reconciliation, and the failure
      modes of the software itself (stale data, duplicated orders, disconnects,
      partial fills, clock skew). Cross-reference every item to a row in 6.2.3.
      Prop-specific requirements: position sizing derived from live headroom to the
      binding barrier rather than from a fixed fractional rule; hard intraday loss
      governors that de-risk and then halt well before the firm's limit, with the
      buffer sized to cover slippage and gap risk; pre-trade simulation of the worst
      case fill for every proposed order against remaining headroom; automated
      flat-by-close for futures mandates; an economic-calendar dependency that blocks
      trading in restricted windows; and continuous reconciliation of the mandate
      engine's view of account equity against the broker's, with trading suspended on
      any discrepancy.
  6.7 Cost model: LLM inference, data subscriptions, infrastructure, execution costs,
      AND the funding pipeline itself — challenge fees across five-plus firms, expected
      resets and retries, and the time cost of evaluation periods. Give a total expected
      cost to reach five funded $200k accounts as a distribution, not a point estimate.
      Then state the monthly run-rate and the gross trading return required, after
      profit split, merely to break even. Show the arithmetic. Compare that break-even
      return against the returns actually documented for the surveyed agentic systems,
      and say plainly whether the gap closes.
  6.8 Regulatory, licensing and operational notes. Cover: the contractual nature of
      prop firm agreements and what recourse exists when a firm declines to pay;
      whether income from funded accounts creates any licensing or tax consequence in
      my jurisdiction; data-vendor licence restrictions on feeding market data to
      third-party LLM APIs; and liability and accountability where an autonomous system
      acts without a human in the loop, including how the audit trail in 6.2 would
      support a dispute with a firm alleging prohibited automation. Flag
      jurisdiction-dependence throughout; do not give legal advice.

TRACK 7 — Verdict
  7.1 A direct answer: given the system I already have, what should I add, in what
      form, and at what scale of commitment? If the honest answer is a much narrower
      agentic layer than the multi-agent trading firm I described — for example agents
      confined entirely to the offline research loop, with the live path left
      deterministic — say so plainly and say why. Note explicitly if the most valuable
      output of this whole exercise turns out to be the barrier-aware evaluation
      harness and the firm mandate engine rather than the agents themselves.
  7.2 Answer the prop-specific question directly: is a multi-agent LLM system the right
      instrument for passing prop evaluations and surviving on funded capital, or would
      a simpler, more deterministic, lower-variance system pass more reliably and cost
      far less to build and run? If the evidence points to the simpler system, say so
      without hedging, and state where — if anywhere — the agentic layer still earns its
      place (my current hypothesis is that it earns it as a trade/no-trade context
      filter rather than as a signal generator; test that hypothesis, do not indulge it).
  7.3 Compare the prop-funded route against the alternatives on risk-adjusted expected
      value: trading my own capital at smaller size with no barrier constraint, and
      building the system as a product or service rather than trading it. Include the
      constraint that prop rules impose an artificial and severe drawdown limit that a
      good long-horizon strategy might never otherwise need to respect.
  7.4 The three most likely ways this project fails, with leading indicators for each.
      Given the structure, candidates to consider: the automation policy or
      correlated-account rules make the plan non-viable; the system passes evaluations
      by luck and is scaled prematurely across five firms; or breach arrives through
      software fault rather than trading decision.
  7.5 The cheapest decisive experiment I can run in the next 30 days that would give me
      real information about whether to continue. Specify it precisely enough to execute.
      Prefer an experiment that tests the binding constraint — automation permissibility
      or breach probability — over one that tests strategy performance.
  7.6 Open research questions where the literature is genuinely silent. Note in
      particular whether ANY published work evaluates LLM trading agents under
      prop-firm-style barrier constraints; if none does, say so, because that gap is
      the central finding of this report and defines what I would have to establish
      myself.
</research_scope>

<evidence_standards>
- Cite every non-obvious factual claim with a resolvable URL. Prefer primary sources:
  the paper, the repository, the docs, the exchange specification.
- NEVER invent a citation. If you cannot verify that a paper, author, repository or
  number exists, either omit it or write "UNVERIFIED — could not confirm" beside it.
  A short accurate report beats a long fabricated one, and I will check.
- Distinguish clearly between: peer-reviewed results, preprints, vendor/marketing
  claims, practitioner blog assertions, and your own inference. Label your own
  inference as such.
- Prefer 2023-present material for LLM-specific content; use older material freely for
  market microstructure, backtesting methodology, and quantitative finance foundations.
- Report numbers with their conditions attached (period, universe, costs assumed,
  rebalance frequency). A Sharpe ratio without its assumptions is not a data point.
- When sources conflict, present both and adjudicate, giving your reasoning.
- Note explicitly where evidence is thin, absent, or of low quality. "The literature
  does not answer this" is a valuable finding — do not paper over gaps with plausible
  prose.
- Do not soften conclusions to be encouraging. I would rather be told not to build
  this than be flattered into building it.
</evidence_standards>

<deliverable>
Format: a professional report as [[.docx / .md / .pdf — if blank, produce Markdown]].
Length: comprehensive; do not truncate for brevity. Target 12,000-20,000 words in the
main body, plus appendices.

Structure:
  0.  Title page, date, and a statement of the report's scope and limitations
  1.  Executive summary (max 2 pages, written so it stands alone; state the verdict
      in the first paragraph — do not bury it)
  2.  Introduction and problem definition
  3.  GATING CONSTRAINTS: prop firm rules, automation policy, and firm counterparty
      risk (Track 0), ending with the Track 0.7 verdict. This chapter comes before the
      literature review because it can invalidate everything after it.
  3a. IMMEDIATE ACTIONS for the five in-flight challenges (Track 0.8). Place this early
      and make it directly executable — capital is at risk today, and this section is
      the only part of the report with a deadline.
  4.  Academic literature review (Track 1)
  5.  Open-source landscape and repository teardowns (Track 2)
  6.  Architectural pattern synthesis (Track 3)
  7.  Critical appraisal and adversarial due diligence (Track 4), including the
      barrier-constrained re-reading of every performance claim
  8.  Where the edge plausibly lies under prop constraints (Track 5)
  9.  Brownfield attachment map: where agents attach to the existing domains, and
      which domains must remain deterministic (Track 6.0), followed by the recommended
      architecture (Track 6.1, with Mermaid diagrams)
  10. Governance: agent role, permission and risk-control matrices, the firm mandate
      engine, and the code-generation promotion pipeline (Track 6.2) — a first-class
      chapter, not an appendix
  11. Technology decisions (Track 6.3)
  12. Phased build plan with go/no-go gates through to five funded accounts (Track 6.4)
  13. Evaluation methodology and risk management design (Track 6.5-6.6)
  14. Cost model, funding-pipeline economics and break-even analysis (Track 6.7)
  15. Regulatory, liability and operational considerations (Track 6.8)
  16. Verdict, failure modes, and the 30-day decisive experiment (Track 7)
  17. Appendices:
        A. Annotated bibliography (every source, one-line assessment each)
        B. Prop firm rule comparison matrix (Track 0.3) and the firm-mandate schema
           with worked examples (Track 0.4)
        C. Repository comparison matrix
        D. Data vendor comparison matrix by asset class and execution venue
        E. Governance matrices in full, if too wide to sit inline in ch. 10
        F. Glossary
        G. Research log — queries run, sources that could not be accessed, and known
           blind spots in this report

Use tables for comparisons. Use Mermaid for architecture and sequence diagrams. Bold
the load-bearing claims. Every recommendation must be traceable to evidence in the
report or explicitly flagged as judgement.
</deliverable>

<method>
0. Complete Track 0 before beginning the literature tracks, and let its findings set
   the constraints that the rest of the research must respect.
1. Begin with broad searches to map the field before narrowing. Search academic
   sources, code hosting, practitioner forums and financial press separately — each
   surfaces material the others miss.
2. Read repositories at the source-code level, not the README level. READMEs describe
   intent; code describes behaviour.
3. Follow citation graphs both directions from the seminal works: what they built on,
   and who has since criticised or failed to replicate them.
4. Actively search for disconfirming evidence and failure reports, not only for
   material supporting the premise. Search for replication failures, retractions, and
   people who tried this and stopped.
5. When you have formed a conclusion, attempt to falsify it before writing it down.
6. Maintain the research log as you go (Appendix G).
7. For Track 0, read the firms' actual Terms of Service, FAQ and rule pages directly
   rather than relying on comparison blogs and affiliate sites, which dominate search
   results for this topic and are almost universally compensated for referrals. Record
   the access date for every rule quoted; these terms are revised frequently and
   sometimes without notice.
</method>

<user_provided_sources>
Treat the following as seed material and starting points ONLY — a small, non-exhaustive
sample I happened to find. The research must extend far beyond them, and you should
critically appraise them on the same terms as anything you find yourself. If any of
them turn out to be weak or unreliable, say so. Several are preprints, vendor blogs, or
promotional content with a commercial interest in the answer — treat them accordingly
and label them as such in the bibliography.

--- PAPERS (read in full where accessible) ---
Orchestration Framework for Financial Agents: From Algorithmic Trading to Agentic Trading
  https://arxiv.org/html/2512.02227v1
Can Agentic Trading Systems Pay for Their Own Intelligence?
  https://arxiv.org/html/2607.10286v1
Agentic Trading: When LLM Agents Meet Financial Markets
  https://arxiv.org/html/2605.19337v1
WebCryptoAgent: Agentic Crypto Trading with Web Informatics
  https://arxiv.org/html/2601.04687v1
AlphaQuanter: An End-to-End Tool-Augmented Agentic Reinforcement Learning Framework for
Stock Trading
  https://arxiv.org/html/2510.14264v2
Trade in Minutes! Rationality-Driven Agentic System for Quantitative Financial Trading
  https://arxiv.org/html/2510.04787v2
AI Agents in Financial Markets: Architecture, Applications, and Systemic Implications
  https://arxiv.org/html/2603.13942v1
Agentic Artificial Intelligence in Finance: A Comprehensive Survey
  https://arxiv.org/html/2604.21672v1
Reasoned Agentic Portfolio Trading with Orchestrated Rebalancing
  https://ceur-ws.org/Vol-4162/paper8.pdf
Agentic AI in Commodity Trading: A Comparative Simulation Study (IJACSA 16:11, 2025)
  https://thesai.org/Downloads/Volume16No11/Paper_2-Agentic_AI_in_Commodity_Trading_A_Comparative_Simulation_Study.pdf

--- ATTACHED DOCUMENTS (read these first; full text is provided) ---
1. "To Trade or Not to Trade: An Agentic Approach to Estimating Market Risk Improves
   Trading Decisions" — Emmanoulopoulos, Olby, Lyon, Stillman (arXiv 2507.08584, Jul 2025).
   LLM-driven discovery of stochastic differential equations to generate risk metrics
   that inform daily trading; evaluated in backtest and in a market simulator with
   synthetic causally-plausible price paths. RELEVANCE: this is the strongest available
   answer to "how do you evaluate an LLM trading agent without pretraining leakage" —
   synthetic-but-plausible paths sidestep the memorisation problem. Assess that claim
   carefully in Track 4.1, and assess the "principled model-building step" argument
   (that sentiment/trend-based agentic analysis is the weak part of the field) in
   Track 5 — it is a direct challenge to the analyst-agent-centric design I described.
   FILE: 2507.08584v1.pdf
2. "Agentic AI in Commodity Trading: A Comparative Simulation Study" — Nunna & Samala,
   IJACSA 16(11), 2025. Hybrid agent-based-modelling + agentic-AI framework; 20
   traditional vs 20 agentic agents across Natural Gas and WTI Crude over 1M-3Y
   horizons, on synthetic series calibrated to historical volatility. RELEVANCE:
   isolates the contribution of memory, planning and autonomous goal-setting. Scrutinise
   external validity and the calibration of the synthetic series in Track 4.
   FILE: Paper_2-Agentic_AI_in_Commodity_Trading_A_Comparative_Simulation_Study.pdf
3. "Agentic AI in Derivatives Markets: Counterparty, Risk, and the Regulatory Gap" —
   Arias-Barrera, Universidad Externado de Colombia (SSRN). Maps the tripartite legal
   void — legal capacity, liability allocation, systemic risk governance — created when
   consequential market decisions are made by non-persons, and proposes
   "accountability anchoring": assigning legal responsibility to identifiable human or
   institutional principals at each decisional layer, calibrated to that layer's
   autonomy. RELEVANCE: this is the conceptual backbone for Track 6.2 and Track 6.8.
   The permission matrix should be readable as an implementation of accountability
   anchoring. FILE: ssrn-6805139.pdf
4. "The Agentic ETF: How Agentic Trading Becomes an Asset Class" — Amandeep Singh (SSRN).
   Defines agentic trading against rule-based algo trading and robo-advice, decomposes
   the agentic-trading stack into six layers, maps incumbents and structural gaps per
   layer, and presents ScalarField.io as a reference implementation; includes an AUM
   sizing exercise to 2030. RELEVANCE: use the six-layer decomposition as a candidate
   organising frame for Track 3, and the incumbent/gap map for Track 5. CAUTION: this
   paper advances a specific commercial reference implementation and a large TAM
   estimate — treat the layer taxonomy as useful and the sizing exercise as advocacy,
   and check its stated assumptions rather than repeating its numbers.
   FILE: ssrn-6872219.pdf

--- REPOSITORIES (inspect at source-code level) ---
https://github.com/TauricResearch/TradingAgents
https://github.com/DaviddTech/ai-trading-agent
https://github.com/kweinmeister/agentic-trading
https://github.com/Open-Finance-Lab/AgenticTrading

--- PRACTITIONER ARTICLES (low evidentiary weight; useful for implementation detail and
    for observing what people actually hit in practice) ---
https://www.mindstudio.ai/blog/build-ai-trading-agent-claude-code-alpaca
https://www.skool.com/zero-one/classroom/acb2342e?md=a3ad9f1bf47b47c18b1a9ba0a8fc658a
https://medium.com/@codehimanshu24/building-my-first-agentic-trading-system-for-the-indian-nse-75d325ec15ca
https://obside.com/trading-ai-agents/agentic-trading-trends
https://blog.openalgo.in/building-an-agentic-trader-from-scratch-a-beginners-guide-bb74b10438b4

--- VIDEO ---
https://www.youtube.com/watch?v=g1GbmCr9MSc
(If the transcript is not retrievable, record that in the research log rather than
inferring its contents.)

Handling instructions for this list:
- Read the four attached PDFs FIRST. They set the frame for Tracks 4, 5 and 6.
- Two of the seed papers speak directly to questions I care most about: whether the
  intelligence pays for itself ("Can Agentic Trading Systems Pay for Their Own
  Intelligence?" — feed this into the Track 6.7 cost model) and how orchestration should
  be structured (the Orchestration Framework paper — feed into Track 3 and 6.1).
- Where seed sources conflict with each other or with what you find independently,
  adjudicate explicitly rather than presenting both uncritically.
</user_provided_sources>

<interaction>
Do not ask clarifying questions before starting. Where my brief is ambiguous, make the
most reasonable assumption, state it explicitly in the report, and continue. Deliver
the complete report in one pass.
</interaction>

=== END PROMPT ===
```

---

## SECTION B — TOOL-SPECIFIC APPENDIX

Paste the matching block directly beneath the prompt.

### B1 — Claude / Cowork

```
<execution_notes>
- Re-attach the four PDFs with this prompt. Extract their full text before browsing;
  they set the frame for Tracks 4, 5 and 6.
- Use WebSearch and web fetch extensively; run many searches, not few.
- Read GitHub repositories through raw file URLs (raw.githubusercontent.com) so you see
  actual source, not rendered pages. Read the orchestration entry point, the agent
  prompt definitions, the backtest loop, and the order-execution path at minimum.
- Where a numerical claim can be checked, check it by running Python in the sandbox
  rather than reasoning about it in prose. Show the code in an appendix.
- Maintain a task list and work through the tracks in order.
- Produce the final report as a .docx in my outputs folder using the docx skill, and
  present the file when complete. Build the content first; only read the format skill
  once the research is done.
- Before finalising, run a verification pass over every citation and every number in
  the executive summary and verdict sections.
</execution_notes>
```

### B2 — ChatGPT Deep Research / Gemini Deep Research

```
<execution_notes>
- This is a single-pass deep research task. Do not ask me clarifying questions; state
  assumptions in the report instead.
- Browse widely: academic preprint servers and digital libraries, code hosting
  platforms, practitioner forums, and financial press. Aim for 60+ distinct sources.
- Inline-cite with links throughout, and compile the full bibliography as Appendix A.
- If a source cannot be accessed, record it in the research log rather than
  substituting a guess about its contents.
- Output the complete report in one response as Markdown, with tables and Mermaid
  diagrams. Do not summarise or abbreviate sections for length.
</execution_notes>
```

---

## SECTION C — SUPPLEMENTARY SEED LEADS

Your sources are already embedded in the prompt above. This section is *additional*
search scaffolding — append it inside `<user_provided_sources>` if you want the
researcher to cast wider. **These are search starting points from memory, not verified
citations** — the prompt instructs the researcher to confirm each one exists before
citing it, and to flag any it cannot.

**Multi-agent LLM trading frameworks to search for**
`TradingAgents multi-agent LLM financial trading framework` · `FinMem LLM trading agent
layered memory` · `FinAgent multimodal foundation agent financial trading` · `FinRobot
AI agent platform financial analysis` · `StockAgent LLM agent simulated stock market` ·
`TradingGPT layered memory multi-agent` · `QuantAgent self-improving LLM trading` ·
`LLM agent portfolio management multi-agent debate`

**Repositories to inspect**
`TauricResearch/TradingAgents` · `AI4Finance-Foundation` (FinRL, FinGPT, FinRobot,
FinNLP) · `microsoft/qlib` · `OpenBB-finance/OpenBB` · `freqtrade/freqtrade` ·
`nautechsystems/nautilus_trader` · `QuantConnect/Lean` · `hummingbot/hummingbot` ·
`polakowo/vectorbt` · `stefan-jansen/machine-learning-for-trading`

**Multi-agent / orchestration foundations**
Multi-agent debate for factuality and reasoning (Du et al.) · CAMEL role-playing agents
· AutoGen · MetaGPT · ChatDev · Reflexion · ReAct · Generative Agents (Park et al.) ·
LangGraph documentation

**LLMs in finance — primitives and scepticism**
`Can ChatGPT forecast stock price movements` (Lopez-Lira & Tang) · FinBERT · BloombergGPT
· financial reasoning benchmarks for LLMs · LLM data contamination and pretraining
leakage in financial backtests

**Methodology and adversarial reading**
López de Prado, *Advances in Financial Machine Learning* (purged CV, embargo, PBO) ·
Bailey & López de Prado, Deflated Sharpe Ratio · Harvey, Liu & Zhu, "…and the
Cross-Section of Expected Returns" · Bailey et al., "Pseudo-Mathematics and Financial
Charlatanism" · McLean & Pontiff, alpha decay after publication

**Governance, permissions and agent security** (feeds Track 6.2)
Least-privilege and capability-based access control for LLM agent tool use · OWASP Top 10
for LLM Applications (excessive agency, insecure output handling, prompt injection) ·
NIST AI Risk Management Framework · indirect prompt injection via retrieved web content ·
human-in-the-loop approval patterns and signed-intent designs in agent frameworks ·
SEC/FCA/ESMA guidance on algorithmic trading controls, pre-trade risk checks and kill
switches (e.g. MiFID II RTS 6, SEC Rule 15c3-5 market access rule) · four-eyes principle
and segregation of duties in trading operations · model risk management (SR 11-7)

**Prop firm rules, economics and enforcement** (feeds Track 0 — read primary sources)
Terms of service and rule pages for a representative sample across both models, e.g.
FTMO, FundedNext, The5%ers, Funding Pips, Alpha Capital, E8, Blueberry Funded (FX/CFD)
and Topstep, Apex Trader Funding, TakeProfit Trader, Earn2Trade, Bulenox (futures) ·
each firm's stated policy on EAs, bots, algorithmic and AI trading, and on copy trading
/ group trading / correlated accounts across firms · consistency-rule definitions and
how they are applied at payout · trailing vs static drawdown mechanics and whether they
ratchet on balance, equity or high-water mark · CFTC action against My Forex Funds and
its aftermath · documented prop firm collapses, term changes and payout disputes ·
industry pass-rate and payout-rate estimates and their provenance · prop firm risk
management vendors and cross-firm trader-behaviour monitoring

**Barrier-constrained strategy theory** (feeds Tracks 4.10, 5.6, 6.5)
First-passage and absorbing-barrier problems · optimal stopping under a profit target
and a loss barrier · drawdown-constrained portfolio optimisation · risk of ruin and
gambler's ruin under realistic edge · Kelly criterion under drawdown constraints and
fractional-Kelly de-risking · path-dependent (barrier) option analogies for evaluation
passing · Monte Carlo estimation of breach probability from a daily return distribution

**Execution-layer references for your stack**
MetaTrader5 Python integration docs · Rithmic R|API, Tradovate API and NinjaTrader
automation interfaces for futures props · broker/venue fee, swap, commission and funding
schedules for your target instruments · CME contract specifications, margin and session
schedules · economic calendar APIs for news-window blackouts · exchange and broker API
rate-limit and order-type documentation

---

## Revision notes

### Revision 3 — brownfield: existing Python system, challenges in flight

The project is not greenfield. There is a working modular Python trading system in
production, and five prop challenges are being traded by it right now.

- **`<my_context>` now carries the full domain inventory**, with an instruction that
  the existing boundaries are constraints to preserve rather than a design to replace.
  Your architecture already enforces most of Track 6.2's separation of duties — `risk`
  as master gate, `strategy` unable to self-execute, `research`/`analytics`/
  `optimization`/`portfolio` advisory by construction. The prompt says so, and says
  that recommending a rewrite is a failure of the assignment.
- **Track 6.0 is new: a brownfield attachment map.** One row per existing domain, with
  the default answer "no agent here" and the burden of proof on adding one. `brokers`,
  `risk` and the execution path of `trading` are flagged as presumptively LLM-free.
  It ends by naming the single smallest viable first integration.
- **Track 0.8 is new: in-flight triage.** Five live challenges traded by one system is
  the correlated-breach scenario from Track 4.11, happening now. The report must answer
  early and bluntly whether to keep trading all five, reduce, or pause — and specify the
  cheapest instrumentation that would reveal true live breach exposure this week.
- **Track 5.4 was rebuilt around the two deployment surfaces**: the offline research
  loop (cheap, slow, reversible failures) versus the live decision path (expensive,
  fast, irreversible). Your stated intent is mostly the former. The prompt asks the
  researcher to test that instinct rather than confirm it.
- **Track 6.2.6 is new: code-generating agent governance.** The coder agent is the
  highest-leverage and highest-risk component, because its output outlives the
  conversation and eventually runs against live accounts. Full promotion pipeline
  specified — sandboxed generation, no network or credentials, purity tests, frozen
  reference replay, constrained simulation, out-of-sample validation, human sign-off,
  versioned registration — plus a hard prohibition on hot-loading generated code.
  The multiple-testing problem gets particular weight: an agent that can propose a
  thousand strategies will find spurious winners at a rate that guarantees
  self-deception, and the prompt asks whether that alone defeats the idea.
- **The phased plan is now brownfield and dependency-ordered, not calendar-ordered**,
  per your instruction. Phase 0 protects the capital already at risk; Phase 1 measures
  your existing strategy's breach probability — the baseline every later phase must
  beat, and plausibly the most valuable single number the project produces.
- **Team and timeline de-emphasised** as you asked, with one substantive carry-through:
  since you're light on quant, the prompt now requires quantitative reasoning to be
  explained in full rather than gestured at.

### Revision 2 — prop firm deployment

The deployment target changed the shape of the whole brief. Five-plus firms at $200,000
each, not yet funded, across both FX/CFD and futures models.

- **Track 0 is new and runs first.** Automation permissibility and the copy-trading /
  correlated-account question are gating, not incidental — if the firms you select
  prohibit autonomous execution or read their group-trading clauses broadly, the
  architecture downstream is moot. The prompt now demands verbatim rule quotes with
  access dates, and separates written policy from enforcement behaviour at payout time,
  which is where the actual risk sits. Track 0 also covers firm counterparty risk (firms
  fail and decline payouts) and the expected cost of the funding pipeline itself.
- **The objective function is restated throughout.** You are not maximising
  risk-adjusted growth; you are solving a first-passage problem with an absorbing
  barrier. Track 4.10 requires every performance claim in the literature to be
  re-examined for breach probability rather than Sharpe ratio — and predicts that most
  papers do not report the daily return distributions needed to do it, which is itself a
  finding worth having.
- **Correlated breach is treated as the dominant risk.** Five accounts sharing one
  decision engine is one position at five times the size. Track 4.11 and section 6.2.5
  make decorrelation an explicit design obligation with a stated cost in expected return.
- **A deterministic Firm Mandate Engine became invariant (viii)** — per-account,
  non-LLM, absolute veto, fails closed, and the permission matrix now carries a
  "Firm-Mandate Override" column that must read N for every row including humans. The
  prompt instructs that this component be designed first and the agent layer made to
  earn its place around it.
- **The phased plan now runs to five funded accounts** with the gates that matter:
  mandate engine passes adversarial tests before any strategy work; one paid evaluation
  at one firm before any scaling; confirmation that a firm actually pays before the
  second account. It states plainly that buying five evaluations before Phase 5 has
  produced evidence is the most expensive available mistake.
- **Track 5.5 adds a testable hypothesis** rather than an assumption: that under a
  barrier constraint the LLM layer's real value is the decision *not* to trade — a
  context and regime filter over a classical signal generator, which is close to the
  inverse of how the surveyed frameworks are built. Track 7.2 forces a direct answer on
  whether a simpler deterministic system would pass more reliably for less money.
- **Section C gains two clusters**: prop firm rules/economics/enforcement, and
  barrier-constrained strategy theory (first passage, risk of ruin, drawdown-constrained
  Kelly).

### Revision 1 — governance matrices and your sources

- **Track 6.2 added**: agent role, permission and risk-control matrices, with separation
  of duties as a hard requirement. Four-value permission scale (N/R/P/X), mandatory
  enforcement-in-code column, prompt-injection reachability analysis for any agent with
  web access. Governance became a first-class chapter rather than an appendix.
- **Tracks 2.6 and 3.4 extended** to extract the de facto permission model of every
  framework surveyed — most let one agent both decide and execute, and documenting that
  failure gives you your specification.
- **All 16 of your sources embedded**, with the four attached PDFs annotated and routed
  to the tracks where each matters most. Arias-Barrera's "accountability anchoring" is
  the stated conceptual backbone of the permission matrix; the Agentic ETF six-layer
  stack is offered as an organising frame for Track 3, flagged for commercial interest.
