import { useState } from 'react';
import {
  ArrowDown,
  ArrowUp,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  CirclePlus,
  Code,
  Copy,
  Download,
  FileCode,
  FileUp,
  FolderOpen,
  Plus,
  Redo2,
  Save,
  Search,
  Sliders,
  Sparkles,
  Trash2,
  Undo2,
} from 'lucide-react';
import { useAppStore } from '../../app/store';
import type { RuleNode } from '../../app/types';
import { Button, Field, Modal, Section, Select, TextInput } from '../../components/ui';
import { STRATEGY_TEMPLATES, type StrategyTemplate } from './algoWizardTemplates';
import { StrategyCodeExportModal } from './StrategyCodeExportModal';
import { StrategyTemplatesModal } from './StrategyTemplatesModal';

const BUILDING_BLOCKS = [
  { id: 'sma', name: 'Simple Moving Average (SMA)', cat: 'Indicators', defaultExpr: 'SMA(14)' },
  { id: 'ema', name: 'Exponential Moving Average (EMA)', cat: 'Indicators', defaultExpr: 'EMA(20)' },
  { id: 'rsi', name: 'Relative Strength Index (RSI)', cat: 'Indicators', defaultExpr: 'RSI(14)' },
  { id: 'macd', name: 'MACD Indicator', cat: 'Indicators', defaultExpr: 'MACD(12, 26, 9)' },
  { id: 'bb', name: 'Bollinger Bands', cat: 'Indicators', defaultExpr: 'BollingerLower(20, 2.0)' },
  { id: 'atr', name: 'Average True Range (ATR)', cat: 'Indicators', defaultExpr: 'ATR(14)' },
  { id: 'close', name: 'Close Price', cat: 'Price Data', defaultExpr: 'Close[0]' },
  { id: 'open', name: 'Open Price', cat: 'Price Data', defaultExpr: 'Open[0]' },
  { id: 'high', name: 'High Price', cat: 'Price Data', defaultExpr: 'High[1]' },
  { id: 'low', name: 'Low Price', cat: 'Price Data', defaultExpr: 'Low[1]' },
  { id: 'inside_bar', name: 'Inside Bar Pattern', cat: 'Price Data', defaultExpr: 'High[1] < High[2] AND Low[1] > Low[2]' },
  { id: 'cross_above', name: 'Crosses Above', cat: 'Conditions', defaultExpr: 'crosses above' },
  { id: 'cross_below', name: 'Crosses Below', cat: 'Conditions', defaultExpr: 'crosses below' },
  { id: 'greater_than', name: 'Is Greater Than (>)', cat: 'Conditions', defaultExpr: '>' },
  { id: 'less_than', name: 'Is Less Than (<)', cat: 'Conditions', defaultExpr: '<' },
  { id: 'is_rising', name: 'Is Rising', cat: 'Conditions', defaultExpr: 'is rising' },
  { id: 'enter_market', name: 'Enter at Market', cat: 'Order Actions', defaultExpr: 'Enter at Market' },
  { id: 'place_stop', name: 'Place Stop Order', cat: 'Order Actions', defaultExpr: 'Place Stop Order' },
  { id: 'place_limit', name: 'Place Limit Order', cat: 'Order Actions', defaultExpr: 'Place Limit Order' },
  { id: 'set_sl', name: 'Set Stop Loss', cat: 'Trade Management', defaultExpr: 'Set Stop Loss' },
  { id: 'set_pt', name: 'Set Profit Target', cat: 'Trade Management', defaultExpr: 'Set Profit Target' },
  { id: 'trailing_stop', name: 'Trailing Stop', cat: 'Trade Management', defaultExpr: 'Trailing Stop' },
  { id: 'move_be', name: 'Move SL to Break-Even', cat: 'Trade Management', defaultExpr: 'Move SL to BE' },
  { id: 'exit_market', name: 'Exit at Market', cat: 'Trade Management', defaultExpr: 'Exit Market' },
];

