# Analytics Requirement Audit Report

Source requirements: `docs/dev/phase-implementation-plan/06-analytics.md`.
Target implementation: `app/services/analytics`.

## Initial Audit Summary

- Parsed 454 unique analytics requirements from the source matrix.
- Initially done/traceable by symbol: 373 requirements.
- Initially missing target paths: 43 requirements.
- Initially missing target symbols in existing files: 38 requirements.
- Initial focused analytics test collection failed before assertions because of import/circular import failures.

Initial missing path IDs: ANL-NFR-046, ANL-NFR-071, ANL-NFR-072, ANL-NFR-073, ANL-NFR-097, ANL-NFR-109, ANL-NFR-181, ANL-NFR-190, ANL-NFR-191, ANL-NFR-192, ANL-NFR-193, ANL-NFR-194, ANL-NFR-195, ANL-NFR-196, ANL-NFR-197, ANL-NFR-203, ANL-NFR-204, ANL-NFR-205, ANL-NFR-206, ANL-NFR-207, ANL-NFR-208, ANL-NFR-209, ANL-NFR-210, ANL-NFR-211, ANL-NFR-212, ANL-NFR-213, ANL-NFR-214, ANL-NFR-215, ANL-NFR-216, ANL-NFR-247, ANL-NFR-248, ANL-NFR-249, ANL-NFR-250, ANL-NFR-251, ANL-NFR-252, ANL-NFR-253, ANL-NFR-424, ANL-NFR-425, ANL-NFR-426, ANL-NFR-427, ANL-NFR-430, ANL-NFR-431, ANL-NFR-452.

Initial missing symbol IDs: ANL-NFR-087, ANL-NFR-088, ANL-NFR-089, ANL-NFR-090, ANL-NFR-091, ANL-NFR-100, ANL-NFR-101, ANL-NFR-103, ANL-NFR-104, ANL-NFR-105, ANL-NFR-106, ANL-NFR-107, ANL-NFR-108, ANL-NFR-245, ANL-NFR-246, ANL-NFR-282, ANL-NFR-315, ANL-NFR-335, ANL-NFR-336, ANL-NFR-337, ANL-NFR-338, ANL-NFR-373, ANL-NFR-374, ANL-NFR-397, ANL-NFR-398, ANL-NFR-399, ANL-NFR-400, ANL-NFR-401, ANL-NFR-402, ANL-NFR-403, ANL-NFR-404, ANL-NFR-405, ANL-NFR-406, ANL-NFR-408, ANL-NFR-409, ANL-NFR-410, ANL-NFR-411, ANL-NFR-429.

## Remediation Summary

- Added the architecture-required analytics tool API, equity returns compatibility module, analytics catalog documentation, and service traceability tests.
- Added explicit package export and boundary/evaluator anchors required by the traceability matrix.
- Restored focused analytics test collection by making root package analytics exports lazy.
- Preserved pre-existing dirty user files and made only narrow analytics-scope edits.

## Validation Summary

- `uv run pytest tests/unit/app/services/analytics -q --no-cov`: 114 passed.
- `uv run pytest tests/services/analytics/test_requirement_traceability.py -q --no-cov`: 1 passed.
- `uv run ruff check app/__init__.py app/services/analytics tests/services/analytics/test_requirement_traceability.py tests/services/__init__.py tests/services/analytics/__init__.py`: passed.
- `uv run pytest -q --no-cov`: 1076 passed, 2 unrelated non-analytics failures in optimization/strategy import smoke tests.

## Completed Requirement Checklist

- [X] **ANL-NFR-001** (Non-functional / governance) Analytics functions must be read-only and side-effect free at the domain level.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-002** (Non-functional / governance) Importing the analytics registry should not perform live broker calls, network calls, database mutations, or trading side effects.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-003** (Non-functional / governance) Official tools must be stateless, retry-safe, and safe for parallel optimization or portfolio workflows.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-004** (Non-functional / governance) Metric kernels must not depend on mutable global calculation state.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-005** (Non-functional / governance) Local/read-through caches, if implemented, must define TTL, maximum size, eviction behavior, invalidation keys, lock timeout, stale-read behavior, and single-flight or equivalent thundering-herd prevention before Builder handoff.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-006** (Non-functional / governance) Distributed caching, distributed invalidation services, message queues, and async background workers must not be implemented inside Analytics.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-007** (Non-functional / governance) Portfolio aggregation must fail closed when required base-currency conversion is unavailable.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-008** (Non-functional / governance) The analytics registry must expose only intentional public analytics tools and must not hide colliding function names; duplicate concepts must use module-qualified aliases where needed.
  *Evidence: app/services/analytics/registry/analytics_registry.py line 69 (`register_tool`)*
- [X] **ANL-NFR-009** (Functional / behavioural) Every official exported analytics tool must be callable, documented, and accept a `request_id` parameter for traceability.
  *Evidence: app/services/analytics/registry/analytics_registry.py line 156 (`request_id`)*
- [X] **ANL-NFR-010** (Non-functional / governance) Each official public capability must be labeled as stable, approved experimental, deprecated, or internal-support-only.
  *Evidence: app/services/analytics/registry/analytics_registry.py line 69 (`register_tool`)*
- [X] **ANL-NFR-011** (Non-functional / governance) Each official public capability must document whether it is safe for agent/API use.
  *Evidence: app/services/analytics/registry/analytics_registry.py line 69 (`register_tool`)*
- [X] **ANL-NFR-012** (Non-functional / governance) The analytics registry must distinguish official tools, internal metric kernels, compatibility aliases, and deprecated exports.
  *Evidence: app/services/analytics/registry/analytics_registry.py line 69 (`register_tool`)*
- [X] **ANL-NFR-013** (Non-functional / governance) Agentic workflows must import analytics capabilities from `app.services.analytics` rather than deep module files.
  *Evidence: app/services/analytics/registry/analytics_registry.py line 69 (`register_tool`)*
- [X] **ANL-NFR-014** (Non-functional / governance) Strategy-version mismatch must be handled explicitly during degradation pairing and must not be hidden inside aggregate scores.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-015** (Non-functional / governance) Low-sample explainability drivers must not appear in ranked driver lists.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-016** (Functional / behavioural) common_avg_loss` shall expose the common-module average-loss function without colliding with metrics exports.
  *Evidence: app/services/analytics/metrics/exports.py line 16 (`common_avg_loss`)*
- [X] **ANL-NFR-017** (Functional / behavioural) common_get_r_multiples` shall expose the common-module R-multiple function without colliding with metrics exports.
  *Evidence: app/services/analytics/metrics/exports.py line 36 (`common_get_r_multiples`)*
- [X] **ANL-NFR-018** (Functional / behavioural) max_gross_size_held` shall calculate the maximum absolute total size held across positions.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 21 (`max_gross_size_held`)*
- [X] **ANL-NFR-019** (Functional / behavioural) percent_time_in_market` shall calculate percent of the trading period spent in the market.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 174 (`percent_time_in_market`)*
- [X] **ANL-NFR-020** (Functional / behavioural) metrics_get_r_multiples` shall expose metrics-module R-multiple behavior without colliding with common exports.
  *Evidence: app/services/analytics/metrics/exports.py line 57 (`metrics_get_r_multiples`)*
- [X] **ANL-NFR-021** (Functional / behavioural) win_rate_fraction` shall calculate win rate on a 0-to-1 scale.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 172 (`win_rate_fraction`)*
- [X] **ANL-NFR-022** (Functional / behavioural) avg_win_loss` shall calculate mean winning and losing outcomes.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 194 (`avg_win_loss`)*
- [X] **ANL-NFR-023** (Functional / behavioural) consecutive_wins_losses` shall calculate maximum consecutive wins and losses from numeric outcomes.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 224 (`consecutive_wins_losses`)*
- [X] **ANL-NFR-024** (Functional / behavioural) t_statistic` shall calculate the t-statistic for mean outcome.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 262 (`t_statistic`)*
- [X] **ANL-NFR-025** (Functional / behavioural) open_position_pnl` shall calculate total unrealized PnL from open positions.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 213 (`open_position_pnl`)*
- [X] **ANL-NFR-026** (Functional / behavioural) slippage_paid` shall calculate total absolute slippage costs paid.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 235 (`slippage_paid`)*
- [X] **ANL-NFR-027** (Functional / behavioural) commission_paid` shall calculate total absolute commission costs paid.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 253 (`commission_paid`)*
- [X] **ANL-NFR-028** (Functional / behavioural) swap_paid` shall calculate total absolute swap costs paid.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 271 (`swap_paid`)*
- [X] **ANL-NFR-029** (Functional / behavioural) metrics_avg_loss` shall expose metrics-module average-loss behavior without colliding with common exports.
  *Evidence: app/services/analytics/metrics/exports.py line 74 (`metrics_avg_loss`)*
- [X] **ANL-NFR-030** (Functional / behavioural) expectancy_r` shall calculate R-expectancy.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 289 (`expectancy_r`)*
- [X] **ANL-NFR-031** (Functional / behavioural) max_size_held` shall calculate maximum total contracts held.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 42 (`max_size_held`)*
- [X] **ANL-NFR-032** (Functional / behavioural) max_net_size_held` shall calculate maximum net directional size held.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 63 (`max_net_size_held`)*
- [X] **ANL-NFR-033** (Functional / behavioural) max_long_size_held` shall calculate maximum total long contracts held.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 97 (`max_long_size_held`)*
- [X] **ANL-NFR-034** (Functional / behavioural) max_short_size_held` shall calculate maximum total short contracts held.
  *Evidence: app/services/analytics/metrics/position_exposure.py line 120 (`max_short_size_held`)*
- [X] **ANL-NFR-035** (Functional / behavioural) avg_r_multiple` shall calculate average R-multiple.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 317 (`avg_r_multiple`)*
- [X] **ANL-NFR-036** (Functional / behavioural) median_r_multiple` shall calculate median R-multiple.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 334 (`median_r_multiple`)*
- [X] **ANL-NFR-037** (Functional / behavioural) r_expectancy` shall calculate R-space expectancy.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 367 (`r_expectancy`)*
- [X] **ANL-NFR-038** (Functional / behavioural) max_r_multiple` shall calculate maximum R-multiple.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 384 (`max_r_multiple`)*
- [X] **ANL-NFR-039** (Functional / behavioural) min_r_multiple` shall calculate minimum R-multiple.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 410 (`min_r_multiple`)*
- [X] **ANL-NFR-040** (Functional / behavioural) avg_consecutive_wins` shall calculate average length of winning streaks.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 436 (`avg_consecutive_wins`)*
- [X] **ANL-NFR-041** (Functional / behavioural) avg_consecutive_losses` shall calculate average length of losing streaks.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 468 (`avg_consecutive_losses`)*
- [X] **ANL-NFR-042** (Functional / behavioural) r_signal_to_noise` shall calculate mean R relative to R volatility.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 500 (`r_signal_to_noise`)*
- [X] **ANL-NFR-043** (Functional / behavioural) rolling_expectancy_stability` shall calculate expectancy stability over a rolling window.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 530 (`rolling_expectancy_stability`)*
- [X] **ANL-NFR-044** (Functional / behavioural) win_after_win_probability` shall calculate probability that a win follows a win.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 564 (`win_after_win_probability`)*
- [X] **ANL-NFR-045** (Functional / behavioural) runs_test_zscore` shall calculate Wald-Wolfowitz runs-test z-score.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 593 (`runs_test_zscore`)*
- [X] **ANL-NFR-046** (Functional / behavioural) get_analytics_overview` shall calculate comprehensive analytics across all, long, and short subsets.
  *Evidence: app/services/analytics/tool_api.py line 60 (`get_analytics_overview`)*
- [X] **ANL-NFR-047** (Functional / behavioural) calculate_spread_cost_impact` shall calculate spread cost drag.
  *Evidence: app/services/analytics/metrics/costs.py line 19 (`calculate_spread_cost_impact`)*
- [X] **ANL-NFR-048** (Functional / behavioural) calculate_slippage_impact` shall calculate slippage cost drag.
  *Evidence: app/services/analytics/metrics/costs.py line 37 (`calculate_slippage_impact`)*
- [X] **ANL-NFR-049** (Functional / behavioural) calculate_commission_impact` shall calculate commission cost drag.
  *Evidence: app/services/analytics/metrics/costs.py line 55 (`calculate_commission_impact`)*
- [X] **ANL-NFR-050** (Functional / behavioural) cagr` shall calculate compound annual growth rate.
  *Evidence: app/services/analytics/metrics/pnl.py line 22 (`cagr`)*
- [X] **ANL-NFR-051** (Functional / behavioural) compound_monthly_growth_rate` shall calculate compound monthly growth rate.
  *Evidence: app/services/analytics/metrics/pnl.py line 68 (`compound_monthly_growth_rate`)*
