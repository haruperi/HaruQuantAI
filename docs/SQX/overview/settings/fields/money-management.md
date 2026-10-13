# Money management — field reference (for UI tests)

> Exact controls, `ng-model` bindings and defaults for the Money management settings tab, extracted from the web plugin source.

Source: `internal/plugins/SettingsMoneyManagement/` (`views/moneyManagement.html`,
`MoneyManagementCtrl.js`, `MoneyManagementService.js`, `module.js`). Tab is registered as `SettingsTab` id
`50`, `testId: 'settings-tab-mm'`, `dataItem: 'builder-settings-mm'`, `configElemName:
'RiskMoneyManagement'`, task: `Build,Optimize,Retest,AutomaticRetest`.

**The list of position-sizing METHODS (Fixed size, Risk fixed %, ATR-based, Martingale, etc.) is cataloged in
[`../../snippets/money-management.md`](../../snippets/money-management.md) — link there for the full
per-method parameter tables.** This page documents only the tab's own UI: the initial-capital field and the
method-picker + Risk-Management-picker widgets that host that catalog.

## Controls

| Label | Config key (ng-model) | Type | Default | Options / notes |
|---|---|---|---|---|
| Use custom MoneyManagement settings | `config.useCustomSettings` | checkbox, `data-testid="settings-mm-custom-switch"` | `false` | Only shown when `isAutoRetestTask` (task type `AutomaticRetest`). Persisted as `RiskMoneyManagement[customSettings]` attribute. |
| Initial capital | `config.initialCapital` | number spinner, `data-testid="settings-mm-initial-capital"` | `10000` | min 0, step 1. Persisted as the `MoneyManagement/InitialCapital` XML text node. Starting account balance/equity the backtest simulates against. |
| Choose Money Management method | `config.mmPropGridInstance` (`<multi-property-grid options="mmMethods">`) | dynamic property grid: method dropdown + that method's parameter fields, `data-testid="settings-mm-mm-grid-btn"` | first available method for the current engine | `mmMethods` = `SQConstants.getConstants().mmMethods`, i.e. every method in the linked catalog. The list shown is filtered live to the methods valid for the current chart's engine (`enableOptionsBasedOnEngine`, matches each method's `ForEngine`); if the currently selected method isn't valid for the new engine, selection resets to the first valid one. |
| Choose Risk Management method | `config.rmPropGridInstance` (`<multi-property-grid options="rmMethods">`) | dynamic property grid, `data-testid="settings-mm-risk-grid-btn"` | — | **Present in the DOM but permanently hidden** — the element carries `ng-show="false"` unconditionally, so it never renders in the current build regardless of state. `rmMethods` = `SQConstants.getConstants().rmMethods`; not documented further here since the feature isn't user-visible (no known UI test surface). |

## Related

- Money management methods catalog: [`../../snippets/money-management.md`](../../snippets/money-management.md)
- Prose page: [../money-management.md](../money-management.md)
- Fields hub: [README.md](README.md)
