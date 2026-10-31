import { useState } from "react";
import {
  DEFAULT_HSL_STRATEGY_DOCUMENT,
  negateHSLCondition,
  type BlockGroupDefinition,
  type CustomBlockDefinition,
  type HSLConditionNode,
  type ResourceCheckResult,
  type WizardBacktestResult,
} from "./algoWizardModel";

export interface VisualBlockPanelProps {
  condition?: HSLConditionNode;
  distributeLogical?: boolean;
  customBlocks?: readonly CustomBlockDefinition[];
  blockGroups?: readonly BlockGroupDefinition[];
  resourceCheck?: ResourceCheckResult;
  backtestResult?: WizardBacktestResult;
  onNegateCondition?: (negated: HSLConditionNode) => void;
  onSaveCustomBlocks?: (blocks: readonly CustomBlockDefinition[]) => void;
  onSaveBlockGroups?: (groups: readonly BlockGroupDefinition[]) => void;
  onRunBacktest?: () => void;
  onStopBacktest?: (runId: string) => void;
}

const DEFAULT_CUSTOM_BLOCKS: readonly CustomBlockDefinition[] = [
  {
    block_id: "custom.rsi_oversold",
    name: "RSI Oversold Condition",
    category: "condition",
    description: "Reusable RSI(14)[1] < 30 entry filter",
    parameters: {
      threshold: {
        type: "float",
        default: 30,
        min: 10,
        max: 50,
        step: 1,
        optimize: false,
        description: "Oversold RSI threshold",
      },
    },
    condition: {
      type: "comparison",
      operator: "comparison.less_than",
      left: {
        type: "indicator",
        indicator_id: "indicator.rsi",
        params: { period: { type: "value", value: 14 } },
      },
      right: { type: "parameter", name: "threshold" },
    },
  },
];

const DEFAULT_BLOCK_GROUPS: readonly BlockGroupDefinition[] = [
  {
    group_id: "group.momentum_entries",
    name: "Momentum Entries",
    description: "Standard momentum and crossover entry blocks",
    block_ids: ["indicator.rsi", "indicator.ema", "comparison.crosses_above"],
  },
];

const DEFAULT_RESOURCE_CHECK: ResourceCheckResult = {
  ready: true,
  missing_symbols: [],
  missing_timeframes: [],
  missing_blocks: [],
};

const DEFAULT_BACKTEST_RESULT: WizardBacktestResult = {
  run_id: "wz-bt-001",
  strategy_id: DEFAULT_HSL_STRATEGY_DOCUMENT.strategy.id,
  status: "COMPLETED",
  bars_processed: 120,
  orders_submitted: 4,
  ending_position: 0,
  net_pnl: 245.5,
  ending_equity: 10245.5,
  trade_log: [
    {
      bar_index: 12,
      timestamp: "2026-01-01T12:00:00Z",
      action: "enter_market",
      side: "long",
      price: 1.085,
      quantity: 1.0,
    },
  ],
};

export function VisualBlockPanel({
  condition = DEFAULT_HSL_STRATEGY_DOCUMENT.strategy.rules[0].when,
  distributeLogical = false,
  customBlocks = DEFAULT_CUSTOM_BLOCKS,
  blockGroups = DEFAULT_BLOCK_GROUPS,
  resourceCheck = DEFAULT_RESOURCE_CHECK,
  backtestResult = DEFAULT_BACKTEST_RESULT,
  onNegateCondition,
  onSaveCustomBlocks,
  onSaveBlockGroups,
  onRunBacktest,
  onStopBacktest,
}: VisualBlockPanelProps) {
  const [activeCondition, setActiveCondition] =
    useState<HSLConditionNode>(condition);

  function handleNegate() {
    const next = negateHSLCondition(activeCondition, distributeLogical);
    setActiveCondition(next);
    onNegateCondition?.(next);
  }

  return (
    <section
      className="visual-block-panel"
      aria-label="Visual Block AST Manipulation and Backtest Preview"
    >
      <header className="visual-block-header">
        <h3>Visual AST Condition &amp; Block Manager</h3>
      </header>

      <div className="visual-condition-negation">
        <h4>Interactive Condition Negation</h4>
        <p>
          Current Condition Type: <code>{activeCondition.type}</code> |
          Operator:{" "}
          <code>
            {activeCondition.operator ??
              activeCondition.condition?.operator ??
              "not"}
          </code>
        </p>
        <button type="button" onClick={handleNegate}>
          Negate Condition
        </button>
      </div>

      <div className="visual-custom-blocks">
        <h4>Custom Blocks ({customBlocks.length})</h4>
        <ul>
          {customBlocks.map((cb) => (
            <li key={cb.block_id} data-custom-block-id={cb.block_id}>
              <strong>{cb.name}</strong> <code>({cb.block_id})</code> [
              {cb.category}] — {cb.description}
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={() => onSaveCustomBlocks?.(customBlocks)}
        >
          Save Custom Blocks
        </button>
      </div>

      <div className="visual-block-groups">
        <h4>Block Palette Groups ({blockGroups.length})</h4>
        <ul>
          {blockGroups.map((group) => (
            <li key={group.group_id} data-block-group-id={group.group_id}>
              <strong>{group.name}</strong> <code>({group.group_id})</code>:{" "}
              {group.block_ids.join(", ")}
            </li>
          ))}
        </ul>
        <button
          type="button"
          onClick={() => onSaveBlockGroups?.(blockGroups)}
        >
          Save Block Groups
        </button>
      </div>

      <div
        className="visual-resource-check"
        data-ready={resourceCheck.ready ? "true" : "false"}
      >
        <h4>
          Resource Check Diagnostics:{" "}
          {resourceCheck.ready ? "READY" : "MISSING DEPENDENCIES"}
        </h4>
        {!resourceCheck.ready && (
          <ul>
            {resourceCheck.missing_symbols.length > 0 && (
              <li>
                Missing Symbols: {resourceCheck.missing_symbols.join(", ")}
              </li>
            )}
            {resourceCheck.missing_timeframes.length > 0 && (
              <li>
                Missing Timeframes:{" "}
                {resourceCheck.missing_timeframes.join(", ")}
              </li>
            )}
            {resourceCheck.missing_blocks.length > 0 && (
              <li>
                Missing Blocks: {resourceCheck.missing_blocks.join(", ")}
              </li>
            )}
          </ul>
        )}
      </div>

      <div className="visual-backtest-preview">
        <h4>Wizard Backtest Preview ({backtestResult.run_id})</h4>
        <div>
          <span>Status: {backtestResult.status}</span> |{" "}
          <span>Bars: {backtestResult.bars_processed}</span> |{" "}
          <span>Orders: {backtestResult.orders_submitted}</span> |{" "}
          <span>Net PnL: {backtestResult.net_pnl.toFixed(2)}</span> |{" "}
          <span>Ending Equity: {backtestResult.ending_equity.toFixed(2)}</span>
        </div>
        <div className="visual-backtest-actions">
          <button type="button" onClick={() => onRunBacktest?.()}>
            Run Wizard Backtest
          </button>
          <button
            type="button"
            onClick={() => onStopBacktest?.(backtestResult.run_id)}
          >
            Stop Backtest
          </button>
        </div>
        {backtestResult.trade_log.length > 0 && (
          <ul className="visual-backtest-trades">
            {backtestResult.trade_log.map((trade, index) => (
              <li key={`${trade.bar_index}-${index}`}>
                Bar #{trade.bar_index} ({trade.timestamp}):{" "}
                <code>{trade.action}</code> {trade.side} {trade.quantity} @{" "}
                {trade.price}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