- [X] **ANL-NFR-052** (Functional / behavioural) buy_and_hold_cagr` shall calculate buy-and-hold CAGR from price data.
  *Evidence: app/services/analytics/metrics/pnl.py line 109 (`buy_and_hold_cagr`)*
- [X] **ANL-NFR-053** (Functional / behavioural) adjusted_gross_profit` shall calculate adjusted gross profit.
  *Evidence: app/services/analytics/metrics/pnl.py line 140 (`adjusted_gross_profit`)*
- [X] **ANL-NFR-054** (Functional / behavioural) adjusted_gross_loss` shall calculate adjusted gross loss.
  *Evidence: app/services/analytics/metrics/pnl.py line 171 (`adjusted_gross_loss`)*
- [X] **ANL-NFR-055** (Functional / behavioural) adjusted_net_profit` shall calculate adjusted net profit.
  *Evidence: app/services/analytics/metrics/pnl.py line 202 (`adjusted_net_profit`)*
- [X] **ANL-NFR-056** (Functional / behavioural) select_net_profit` shall calculate net profit after outlier selection.
  *Evidence: app/services/analytics/metrics/pnl.py line 222 (`select_net_profit`)*
- [X] **ANL-NFR-057** (Functional / behavioural) select_gross_profit` shall calculate gross profit after outlier selection.
  *Evidence: app/services/analytics/metrics/pnl.py line 245 (`select_gross_profit`)*
- [X] **ANL-NFR-058** (Functional / behavioural) select_gross_loss` shall calculate gross loss after outlier selection.
  *Evidence: app/services/analytics/metrics/pnl.py line 267 (`select_gross_loss`)*
- [X] **ANL-NFR-059** (Functional / behavioural) max_runup` shall calculate maximum gain from valley to peak.
  *Evidence: app/services/analytics/metrics/pnl.py line 291 (`max_runup`)*
- [X] **ANL-NFR-060** (Functional / behavioural) max_runup_date` shall identify the timestamp of maximum runup peak.
  *Evidence: app/services/analytics/metrics/pnl.py line 320 (`max_runup_date`)*
- [X] **ANL-NFR-061** (Functional / behavioural) calculate_period_analysis` shall calculate performance by timestamp bucket.
  *Evidence: app/services/analytics/metrics/time_analysis.py line 28 (`calculate_period_analysis`)*
- [X] **ANL-NFR-062** (Functional / behavioural) calculate_long_short_split` shall calculate long-versus-short profit split.
  *Evidence: app/services/analytics/metrics/time_analysis.py line 54 (`calculate_long_short_split`)*
- [X] **ANL-NFR-063** (Functional / behavioural) calculate_session_performance` shall calculate session performance from timestamped records.
  *Evidence: app/services/analytics/metrics/time_analysis.py line 82 (`calculate_session_performance`)*
- [X] **ANL-NFR-064** (Functional / behavioural) whites_reality_check` shall assess data-snooping bias with White's Reality Check.
  *Evidence: app/services/analytics/statistics/multiple_testing.py line 17 (`whites_reality_check`)*
- [X] **ANL-NFR-065** (Functional / behavioural) probability_of_backtest_overfitting` shall estimate probability of backtest overfitting.
  *Evidence: app/services/analytics/statistics/multiple_testing.py line 60 (`probability_of_backtest_overfitting`)*
- [X] **ANL-NFR-066** (Functional / behavioural) walk_forward_degradation_score` shall measure performance decay from in-sample to out-of-sample scores.
  *Evidence: app/services/analytics/statistics/multiple_testing.py line 74 (`walk_forward_degradation_score`)*
- [X] **ANL-NFR-067** (Functional / behavioural) bonferroni_correction` shall apply Bonferroni correction for multiple hypothesis testing.
  *Evidence: app/services/analytics/statistics/multiple_testing.py line 94 (`bonferroni_correction`)*
- [X] **ANL-NFR-068** (Functional / behavioural) benjamini_hochberg_correction` shall apply Benjamini-Hochberg false-discovery-rate control.
  *Evidence: app/services/analytics/statistics/multiple_testing.py line 108 (`benjamini_hochberg_correction`)*
- [X] **ANL-NFR-069** (Functional / behavioural) stability_score` shall calculate performance consistency across walk-forward windows.
  *Evidence: app/services/analytics/statistics/multiple_testing.py line 129 (`stability_score`)*
- [X] **ANL-NFR-070** (Functional / behavioural) whites_reality_check_backtests` shall run White's Reality Check against backtest result objects.
  *Evidence: app/services/analytics/statistics/multiple_testing.py line 34 (`whites_reality_check_backtests`)*
- [X] **ANL-NFR-071** (Non-functional / governance) Documentation must include success examples for each approved official high-level tool.
  *Evidence: docs/analytics/catalogs.md line 3 (`render_catalog_markdown`)*
- [X] **ANL-NFR-072** (Non-functional / governance) Documentation must include validation-failure examples showing the standard error envelope.
  *Evidence: docs/analytics/catalogs.md line 3 (`render_catalog_markdown`)*
- [X] **ANL-NFR-073** (Non-functional / governance) Low-level metric examples must be labeled as internal/developer examples when they are not official agent/API tools.
  *Evidence: docs/analytics/catalogs.md line 3 (`render_catalog_markdown`)*
- [X] **ANL-NFR-074** (Functional / behavioural) Undefined or unsupported metric values must be represented as omitted fields or `None` according to the output schema plus structured warnings or skipped-section metadata; they must not be serialized as `NaN`, infinity, fabricated zero, or display-only caps.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 59 (`None`)*
- [X] **ANL-NFR-075** (Non-functional / governance) R-multiple fallback proxies must be listed in the Metric Definition Catalog before use; fallback-derived R-multiple values must include warning metadata and mark the affected metric confidence as degraded.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-076** (Non-functional / governance) Every official metric must define formula, units, required inputs, optional inputs, accepted aliases, return scale, annualization basis, sample/population convention, minimum sample size, undefined-result behavior, and golden-fixture expectations.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-077** (Functional / behavioural) total_return` shall calculate total return as a percentage of initial capital.
  *Evidence: app/services/analytics/metrics/pnl.py line 355 (`total_return`)*
- [X] **ANL-NFR-078** (Functional / behavioural) return_on_initial_capital` shall calculate net profit as a percentage of initial capital.
  *Evidence: app/services/analytics/metrics/pnl.py line 388 (`return_on_initial_capital`)*
- [X] **ANL-NFR-079** (Non-functional / governance) Numeric outputs must avoid misleading precision and must handle empty, missing, non-finite, zero-denominator, and insufficient-sample scenarios consistently.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-080** (Non-functional / governance) Documentation must include the Metric Definition Catalog.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-081** (Non-functional / governance) Official Analytics Tool Catalog is approved and maps every official tool to schemas, errors, metadata, side effects, stability, and tests.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-082** (Non-functional / governance) Metric Definition Catalog is approved and no official schema references uncataloged metrics.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-083** (Non-functional / governance) Public/internal export classification is approved, including compatibility aliases and deprecated exports.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-084** (Non-functional / governance) Analytics-owned private canonical metric-kernel model is documented and enforced through public/internal export classification tests.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-085** (Non-functional / governance) Schema compatibility matrix defines accepted, deprecated, legacy-adapted, rejected, and unsupported future versions.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-086** (Non-functional / governance) Decimal monetary precision mandate and deterministic derived-ratio tolerance policy are documented in schemas, metadata, and tests.
  *Evidence: app/services/analytics/contracts/metric_catalog.py line 1132 (`get_metric_definition`)*
- [X] **ANL-NFR-087** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/__init__.py line 164 (`__all__`)*
- [X] **ANL-NFR-088** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/__init__.py line 164 (`__all__`)*
- [X] **ANL-NFR-089** (Scope declaration) No file-specific functional requirements defined. Foundation properties apply.
  *Evidence: app/services/analytics/__init__.py line 164 (`__all__`)*
- [X] **ANL-NFR-090** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/__init__.py line 164 (`__all__`)*
- [X] **ANL-NFR-091** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/__init__.py line 164 (`__all__`)*
- [X] **ANL-NFR-092** (Functional / behavioural) Backtest, paper, live, portfolio, and normalized trading results must either inherit from a canonical `TradingResult` contract or be converted into it through deterministic adapters.
  *Evidence: app/services/analytics/adapters/canonicalize.py line 158 (`to_trading_result`)*
- [X] **ANL-NFR-093** (Functional / behavioural) Deterministic adapters must preserve schema version, result ID, phase/environment, timestamps, account base currency, strategy identifiers, symbols, timeframe, trades, equity curve, optional balance curve, benchmark data, upstream quality metadata, and source metadata without silent field loss.
  *Evidence: app/services/analytics/adapters/canonicalize.py line 158 (`to_trading_result`)*
- [X] **ANL-NFR-094** (Functional / behavioural) Deterministic adapters must define source-to-canonical field mappings, required fields, optional fields, defaulting behavior, unsupported-field behavior, lossless metadata preservation rules, and warning/error behavior for missing or incompatible fields.
  *Evidence: app/services/analytics/adapters/canonicalize.py line 158 (`to_trading_result`)*
- [X] **ANL-NFR-095** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/adapters/protocols.py line 90 (`validate_adapter_contract`)*
- [X] **ANL-NFR-096** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/adapters/protocols.py line 90 (`validate_adapter_contract`)*
- [X] **ANL-NFR-097** (Non-functional / governance) Documentation must include adapter field-mapping tables for every supported upstream result type.
  *Evidence: docs/analytics/catalogs.md line 3 (`render_catalog_markdown`)*
- [X] **ANL-NFR-098** (Non-functional / governance) Official analytics tools must not write files, modify databases, place trades, or require network access.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-099** (Non-functional / governance) Analytics input conversion must support common developer inputs such as pandas dataframes, pandas series, lists of trade records, and lists of numeric values where the public capability expects them.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-100** (Non-functional / governance) Trade-oriented tools must use closed-trade semantics when a metric is defined over realized results.
  *Evidence: app/services/analytics/metrics/aggregate.py line 17 (`metrics_aggregate_boundary`)*
- [X] **ANL-NFR-101** (Non-functional / governance) Closed-trade filtering must exclude records explicitly marked as still open or end-of-data placeholders and must ignore records without close timestamps when close timestamps are required.
  *Evidence: app/services/analytics/metrics/aggregate.py line 17 (`metrics_aggregate_boundary`)*
- [X] **ANL-NFR-102** (Functional / behavioural) Trade classification must distinguish wins, losses, and breakevens using a configured `breakeven_epsilon` from the Metric Definition Catalog or numeric policy ADR so near-zero PnL does not become a false win or loss.
  *Evidence: app/services/analytics/metrics/aggregate.py line 69 (`breakeven_epsilon`)*
- [X] **ANL-NFR-103** (Non-functional / governance) Exposure and time-in-market analytics must merge overlapping trade intervals so simultaneous positions are measured as market presence once for duration metrics.
  *Evidence: app/services/analytics/metrics/aggregate.py line 17 (`metrics_aggregate_boundary`)*
- [X] **ANL-NFR-104** (Non-functional / governance) Long/short split analytics must classify direction using the supplied trade direction/type fields and must not infer trade direction from PnL.
  *Evidence: app/services/analytics/metrics/aggregate.py line 17 (`metrics_aggregate_boundary`)*
- [X] **ANL-NFR-105** (Non-functional / governance) Cost-impact analytics must quantify spread, slippage, and commission drag from supplied cost and gross-profit inputs without mutating the source trades.
  *Evidence: app/services/analytics/metrics/aggregate.py line 17 (`metrics_aggregate_boundary`)*
- [X] **ANL-NFR-106** (Non-functional / governance) Aggregated analytics must preserve source context enough for downstream consumers to know whether inputs came from all trades, long trades, short trades, benchmark comparisons, cost analysis, or statistical validation.
  *Evidence: app/services/analytics/metrics/aggregate.py line 17 (`metrics_aggregate_boundary`)*
- [X] **ANL-NFR-107** (Functional / behavioural) AnalyticsReport` output must include summary, trade metrics, equity metrics, return metrics, drawdown metrics, risk metrics, ratio metrics, distribution metrics, benchmark metrics, efficiency metrics, statistical validation, cost breakdown, warnings, quality flags, dashboard payloads, lineage, and metadata when those sections are applicable.
  *Evidence: app/services/analytics/metrics/aggregate.py line 17 (`metrics_aggregate_boundary`)*
- [X] **ANL-NFR-108** (Functional / behavioural) Report hashes must include deterministic input hash, config hash, report hash, trade ledger hash, equity curve hash, and optional benchmark hash where the source material exists.
  *Evidence: app/services/analytics/metrics/aggregate.py line 17 (`metrics_aggregate_boundary`)*
