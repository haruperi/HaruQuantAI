# Dashboard & User Plugins — Results tab

> Two extensibility surfaces: the live Dashboard panels that stream the top-N strategies during a run, and user-authored iframe Results plugins that add custom tabs to the Results view.

## What it shows

This page covers two related pieces of the Results layer that both go beyond the built-in tabs:

- **Dashboard (live top-N)** — during a project run, the Dashboard shows mini-panels for the best strategies found so far. Each panel carries a small equity chart plus an overview snippet, updated live as better strategies are discovered.
- **User Results plugins** — user-authored HTML/JS "tabs" that appear in the Results view alongside the built-in ones. Each plugin is a single-page app loaded in an iframe, free to render the selected strategy's data however the author wants.

## How it works

**Dashboard.** The Dashboard Results plugin (`Plugins/Dashboard/impl/Results/`) subscribes to the WebSocket `best-results-channel` (`BestResultsChannel`). As a run progresses, the channel pushes messages of the form `{ranking, strategy, chart, overview}`; the panel renders the mini equity chart and overview HTML. Clicking a panel fires the same `showResults` action a databank double-click does, opening the full Results view for that strategy.

**User plugins.** The `ResultsPluginsServlet` scans `user/extend/ResultsPlugins/<Name>/index.html` and registers each discovered plugin as a tab (subject to a per-edition license limit on how many plugins are allowed). The tab is a `pluginIframe.html` wrapper that loads the plugin's `index.html` from `/plugins/ResultsPlugins/<Name>/` and bridges it via `postMessage`:

- **In (SQX → plugin):** `STRATEGY_DATA` (project/databank/strategy/resultKey/backtestID when a strategy is selected or the tab activated), `SET_THEME` (`dark|light`), `SET_LANGUAGE`.
- **Out (plugin → SQX):** `GET_STATS`, `GET_ORDERS`, `GET_LAST_SETTINGS_XML`, `GET_SOURCE_CODE`, `GET_SYMBOL_INFO` — served by the plugin's data API (`stats` → SQStats JSON, `orders` → trades, `settings` → XML).

This is the "new tab without Java" extension point: the plugin gets the same underlying `ResultsGroup` data the built-in tabs use, but renders it in its own iframe.

## Options & settings

- **Dashboard panels** — number of top-N panels and their live updates are driven by the run; clicking a panel opens the full result.
- **Add a plugin** — drop a `<Name>/index.html` (optionally a local Vue bundle and `locales/*.json`) into `user/extend/ResultsPlugins/`; it is discovered via `/resultsPlugins/list`. The servlet also supports `create/rename/delete`.
- **Theme & language** — plugins receive `SET_THEME` and `SET_LANGUAGE` so they can match the app.
- A full authoring guide exists at `work_directory/StrategyQuant/user/extend/ResultsPlugins/CLAUDE.md`.

## Related

- Endpoints: `/dashboardResults/` (via `BestResultsChannel`) and `/resultsPlugins/` (`list/create/rename/delete` + `stats/orders/settings`)
- Results & Databank overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [Walk-Forward](walk-forward.md) · [Robustness Tests](robustness-tests.md) · [Optimization Profile](optimization-profile.md)
- Developer/architecture detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
