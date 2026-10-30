import { useMemo, useState } from 'react';
import { ArrowDownCircle, ArrowUpCircle, Search, XCircle } from 'lucide-react';
import { Button, Field, Modal, TextInput } from '../../../common/components/ui';
import { useTradingStore } from '../tradingStore';

export function PositionsTable() {
  const store = useTradingStore();
  const [filter, setFilter] = useState('');
  const [modifyingTicket, setModifyingTicket] = useState<number | null>(null);
  const [modSL, setModSL] = useState(0);
  const [modTP, setModTP] = useState(0);

  const filteredPositions = useMemo(
    () =>
      store.positions.filter(p =>
        `${p.ticket} ${p.symbol} ${p.comment}`.toLowerCase().includes(filter.toLowerCase())
      ),
    [store.positions, filter]
  );

  const handleOpenModify = (ticket: number, currentSL: number, currentTP: number) => {
    setModifyingTicket(ticket);
    setModSL(currentSL);
    setModTP(currentTP);
  };

  const handleSaveModify = () => {
    if (modifyingTicket !== null) {
      store.modifyPosition(modifyingTicket, modSL, modTP);
      setModifyingTicket(null);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <TextInput
            value={filter}
            onChange={e => setFilter(e.target.value)}
            placeholder="Search positions by ticket or symbol..."
            className="pl-9"
          />
        </div>
        <div className="text-xs text-text-muted">
          Showing {filteredPositions.length} of {store.positions.length} positions
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border border-border bg-surface-subtle">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface text-text-muted font-medium">
              <th className="p-3">Ticket</th>
              <th className="p-3">Symbol</th>
              <th className="p-3">Side</th>
              <th className="p-3 text-right">Lots</th>
              <th className="p-3 text-right">Open</th>
              <th className="p-3 text-right">Current</th>
              <th className="p-3 text-right">SL</th>
              <th className="p-3 text-right">TP</th>
              <th className="p-3 text-right">PnL</th>
              <th className="p-3 text-center">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {filteredPositions.length === 0 ? (
              <tr>
                <td colSpan={10} className="p-6 text-center text-text-muted">
                  No active open positions.
                </td>
              </tr>
            ) : (
              filteredPositions.map(pos => {
                const isBuy = pos.side === 'Buy';
                const isProfitable = pos.pnl >= 0;
                return (
                  <tr key={pos.id} className="hover:bg-surface/50 transition-colors">
                    <td className="p-3 font-mono">#{pos.ticket}</td>
                    <td className="p-3 font-bold text-text">{pos.symbol}</td>
                    <td className="p-3">
                      <span
                        className={`inline-flex items-center gap-1 font-semibold ${
                          isBuy ? 'text-accent-success' : 'text-accent-danger'
                        }`}
                      >
                        {isBuy ? (
                          <ArrowUpCircle className="w-3.5 h-3.5" />
                        ) : (
                          <ArrowDownCircle className="w-3.5 h-3.5" />
                        )}
                        {pos.side}
                      </span>
                    </td>
                    <td className="p-3 text-right font-mono">{pos.lots.toFixed(2)}</td>
                    <td className="p-3 text-right font-mono">{pos.openPrice.toFixed(5)}</td>
                    <td className="p-3 text-right font-mono">{pos.currentPrice.toFixed(5)}</td>
                    <td className="p-3 text-right font-mono text-text-muted">
                      {pos.stopLoss > 0 ? pos.stopLoss.toFixed(5) : '-'}
                    </td>
                    <td className="p-3 text-right font-mono text-text-muted">
                      {pos.takeProfit > 0 ? pos.takeProfit.toFixed(5) : '-'}
                    </td>
                    <td
                      className={`p-3 text-right font-mono font-bold ${
                        isProfitable ? 'text-accent-success' : 'text-accent-danger'
                      }`}
                    >
                      {isProfitable ? '+' : ''}
                      {pos.pnl.toFixed(2)}
                    </td>
                    <td className="p-3 text-center">
                      <div className="flex items-center justify-center gap-1.5">
                        <Button
                          onClick={() => handleOpenModify(pos.ticket, pos.stopLoss, pos.takeProfit)}
                          className="h-7 px-2 text-xs"
                        >
                          Modify
                        </Button>
                        <Button
                          onClick={() => store.closePosition(pos.ticket)}
                          className="danger h-7 px-2 text-xs gap-1"
                        >
                          <XCircle className="w-3 h-3" />
                          Close
                        </Button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Modify SL/TP Modal */}
      {modifyingTicket !== null && (
        <Modal
          title={`Modify Position #${modifyingTicket}`}
          onClose={() => setModifyingTicket(null)}
        >
          <div className="space-y-4">
            <Field label="Stop Loss (Price)">
              <TextInput
                type="number"
                step="0.0001"
                value={modSL}
                onChange={e => setModSL(parseFloat(e.target.value) || 0)}
              />
            </Field>
            <Field label="Take Profit (Price)">
              <TextInput
                type="number"
                step="0.0001"
                value={modTP}
                onChange={e => setModTP(parseFloat(e.target.value) || 0)}
              />
            </Field>
            <div className="flex justify-end gap-2 pt-2">
              <Button onClick={() => setModifyingTicket(null)}>
                Cancel
              </Button>
              <Button className="primary" onClick={handleSaveModify}>
                Apply Protection
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