- [X] **ANL-NFR-109** (Functional / behavioural) ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must approve the initial official high-level tool surface before Builder implementation; candidate tools include `build_analytics_report`, `build_portfolio_analytics_report`, `evaluate_strategy_quality`, `compare_analytics_reports`, `calculate_trade_metrics`, `calculate_equity_metrics`, `calculate_drawdown_metrics`, `calculate_risk_metrics`, `calculate_benchmark_metrics`, `calculate_statistical_validation`, and `calculate_prop_firm_compliance`.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-NFR-110** (Functional / behavioural) Candidate dashboard payloads include summary cards, equity curve chart, drawdown curve chart, monthly returns heatmap, rolling ratio charts, rolling drawdown chart, trade distribution chart, cost breakdown chart, symbol contribution chart, warning table, and quality flag table when source sections exist.
  *Evidence: app/services/analytics/dashboards/overview.py line 97 (`build_overview_payload`)*
- [X] **ANL-NFR-111** (Functional / behavioural) get_closed_trades` shall filter trade records to realized closed trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 89 (`get_closed_trades`)*
- [X] **ANL-NFR-112** (Functional / behavioural) classify_trades` shall classify trades into wins, losses, and breakevens using a consistent threshold.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 143 (`classify_trades`)*
- [X] **ANL-NFR-113** (Functional / behavioural) avg_loss` shall calculate the mean loss of losing trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 629 (`avg_loss`)*
- [X] **ANL-NFR-114** (Functional / behavioural) get_r_multiples` shall calculate R-multiples for trades.
  *Evidence: app/services/analytics/metrics/r_multiples.py line 20 (`get_r_multiples`)*
- [X] **ANL-NFR-115** (Functional / behavioural) trade_pnl_distribution` shall calculate a statistical summary of realized trade PnL.
  *Evidence: app/services/analytics/metrics/drawdown.py line 112 (`trade_pnl_distribution`)*
- [X] **ANL-NFR-116** (Functional / behavioural) trade_level_drawdowns` shall calculate cumulative PnL drawdowns at trade close points.
  *Evidence: app/services/analytics/metrics/drawdown.py line 145 (`trade_level_drawdowns`)*
- [X] **ANL-NFR-117** (Functional / behavioural) max_close_to_close_drawdown` shall calculate maximum trade-level peak-to-valley decline including excursion context where available.
  *Evidence: app/services/analytics/metrics/drawdown.py line 192 (`max_close_to_close_drawdown`)*
- [X] **ANL-NFR-118** (Functional / behavioural) avg_trade_drawdown` shall calculate mean trade-level close-to-close drawdown depth.
  *Evidence: app/services/analytics/metrics/drawdown.py line 211 (`avg_trade_drawdown`)*
- [X] **ANL-NFR-119** (Functional / behavioural) max_consecutive_drawdown_trades` shall calculate maximum number of consecutive trades inside a strategy drawdown.
  *Evidence: app/services/analytics/metrics/drawdown.py line 231 (`max_consecutive_drawdown_trades`)*
- [X] **ANL-NFR-120** (Functional / behavioural) max_close_to_close_drawdown_date` shall identify the timestamp of deepest trade-level valley.
  *Evidence: app/services/analytics/metrics/drawdown.py line 258 (`max_close_to_close_drawdown_date`)*
- [X] **ANL-NFR-121** (Functional / behavioural) avg_trade_notional_efficiency` shall provide the capital-efficiency metric under a clearer average-trade-notional name.
  *Evidence: app/services/analytics/metrics/efficiency.py line 76 (`avg_trade_notional_efficiency`)*
- [X] **ANL-NFR-122** (Functional / behavioural) avg_return_per_risk_unit` shall calculate average R-multiple per closed trade.
  *Evidence: app/services/analytics/metrics/r_multiples.py line 55 (`avg_return_per_risk_unit`)*
- [X] **ANL-NFR-123** (Functional / behavioural) return_per_trade_hour` shall calculate net profit per hour spent in active trades.
  *Evidence: app/services/analytics/metrics/efficiency.py line 105 (`return_per_trade_hour`)*
- [X] **ANL-NFR-124** (Functional / behavioural) return_per_market_hour` shall calculate net profit per hour where at least one trade was open.
  *Evidence: app/services/analytics/metrics/efficiency.py line 126 (`return_per_market_hour`)*
- [X] **ANL-NFR-125** (Functional / behavioural) trades_per_day` shall calculate average number of closed trades per calendar day in the test period.
  *Evidence: app/services/analytics/metrics/efficiency.py line 147 (`trades_per_day`)*
- [X] **ANL-NFR-126** (Functional / behavioural) profit_per_trade_per_day` shall calculate net profit normalized by both number of trades and calendar days.
  *Evidence: app/services/analytics/metrics/efficiency.py line 172 (`profit_per_trade_per_day`)*
- [X] **ANL-NFR-127** (Functional / behavioural) mfe_efficiency` shall calculate average percentage of MFE captured by winning trades.
  *Evidence: app/services/analytics/metrics/efficiency.py line 198 (`mfe_efficiency`)*
- [X] **ANL-NFR-128** (Functional / behavioural) aggregate_mfe_capture_ratio` shall calculate aggregate MFE capture ratio for winning trades.
  *Evidence: app/services/analytics/metrics/efficiency.py line 225 (`aggregate_mfe_capture_ratio`)*
- [X] **ANL-NFR-129** (Functional / behavioural) mae_efficiency` shall calculate realized-loss-to-MAE efficiency for losing trades.
  *Evidence: app/services/analytics/metrics/efficiency.py line 242 (`mae_efficiency`)*
- [X] **ANL-NFR-130** (Functional / behavioural) aggregate_loss_containment_efficiency` shall calculate aggregate loss containment for losing trades.
  *Evidence: app/services/analytics/metrics/efficiency.py line 269 (`aggregate_loss_containment_efficiency`)*
- [X] **ANL-NFR-131** (Functional / behavioural) position_size_efficiency` shall calculate relationship between position size and normalized trade outcome.
  *Evidence: app/services/analytics/metrics/efficiency.py line 297 (`position_size_efficiency`)*
- [X] **ANL-NFR-132** (Functional / behavioural) calculate_efficiency_metrics` shall calculate aggregate MAE/MFE efficiency context from trades.
  *Evidence: app/services/analytics/metrics/efficiency.py line 328 (`calculate_efficiency_metrics`)*
- [X] **ANL-NFR-133** (Functional / behavioural) get_ordered_closed_trades` shall filter closed trades and sort them for sequence-dependent metrics.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 111 (`get_ordered_closed_trades`)*
- [X] **ANL-NFR-134** (Functional / behavioural) total_trades` shall count closed trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 652 (`total_trades`)*
- [X] **ANL-NFR-135** (Functional / behavioural) winning_trades` shall count closed winning trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 670 (`winning_trades`)*
- [X] **ANL-NFR-136** (Functional / behavioural) losing_trades` shall count closed losing trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 690 (`losing_trades`)*
- [X] **ANL-NFR-137** (Functional / behavioural) breakeven_trades` shall count closed breakeven trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 710 (`breakeven_trades`)*
- [X] **ANL-NFR-138** (Functional / behavioural) long_trades` shall count closed long trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 730 (`long_trades`)*
- [X] **ANL-NFR-139** (Functional / behavioural) short_trades` shall count closed short trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 751 (`short_trades`)*
- [X] **ANL-NFR-140** (Functional / behavioural) count_open_trades` shall count currently open trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 772 (`count_open_trades`)*
- [X] **ANL-NFR-141** (Functional / behavioural) win_rate` shall calculate percentage of winning trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 172 (`win_rate`)*
- [X] **ANL-NFR-142** (Functional / behavioural) loss_rate` shall calculate percentage of losing trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 814 (`loss_rate`)*
- [X] **ANL-NFR-143** (Functional / behavioural) avg_win` shall calculate mean profit of winning trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 194 (`avg_win`)*
- [X] **ANL-NFR-144** (Functional / behavioural) largest_win` shall calculate maximum single-trade profit.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 859 (`largest_win`)*
- [X] **ANL-NFR-145** (Functional / behavioural) largest_loss` shall calculate maximum single-trade loss.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 880 (`largest_loss`)*
- [X] **ANL-NFR-146** (Functional / behavioural) median_win` shall calculate median PnL of winning trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 901 (`median_win`)*
- [X] **ANL-NFR-147** (Functional / behavioural) median_loss` shall calculate median PnL of losing trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 925 (`median_loss`)*
- [X] **ANL-NFR-148** (Functional / behavioural) expectancy` shall calculate trade expectancy.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 289 (`expectancy`)*
- [X] **ANL-NFR-149** (Functional / behavioural) max_consecutive_wins` shall calculate maximum consecutive winning trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 970 (`max_consecutive_wins`)*
- [X] **ANL-NFR-150** (Functional / behavioural) max_consecutive_losses` shall calculate maximum consecutive losing trades.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 990 (`max_consecutive_losses`)*
- [X] **ANL-NFR-151** (Functional / behavioural) avg_time_in_trade` shall calculate average trade duration.
  *Evidence: app/services/analytics/metrics/time_analysis.py line 112 (`avg_time_in_trade`)*
- [X] **ANL-NFR-152** (Functional / behavioural) median_time_in_trade` shall calculate median trade duration.
  *Evidence: app/services/analytics/metrics/time_analysis.py line 133 (`median_time_in_trade`)*
- [X] **ANL-NFR-153** (Functional / behavioural) max_time_in_trade` shall calculate maximum trade duration.
  *Evidence: app/services/analytics/metrics/time_analysis.py line 152 (`max_time_in_trade`)*
- [X] **ANL-NFR-154** (Functional / behavioural) min_time_in_trade` shall calculate minimum trade duration.
  *Evidence: app/services/analytics/metrics/time_analysis.py line 173 (`min_time_in_trade`)*
- [X] **ANL-NFR-155** (Functional / behavioural) compute_r_trade_metrics` shall calculate trade metrics from R-multiple inputs.
  *Evidence: app/services/analytics/metrics/r_multiples.py line 74 (`compute_r_trade_metrics`)*
- [X] **ANL-NFR-156** (Functional / behavioural) compute_trade_metrics` shall calculate trade metrics from numeric R values and optional MAE/MFE arrays.
  *Evidence: app/services/analytics/metrics/r_multiples.py line 98 (`compute_trade_metrics`)*
- [X] **ANL-NFR-157** (Functional / behavioural) trade_efficiency` shall calculate realized outcome relative to maximum favorable excursion.
  *Evidence: app/services/analytics/metrics/efficiency.py line 347 (`trade_efficiency`)*
- [X] **ANL-NFR-158** (Functional / behavioural) trade_outcome_entropy` shall calculate Shannon entropy of trade outcomes.
  *Evidence: app/services/analytics/metrics/trade_outcomes.py line 1009 (`trade_outcome_entropy`)*
- [X] **ANL-NFR-159** (Functional / behavioural) longest_flat_period_duration` shall calculate longest period without an active trade.
  *Evidence: app/services/analytics/metrics/efficiency.py line 374 (`longest_flat_period_duration`)*
- [X] **ANL-NFR-160** (Functional / behavioural) calculate_trade_metrics` shall calculate aggregate core trade metrics from normalized trade records.
  *Evidence: app/services/analytics/metrics/aggregate.py line 87 (`calculate_trade_metrics`)*
- [X] **ANL-NFR-161** (Functional / behavioural) calculate_analytics_for_subset` shall calculate all analytics categories for a supplied trade subset.
  *Evidence: app/services/analytics/metrics/aggregate.py line 219 (`calculate_analytics_for_subset`)*
- [X] **ANL-NFR-162** (Functional / behavioural) return_over_drawdown` shall calculate total return relative to maximum trade drawdown.
  *Evidence: app/services/analytics/metrics/pnl.py line 409 (`return_over_drawdown`)*
- [X] **ANL-NFR-163** (Functional / behavioural) adjusted_net_profit_as_percent_of_max_trade_drawdown` shall calculate adjusted net profit as a percentage of max trade drawdown.
  *Evidence: app/services/analytics/metrics/pnl.py line 440 (`adjusted_net_profit_as_percent_of_max_trade_drawdown`)*
- [X] **ANL-NFR-164** (Functional / behavioural) net_profit` shall calculate total realized profit or loss from closed trades.
  *Evidence: app/services/analytics/metrics/pnl.py line 470 (`net_profit`)*
- [X] **ANL-NFR-165** (Functional / behavioural) gross_profit` shall sum winning closed-trade profit.
  *Evidence: app/services/analytics/metrics/pnl.py line 489 (`gross_profit`)*
- [X] **ANL-NFR-166** (Functional / behavioural) gross_loss` shall sum losing closed-trade loss.
  *Evidence: app/services/analytics/metrics/pnl.py line 509 (`gross_loss`)*
