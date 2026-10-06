import { useMemo, useState } from 'react';
import {
  AlertOctagon,
  ArrowDownCircle,
  ArrowUpCircle,
  CheckCircle2,
  Download,
  Flame,
  PauseCircle,
  PlayCircle,
  Radio,
  RefreshCw,
  Search,
  Send,
  ShieldAlert,
  Trash2,
  TrendingDown,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import type { OrderKind, OrderSide } from '../../host/types';
import { Button, Field, Modal, Section, Stat, TextInput } from '../../components/ui';
import { useTradingStore } from './tradingStore';

export function TradingDashboard() {
  const store = useTradingStore();

  // Active account
  const account = useMemo(
    () => store.accounts.find(a => a.id === store.selectedAccountId) ?? store.accounts[0],
    [store.accounts, store.selectedAccountId]
  );

  // Total Floating P/L
  const totalFloatingPnl = useMemo(
    () => store.positions.reduce((acc, p) => acc + p.pnl, 0),
    [store.positions]
  );

  // Order Ticket Form State
  const [symbol, setSymbol] = useState('EURUSD');
  const [side, setSide] = useState<OrderSide>('Buy');
  const [kind, setKind] = useState<OrderKind>('Market');
  const [lots, setLots] = useState(1.0);
  const [price, setPrice] = useState(1.085);
  const [stopLoss, setStopLoss] = useState(1.079);
  const [takeProfit, setTakeProfit] = useState(1.095);
  const [comment, setComment] = useState('');
  const [feedback, setFeedback] = useState<string | null>(null);

  // Position Modification Modal State
  const [modifyingTicket, setModifyingTicket] = useState<number | null>(null);
  const [modSL, setModSL] = useState(0);
  const [modTP, setModTP] = useState(0);

  // Position search
  const [posFilter, setPosFilter] = useState('');
  const filteredPositions = useMemo(
    () => store.positions.filter(p => `${p.ticket} ${p.symbol} ${p.comment}`.toLowerCase().includes(posFilter.toLowerCase())),
    [store.positions, posFilter]
  );

  const handleSubmitOrder = (orderSide: OrderSide) => {
    const result = store.submitOrder({
      symbol,
      side: orderSide,
      kind,
      lots,
      price: kind !== 'Market' ? price : undefined,
      stopLoss: stopLoss > 0 ? stopLoss : undefined,
      takeProfit: takeProfit > 0 ? takeProfit : undefined,
      comment,
    });
    setFeedback(result.message);
    setTimeout(() => setFeedback(null), 4000);
  };

  const handleOpenModify = (ticket: number, sl: number, tp: number) => {
    setModifyingTicket(ticket);
    setModSL(sl);
    setModTP(tp);
  };

  const handleSaveModify = () => {
    if (modifyingTicket !== null) {
      store.modifyPosition(modifyingTicket, modSL, modTP);
      setModifyingTicket(null);
    }
  };

  return (
    <div className="trading-dashboard p-4 space-y-4 max-w-[1600px] mx-auto overflow-y-auto">
      {/* Top Header & Emergency Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-surface p-4 rounded border border-border">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="text-emerald-500 animate-pulse" size={18} />
            <h1 className="text-xl font-bold">Trading Dashboard</h1>
            <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
              LIVE ENGINE READY
            </span>
          </div>
          <span className="text-sm text-muted">
            Order routing, live positions, circuit breakers, and emergency flatten controls.
          </span>
        </div>

        {/* Action Buttons & Emergency Kill Switch */}
        <div className="flex items-center gap-3">
          <Button
            onClick={store.toggleTrading}
            className={store.tradingPaused ? 'bg-amber-600 hover:bg-amber-700 text-white' : ''}
          >
            {store.tradingPaused ? <PlayCircle size={15} /> : <PauseCircle size={15} />}
            {store.tradingPaused ? 'Resume Strategy Execution' : 'Pause Automated Trading'}
          </Button>

          <Button
            className="bg-red-600 hover:bg-red-700 text-white font-semibold flex items-center gap-1.5"
            onClick={() => store.setKillSwitchModalOpen(true)}
          >
            <AlertOctagon size={16} />
            EMERGENCY KILL SWITCH
          </Button>
        </div>
      </div>

      {/* Account Switcher & Broker Connections Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {store.accounts.map(acc => (
          <div
            key={acc.id}
            onClick={() => store.selectAccount(acc.id)}
            className={`p-3 rounded border cursor-pointer transition-all ${
              acc.id === store.selectedAccountId
                ? 'bg-primary/10 border-primary shadow-sm'
                : 'bg-surface border-border hover:border-border/80'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="font-semibold text-sm">{acc.broker}</span>
              <span className="flex items-center gap-1 text-xs text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                {acc.latencyMs}ms
              </span>
            </div>
            <div className="mt-1 flex items-baseline justify-between text-xs text-muted">
              <span>Acc: {acc.accountNumber} ({acc.server})</span>
              <span className="font-mono text-foreground font-semibold">
                ${acc.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })} {acc.currency}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Account Metrics Strip */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <Stat label="Balance" value={`$${account.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
        <Stat
          label="Equity"
          value={`$${(account.balance + totalFloatingPnl).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          tone={totalFloatingPnl >= 0 ? 'good' : 'bad'}
        />
        <Stat
          label="Floating P/L"
          value={`${totalFloatingPnl >= 0 ? '+$' : '-$'}${Math.abs(totalFloatingPnl).toFixed(2)}`}
          tone={totalFloatingPnl >= 0 ? 'good' : 'bad'}
        />
        <Stat label="Margin Used" value={`$${account.margin.toLocaleString()}`} />
        <Stat label="Free Margin" value={`$${(account.freeMargin + totalFloatingPnl).toLocaleString(undefined, { maximumFractionDigits: 0 })}`} />
        <Stat label="Margin Level" value={account.margin > 0 ? `${account.marginLevel.toFixed(1)}%` : '∞'} tone="good" />
      </div>

      {/* Main Trading Area: Order Form & Active Positions */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Left Column: Order Ticket */}
        <div className="lg:col-span-1 bg-surface p-4 rounded border border-border space-y-4">
          <div className="flex items-center justify-between border-b border-border pb-2">
            <strong className="text-sm">Order Ticket</strong>
            <span className="text-xs text-muted">Instant routing</span>
          </div>

          <Field label="Symbol">
            <select
              className="text-input w-full"
              value={symbol}
              onChange={e => setSymbol(e.target.value)}
            >
              <option value="EURUSD">EURUSD (Euro / US Dollar)</option>
              <option value="GBPUSD">GBPUSD (Great Britain Pound)</option>
              <option value="USDJPY">USDJPY (US Dollar / Japanese Yen)</option>
              <option value="NQ100">NQ100 (Nasdaq 100 Index)</option>
              <option value="US500">US500 (S&P 500 Index)</option>
              <option value="BTCUSDT">BTCUSDT (Bitcoin / Tether)</option>
            </select>
          </Field>

          <Field label="Order Type">
            <select
              className="text-input w-full"
              value={kind}
              onChange={e => setKind(e.target.value as OrderKind)}
            >
              <option value="Market">Market Order (Immediate)</option>
              <option value="Limit">Limit Order (Pending)</option>
              <option value="Stop">Stop Order (Pending)</option>
            </select>
          </Field>

          <div className="grid grid-cols-2 gap-2">
            <Field label="Volume (Lots)">
              <TextInput
                type="number"
                step="0.01"
                min="0.01"
                value={lots}
                onChange={e => setLots(Number(e.target.value))}
              />
            </Field>
            {kind !== 'Market' && (
              <Field label="Order Price">
                <TextInput
                  type="number"
                  step="0.0001"
                  value={price}
                  onChange={e => setPrice(Number(e.target.value))}
                />
              </Field>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Field label="Stop Loss">
              <TextInput
                type="number"
                step="0.0001"
                value={stopLoss}
                onChange={e => setStopLoss(Number(e.target.value))}
              />
            </Field>
            <Field label="Take Profit">
              <TextInput
                type="number"
                step="0.0001"
                value={takeProfit}
                onChange={e => setTakeProfit(Number(e.target.value))}
              />
            </Field>
          </div>

          <Field label="Comment">
            <TextInput
              placeholder="e.g. Manual test"
              value={comment}
              onChange={e => setComment(e.target.value)}
            />
          </Field>

          {feedback && (
            <div className="text-xs p-2 rounded bg-primary/10 border border-primary/30 text-foreground">
              {feedback}
            </div>
          )}

          <div className="grid grid-cols-2 gap-2 pt-2">
            <Button
              className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 flex items-center justify-center gap-1"
              disabled={store.tradingPaused}
              onClick={() => handleSubmitOrder('Buy')}
            >
              <ArrowUpCircle size={16} />
              BUY {lots} LOT
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 flex items-center justify-center gap-1"
              disabled={store.tradingPaused}
              onClick={() => handleSubmitOrder('Sell')}
            >
              <ArrowDownCircle size={16} />
              SELL {lots} LOT
            </Button>
          </div>
        </div>

        {/* Right Column: Positions, Orders & Log */}
        <div className="lg:col-span-3 space-y-4">
          {/* Active Positions Table */}
          <div className="bg-surface p-4 rounded border border-border space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2">
              <div className="flex items-center gap-2">
                <strong className="text-sm">Open Positions ({store.positions.length})</strong>
                <span className="text-xs text-muted">Broker-reconciled active tickets</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="search flex items-center gap-1 bg-background px-2 py-1 rounded border border-border text-xs">
                  <Search size={13} className="text-muted" />
                  <input
                    placeholder="Filter positions..."
                    className="bg-transparent border-none outline-none text-xs w-36"
                    value={posFilter}
                    onChange={e => setPosFilter(e.target.value)}
                  />
                </div>
                <Button
                  disabled={!store.positions.length}
                  onClick={store.closeAllPositions}
                  className="text-xs text-red-400 hover:text-red-300"
                >
                  <Flame size={13} />
                  Flatten All Positions
                </Button>
              </div>
            </div>

            <div className="plain-table-wrap overflow-x-auto">
              <table className="plain-table w-full text-xs">
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Open Time</th>
                    <th>Side</th>
                    <th>Symbol</th>
                    <th>Lots</th>
                    <th>Open Price</th>
                    <th>Current</th>
                    <th>S/L</th>
                    <th>T/P</th>
                    <th>P/L ($)</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPositions.length === 0 ? (
                    <tr>
                      <td colSpan={11} className="text-center py-6 text-muted">
                        No open positions. Use Order Ticket to execute orders.
                      </td>
                    </tr>
                  ) : (
                    filteredPositions.map(pos => (
                      <tr key={pos.ticket}>
                        <td className="font-mono">{pos.ticket}</td>
                        <td className="text-muted">{pos.openTime}</td>
                        <td>
                          <span className={`pill ${pos.side === 'Buy' ? 'green' : 'red'}`}>
                            {pos.side}
                          </span>
                        </td>
                        <td><strong>{pos.symbol}</strong></td>
                        <td>{pos.lots.toFixed(2)}</td>
                        <td>{pos.openPrice.toFixed(pos.symbol.includes('JPY') ? 3 : 5)}</td>
                        <td>{pos.currentPrice.toFixed(pos.symbol.includes('JPY') ? 3 : 5)}</td>
                        <td className="text-muted">{pos.stopLoss || '—'}</td>
                        <td className="text-muted">{pos.takeProfit || '—'}</td>
                        <td className={pos.pnl >= 0 ? 'positive font-bold' : 'negative font-bold'}>
                          {pos.pnl >= 0 ? `+$${pos.pnl.toFixed(2)}` : `-$${Math.abs(pos.pnl).toFixed(2)}`}
                        </td>
                        <td>
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              className="px-2 py-0.5 rounded bg-background hover:bg-border text-xs border border-border"
                              onClick={() => handleOpenModify(pos.ticket, pos.stopLoss, pos.takeProfit)}
                            >
                              Modify
                            </button>
                            <button
                              type="button"
                              className="px-2 py-0.5 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs border border-red-500/30"
                              onClick={() => store.closePosition(pos.ticket)}
                            >
                              Close
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pending Orders Table */}
          <div className="bg-surface p-4 rounded border border-border space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <strong className="text-sm">Pending Orders ({store.pendingOrders.length})</strong>
              <Button
                disabled={!store.pendingOrders.length}
                onClick={store.cancelAllOrders}
                className="text-xs"
              >
                Cancel All Orders
              </Button>
            </div>

            <div className="plain-table-wrap overflow-x-auto">
              <table className="plain-table w-full text-xs">
                <thead>
                  <tr>
                    <th>Ticket</th>
                    <th>Type</th>
                    <th>Symbol</th>
                    <th>Volume</th>
                    <th>Order Price</th>
                    <th>Market Price</th>
                    <th>S/L</th>
                    <th>T/P</th>
                    <th>Comment</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {store.pendingOrders.length === 0 ? (
                    <tr>
                      <td colSpan={10} className="text-center py-4 text-muted">
                        No active pending orders.
                      </td>
                    </tr>
                  ) : (
                    store.pendingOrders.map(ord => (
                      <tr key={ord.ticket}>
                        <td className="font-mono">{ord.ticket}</td>
                        <td><span className="pill">{ord.kind}</span></td>
                        <td><strong>{ord.symbol}</strong></td>
                        <td>{ord.lots.toFixed(2)}</td>
                        <td>{ord.orderPrice.toFixed(5)}</td>
                        <td>{ord.currentPrice.toFixed(5)}</td>
                        <td>{ord.stopLoss || '—'}</td>
                        <td>{ord.takeProfit || '—'}</td>
                        <td className="text-muted">{ord.comment}</td>
                        <td>
                          <button
                            type="button"
                            className="px-2 py-0.5 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs border border-red-500/30"
                            onClick={() => store.cancelOrder(ord.ticket)}
                          >
                            Cancel
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Execution Log / Journal */}
          <div className="bg-surface p-4 rounded border border-border space-y-2">
            <div className="flex items-center justify-between border-b border-border pb-2">
              <strong className="text-sm">Execution Audit Journal</strong>
              <span className="text-xs text-muted">Real-time router events</span>
            </div>
            <div className="space-y-1 max-h-40 overflow-y-auto font-mono text-xs">
              {store.logs.map(l => (
                <div key={l.id} className="flex items-start gap-2 py-0.5 border-b border-border/40">
                  <span className="text-muted whitespace-nowrap">{l.timestamp}</span>
                  <span className={`pill ${l.level === 'SUCCESS' ? 'green' : l.level === 'ERROR' ? 'red' : ''}`}>
                    {l.level}
                  </span>
                  <span className="font-semibold text-muted">[{l.source}]</span>
                  <span className="text-foreground">{l.message}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Modify Position Modal */}
      {modifyingTicket !== null && (
        <Modal
          title={`Modify Position #${modifyingTicket}`}
          onClose={() => setModifyingTicket(null)}
          footer={
            <>
              <Button onClick={() => setModifyingTicket(null)}>Cancel</Button>
              <Button className="primary" onClick={handleSaveModify}>Save Parameters</Button>
            </>
          }
        >
          <div className="space-y-3">
            <p className="text-xs text-muted">
              Update Stop Loss and Take Profit levels for ticket #{modifyingTicket}.
            </p>
            <Field label="Stop Loss Price">
              <TextInput
                type="number"
                step="0.0001"
                value={modSL}
                onChange={e => setModSL(Number(e.target.value))}
              />
            </Field>
            <Field label="Take Profit Price">
              <TextInput
                type="number"
                step="0.0001"
                value={modTP}
                onChange={e => setModTP(Number(e.target.value))}
              />
            </Field>
          </div>
        </Modal>
      )}

      {/* Emergency Kill Switch Modal */}
      {store.killSwitchModalOpen && (
        <Modal
          title="CONFIRM EMERGENCY KILL SWITCH"
          onClose={() => store.setKillSwitchModalOpen(false)}
          footer={
            <>
              <Button onClick={() => store.setKillSwitchModalOpen(false)}>Cancel</Button>
              <Button
                className="bg-red-600 hover:bg-red-700 text-white font-bold"
                onClick={store.executeEmergencyKillSwitch}
              >
                EXECUTE IMMEDIATE KILL SWITCH
              </Button>
            </>
          }
        >
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-red-400 font-bold">
              <ShieldAlert size={22} />
              <span>CRITICAL SAFETY OVERRIDE</span>
            </div>
            <p className="text-sm">
              Executing the Emergency Kill Switch will immediately:
            </p>
            <ul className="list-disc list-inside text-xs space-y-1 text-muted">
              <li>Send market close orders for <strong>all {store.positions.length} active positions</strong>.</li>
              <li>Cancel <strong>all {store.pendingOrders.length} pending orders</strong>.</li>
              <li>Halt automated strategy and bot executions across all connected brokers.</li>
            </ul>
            <p className="text-xs text-red-300">
              This action takes immediate effect across the network router.
            </p>
          </div>
        </Modal>
      )}
    </div>
  );
}
export { TradingDashboard as TradingWorkspace };
