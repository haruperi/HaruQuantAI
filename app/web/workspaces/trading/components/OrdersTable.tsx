import { useMemo, useState } from 'react';
import { Search, XCircle } from 'lucide-react';
import { Button, TextInput } from '../../../common/components/ui';
import { useTradingStore } from '../tradingStore';

export function OrdersTable() {
  const store = useTradingStore();
  const [filter, setFilter] = useState('');

  const filteredOrders = useMemo(
    () =>
      store.pendingOrders.filter(o =>
        `${o.ticket} ${o.symbol} ${o.kind} ${o.comment}`.toLowerCase().includes(filter.toLowerCase())
      ),
    [store.pendingOrders, filter]
  );

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <TextInput
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Search pending orders..."
            className="pl-9"
          />
        </div>
        <div className="text-xs text-text-muted">
          Showing {filteredOrders.length} of {store.pendingOrders.length} pending orders
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border bg-surface-subtle">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface text-text-muted font-medium">
              <th className="p-3">Ticket</th>
              <th className="p-3">Symbol</th>
              <th className="p-3">Order Kind</th>
              <th className="p-3 text-right">Lots</th>
              <th className="p-3 text-right">Order Price</th>
              <th className="p-3 text-right">Current Price</th>
              <th className="p-3 text-right">Stop Loss</th>
              <th className="p-3 text-right">Take Profit</th>
              <th className="p-3">Expiration</th>
              <th className="p-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filteredOrders.length === 0 ? (
              <tr>
                <td colSpan={10} className="p-6 text-center text-text-muted">
                  No working pending orders.
                </td>
              </tr>
            ) : (
              filteredOrders.map(order => (
                <tr key={order.id} className="hover:bg-surface/50 transition-colors">
                  <td className="p-3 font-mono">#{order.ticket}</td>
                  <td className="p-3 font-bold text-text">{order.symbol}</td>
                  <td className="p-3 font-semibold text-warning">{order.kind}</td>
                  <td className="p-3 text-right font-mono">{order.lots.toFixed(2)}</td>
                  <td className="p-3 text-right font-mono">{order.orderPrice.toFixed(5)}</td>
                  <td className="p-3 text-right font-mono">{order.currentPrice.toFixed(5)}</td>
                  <td className="p-3 text-right font-mono text-text-muted">
                    {order.stopLoss > 0 ? order.stopLoss.toFixed(5) : '-'}
                  </td>
                  <td className="p-3 text-right font-mono text-text-muted">
                    {order.takeProfit > 0 ? order.takeProfit.toFixed(5) : '-'}
                  </td>
                  <td className="p-3 text-text-muted">{order.expiration}</td>
                  <td className="p-3 text-center">
                    <Button
                      onClick={() => store.cancelOrder(order.ticket)}
                      className="danger h-7 px-2 text-xs gap-1"
                    >
                      <XCircle className="w-3 h-3" />
                      Cancel
                    </Button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