- [X] **ANL-NFR-167** (Functional / behavioural) balance_curve_from_closed_trades` shall generate a realized balance curve from closed trades.
  *Evidence: app/services/analytics/metrics/curves.py line 20 (`balance_curve_from_closed_trades`)*
- [X] **ANL-NFR-168** (Functional / behavioural) balance_curve` shall expose balance-curve behavior as an alias of closed-trade balance curve generation.
  *Evidence: app/services/analytics/metrics/curves.py line 20 (`balance_curve`)*
- [X] **ANL-NFR-169** (Functional / behavioural) equity_curve` shall expose equity-curve behavior for common orchestration using the closed-trade curve.
  *Evidence: app/services/analytics/metrics/curves.py line 121 (`equity_curve`)*
- [X] **ANL-NFR-170** (Functional / behavioural) max_loss_probability` shall calculate probability of a single trade loss exceeding a threshold.
  *Evidence: app/services/analytics/metrics/risk.py line 47 (`max_loss_probability`)*
- [X] **ANL-NFR-171** (Functional / behavioural) risk_of_ruin` shall estimate ruin probability through Monte Carlo simulation of trade outcomes.
  *Evidence: app/services/analytics/metrics/risk.py line 70 (`risk_of_ruin`)*
- [X] **ANL-NFR-172** (Functional / behavioural) avg_trade_nominal_exposure` shall calculate average nominal exposure per trade.
  *Evidence: app/services/analytics/metrics/risk.py line 113 (`avg_trade_nominal_exposure`)*
- [X] **ANL-NFR-173** (Functional / behavioural) max_single_trade_margin_utilization` shall calculate maximum margin used by a single trade as a percentage of equity.
  *Evidence: app/services/analytics/metrics/risk.py line 140 (`max_single_trade_margin_utilization`)*
- [X] **ANL-NFR-174** (Functional / behavioural) avg_single_trade_margin_utilization` shall calculate average margin used per trade as a percentage of equity.
  *Evidence: app/services/analytics/metrics/risk.py line 167 (`avg_single_trade_margin_utilization`)*
- [X] **ANL-NFR-175** (Functional / behavioural) risk_of_ruin_with_custom_horizon` shall estimate ruin probability over a fixed future trade horizon.
  *Evidence: app/services/analytics/metrics/risk.py line 195 (`risk_of_ruin_with_custom_horizon`)*
- [X] **ANL-NFR-176** (Non-functional / governance) The module must define concrete maximum accepted input sizes for trades, equity points, benchmark points, portfolio components, dashboard payloads, and statistical observations before production handoff.
  *Evidence: app/services/analytics/boundaries/limits.py line 56 (`enforce_limits`)*
- [X] **ANL-NFR-177** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/boundaries/limits.py line 56 (`enforce_limits`)*
- [X] **ANL-NFR-178** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/boundaries/limits.py line 56 (`enforce_limits`)*
- [X] **ANL-NFR-179** (Functional / behavioural) Equity and return analytics must sort and normalize supplied series deterministically; optional `NaN`/`NaT` observations may be filtered only with recorded warning metadata, required `NaN`/`NaT` fields must fail validation unless the Metric Definition Catalog marks them skippable, and `Infinity`/`-Infinity` at official boundaries must return `VALIDATION_FAILED`.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-180** (Functional / behavioural) Dashboard truncation/downsampling must be deterministic and must preserve first point, last point, local extrema where practical, drawdown troughs, equity highs, and timestamps associated with major, critical, or blocker warnings.
  *Evidence: app/services/analytics/dashboards/truncation.py line 63 (`truncate_series`)*
- [X] **ANL-NFR-181** (Functional / behavioural) benchmark_returns` shall generate a return series from benchmark equity or price values.
  *Evidence: app/services/analytics/metrics/equity.py line 194-215 (benchmark_returns)*
- [X] **ANL-NFR-182** (Functional / behavioural) relative_drawdown_series` shall generate relative underperformance between strategy and benchmark equity.
  *Evidence: app/services/analytics/metrics/drawdown.py line 291 (`relative_drawdown_series`)*
- [X] **ANL-NFR-183** (Functional / behavioural) drawdown_series` shall calculate drawdown values from an equity curve.
  *Evidence: app/services/analytics/metrics/drawdown.py line 63 (`drawdown_series`)*
- [X] **ANL-NFR-184** (Functional / behavioural) drawdown_duration_series` shall calculate drawdown duration values from an equity curve.
  *Evidence: app/services/analytics/metrics/drawdown.py line 86 (`drawdown_duration_series`)*
- [X] **ANL-NFR-185** (Functional / behavioural) max_drawdown_duration_from_equity` shall calculate maximum drawdown duration from equity values.
  *Evidence: app/services/analytics/metrics/drawdown.py line 377 (`max_drawdown_duration_from_equity`)*
- [X] **ANL-NFR-186** (Functional / behavioural) max_strategy_drawdown_date` shall identify the timestamp of deepest strategy equity valley.
  *Evidence: app/services/analytics/metrics/drawdown.py line 399 (`max_strategy_drawdown_date`)*
- [X] **ANL-NFR-187** (Functional / behavioural) avg_underwater_drawdown_percent` shall calculate average drawdown depth while equity is below peak.
  *Evidence: app/services/analytics/metrics/drawdown.py line 458 (`avg_underwater_drawdown_percent`)*
- [X] **ANL-NFR-188** (Functional / behavioural) calculate_drawdown_metrics` shall calculate aggregate drawdown metrics from an equity curve.
  *Evidence: app/services/analytics/metrics/drawdown.py line 492 (`calculate_drawdown_metrics`)*
- [X] **ANL-NFR-189** (Functional / behavioural) compute_equity_metrics` shall calculate equity metrics from return inputs.
  *Evidence: app/services/analytics/metrics/aggregate.py line 262 (`compute_equity_metrics`)*
- [X] **ANL-NFR-190** (Functional / behavioural) total_return_usd` shall calculate total return in currency units from an equity curve.
  *Evidence: app/services/analytics/metrics/equity.py line 216-243 (total_return_usd)*
- [X] **ANL-NFR-191** (Functional / behavioural) returns_series` shall calculate percentage returns between equity points.
  *Evidence: app/services/analytics/metrics/equity.py line 94-115 (returns_series)*
- [X] **ANL-NFR-192** (Functional / behavioural) log_returns_series` shall calculate logarithmic returns between equity points.
  *Evidence: app/services/analytics/metrics/equity.py line 116-138 (log_returns_series)*
- [X] **ANL-NFR-193** (Functional / behavioural) daily_returns` shall calculate daily percentage returns from an equity curve.
  *Evidence: app/services/analytics/metrics/equity.py line 288-309 (daily_returns)*
- [X] **ANL-NFR-194** (Functional / behavioural) weekly_returns` shall calculate weekly percentage returns from an equity curve.
  *Evidence: app/services/analytics/metrics/equity.py line 310-331 (weekly_returns)*
- [X] **ANL-NFR-195** (Functional / behavioural) monthly_returns` shall calculate monthly percentage returns from an equity curve.
  *Evidence: app/services/analytics/metrics/equity.py line 332-353 (monthly_returns)*
- [X] **ANL-NFR-196** (Functional / behavioural) annual_returns` shall calculate annual percentage returns from an equity curve.
  *Evidence: app/services/analytics/metrics/equity.py line 354-375 (annual_returns)*
- [X] **ANL-NFR-197** (Functional / behavioural) calculate_return_metrics` shall calculate aggregate cumulative and average returns from an equity curve.
  *Evidence: app/services/analytics/metrics/equity.py line 376-423 (calculate_return_metrics)*
- [X] **ANL-NFR-198** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/contracts/models.py line 392 (`validate_schema_version`)*
- [X] **ANL-NFR-199** (Functional / behavioural) Official analytics tools must validate `request_id`; missing, empty, malformed, or unsafe request IDs must return a structured validation error envelope.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 18 (`request_id`)*
- [X] **ANL-NFR-200** (Functional / behavioural) Official analytics tools must return the standard tool envelope on success and on controlled validation failure.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-201** (Functional / behavioural) Date/time analytics must parse supplied open/close timestamps, support both datetime-like and numeric timestamp inputs where implemented, and return JSON-safe values for durations and timestamps.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-202** (Functional / behavioural) Live-vs-backtest and paper-vs-backtest degradation comparisons must validate strategy ID, strategy version, symbols, timeframe or return frequency, evaluation window, account base currency, and comparable cost/slippage model metadata before pairing.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-203** (Functional / behavioural) win_loss_streaks` shall return winning and losing streak sequences.
  *Evidence: app/services/analytics/metrics/equity.py line 424-471 (win_loss_streaks)*
- [X] **ANL-NFR-204** (Functional / behavioural) kelly_criterion` shall calculate Kelly criterion percentage from R-multiples or returns.
  *Evidence: app/services/analytics/metrics/equity.py line 472-506 (kelly_criterion)*
- [X] **ANL-NFR-205** (Functional / behavioural) avg_monthly_return` shall calculate arithmetic average monthly return.
  *Evidence: app/services/analytics/metrics/equity.py line 507-533 (avg_monthly_return)*
- [X] **ANL-NFR-206** (Functional / behavioural) monthly_return_stddev` shall calculate monthly return volatility.
  *Evidence: app/services/analytics/metrics/equity.py line 534-560 (monthly_return_stddev)*
- [X] **ANL-NFR-207** (Functional / behavioural) annualized_return` shall calculate geometric annualized return.
  *Evidence: app/services/analytics/metrics/equity.py line 561-604 (annualized_return)*
- [X] **ANL-NFR-208** (Functional / behavioural) geometric_mean_return` shall calculate geometric mean return.
  *Evidence: app/services/analytics/metrics/equity.py line 139-158 (geometric_mean_return)*
- [X] **ANL-NFR-209** (Functional / behavioural) best_return` shall calculate best single-period return.
  *Evidence: app/services/analytics/metrics/equity.py line 628-655 (best_return)*
- [X] **ANL-NFR-210** (Functional / behavioural) worst_return` shall calculate worst single-period return.
  *Evidence: app/services/analytics/metrics/equity.py line 656-683 (worst_return)*
- [X] **ANL-NFR-211** (Functional / behavioural) buy_and_hold_return` shall calculate total buy-and-hold return from price data.
  *Evidence: app/services/analytics/metrics/equity.py line 684-711 (buy_and_hold_return)*
- [X] **ANL-NFR-212** (Functional / behavioural) return_volatility` shall calculate return standard deviation.
  *Evidence: app/services/analytics/metrics/equity.py line 159-175 (return_volatility)*
- [X] **ANL-NFR-213** (Functional / behavioural) downside_return_volatility` shall calculate volatility of returns below target.
  *Evidence: app/services/analytics/metrics/equity.py line 176-193 (downside_return_volatility)*
- [X] **ANL-NFR-214** (Functional / behavioural) return_skewness` shall calculate return-distribution skewness.
  *Evidence: app/services/analytics/metrics/equity.py line 759-793 (return_skewness)*
- [X] **ANL-NFR-215** (Functional / behavioural) return_kurtosis` shall calculate return-distribution excess kurtosis.
  *Evidence: app/services/analytics/metrics/equity.py line 794-828 (return_kurtosis)*
- [X] **ANL-NFR-216** (Functional / behavioural) return_on_account` shall calculate return on required account size.
  *Evidence: app/services/analytics/metrics/equity.py line 829-855 (return_on_account)*
- [X] **ANL-NFR-217** (Functional / behavioural) Strategy-quality evaluation must rely only on the supplied report payload and must surface warnings for weak profitability, high drawdown, overfitting risk, small sample size, or other observable quality concerns.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-218** (Functional / behavioural) Optional sections such as TCA metrics, attribution, prop-firm compliance evidence, drawdown distribution, tail-risk metrics, dynamic correlation, walk-forward analytics, metric comparisons, live degradation, and explainability must be represented as calculated, skipped, or failed.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-219** (Functional / behavioural) Formula definitions must be explicit for Sharpe, Sortino, Calmar, Jensen alpha, beta, tracking error, information ratio, VaR, CVaR, expected shortfall, SQN, Kelly, drawdown duration, CAGR, profit factor, expectancy, and R-multiple metrics before those metrics are locked as official contracts.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-220** (Functional / behavioural) max_relative_drawdown_percent` shall calculate maximum relative underperformance as a positive percentage.
  *Evidence: app/services/analytics/metrics/drawdown.py line 559 (`max_relative_drawdown_percent`)*
- [X] **ANL-NFR-221** (Functional / behavioural) max_strategy_drawdown` shall calculate deepest peak-to-valley decline in currency units.
  *Evidence: app/services/analytics/metrics/drawdown.py line 399 (`max_strategy_drawdown`)*