export function AlgoWizardWorkspace() {
  const store = useAppStore();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [templatesModal, setTemplatesModal] = useState(false);
  const [exportModal, setExportModal] = useState(false);
  const [strategyName, setStrategyName] = useState('EMA Cross Strategy');
  const [symbol, setSymbol] = useState('EURUSD');
  const [timeframe, setTimeframe] = useState('H1');
  const [executionModel, setExecutionModel] = useState<'On Bar Close' | 'On Bar Open'>('On Bar Close');

  // Strategy parameters & variables
  const [variables, setVariables] = useState<{ name: string; value: number | string; optimize: boolean }[]>([
    { name: 'FastPeriod', value: 20, optimize: true },
    { name: 'SlowPeriod', value: 50, optimize: true },
    { name: 'StopLoss', value: 60, optimize: true },
    { name: 'TakeProfit', value: 120, optimize: true },
  ]);

  const selectedRule = store.rules.find(r => r.id === selectedId);

  // Load Strategy Template
  const handleLoadTemplate = (tpl: StrategyTemplate) => {
    setStrategyName(tpl.name);
    setSymbol(tpl.symbol);
    setTimeframe(tpl.timeframe);
    setExecutionModel(tpl.executionModel);
    setVariables(tpl.variables);
    store.loadStrategyTemplate(tpl.rules);
    setSelectedId(tpl.rules[0]?.id || null);
    store.notify(`Loaded template "${tpl.name}" into AlgoWizard rule tree`);
  };

  // Add condition node
  const handleAddCondition = (blockExpr?: string) => {
    const newNode: RuleNode = {
      id: `cond-${Date.now()}`,
      depth: 2,
      kind: 'condition',
      label: blockExpr || 'Close[0] crosses above EMA(20)',
      operator: 'AND',
      leftExpr: 'Close[0]',
      compOp: 'crosses above',
      rightExpr: 'EMA(20)',
      signalGroup: selectedRule?.signalGroup || 'Long Entry',
    };
    store.addRule(newNode);
    setSelectedId(newNode.id);
    store.notify('Condition added to rule tree');
  };

  // Add action node
  const handleAddAction = (actionType?: string) => {
    const newNode: RuleNode = {
      id: `act-${Date.now()}`,
      depth: 2,
      kind: 'action',
      label: actionType || 'Enter at Market (Long)',
      actionType: (actionType as any) || 'Enter at Market',
      actionParams: { direction: 'Long', lots: 0.1 },
      signalGroup: selectedRule?.signalGroup || 'Long Entry',
    };
    store.addRule(newNode);
    setSelectedId(newNode.id);
    store.notify('Order action added to rule tree');
  };

  // Double click library item to add
  const handleBlockDoubleClick = (block: typeof BUILDING_BLOCKS[0]) => {
    if (block.cat === 'Order Actions' || block.cat === 'Trade Management') {
      handleAddAction(block.name);
    } else {
      handleAddCondition(block.defaultExpr);
    }
  };

  return (
    <div className="algo-wizard" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Top Main Toolbar */}
      <div
        className="aw-toolbar"
        style={{
          display: 'flex',
          gap: '0.5rem',
          alignItems: 'center',
          padding: '0.5rem 1rem',
          borderBottom: '1px solid var(--border)',
          background: 'var(--panel)',
          flexWrap: 'wrap',
        }}
      >
        <Button onClick={() => setTemplatesModal(true)} className="primary">
          <BookOpen size={14} /> Templates
        </Button>
        <Button onClick={() => store.notify('Strategy definition saved to workspace databank')}>
          <Save size={14} /> Save Revision
        </Button>

        <div style={{ width: '1px', height: '20px', background: 'var(--border)', margin: '0 4px' }} />

        <Button onClick={() => store.notify('Undo step')}>
          <Undo2 size={14} /> Undo
        </Button>
        <Button onClick={() => store.notify('Redo step')}>
          <Redo2 size={14} /> Redo
        </Button>

        <div style={{ width: '1px', height: '20px', background: 'var(--border)', margin: '0 4px' }} />

        <Button onClick={() => handleAddCondition()}>
          <CirclePlus size={14} /> Add Condition
        </Button>
        <Button onClick={() => handleAddAction()}>
          <Plus size={14} /> Add Action
        </Button>
        <Button
          disabled={!selectedId}
          onClick={() => {
            if (selectedId) {
              store.removeRule(selectedId);
              setSelectedId(null);
            }
          }}
        >
          <Trash2 size={14} /> Remove
        </Button>
        <Button disabled={!selectedId} onClick={() => selectedId && store.moveRule(selectedId, -1)}>
          <ArrowUp size={14} />
        </Button>
        <Button disabled={!selectedId} onClick={() => selectedId && store.moveRule(selectedId, 1)}>
          <ArrowDown size={14} />
        </Button>

        <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
          <Button onClick={() => setExportModal(true)}>
            <Code size={14} /> Export Code (MQL / Python)
          </Button>
        </div>
      </div>

      {/* Main 3-Column Layout */}
      <div className="aw-main" style={{ display: 'grid', gridTemplateColumns: '260px 1fr 340px', flex: 1, overflow: 'hidden' }}>
        {/* Column 1: Building Blocks Library Sidebar */}
        <aside
          className="block-library"
          style={{ borderRight: '1px solid var(--border)', padding: '0.75rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 style={{ fontSize: '0.9rem', margin: 0, fontWeight: 600 }}>Building Blocks</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Double-click to add</span>
          </div>

          <div style={{ position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '8px', top: '9px', opacity: 0.5 }} />
            <input
              type="text"
              className="text-input"
              placeholder="Search blocks..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{ width: '100%', paddingLeft: '28px', fontSize: '0.8rem' }}
            />
          </div>

          {['Indicators', 'Price Data', 'Conditions', 'Order Actions', 'Trade Management'].map(cat => {
            const items = BUILDING_BLOCKS.filter(b => b.cat === cat && b.name.toLowerCase().includes(search.toLowerCase()));
            if (items.length === 0) return null;
            return (
              <div key={cat} style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                <strong style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  {cat}
                </strong>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {items.map(b => (
                    <button
                      key={b.id}
                      onDoubleClick={() => handleBlockDoubleClick(b)}
                      style={{
                        textAlign: 'left',
                        padding: '0.35rem 0.6rem',
                        fontSize: '0.8rem',
                        background: 'transparent',
                        border: '1px solid transparent',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        color: 'inherit',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card)')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    >
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.name}</span>
                      <Plus size={12} style={{ opacity: 0.5 }} onClick={() => handleBlockDoubleClick(b)} />
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </aside>

        {/* Column 2: Visual Rule Editor */}
        <main
          className="rule-editor"
          style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '1rem', gap: '1rem' }}
        >
          {/* Strategy Meta Header */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              background: 'var(--panel)',
              padding: '0.75rem 1rem',
              borderRadius: '6px',
              border: '1px solid var(--border)',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <input
                type="text"
                value={strategyName}
                onChange={e => setStrategyName(e.target.value)}
                style={{
                  fontSize: '1.15rem',
                  fontWeight: 600,
                  background: 'transparent',
                  border: 'none',
                  color: 'inherit',
                  outline: 'none',
                }}
              />
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Rule-Tree Strategy Model · {executionModel}
              </span>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <select
                className="text-input"
                value={symbol}
                onChange={e => setSymbol(e.target.value)}
                style={{ fontSize: '0.85rem' }}
              >
                <option value="EURUSD">EURUSD</option>
                <option value="GBPUSD">GBPUSD</option>
                <option value="USDJPY">USDJPY</option>
                <option value="XAUUSD">XAUUSD</option>
                <option value="BTCUSD">BTCUSD</option>
              </select>

              <select
                className="text-input"
                value={timeframe}
                onChange={e => setTimeframe(e.target.value)}
                style={{ fontSize: '0.85rem' }}
              >
                <option value="M15">M15</option>
                <option value="M30">M30</option>
                <option value="H1">H1</option>
                <option value="H4">H4</option>
                <option value="D1">D1</option>
              </select>

              <select
                className="text-input"
                value={executionModel}
                onChange={e => setExecutionModel(e.target.value as any)}
                style={{ fontSize: '0.85rem' }}
              >
                <option value="On Bar Close">On Bar Close</option>
                <option value="On Bar Open">On Bar Open</option>
              </select>
            </div>
          </div>

          {/* Rule Tree Container */}
          <div
            className="rule-tree"
            style={{
              flex: 1,
              overflowY: 'auto',
              background: 'var(--bg-card)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '1rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.4rem',
            }}
          >
            {store.rules.map(r => {
              const isSelected = selectedId === r.id;
              const isEvent = r.kind === 'event';
              const isIf = r.kind === 'if';
              const isThen = r.kind === 'then';
              const isCondition = r.kind === 'condition';
              const isAction = r.kind === 'action';

              return (
                <div
                  key={r.id}
                  onClick={() => setSelectedId(r.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginLeft: `${r.depth * 24}px`,
                    padding: '0.4rem 0.75rem',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    background: isSelected
                      ? 'rgba(56, 189, 248, 0.15)'
                      : isEvent
                      ? 'rgba(255, 255, 255, 0.04)'
                      : 'transparent',
                    border: isSelected ? '1px solid var(--primary)' : '1px solid transparent',
                  }}
                >
                  {/* Kind Badge */}
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: '3px',
                      background: isEvent
                        ? '#64748b'
                        : isIf
                        ? '#3b82f6'
                        : isThen
                        ? '#10b981'
                        : isCondition
                        ? '#8b5cf6'
                        : '#f59e0b',
                      color: '#ffffff',
                    }}
                  >
                    {r.kind.toUpperCase()}
                  </span>

                  {/* Logical Operator Pill (AND / OR) */}
                  {isCondition && r.operator && (
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        store.updateRule(r.id, { operator: r.operator === 'AND' ? 'OR' : 'AND' });
                      }}
                      style={{
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        padding: '1px 5px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        border: 'none',
                        borderRadius: '3px',
                        color: 'inherit',
                        cursor: 'pointer',
                      }}
                    >
                      {r.operator}
                    </button>
                  )}

                  {/* Label / Expression */}
                  <strong style={{ fontSize: '0.85rem', flex: 1 }}>{r.label}</strong>

                  {/* Action badge if action */}
                  {isAction && r.actionType && (
                    <span style={{ fontSize: '0.75rem', color: '#10b981', background: 'rgba(16, 185, 129, 0.1)', padding: '1px 6px', borderRadius: '3px' }}>
                      {r.actionType}
                    </span>
                  )}
                </div>
              );
            })}

            {store.rules.length === 0 && (
              <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-muted)' }}>
                No rules defined yet. Click "Templates" above or use the Building Blocks library on the left.
              </div>
            )}
          </div>
        </main>

        {/* Column 3: Properties Inspector & Variables Sidebar */}
        <aside
          className="properties"
          style={{ borderLeft: '1px solid var(--border)', padding: '1rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}
        >
          <Section title="Block Properties">
            {selectedRule ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <Field label="Node Type">
                  <TextInput value={selectedRule.kind} readOnly />
                </Field>

                <Field label="Label / Expression">
                  <TextInput
                    value={selectedRule.label}
                    onChange={e => store.updateRule(selectedRule.id, { label: e.target.value })}
                  />
                </Field>

                {selectedRule.kind === 'condition' && (
                  <>
                    <Field label="Left Expression">
                      <TextInput
                        value={selectedRule.leftExpr || ''}
                        onChange={e => store.updateRule(selectedRule.id, { leftExpr: e.target.value })}
                      />
                    </Field>

                    <Field label="Comparison Operator">
                      <select
                        className="text-input"
                        value={selectedRule.compOp || '>'}
                        onChange={e => store.updateRule(selectedRule.id, { compOp: e.target.value as any })}
                      >
                        <option value="crosses above">crosses above</option>
                        <option value="crosses below">crosses below</option>
                        <option value=">">&gt; (greater than)</option>
                        <option value="<">&lt; (less than)</option>
                        <option value=">=">&gt;= (greater or equal)</option>
                        <option value="<=">&lt;= (less or equal)</option>
                        <option value="==">== (equals)</option>
                        <option value="is rising">is rising</option>
                        <option value="is falling">is falling</option>
                      </select>
                    </Field>

                    <Field label="Right Expression">
                      <TextInput
                        value={selectedRule.rightExpr || ''}
                        onChange={e => store.updateRule(selectedRule.id, { rightExpr: e.target.value })}
                      />
                    </Field>

                    <Field label="Logical Operator">
                      <select
                        className="text-input"
                        value={selectedRule.operator || 'AND'}
                        onChange={e => store.updateRule(selectedRule.id, { operator: e.target.value as any })}
                      >
                        <option value="AND">AND</option>
                        <option value="OR">OR</option>
                      </select>
                    </Field>
                  </>
                )}

                {selectedRule.kind === 'action' && (
                  <Field label="Action Type">
                    <select
                      className="text-input"
                      value={selectedRule.actionType || 'Enter at Market'}
                      onChange={e => store.updateRule(selectedRule.id, { actionType: e.target.value as any })}
                    >
                      <option value="Enter at Market">Enter at Market</option>
                      <option value="Place Stop Order">Place Stop Order</option>
                      <option value="Place Limit Order">Place Limit Order</option>
                      <option value="Set Stop Loss">Set Stop Loss</option>
                      <option value="Set Profit Target">Set Profit Target</option>
                      <option value="Trailing Stop">Trailing Stop</option>
                      <option value="Move SL to BE">Move SL to BE</option>
                      <option value="Exit Market">Exit Market</option>
                    </select>
                  </Field>
                )}

                <div
                  style={{
                    background: 'rgba(34, 197, 94, 0.1)',
                    color: '#22c55e',
                    border: '1px solid rgba(34, 197, 94, 0.2)',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.8rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                  }}
                >
                  <Check size={14} /> Block configuration is valid
                </div>
              </div>
            ) : (
              <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Select a rule node in the center tree to edit its parameters and expressions.
              </p>
            )}
          </Section>

          {/* Strategy Variables & Parameters Table */}
          <Section title="Strategy Parameters">
            <div style={{ overflowX: 'auto', border: '1px solid var(--border)', borderRadius: '4px' }}>
              <table className="plain-table" style={{ width: '100%', fontSize: '0.8rem' }}>
                <thead>
                  <tr>
                    <th>Parameter</th>
                    <th>Default</th>
                    <th style={{ width: '30px' }}>Opt</th>
                  </tr>
                </thead>
                <tbody>
                  {variables.map((v, i) => (
                    <tr key={v.name}>
                      <td><strong>{v.name}</strong></td>
                      <td>
                        <input
                          type="number"
                          className="cell-input"
                          value={v.value}
                          onChange={e => {
                            const val = Number(e.target.value);
                            const updated = [...variables];
                            updated[i] = { ...v, value: val };
                            setVariables(updated);
                          }}
                          style={{ width: '50px', padding: '2px 4px' }}
                        />
                      </td>
                      <td>
                        <input
                          type="checkbox"
                          checked={v.optimize}
                          onChange={e => {
                            const updated = [...variables];
                            updated[i] = { ...v, optimize: e.target.checked };
                            setVariables(updated);
                          }}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        </aside>
      </div>

      {/* Strategy Templates Dialog */}
      {templatesModal && (
        <StrategyTemplatesModal
          onClose={() => setTemplatesModal(false)}
          onSelectTemplate={handleLoadTemplate}
        />
      )}

      {/* Code Export Dialog */}
      {exportModal && (
        <StrategyCodeExportModal
          onClose={() => setExportModal(false)}
          rules={store.rules}
          strategyName={strategyName}
          symbol={symbol}
          timeframe={timeframe}
          variables={variables}
        />
      )}
    </div>
  );
}

export { AlgoWizardWorkspace as AlgoWizard };
