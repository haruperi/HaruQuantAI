import { useMemo, useState } from 'react';
import {
  PauseCircle,
  PlayCircle,
  PlusCircle,
  TrendingDown,
  TrendingUp,
} from 'lucide-react';
import { Button, Stat } from '../../common/components/ui';
import { EmergencyControls } from './components/EmergencyControls';
import { OrderEntryModal } from './components/OrderEntryModal';
import { OrdersTable } from './components/OrdersTable';
import { PositionsTable } from './components/PositionsTable';
import { useTradingStore } from './tradingStore';

export function TradingDashboard() {
  const store = useTradingStore();
  const [activeTab, setActiveTab] = useState<'positions' | 'orders' | 'logs'>('positions');
  const [orderEntryOpen, setOrderEntryOpen] = useState(false);

  // Active account
  const account = useMemo(
    () => store.accounts.find(a => a.id === store.selectedAccountId) ?? store.accounts[0],
    [store.accounts, store.selectedAccountId]
  );

  // Total Floating PnL
  const totalFloatingPnl = useMemo(
    () => store.positions.reduce((acc, p) => acc + p.pnl, 0),
    [store.positions]
  );

  return (
    <div className="space-y-6">
      {/* Top Banner / Account & Emergency Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-surface border border-border">
        <div className="flex items-center gap-4">
          <div>
            <label className="text-xs font-semibold text-text-muted block mb-1">
              Active Connection
            </label>
            <select
              value={store.selectedAccountId}
              onChange={e => store.selectAccount(e.target.value)}
              className="bg-surface-subtle border border-border rounded-lg px-3 py-1.5 text-sm font-semibold focus:outline-none focus:border-primary"
            >
              {store.accounts.map(acc => (
                <option key={acc.id} value={acc.id}>
                  {acc.broker} — #{acc.accountNumber} ({acc.currency})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2 pt-4">
            <Button
              onClick={store.toggleTrading}
              className={`gap-1.5 ${
                store.tradingPaused
                  ? 'border-warning/40 text-warning hover:bg-warning/10'
                  : 'bg-accent-success text-white hover:bg-accent-success/90'
              }`}
            >
              {store.tradingPaused ? (
                <>
                  <PlayCircle className="w-4 h-4" />
                  Resume Trading
                </>
              ) : (
                <>
                  <PauseCircle className="w-4 h-4" />
                  Trading Active
                </>
              )}
            </Button>

            <Button
              onClick={() => setOrderEntryOpen(true)}
              className="primary gap-1.5 font-semibold"
            >
              <PlusCircle className="w-4 h-4" />
              New Order
            </Button>
          </div>
        </div>

        {/* Emergency Panic Controls */}
        <EmergencyControls />
      </div>

      {/* Account Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="card p-3">
          <Stat
            label="Balance"
            value={`${account ? account.currency : '$'} ${(account?.balance ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          />
        </div>
        <div className="card p-3">
          <Stat
            label="Equity"
            value={`${account ? account.currency : '$'} ${(account?.equity ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          />
        </div>
        <div className="card p-3">
          <Stat
            label="Used Margin"
            value={`${account ? account.currency : '$'} ${(account?.margin ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          />
        </div>
        <div className="card p-3">
          <Stat
            label="Free Margin"
            value={`${account ? account.currency : '$'} ${(account?.freeMargin ?? 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          />
        </div>
        <div className="card p-3">
          <Stat
            label="Margin Level"
            value={`${(account?.marginLevel ?? 0).toFixed(1)}%`}
          />
        </div>
        <div className="card p-3">
          <Stat
            label="Floating P/L"
            value={`${totalFloatingPnl >= 0 ? '+' : ''}${totalFloatingPnl.toFixed(2)}`}
            tone={totalFloatingPnl >= 0 ? 'good' : 'bad'}
          />
        </div>
      </div>

      {/* Workspace Tab Navigation */}
      <div className="flex border-b border-border gap-6">
        <button
          type="button"
          onClick={() => setActiveTab('positions')}
          className={`pb-3 text-sm font-semibold transition-colors relative ${
            activeTab === 'positions'
              ? 'text-primary'
              : 'text-text-muted hover:text-text'
          }`}
        >
          Open Positions ({store.positions.length})
          {activeTab === 'positions' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('orders')}
          className={`pb-3 text-sm font-semibold transition-colors relative ${
            activeTab === 'orders'
              ? 'text-primary'
              : 'text-text-muted hover:text-text'
          }`}
        >
          Pending Orders ({store.pendingOrders.length})
          {activeTab === 'orders' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('logs')}
          className={`pb-3 text-sm font-semibold transition-colors relative ${
            activeTab === 'logs'
              ? 'text-primary'
              : 'text-text-muted hover:text-text'
          }`}
        >
          Execution Journal ({store.logs.length})
          {activeTab === 'logs' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
          )}
        </button>
      </div>

      {/* Tab Panels */}
      <div>
        {activeTab === 'positions' && <PositionsTable />}
        {activeTab === 'orders' && <OrdersTable />}
        {activeTab === 'logs' && (
          <div className="rounded-lg border border-border bg-surface-subtle p-3 space-y-2 max-h-96 overflow-y-auto font-mono text-xs">
            {store.logs.length === 0 ? (
              <div className="p-4 text-center text-text-muted">No journal records.</div>
            ) : (
              store.logs.map(log => (
                <div key={log.id} className="flex items-center gap-3 py-1 border-b border-border/50">
                  <span className="text-text-muted">{log.timestamp}</span>
                  <span
                    className={`font-bold px-1.5 py-0.5 rounded text-[10px] ${
                      log.level === 'ERROR'
                        ? 'bg-red-500/20 text-red-400'
                        : log.level === 'WARN'
                        ? 'bg-amber-500/20 text-amber-400'
                        : 'bg-emerald-500/20 text-emerald-400'
                    }`}
                  >
                    {log.level}
                  </span>
                  <span className="text-text-muted">[{log.source}]</span>
                  <span className="text-text">{log.message}</span>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Manual Order Modal */}
      {orderEntryOpen && (
        <OrderEntryModal onClose={() => setOrderEntryOpen(false)} />
      )}
    </div>
  );
}