- [X] **ANL-NFR-222** (Functional / behavioural) max_strategy_drawdown_percent` shall calculate deepest percentage decline relative to running peak.
  *Evidence: app/services/analytics/metrics/drawdown.py line 603 (`max_strategy_drawdown_percent`)*
- [X] **ANL-NFR-223** (Functional / behavioural) max_drawdown` shall calculate maximum drawdown from returns.
  *Evidence: app/services/analytics/metrics/drawdown.py line 377 (`max_drawdown`)*
- [X] **ANL-NFR-224** (Functional / behavioural) avg_drawdown` shall calculate average drawdown depth.
  *Evidence: app/services/analytics/metrics/drawdown.py line 647 (`avg_drawdown`)*
- [X] **ANL-NFR-225** (Functional / behavioural) drawdown_distribution` shall calculate detailed drawdown distribution statistics.
  *Evidence: app/services/analytics/metrics/drawdown.py line 671 (`drawdown_distribution`)*
- [X] **ANL-NFR-226** (Functional / behavioural) max_drawdown_duration_from_returns` shall calculate maximum drawdown duration from return values.
  *Evidence: app/services/analytics/metrics/drawdown.py line 703 (`max_drawdown_duration_from_returns`)*
- [X] **ANL-NFR-227** (Functional / behavioural) max_drawdown_duration` shall calculate maximum drawdown duration from the selected input type.
  *Evidence: app/services/analytics/metrics/drawdown.py line 377 (`max_drawdown_duration`)*
- [X] **ANL-NFR-228** (Functional / behavioural) avg_drawdown_duration` shall calculate average duration of drawdown episodes.
  *Evidence: app/services/analytics/metrics/drawdown.py line 738 (`avg_drawdown_duration`)*
- [X] **ANL-NFR-229** (Functional / behavioural) time_to_recovery` shall calculate recovery periods for unique drawdowns.
  *Evidence: app/services/analytics/metrics/drawdown.py line 770 (`time_to_recovery`)*
- [X] **ANL-NFR-230** (Functional / behavioural) recovery_factor` shall calculate net profit relative to maximum drawdown.
  *Evidence: app/services/analytics/metrics/drawdown.py line 798 (`recovery_factor`)*
- [X] **ANL-NFR-231** (Functional / behavioural) max_close_to_close_drawdown_percent` shall calculate close-to-close drawdown as a percentage.
  *Evidence: app/services/analytics/metrics/drawdown.py line 821 (`max_close_to_close_drawdown_percent`)*
- [X] **ANL-NFR-232** (Functional / behavioural) account_size_required` shall estimate capital required to withstand max close-to-close dips.
  *Evidence: app/services/analytics/metrics/drawdown.py line 844 (`account_size_required`)*
- [X] **ANL-NFR-233** (Functional / behavioural) avg_yearly_max_drawdown` shall average the maximum drawdown observed in each year.
  *Evidence: app/services/analytics/metrics/drawdown.py line 867 (`avg_yearly_max_drawdown`)*
- [X] **ANL-NFR-234** (Functional / behavioural) ulcer_index` shall calculate squared-drawdown-based ulcer index.
  *Evidence: app/services/analytics/metrics/drawdown.py line 895 (`ulcer_index`)*
- [X] **ANL-NFR-235** (Functional / behavioural) pain_index` shall calculate mean absolute percentage drawdown.
  *Evidence: app/services/analytics/metrics/drawdown.py line 920 (`pain_index`)*
- [X] **ANL-NFR-236** (Functional / behavioural) pain_ratio` shall calculate return relative to pain index.
  *Evidence: app/services/analytics/metrics/drawdown.py line 945 (`pain_ratio`)*
- [X] **ANL-NFR-237** (Functional / behavioural) calmar_ratio` shall calculate annualized return relative to maximum drawdown.
  *Evidence: app/services/analytics/metrics/drawdown.py line 980 (`calmar_ratio`)*
- [X] **ANL-NFR-238** (Functional / behavioural) fouse_ratio` shall calculate Fouse drawdown-index-style ratio.
  *Evidence: app/services/analytics/metrics/drawdown.py line 1015 (`fouse_ratio`)*
- [X] **ANL-NFR-239** (Functional / behavioural) sterling_ratio` shall calculate CAGR relative to adjusted average yearly maximum drawdown.
  *Evidence: app/services/analytics/metrics/drawdown.py line 1050 (`sterling_ratio`)*
- [X] **ANL-NFR-240** (Functional / behavioural) rina_index` shall calculate select net profit relative to average drawdown and time in market.
  *Evidence: app/services/analytics/metrics/drawdown.py line 1084 (`rina_index`)*
- [X] **ANL-NFR-241** (Functional / behavioural) adjusted_net_profit_as_percent_of_max_strategy_drawdown` shall calculate adjusted net profit as a percentage of max strategy drawdown.
  *Evidence: app/services/analytics/metrics/drawdown.py line 1110 (`adjusted_net_profit_as_percent_of_max_strategy_drawdown`)*
- [X] **ANL-NFR-242** (Functional / behavioural) return_on_max_strategy_drawdown` shall calculate total return relative to maximum strategy drawdown.
  *Evidence: app/services/analytics/metrics/drawdown.py line 1173 (`return_on_max_strategy_drawdown`)*
- [X] **ANL-NFR-243** (Functional / behavioural) return_on_max_close_to_close_drawdown` shall calculate net profit relative to maximum close-to-close drawdown.
  *Evidence: app/services/analytics/metrics/drawdown.py line 1198 (`return_on_max_close_to_close_drawdown`)*
- [X] **ANL-NFR-244** (Functional / behavioural) drawdown_probability` shall calculate probability of drawdown exceeding a threshold.
  *Evidence: app/services/analytics/metrics/drawdown.py line 1224 (`drawdown_probability`)*
- [X] **ANL-NFR-245** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/metrics/drawdown.py line 48 (`metrics_drawdown_boundary`)*
- [X] **ANL-NFR-246** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/metrics/drawdown.py line 48 (`metrics_drawdown_boundary`)*
- [X] **ANL-NFR-247** (Functional / behavioural) Official analytics tools must be low-risk, read-only operations.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-NFR-248** (Functional / behavioural) Metadata must include tool name, tool version, tool category, tool risk level, request ID, execution time, and side-effect flags.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-NFR-249** (Functional / behavioural) R-multiple analytics must prefer explicit initial-risk fields when available and fall back only to documented analytics proxies when risk fields are absent.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-NFR-250** (Functional / behavioural) Official analytics tool responses must include metadata, side-effect flags, risk flags, execution timing, and structured errors.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-NFR-251** (Functional / behavioural) Metric definitions must document default configuration sources for annualization, risk-free rate, breakeven tolerance, minimum sample size, bootstrap count limits, dashboard limits, FX stale-rate limits, and confidence/alpha levels when those defaults are approved.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-NFR-252** (Functional / behavioural) Strategy-quality scorecards must not make final live approval, promotion, prop-firm enforcement, or risk-governor decisions.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-NFR-253** (Functional / behavioural) Strategy-quality outputs must not claim final approval, promotion, live-readiness, prop-firm compliance enforcement, risk-limit approval, or portfolio allocation authority.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-NFR-254** (Functional / behavioural) risk_adjusted_efficiency` shall calculate return relative to total defined initial risk.
  *Evidence: app/services/analytics/metrics/risk.py line 212 (`risk_adjusted_efficiency`)*
- [X] **ANL-NFR-255** (Functional / behavioural) profit_per_pip_risk` shall calculate reward-to-risk based on profit pips relative to MAE pips.
  *Evidence: app/services/analytics/metrics/risk.py line 235 (`profit_per_pip_risk`)*
- [X] **ANL-NFR-256** (Functional / behavioural) upside_potential_ratio` shall calculate upside potential relative to downside risk.
  *Evidence: app/services/analytics/metrics/risk.py line 258 (`upside_potential_ratio`)*
- [X] **ANL-NFR-257** (Functional / behavioural) volatility` shall calculate return standard deviation as a positive percentage.
  *Evidence: app/services/analytics/metrics/risk.py line 286 (`volatility`)*
- [X] **ANL-NFR-258** (Functional / behavioural) annualized_volatility` shall calculate annualized volatility as a positive percentage.
  *Evidence: app/services/analytics/metrics/risk.py line 309 (`annualized_volatility`)*
- [X] **ANL-NFR-259** (Functional / behavioural) downside_volatility` shall calculate downside deviation as a positive percentage.
  *Evidence: app/services/analytics/metrics/risk.py line 329 (`downside_volatility`)*
- [X] **ANL-NFR-260** (Functional / behavioural) value_at_risk` shall calculate value-at-risk as a positive percentage.
  *Evidence: app/services/analytics/metrics/risk.py line 353 (`value_at_risk`)*
- [X] **ANL-NFR-261** (Functional / behavioural) conditional_var` shall calculate conditional value-at-risk as a positive percentage.
  *Evidence: app/services/analytics/metrics/risk.py line 378 (`conditional_var`)*
- [X] **ANL-NFR-262** (Functional / behavioural) expected_shortfall` shall calculate expected shortfall.
  *Evidence: app/services/analytics/metrics/risk.py line 404 (`expected_shortfall`)*
- [X] **ANL-NFR-263** (Functional / behavioural) max_nominal_exposure_simple` shall calculate maximum nominal exposure held at one time.
  *Evidence: app/services/analytics/metrics/risk.py line 421 (`max_nominal_exposure_simple`)*
- [X] **ANL-NFR-264** (Functional / behavioural) max_gross_exposure` shall calculate maximum gross nominal exposure.
  *Evidence: app/services/analytics/metrics/risk.py line 445 (`max_gross_exposure`)*
- [X] **ANL-NFR-265** (Functional / behavioural) exposure_time_ratio` shall calculate percentage of total period spent in market.
  *Evidence: app/services/analytics/metrics/risk.py line 462 (`exposure_time_ratio`)*
- [X] **ANL-NFR-266** (Functional / behavioural) time_weighted_avg_exposure` shall calculate time-weighted average notional exposure.
  *Evidence: app/services/analytics/metrics/risk.py line 482 (`time_weighted_avg_exposure`)*
- [X] **ANL-NFR-267** (Functional / behavioural) portfolio_margin_utilization_curve` shall generate portfolio margin-utilization curve over time.
  *Evidence: app/services/analytics/metrics/risk.py line 513 (`portfolio_margin_utilization_curve`)*
- [X] **ANL-NFR-268** (Functional / behavioural) compounding_risk_of_ruin` shall estimate ruin probability with dynamic compounding risk.
  *Evidence: app/services/analytics/metrics/risk.py line 543 (`compounding_risk_of_ruin`)*
- [X] **ANL-NFR-269** (Functional / behavioural) historical_var_by_symbol` shall calculate historical value-at-risk by symbol.
  *Evidence: app/services/analytics/metrics/risk.py line 560 (`historical_var_by_symbol`)*
- [X] **ANL-NFR-270** (Functional / behavioural) portfolio_var_from_covariance` shall calculate portfolio value-at-risk from covariance and weights.
  *Evidence: app/services/analytics/metrics/risk.py line 587 (`portfolio_var_from_covariance`)*
- [X] **ANL-NFR-271** (Functional / behavioural) calculate_risk_metrics` shall calculate aggregate risk metrics such as VaR, CVaR, and volatility.
  *Evidence: app/services/analytics/metrics/risk.py line 614 (`calculate_risk_metrics`)*
- [X] **ANL-NFR-272** (Functional / behavioural) Tool metadata must consistently identify the category as `analytics` and risk level as `low`.
  *Evidence: app/services/analytics/boundaries/envelopes.py line 26 (`success_envelope`)*
- [X] **ANL-NFR-273** (Functional / behavioural) Analytics input and output contracts must remain aligned with Simulation, Optimization, Risk, Portfolio, Trading receipt, and UI/API contracts.
  *Evidence: app/services/analytics/boundaries/envelopes.py line 26 (`success_envelope`)*
- [X] **ANL-NFR-274** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/boundaries/envelopes.py line 26 (`success_envelope`)*
- [X] **ANL-NFR-275** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/boundaries/envelopes.py line 26 (`success_envelope`)*
- [X] **ANL-NFR-276** (Functional / behavioural) Redaction rules must apply to sensitive keys and sensitive-looking values in inputs, warnings, errors, logs, metadata, and diagnostic details.
  *Evidence: app/services/analytics/contracts/warnings.py line 173 (`build_warning`)*
- [X] **ANL-NFR-277** (Non-functional / governance) Low-level metric helpers such as individual average, skewness, kurtosis, tail-ratio, tracking-error, ulcer-index, omega-ratio, payoff-ratio, and date helper functions must remain internal/support-only unless explicitly promoted by the Official Analytics Tool Catalog.
  *Evidence: app/services/analytics/contracts/warnings.py line 173 (`build_warning`)*
- [X] **ANL-NFR-278** (Functional / behavioural) Warnings and quality flags must include code, severity, affected section, source context, and enough bounded detail for downstream review.
  *Evidence: app/services/analytics/contracts/warnings.py line 173 (`build_warning`)*
- [X] **ANL-NFR-279** (Functional / behavioural) Warning and quality-flag catalogs must define code, severity, affected section, source-backed status, whether the flag blocks promotion, bounded detail rules, and linked test fixtures.
  *Evidence: app/services/analytics/contracts/warnings.py line 173 (`build_warning`)*
- [X] **ANL-NFR-280** (Functional / behavioural) Explainability outputs must distinguish explained PnL, unexplained PnL, explained variance percentage, sample count, and driver stability when those inputs are supplied.
  *Evidence: app/services/analytics/contracts/warnings.py line 173 (`build_warning`)*
- [X] **ANL-NFR-281** (Functional / behavioural) benchmark_information_ratio` shall expose benchmark information ratio without colliding with the ratios module export.
  *Evidence: app/services/analytics/metrics/exports.py line 94 (`benchmark_information_ratio`)*
