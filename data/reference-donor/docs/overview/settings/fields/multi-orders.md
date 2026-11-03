# Multiple orders (same direction) — field reference (for UI tests)

> Not a Builder generator setting and not a settings-tab UI control anywhere in `internal/plugins` —
> confirmed by source search. It is a manual technique performed inside the AlgoWizard strategy editor.

Places searched for a UI (none found):
- `internal/plugins/**` — grep (case-insensitive) for `pyramid`, `multiple entries`, `multiEntry`,
  `sameDirectionOrders`, `multiOrder`, `"same direction"`, `"multiple orders"`, `numOrders`,
  `ordersCount`, `orderCount` across every plugin `.js`/`.html`: **zero matches**.
- `internal/langs/English.csv` — the only hit for "multiple orders to the same direction" is a runtime
  **warning string** shown for the TradeStation/MultiCharts platform ("Note - Tradestation/MultiCharts
  doesn't allow independent handling of multiple orders to the same direction, exits of these orders
  will be not applied correctly!"), not a setting label.
- `internal/plugins/SettingsWhatToBuild/**`, `internal/plugins/SettingsOptions/**` (Trading options),
  `internal/plugins/SettingsMoneyManagement/**` — no order-count / pyramiding control in any of these.

Backend confirmation this is generation-side, not UI-side:
- `projects/libs/SQAppLib/src/com/strategyquant/tradinglib/simulator/impl/TradestationSimulator.java`
  (~line 880) — runtime logic skipping same-direction market orders when not using ATM; this is
  generator/simulator behavior, not a config surface.
- Existing prose page `../multi-orders.md` — states explicitly: *"Applies to: manual strategy building
  / editing the default strategy template in AlgoWizard (not a generator setting)"* and that the
  Builder **keeps strategies to a single order per direction** by design.

## What actually "configures" this

There is no field to record. Per the prose page, a user achieves multiple same-direction orders by
manually adding several `EnterAtMarket` / `EnterAtStop` / `EnterAtLimit` action blocks in the AlgoWizard
editor for the same strategy — each such action block carries its own **MagicNumber** parameter (a
standard block parameter, defined via the block's Java `@Parameter` annotations, not a Building-blocks
setting), which is what lets MetaTrader tell the resulting orders' exits apart. TradeStation/MultiCharts
has no equivalent mechanism, hence the warning string above.

| What a UI test could exercise | Where | Notes |
|---|---|---|
| Presence of the TradeStation/MultiCharts warning | Wherever that platform + multi-order strategy combination surfaces (source export / strategy save flow) | Warning text is a static, non-configurable string (`English.csv`); not a form field. |
| Adding a second `EnterAtXXX` action with a distinct MagicNumber | AlgoWizard editor, per-rule "Actions" list | AlgoWizard is a compiled Vue SPA (see [custom-blocks.md](custom-blocks.md) for the same limitation) — no ng-model source available in this repo to cite exact selectors. |

## Related

- Prose page: [../multi-orders.md](../multi-orders.md)
- Fields hub: [README.md](README.md)
- Exit-side counterpart (multiple exits **is** configurable): [multiple-exits.md](multiple-exits.md)
- The AlgoWizard editor: [../../algowizard.md](../../algowizard.md)
