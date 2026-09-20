# SQ Equity and Futures add-data coverage

Reference root: `C:/SQX_144_2953_win_20260601`. Approved task: FEAT-UI-SQ-DATA-ADD.
The machine-readable entries below also appear in coverage.json.

## Source trace
Providers register at priority 20, add actions at priority 10, source `data`.
LayoutCtrl exposes them for StrategyQuant. Generated build/layout.js duplicates the registration.
Both controllers load exchanges and subscription availability, then lookup ticker tuples.
Equity tuples include ticker/name/exchange/type/dataFrom/allowed; futures omit type.
Equity disables only strictly false allowed flags; futures requires a truthy flag.
The mock normalizes these responses to explicit eligible fixture records.
Services call /sqEquityData or /sqFuturesData operations getExchanges, verifySubscription,
lookup (POST), add (POST), addCancel. No provider request is made by this implementation.
Source LICENSE_CHANGED re-verification maps to reactive app profile state.
Source Add serializes selected tickers as comma-separated config.symbols, queues root progress,
registers cancellation, and hides the popup. Mock retains normalized selected definitions instead.
Source config controls exchange, search booleans/text, postfix, barType and timezone fields;
futures adds onlyContFutures. Both default to end-of-bar and exchange timezone.
The unused timeFrame controller variable has no visible control and is not reproduced.

## Inclusion/exclusion register
Included: both search/results flows, eligibility, subscriptions display, sorted selectable grids,
all source settings, nested usage conditions, persistent mock add lifecycle, collision guards.
Excluded: separate update/updateBr workflows (outside request), native ingestion and proprietary
catalogues (compiled/backend gap), remote banner image fetch (local themed promotional slot),
real purchasing/verification (no backend), generated duplicate screens and unused controller state.
No catalogue CSV was found: JAR resource metadata and installation filenames were inspected.
Fixtures expose 12 equities and 10 futures; dates, exchange lists and free eligibility are mock.
Full enables simulated EOD/M1; Starter exposes fixture free symbols. These are not actual entitlements.
New definitions have no downloaded timeframe/history. Availability metadata stays separate.

## Feature entries

### SQ-EQUITY-ADD-001

- **product**: SQX Data Manager / DataSourceSQEquityData
- **screen**: Add SQ Equity Data search and results
- **sources**: ["internal/plugins/DataSourceSQEquityData/module.js", "internal/plugins/DataSourceSQEquityData/add/module.js", "internal/plugins/DataSourceSQEquityData/add/addPopup.html", "internal/plugins/DataSourceSQEquityData/add/SQEquityDataAddCtrl.js", "internal/plugins/DataSourceSQEquityData/SQEquityDataService.js", "internal/plugins/DataSourceSQEquityData/styles.css", "internal/web/SQMANAGER/layout/LayoutCtrl.js", "internal/web/SQMANAGER/timezones.csv"]
- **trigger**: SQ Equity data > Find and add equity data
- **controls**: ["exchange", "ticker/name/exact", "multiline terms", "Lookup", "subscription availability/free list/Subscribe", "eligible checkbox grid and sorting", "Search again", "postfix", "bar type", "exchange/fixed/named timezone", "consent", "conditions", "Close", "Add"]
- **preconditions**: ["SQX menu applicability", "mock catalogue loaded", "eligible selected tickers for Add", "no active provider operation"]
- **validation**: ["consent", "selected eligible tickers", "unique valid global dataset names", "bounded strings/selection", "integer shift -23..23", "valid timezone", "successful storage"]
- **transitions**: ["search", "lookup pending", "results or empty", "select/configure", "conditions and return", "add or validation error", "close", "reload persisted work"]
- **outcome**: empty configured mock definitions added; availability dates are not downloaded coverage
- **mockOperation**: lookupSQ / sqSubscription / planSQAdd / useSQData.start
- **persistence**: sqx-sq-data-v1 definitions, preferred options and add job; selection/search/consent reset on reopen
- **status**: {"visual": "implemented", "interaction": "implemented", "state": "implemented"}
- **verification**: {"visual": "dark/light desktop and narrow layout inspected; source structure with app theme", "interaction": "SQ Playwright scenarios plus source-ribbon regression passed", "state": "SQ unit lifecycle/validation/storage tests and browser add/reload checks passed; reactive profile invalidation reviewed in code"}
- **gaps**: Backend exchange/catalogue/entitlement responses unavailable; explicit small offline fixtures. Full/Starter mapping is a simulation. Native runtime not observed. Subscription banner local, link source-derived. Separate updates excluded.

### SQ-FUTURES-ADD-001