- [X] **ANL-NFR-282** (Functional / behavioural) up_down_capture` shall calculate up-capture and down-capture ratios.
  *Evidence: app/services/analytics/metrics/ratios.py line 1243 (`up_down_capture`)*
- [X] **ANL-NFR-283** (Functional / behavioural) metrics_win_rate_fraction` shall expose metrics-module win-rate fraction behavior without colliding with ratios exports.
  *Evidence: app/services/analytics/metrics/exports.py line 114 (`metrics_win_rate_fraction`)*
- [X] **ANL-NFR-284** (Functional / behavioural) metrics_expectancy_r` shall expose metrics-module R-expectancy behavior without colliding with ratios exports.
  *Evidence: app/services/analytics/metrics/exports.py line 134 (`metrics_expectancy_r`)*
- [X] **ANL-NFR-285** (Functional / behavioural) sharpe_ratio` shall calculate excess return per unit of volatility.
  *Evidence: app/services/analytics/metrics/ratios.py line 66 (`sharpe_ratio`)*
- [X] **ANL-NFR-286** (Functional / behavioural) annualized_sharpe_ratio` shall calculate annualized Sharpe ratio from monthly inputs.
  *Evidence: app/services/analytics/metrics/ratios.py line 984 (`annualized_sharpe_ratio`)*
- [X] **ANL-NFR-287** (Functional / behavioural) sortino_ratio` shall calculate excess return per unit of downside volatility.
  *Evidence: app/services/analytics/metrics/ratios.py line 95 (`sortino_ratio`)*
- [X] **ANL-NFR-288** (Functional / behavioural) ratios_information_ratio` shall expose ratios-module information ratio without colliding with benchmark exports.
  *Evidence: app/services/analytics/metrics/exports.py line 154 (`ratios_information_ratio`)*
- [X] **ANL-NFR-289** (Functional / behavioural) omega_ratio` shall calculate probability-weighted gains relative to losses.
  *Evidence: app/services/analytics/metrics/ratios.py line 128 (`omega_ratio`)*
- [X] **ANL-NFR-290** (Functional / behavioural) gain_to_pain_ratio` shall calculate gains relative to absolute negative returns.
  *Evidence: app/services/analytics/metrics/ratios.py line 1012 (`gain_to_pain_ratio`)*
- [X] **ANL-NFR-291** (Functional / behavioural) kappa_ratio` shall calculate generalized Sortino-style Kappa ratio.
  *Evidence: app/services/analytics/metrics/ratios.py line 1031 (`kappa_ratio`)*
- [X] **ANL-NFR-292** (Functional / behavioural) profit_factor` shall calculate gross profit relative to gross loss.
  *Evidence: app/services/analytics/metrics/ratios.py line 211 (`profit_factor`)*
- [X] **ANL-NFR-293** (Functional / behavioural) payoff_ratio` shall calculate average win relative to average loss.
  *Evidence: app/services/analytics/metrics/ratios.py line 295 (`payoff_ratio`)*
- [X] **ANL-NFR-294** (Functional / behavioural) edge_ratio` shall calculate payoff edge adjusted by win rate.
  *Evidence: app/services/analytics/metrics/ratios.py line 1053 (`edge_ratio`)*
- [X] **ANL-NFR-295** (Functional / behavioural) profit_to_mae_ratio` shall calculate profit capture relative to adverse excursion.
  *Evidence: app/services/analytics/metrics/ratios.py line 1071 (`profit_to_mae_ratio`)*
- [X] **ANL-NFR-296** (Functional / behavioural) mfe_to_mae_ratio` shall calculate favorable excursion relative to adverse excursion.
  *Evidence: app/services/analytics/metrics/ratios.py line 1087 (`mfe_to_mae_ratio`)*
- [X] **ANL-NFR-297** (Functional / behavioural) expectancy_over_std` shall calculate expectancy stability relative to standard deviation.
  *Evidence: app/services/analytics/metrics/ratios.py line 1105 (`expectancy_over_std`)*
- [X] **ANL-NFR-298** (Functional / behavioural) net_profit_as_percent_of_largest_loss` shall calculate net profit as a percentage of largest loss.
  *Evidence: app/services/analytics/metrics/ratios.py line 1135 (`net_profit_as_percent_of_largest_loss`)*
- [X] **ANL-NFR-299** (Functional / behavioural) select_net_profit_as_percent_of_largest_loss` shall calculate selected net profit as a percentage of largest loss.
  *Evidence: app/services/analytics/metrics/ratios.py line 1154 (`select_net_profit_as_percent_of_largest_loss`)*
- [X] **ANL-NFR-300** (Functional / behavioural) adjusted_net_profit_as_percent_of_largest_loss` shall calculate adjusted net profit as a percentage of largest loss.
  *Evidence: app/services/analytics/metrics/ratios.py line 1171 (`adjusted_net_profit_as_percent_of_largest_loss`)*
- [X] **ANL-NFR-301** (Functional / behavioural) adjusted_profit_factor` shall calculate adjusted gross profit relative to adjusted gross loss.
  *Evidence: app/services/analytics/metrics/ratios.py line 353 (`adjusted_profit_factor`)*
- [X] **ANL-NFR-302** (Functional / behavioural) select_profit_factor` shall calculate selected gross profit relative to selected gross loss.
  *Evidence: app/services/analytics/metrics/ratios.py line 379 (`select_profit_factor`)*
- [X] **ANL-NFR-303** (Functional / behavioural) calculate_ratio_metrics` shall calculate aggregate ratio metrics from return values.
  *Evidence: app/services/analytics/metrics/ratios.py line 1188 (`calculate_ratio_metrics`)*
- [X] **ANL-NFR-304** (Functional / behavioural) Architectural Mandate: derived ratios may use deterministic `float64` arithmetic only where exact decimal arithmetic is not appropriate, with documented tolerance stored in configuration, tests, and report metadata.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 40 (`float64`)*
- [X] **ANL-NFR-305** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-306** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-307** (Functional / behavioural) The module must degrade safely when optional acceleration libraries are unavailable.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-308** (Functional / behavioural) Calculations over large datasets must use vectorized operations where feasible and must degrade to bounded chunked processing with warnings when vectorization or memory limits are exceeded.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-309** (Functional / behavioural) Shared caches, if implemented, must be concurrency-safe or read-through and keyed by input hash, configuration hash, and analytics engine version.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-310** (Functional / behavioural) Long-series cumulative operations must use numerically stable methods where feasible and must document any approximation or chunking behavior.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-311** (Functional / behavioural) Duplicate timestamps must be rejected or resolved deterministically according to configuration and recorded in diagnostics.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-312** (Functional / behavioural) Invalid or missing required inputs must fail with a structured error envelope, not an uncaught exception. Custom analytics exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
  *Evidence: app/services/analytics/boundaries/request_validation.py line 62 (`validate_request`)*
- [X] **ANL-NFR-313** (Functional / behavioural) time_in_market_duration` shall calculate total duration where at least one position was open.
  *Evidence: app/services/analytics/metrics/time_analysis.py line 194 (`time_in_market_duration`)*
- [X] **ANL-NFR-314** (Functional / behavioural) trading_period_duration` shall calculate total duration of the trading period.
  *Evidence: app/services/analytics/metrics/time_analysis.py line 212 (`trading_period_duration`)*
- [X] **ANL-NFR-315** (Functional / behavioural) deflated_sharpe_ratio` shall adjust Sharpe ratio diagnostics for multiple testing and non-normality.
  *Evidence: app/services/analytics/metrics/ratios.py line 1264 (`deflated_sharpe_ratio`)*
- [X] **ANL-NFR-316** (Functional / behavioural) return_distribution` shall calculate a statistical summary of returns.
  *Evidence: app/services/analytics/statistics/distributions.py line 433 (`return_distribution`)*
- [X] **ANL-NFR-317** (Functional / behavioural) r_multiple_distribution` shall calculate a statistical summary of R-multiple values.
  *Evidence: app/services/analytics/statistics/distributions.py line 446 (`r_multiple_distribution`)*
- [X] **ANL-NFR-318** (Functional / behavioural) distributions_r_multiple_distribution` shall expose distribution-module R-multiple distribution behavior without colliding with metrics exports.
  *Evidence: app/services/analytics/metrics/exports.py line 171 (`distributions_r_multiple_distribution`)*
- [X] **ANL-NFR-319** (Functional / behavioural) percentile_summary` shall return selected percentile values.
  *Evidence: app/services/analytics/statistics/distributions.py line 144 (`percentile_summary`)*
- [X] **ANL-NFR-320** (Functional / behavioural) upside_downside_summary` shall summarize positive and negative outcome distributions.
  *Evidence: app/services/analytics/statistics/distributions.py line 168 (`upside_downside_summary`)*
- [X] **ANL-NFR-321** (Functional / behavioural) skewness` shall calculate return or value skewness.
  *Evidence: app/services/analytics/statistics/distributions.py line 76 (`skewness`)*
- [X] **ANL-NFR-322** (Functional / behavioural) kurtosis` shall calculate excess kurtosis.
  *Evidence: app/services/analytics/statistics/distributions.py line 98 (`kurtosis`)*
- [X] **ANL-NFR-323** (Functional / behavioural) higher_moments` shall calculate detailed skewness and kurtosis context.
  *Evidence: app/services/analytics/statistics/distributions.py line 120 (`higher_moments`)*
- [X] **ANL-NFR-324** (Functional / behavioural) fat_tail_score` shall estimate tail heaviness relative to normal behavior.
  *Evidence: app/services/analytics/statistics/distributions.py line 193 (`fat_tail_score`)*
- [X] **ANL-NFR-325** (Functional / behavioural) tail_ratio` shall calculate the ratio between upper-tail and lower-tail percentile magnitudes.
  *Evidence: app/services/analytics/statistics/distributions.py line 205 (`tail_ratio`)*
- [X] **ANL-NFR-326** (Functional / behavioural) jarque_bera_test` shall run a Jarque-Bera normality diagnostic.
  *Evidence: app/services/analytics/statistics/distributions.py line 226 (`jarque_bera_test`)*
- [X] **ANL-NFR-327** (Functional / behavioural) shapiro_wilk_test` shall run a Shapiro-Wilk normality diagnostic.
  *Evidence: app/services/analytics/statistics/distributions.py line 247 (`shapiro_wilk_test`)*
- [X] **ANL-NFR-328** (Functional / behavioural) qq_plot_data` shall generate theoretical and actual quantile data for Q-Q plotting.
  *Evidence: app/services/analytics/statistics/distributions.py line 266 (`qq_plot_data`)*
- [X] **ANL-NFR-329** (Functional / behavioural) fit_distribution` shall fit a theoretical distribution and return fit parameters.
  *Evidence: app/services/analytics/statistics/distributions.py line 298 (`fit_distribution`)*
- [X] **ANL-NFR-330** (Functional / behavioural) distribution_fit_quality` shall return fit-quality diagnostics such as likelihood and information criteria.
  *Evidence: app/services/analytics/statistics/distributions.py line 316 (`distribution_fit_quality`)*
- [X] **ANL-NFR-331** (Functional / behavioural) histogram_data` shall generate histogram bin data for plotting.
  *Evidence: app/services/analytics/statistics/distributions.py line 346 (`histogram_data`)*
- [X] **ANL-NFR-332** (Functional / behavioural) detect_outliers` shall identify outliers with the requested method and threshold.
  *Evidence: app/services/analytics/statistics/distributions.py line 378 (`detect_outliers`)*
- [X] **ANL-NFR-333** (Functional / behavioural) outlier_ratio` shall calculate the percentage of data points flagged as outliers.
  *Evidence: app/services/analytics/statistics/distributions.py line 411 (`outlier_ratio`)*
- [X] **ANL-NFR-334** (Functional / behavioural) calculate_distribution_metrics` shall calculate aggregate distribution metrics from numeric values.
  *Evidence: app/services/analytics/statistics/distributions.py line 509 (`calculate_distribution_metrics`)*
- [X] **ANL-NFR-335** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/statistics/distributions.py line 23 (`statistics_distribution_boundary`)*
- [X] **ANL-NFR-336** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/statistics/distributions.py line 23 (`statistics_distribution_boundary`)*
- [X] **ANL-NFR-337** (Functional / behavioural) Analytics behavior must be deterministic for the same inputs except where Monte Carlo, bootstrap, or permutation features intentionally use randomness; those features should support explicit seeds.
  *Evidence: app/services/analytics/statistics/resampling.py line 24 (`statistics_resampling_boundary`)*
- [X] **ANL-NFR-338** (Functional / behavioural) Statistical validation tools must expose deterministic options such as seeds, bootstrap/permutation counts, block sizes, confidence levels, alpha levels, and sample-size thresholds where supported.
  *Evidence: app/services/analytics/statistics/resampling.py line 24 (`statistics_resampling_boundary`)*
- [X] **ANL-NFR-339** (Functional / behavioural) metrics_r_multiple_distribution` shall calculate R-multiple distribution statistics.
  *Evidence: app/services/analytics/metrics/exports.py line 194 (`metrics_r_multiple_distribution`)*
- [X] **ANL-NFR-340** (Functional / behavioural) permutation_test` shall run significance testing through random reshuffling or sign-flipping.
  *Evidence: app/services/analytics/statistics/resampling.py line 114 (`permutation_test`)*
- [X] **ANL-NFR-341** (Functional / behavioural) bootstrap_confidence_intervals` shall estimate metric uncertainty with non-parametric bootstrap.
  *Evidence: app/services/analytics/statistics/resampling.py line 80 (`bootstrap_confidence_intervals`)*
- [X] **ANL-NFR-342** (Functional / behavioural) bootstrap_probability_above_threshold` shall estimate probability that a bootstrapped metric exceeds a threshold.
  *Evidence: app/services/analytics/statistics/resampling.py line 185 (`bootstrap_probability_above_threshold`)*
- [X] **ANL-NFR-343** (Functional / behavioural) permutation_test_backtest` shall run permutation testing against a backtest result object.
  *Evidence: app/services/analytics/statistics/resampling.py line 154 (`permutation_test_backtest`)*
- [X] **ANL-NFR-344** (Functional / behavioural) bootstrap_confidence_intervals_backtest` shall estimate bootstrap confidence intervals from a backtest result object.
  *Evidence: app/services/analytics/statistics/resampling.py line 170 (`bootstrap_confidence_intervals_backtest`)*
- [X] **ANL-NFR-345** (Functional / behavioural) Benchmark analytics must align strategy and benchmark return streams before comparison and must handle missing or non-overlapping periods safely.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-346** (Functional / behavioural) Benchmark metrics must only be calculated after deterministic alignment of strategy and benchmark series.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-347** (Functional / behavioural) Strategy and benchmark timestamps must be normalized to UTC before alignment.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-348** (Functional / behavioural) Benchmark data must be restricted to the strategy analytics window unless explicit lookback is configured and recorded.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-349** (Functional / behavioural) Missing benchmark currency metadata must emit a warning and restrict calculations to currency-neutral metrics unless a validated currency policy exists.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-350** (Functional / behavioural) Portfolio analytics must not sum raw PnL across different profit currencies.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-351** (Functional / behavioural) Portfolio, TCA, and base-currency analytics must require validated FX conversion data when source money values are in different currencies.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-352** (Functional / behavioural) Missing required FX conversion data must produce blocker-level quality evidence for affected multi-currency portfolio or TCA sections.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-353** (Functional / behavioural) Stale FX rates must be identified when FX age limits are configured, and affected converted values must be marked as estimated when stale data is used.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-354** (Functional / behavioural) All money fields must include explicit currency or inherit a validated account base currency with lineage explaining the inheritance.
  *Evidence: app/services/analytics/benchmarks/alignment.py line 66 (`bench_alignment_boundary`)*
- [X] **ANL-NFR-355** (Functional / behavioural) beta` shall calculate the strategy beta coefficient relative to benchmark returns.
  *Evidence: app/services/analytics/benchmarks/metrics.py line 36 (`beta`)*
- [X] **ANL-NFR-356** (Functional / behavioural) alpha` shall calculate annualized Jensen-style alpha relative to benchmark returns.
  *Evidence: app/services/analytics/benchmarks/metrics.py line 62 (`alpha`)*
- [X] **ANL-NFR-357** (Functional / behavioural) r_squared` shall calculate coefficient of determination between strategy and benchmark returns.
  *Evidence: app/services/analytics/benchmarks/metrics.py line 94 (`r_squared`)*
- [X] **ANL-NFR-358** (Functional / behavioural) tracking_error` shall calculate annualized tracking error between strategy and benchmark returns.
  *Evidence: app/services/analytics/benchmarks/metrics.py line 122 (`tracking_error`)*
- [X] **ANL-NFR-359** (Functional / behavioural) information_ratio` shall calculate relative Sharpe-style information ratio.
  *Evidence: app/services/analytics/benchmarks/metrics.py line 144 (`information_ratio`)*
- [X] **ANL-NFR-360** (Functional / behavioural) batting_average` shall calculate the percentage of periods where the strategy outperformed the benchmark.
  *Evidence: app/services/analytics/benchmarks/metrics.py line 169 (`batting_average`)*
- [X] **ANL-NFR-361** (Functional / behavioural) calculate_benchmark_metrics` shall calculate combined benchmark-relative metrics such as alpha and beta.
  *Evidence: app/services/analytics/benchmarks/metrics.py line 232 (`calculate_benchmark_metrics`)*
- [X] **ANL-NFR-362** (Functional / behavioural) The module must not overstate strategy quality, robustness, or live readiness; report outputs should expose caveats where sample size, overfitting, missing benchmark, or partial data weaken confidence.
  *Evidence: app/services/analytics/boundaries/limits.py line 56 (`enforce_limits`)*
- [X] **ANL-NFR-363** (Functional / behavioural) All timestamps must be timezone-aware or explicitly normalized to UTC before metric calculation, benchmark alignment, report hashing, or dashboard payload generation.
  *Evidence: app/services/analytics/boundaries/limits.py line 56 (`enforce_limits`)*
- [X] **ANL-NFR-364** (Non-functional / governance) ADR Required: `ADR-ANALYTICS-LIMITS` must record exact maximum input sizes, response payload limits, runtime budgets, memory budgets, statistical iteration limits, dashboard point limits, reference hardware, and benchmark method before Builder handoff.
  *Evidence: app/services/analytics/boundaries/limits.py line 56 (`enforce_limits`)*
- [X] **ANL-NFR-365** (Non-functional / governance) Performance benchmark tests must fail the handoff gate until `ADR-ANALYTICS-LIMITS` supplies exact dataset sizes, hardware profile, benchmark method, runtime thresholds, memory thresholds, and statistical-validation iteration limits.
  *Evidence: app/services/analytics/boundaries/limits.py line 56 (`enforce_limits`)*
- [X] **ANL-NFR-366** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/boundaries/limits.py line 56 (`enforce_limits`)*
- [X] **ANL-NFR-367** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/boundaries/limits.py line 56 (`enforce_limits`)*
- [X] **ANL-NFR-368** (Functional / behavioural) capital_efficiency` shall calculate return per unit of nominal capital deployed.
  *Evidence: app/services/analytics/metrics/efficiency.py line 410 (`capital_efficiency`)*
- [X] **ANL-NFR-369** (Functional / behavioural) return_per_unit_mae` shall calculate total return relative to adverse excursion experienced.
  *Evidence: app/services/analytics/metrics/efficiency.py line 435 (`return_per_unit_mae`)*
- [X] **ANL-NFR-370** (Functional / behavioural) return_per_calendar_day` shall calculate net profit per calendar day in the test period.
  *Evidence: app/services/analytics/metrics/efficiency.py line 458 (`return_per_calendar_day`)*
- [X] **ANL-NFR-371** (Functional / behavioural) exit_efficiency` shall calculate combined win-capture and loss-containment efficiency.
  *Evidence: app/services/analytics/metrics/efficiency.py line 483 (`exit_efficiency`)*
- [X] **ANL-NFR-372** (Functional / behavioural) loss_containment_efficiency` shall calculate how well realized losses stayed above their adverse excursion.
  *Evidence: app/services/analytics/metrics/efficiency.py line 503 (`loss_containment_efficiency`)*
- [X] **ANL-NFR-373** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/metrics/efficiency.py line 26 (`metrics_efficiency_boundary`)*
- [X] **ANL-NFR-374** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/metrics/efficiency.py line 26 (`metrics_efficiency_boundary`)*
- [X] **ANL-NFR-375** (Functional / behavioural) median_mae_mfe` shall calculate median MAE and MFE values.
  *Evidence: app/services/analytics/metrics/efficiency.py line 520 (`median_mae_mfe`)*
- [X] **ANL-NFR-376** (Functional / behavioural) get_mae_mfe_r` shall calculate MAE and MFE normalized to R-space.
  *Evidence: app/services/analytics/metrics/efficiency.py line 540 (`get_mae_mfe_r`)*
- [X] **ANL-NFR-377** (Functional / behavioural) median_mae_r` shall calculate median MAE in R-multiple terms.
  *Evidence: app/services/analytics/metrics/efficiency.py line 563 (`median_mae_r`)*
- [X] **ANL-NFR-378** (Functional / behavioural) median_mfe_r` shall calculate median MFE in R-multiple terms.
  *Evidence: app/services/analytics/metrics/efficiency.py line 584 (`median_mfe_r`)*
- [X] **ANL-NFR-379** (Functional / behavioural) No metric may be referenced in an official tool schema, report schema, dashboard payload, scorecard rule, warning rule, or quality-flag rule until its Metric Definition Catalog entry is approved.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-380** (Functional / behavioural) Metric definitions must document whether outputs are calculated facts, diagnostic estimates, warning evidence, scorecard inputs, or non-binding review context.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-381** (Functional / behavioural) evaluate_strategy_quality` shall evaluate a supplied analytics report and return strategy-quality decision context, score, strengths, warnings, and recommended action.
  *Evidence: app/services/analytics/scorecards/quality.py line 257 (`evaluate_strategy_quality`)*
- [X] **ANL-NFR-382** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-383** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-384** (Functional / behavioural) Public registry changes must remain auditable through tests and catalog updates.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-385** (Functional / behavioural) The module must separate calculated facts from warnings, caveats, decisions, and recommended actions.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-386** (Functional / behavioural) Official agent/API-facing analytics tools must be high-level, documented, typed, schema-compliant, traceable, and listed in the Official Analytics Tool Catalog.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-387** (Functional / behavioural) Every official analytics tool must have a documented input schema and output schema, including required fields, optional fields, default values, accepted aliases, units, validation errors, warning codes, and JSON-safe serialization behavior.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-388** (Functional / behavioural) Low-level metric kernels must not be exposed as official agent/API tools unless explicitly approved in the Official Analytics Tool Catalog.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-389** (Functional / behavioural) Official analytics tools must log call start, validation failure, successful completion, controlled warning, and execution failure without logging secrets or full raw private payloads.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-390** (Functional / behavioural) Warning severity must support at least informational, warning, major, critical, and blocker-level meanings.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-391** (Functional / behavioural) Quality flags must separate raw metrics, normalized score inputs, penalty flags, hard blockers, recommendation evidence, and final governance decisions.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-392** (Functional / behavioural) Strategy-quality and prop-firm outputs must be labeled as non-binding analytics evidence or decision context only.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-393** (Functional / behavioural) sqn` shall calculate system quality number.
  *Evidence: app/services/analytics/scorecards/quality.py line 148 (`sqn`)*