- **product**: SQX Data Manager / DataSourceSQFuturesData
- **screen**: Add SQ Futures Data search and results
- **sources**: ["internal/plugins/DataSourceSQFuturesData/module.js", "internal/plugins/DataSourceSQFuturesData/add/module.js", "internal/plugins/DataSourceSQFuturesData/add/addPopup.html", "internal/plugins/DataSourceSQFuturesData/add/SQFuturesDataAddCtrl.js", "internal/plugins/DataSourceSQFuturesData/SQFuturesDataService.js", "internal/plugins/DataSourceSQFuturesData/styles.css", "internal/web/SQMANAGER/layout/LayoutCtrl.js", "internal/web/SQMANAGER/timezones.csv"]
- **trigger**: SQ Futures data > Find and add futures data
- **controls**: ["exchange", "ticker/name/exact", "multiline terms", "Lookup", "subscription availability/free list/Subscribe", "eligible checkbox grid and sorting", "Search again", "postfix", "bar type", "exchange/fixed/named timezone", "consent", "conditions", "Close", "Add", "continuous-only"]
- **preconditions**: ["SQX menu applicability", "mock catalogue loaded", "eligible selected tickers for Add", "no active provider operation"]
- **validation**: ["consent", "selected eligible tickers", "unique valid global dataset names", "bounded strings/selection", "integer shift -23..23", "valid timezone", "successful storage"]
- **transitions**: ["search", "lookup pending", "results or empty", "select/configure", "conditions and return", "add or validation error", "close", "reload persisted work"]
- **outcome**: empty configured mock definitions added; availability dates are not downloaded coverage
- **mockOperation**: lookupSQ / sqSubscription / planSQAdd / useSQData.start
- **persistence**: sqx-sq-data-v1 definitions, preferred options and add job; selection/search/consent reset on reopen
- **status**: {"visual": "implemented", "interaction": "implemented", "state": "implemented"}
- **verification**: {"visual": "dark/light desktop and narrow layout inspected; source structure with app theme", "interaction": "SQ Playwright scenarios plus source-ribbon regression passed", "state": "SQ unit lifecycle/validation/storage tests and browser add/reload checks passed; reactive profile invalidation reviewed in code"}
- **gaps**: Backend exchange/catalogue/entitlement responses unavailable; explicit small offline fixtures. Full/Starter mapping is a simulation. Native runtime not observed. Subscription banner local, link source-derived. Separate updates excluded.

### SQ-DATA-CONDITIONS-001

- **product**: SQX Data Manager / both SQ providers
- **screen**: StrategyQuant Data Usage Conditions
- **sources**: ["internal/plugins/DataSourceSQEquityData/add/dataUsageConditionsPopup.html", "internal/plugins/DataSourceSQFuturesData/add/dataUsageConditionsPopup.html"]
- **trigger**: Usage conditions link in either add dialog
- **controls**: ["source heading and four paragraphs", "Close", "Escape"]
- **preconditions**: ["add dialog open"]
- **validation**: ["no external acceptance or submission"]
- **transitions**: ["parent draft retained", "conditions open", "close restores parent and link focus"]
- **outcome**: source text readable in themed nested dialog
- **mockOperation**: SQDataAddDialog local conditions state
- **persistence**: none; parent draft remains transient
- **status**: {"visual": "implemented", "interaction": "implemented", "state": "implemented"}
- **verification**: {"visual": "themed modal implementation", "interaction": "browser Escape and return focus passed", "state": "parent selection/configuration retained"}
- **gaps**: Local mock consent only; no license transaction.

### SQ-DATA-JOB-001

- **product**: HaruQuantAI Data Manager mock adapter
- **screen**: Shared progress and trailing dataset status
- **sources**: ["internal/plugins/DataSourceSQEquityData/add/SQEquityDataAddCtrl.js", "internal/plugins/DataSourceSQFuturesData/add/SQFuturesDataAddCtrl.js", "internal/plugins/DataSourceSQEquityData/SQEquityDataService.js", "internal/plugins/DataSourceSQFuturesData/SQFuturesDataService.js"]
- **trigger**: Add with valid form and consent
- **controls**: ["shared Pause/Resume all", "Stop all", "trailing row status"]
- **preconditions**: ["no active job", "readable storage", "no duplicate names"]
- **validation**: ["bounded persisted schema", "storage success", "cross-provider names and operation exclusion"]
- **transitions**: ["running", "paused", "resume", "cancelled", "failed", "completed", "reload running as paused"]
- **outcome**: atomic completed definitions retained, unfinished cancelled work discarded; zero actual history records
- **mockOperation**: useSQData.start/advance/action; reservedSQDefinitions
- **persistence**: sqx-sq-data-v1; no changes to other storage schemas
- **status**: {"visual": "implemented", "interaction": "implemented", "state": "implemented"}
- **verification**: {"visual": "single shared progress / trailing status verified", "interaction": "pause/resume/stop/exclusion browser checks passed", "state": "atomic completion, reload, corruption, quota/start and mid-job failure unit checks passed"}
- **gaps**: Deterministic mock timing and incremental commits; backend implementation unavailable. Existing SQ update simulations unchanged.

## Verification limits

Native SQX runtime not observed; source-backed parity is structural/behavioral, not pixel parity.
Full Python CI remains blocked by the existing logging lock: 101 passed, 8 failed, 93.95% coverage.