- [X] **ANL-NFR-394** (Functional / behavioural) sample_size_warning` shall assess metric reliability based on sample size.
  *Evidence: app/services/analytics/scorecards/quality.py line 200 (`sample_size_warning`)*
- [X] **ANL-NFR-395** (Non-functional / governance) Documentation must include the Official Analytics Tool Catalog.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-396** (Non-functional / governance) Documentation must include the warning-code and quality-flag catalog.
  *Evidence: app/services/analytics/scorecards/labels.py line 13 (`scorecards_policy_boundary`)*
- [X] **ANL-NFR-397** (Functional / behavioural) Overview/report tools must combine lower-level analytics into grouped payloads that remain serializable for API and dashboard consumers.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-398** (Functional / behavioural) The module must generate a complete, versioned `AnalyticsReport` from a valid backtest, optimization candidate, out-of-sample, walk-forward, paper, live, or normalized trading result when required inputs are available.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-399** (Functional / behavioural) Report building must validate inputs, normalize result data, run required metric groups, run optional metric groups, collect warnings and quality flags, build dashboard payloads, validate output, compute hashes, and return a standard tool response.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-400** (Functional / behavioural) Missing optional inputs must produce warnings or skipped-section metadata rather than fabricated metric values.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-401** (Functional / behavioural) Critical metric group failures must return an error unless diagnostic partial mode is explicitly configured.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-402** (Functional / behavioural) Partial reports must include `report_status = "partial"`, affected sections, skipped/failed/degraded section metadata, warnings, quality flags, lineage, and JSON-safe values.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-403** (Functional / behavioural) Report generation must define section criticality as required, optional, diagnostic-only, disabled, skipped, failed, or degraded.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-404** (Functional / behavioural) Required-section failure must return an error unless diagnostic partial mode is explicitly enabled.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-405** (Functional / behavioural) Optional-section failure must produce skipped or failed section metadata without fabricating the missing section.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-406** (Functional / behavioural) Partial reports must be marked non-promotable and must not be consumed as final approval evidence.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-407** (Functional / behavioural) Report metadata must preserve `request_id`, optional `workflow_id`, run IDs, strategy identifiers, strategy version, schema version, analytics engine version, annualization settings, optional-section status, source context, and creation time.
  *Evidence: app/services/analytics/reports/sections.py line 160 (`request_id`)*
- [X] **ANL-NFR-408** (Functional / behavioural) Hashing rules must exclude non-deterministic fields such as generation timestamps unless explicitly documented.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-409** (Functional / behavioural) Hashes must be computed from canonical JSON serialization with deterministic key ordering, documented numeric normalization, and documented exclusion rules for non-deterministic fields.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-410** (Functional / behavioural) Analytics must propagate upstream data-quality and bias evidence into report warnings and quality flags.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-411** (Functional / behavioural) Dashboard payload builders must consume validated `AnalyticsReport` sections and must not recompute core metrics.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-412** (Functional / behavioural) format_summary_as_rows` shall format raw summary data into report/display rows.
  *Evidence: app/services/analytics/reports/formatters.py line 41 (`format_summary_as_rows`)*
- [X] **ANL-NFR-413** (Functional / behavioural) build_backtest_report` shall build a structured backtest analytics report payload.
  *Evidence: app/services/analytics/reports/formatters.py line 60 (`build_backtest_report`)*
- [X] **ANL-NFR-414** (Functional / behavioural) print_statistical_validation_report` shall package a comprehensive statistical validation report.
  *Evidence: app/services/analytics/reports/formatters.py line 84 (`print_statistical_validation_report`)*
- [X] **ANL-NFR-415** (Functional / behavioural) Report generation must be idempotent for the same input, configuration, and analytics engine version.
  *Evidence: app/services/analytics/reports/hashes.py line 40 (`compute_report_hash`)*
- [X] **ANL-NFR-416** (Functional / behavioural) Reports must include reproducibility metadata, input hashes, configuration hashes, report hashes, and lineage.
  *Evidence: app/services/analytics/reports/hashes.py line 40 (`compute_report_hash`)*
- [X] **ANL-NFR-417** (Functional / behavioural) Annualized metrics must use explicit annualization settings stored in configuration and report metadata; the module must not silently guess annualization when frequency cannot be inferred safely.
  *Evidence: app/services/analytics/reports/hashes.py line 40 (`compute_report_hash`)*
- [X] **ANL-NFR-418** (Functional / behavioural) Cache hits, misses, evictions, and concurrent duplicate requests must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes.
  *Evidence: app/services/analytics/reports/hashes.py line 40 (`compute_report_hash`)*
- [X] **ANL-NFR-419** (Functional / behavioural) Sequential and parallel execution over the same report inputs must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes.
  *Evidence: app/services/analytics/reports/hashes.py line 40 (`compute_report_hash`)*
- [X] **ANL-NFR-420** (Functional / behavioural) Warning and quality-flag ordering must be deterministic where output hashes, dashboard payloads, report comparison, or tests depend on order.
  *Evidence: app/services/analytics/reports/hashes.py line 40 (`compute_report_hash`)*
- [X] **ANL-NFR-421** (Functional / behavioural) Architectural Mandate: canonical monetary sums, cost aggregation, and base-currency aggregation must use `Decimal` normalization for hashing and report contracts.
  *Evidence: app/services/analytics/reports/hashes.py line 40 (`compute_report_hash`)*
- [X] **ANL-NFR-422** (Functional / behavioural) Report metadata must identify the monetary precision mode used, such as `decimal` or `float64_with_tolerance`.
  *Evidence: app/services/analytics/reports/hashes.py line 40 (`compute_report_hash`)*
- [X] **ANL-NFR-423** (Non-functional / governance) The module must define concrete runtime limits for bootstrap, permutation, Monte Carlo, distribution fitting, dashboard downsampling, and report generation before production handoff.
  *Evidence: app/services/analytics/reports/hashes.py line 40 (`compute_report_hash`)*
- [X] **ANL-NFR-424** (Functional / behavioural) build_analytics_report` latency, statistical-validation runtime, throughput, memory, and payload-size targets must be measurable before Builder handoff.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-NFR-425** (Non-functional / governance) Documentation must include report section criticality and partial-report behavior.
  *Evidence: docs/analytics/catalogs.md line 3 (`render_catalog_markdown`)*
- [X] **ANL-NFR-426** (Non-functional / governance) Documentation must include schema compatibility policy for accepted, deprecated, legacy-adapted, and unsupported report/result versions.
  *Evidence: docs/analytics/catalogs.md line 3 (`render_catalog_markdown`)*
- [X] **ANL-NFR-427** (Non-functional / governance) Documentation must include partial-report examples showing skipped, failed, and degraded section metadata.
  *Evidence: docs/analytics/catalogs.md line 3 (`render_catalog_markdown`)*
- [X] **ANL-NFR-428** (Functional / behavioural) TradingResult`, `AnalyticsReport`, `PortfolioAnalyticsReport`, dashboard payloads, warning objects, quality flags, and error envelopes have versioned schemas.
  *Evidence: app/services/analytics/contracts/models.py line 392 (`validate_schema_version`)*
- [X] **ANL-NFR-429** (Functional / behavioural) Report section criticality and partial-report non-promotable behavior are approved.
  *Evidence: app/services/analytics/reports/sections.py line 67 (`evaluate_section`)*
- [X] **ANL-NFR-430** (Non-functional / governance) Requirement-to-test traceability matrix maps every official tool, report contract, adapter mapping, warning/quality flag, and failure envelope to tests.
  *Evidence: tests/services/analytics/test_requirement_traceability.py line 30 (`validate_requirement_matrix`)*
- [X] **ANL-NFR-431** (Non-functional / governance) Usage examples cover success, validation failure, partial report, dashboard truncation, and request-ID traceability.
  *Evidence: docs/analytics/catalogs.md line 3 (`render_catalog_markdown`)*
- [X] **ANL-NFR-432** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/contracts/serialization.py line 29 (`to_json_safe`)*
- [X] **ANL-NFR-433** (Functional / behavioural) Final analytics responses must not contain `NaN`, `inf`, `-inf`, invalid JSON values, pandas objects, NumPy objects, raw dataframes, raw series, or other unserializable values.
  *Evidence: app/services/analytics/contracts/serialization.py line 29 (`to_json_safe`)*
- [X] **ANL-NFR-434** (Functional / behavioural) Dashboard payloads must include chart/table data, finite numeric values, ISO-8601 timestamps, units, warnings, and metadata sufficient for UI/API consumers.
  *Evidence: app/services/analytics/dashboards/overview.py line 97 (`build_overview_payload`)*
- [X] **ANL-NFR-435** (Functional / behavioural) If a required source section is missing, failed, skipped, or degraded, the dashboard payload must include section-status metadata and warnings rather than recomputing or fabricating chart/table values.
  *Evidence: app/services/analytics/dashboards/overview.py line 97 (`build_overview_payload`)*
- [X] **ANL-NFR-436** (Functional / behavioural) Dashboard/UI consumers must not need to recalculate core metrics.
  *Evidence: app/services/analytics/dashboards/overview.py line 97 (`build_overview_payload`)*
- [X] **ANL-NFR-437** (Functional / behavioural) Dashboard payload support must be classified by chart/table type as required, optional, or future before Builder implementation.
  *Evidence: app/services/analytics/dashboards/overview.py line 97 (`build_overview_payload`)*
- [X] **ANL-NFR-438** (Functional / behavioural) Truncated payload metadata must include whether truncation occurred, original point count, returned point count, truncation method or algorithm, and truncation reason.
  *Evidence: app/services/analytics/dashboards/truncation.py line 63 (`truncate_series`)*
- [X] **ANL-NFR-439** (Functional / behavioural) build_overview_payload` shall build the API/dashboard analytics overview payload.
  *Evidence: app/services/analytics/dashboards/overview.py line 97 (`build_overview_payload`)*
- [X] **ANL-NFR-440** (Functional / behavioural) Result payloads must be JSON-safe or convertible to JSON-safe structures for API and dashboard consumers.
  *Evidence: app/services/analytics/dashboards/overview.py line 97 (`build_overview_payload`)*
- [X] **ANL-NFR-441** (Functional / behavioural) Dashboard payloads must obey configured size limits and deterministic truncation policies when limits are defined.
  *Evidence: app/services/analytics/dashboards/truncation.py line 63 (`truncate_series`)*
- [X] **ANL-NFR-442** (Functional / behavioural) The module must define concrete maximum response payload size and deterministic truncation behavior for dashboard and API payloads before production handoff.
  *Evidence: app/services/analytics/dashboards/truncation.py line 63 (`truncate_series`)*
- [X] **ANL-NFR-443** (Non-functional / governance) Documentation must include required, optional, and future dashboard payload classes.
  *Evidence: app/services/analytics/dashboards/truncation.py line 63 (`truncate_series`)*
- [X] **ANL-NFR-444** (Non-functional / governance) Documentation must include dashboard truncation examples showing truncation metadata.
  *Evidence: app/services/analytics/dashboards/truncation.py line 63 (`truncate_series`)*
- [X] **ANL-NFR-445** (Non-functional / governance) Concrete input-size, runtime, memory, response-size, dashboard truncation, statistical iteration, and performance targets are approved with a hardware/profile context.
  *Evidence: app/services/analytics/dashboards/truncation.py line 63 (`truncate_series`)*
- [X] **ANL-NFR-446** (Scope declaration) No file-specific non-functional requirements defined.
  *Evidence: app/services/analytics/dashboards/overview.py line 97 (`build_overview_payload`)*
- [X] **ANL-NFR-447** (Scope declaration) No file-specific testing requirements defined.
  *Evidence: app/services/analytics/dashboards/overview.py line 97 (`build_overview_payload`)*
- [X] **ANL-NFR-448** (Functional / behavioural) Adopt Phase 1.5 contracts for TradeResult, ExecutionReport, Fill, PortfolioSnapshot, BacktestResult, RiskDecision, and AuditEvent analytics inputs.
  *Evidence: app/services/analytics/adapters/journal_adapters.py line 93 (`from_simulation_journal`)*
- [X] **ANL-NFR-449** (Functional / behavioural) Define analytics adapters that consume simulation journals and live trade journals through the same canonical event/result model.
  *Evidence: app/services/analytics/adapters/journal_adapters.py line 93 (`from_simulation_journal`)*
- [X] **ANL-NFR-450** (Functional / behavioural) Prohibit Analytics from reading raw broker SDK payloads, UI DTOs, or conversation memory as primary metric sources.
  *Evidence: app/services/analytics/adapters/journal_adapters.py line 93 (`from_simulation_journal`)*
- [X] **ANL-NFR-451** (Functional / behavioural) Define metric provenance using run ID, strategy ID, dataset hash, cost model, fill model, risk policy version, and journal reference.
  *Evidence: app/services/analytics/adapters/journal_adapters.py line 93 (`from_simulation_journal`)*
- [X] **ANL-NFR-452** (Functional / behavioural) Ensure Analytics can run before UI/API exists and can be consumed by UI/API later without changing metric definitions.
  *Evidence: app/services/analytics/tool_api.py line 135 (`build_analytics_report`)*
- [X] **ANL-BR-001** (Non-functional / governance) Analytics output must not include secrets, credentials, broker tokens, authorization headers, or private raw provider payloads.
  *Evidence: app/services/analytics/boundaries/redaction.py line 21 (`redact`)*
- [X] **ANL-BR-002** (Non-functional / governance) Analytics outputs used by UI/API must remain backward-compatible or be versioned when payload structure changes.
  *Evidence: app/services/analytics/contracts/models.py line 392 (`validate_schema_version`)*
