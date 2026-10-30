import { useState, useMemo } from 'react';
import { Send, Calculator } from 'lucide-react';
import type { OrderKind, OrderSide } from '../../../shell/types';
import { Button, Field, Modal, TextInput } from '../../../common/components/ui';
import { useTradingStore } from '../tradingStore';

interface OrderEntryModalProps {
  onClose: () => void;
}

export function OrderEntryModal({ onClose }: OrderEntryModalProps) {
  const store = useTradingStore();
  const account = useMemo(
    () => store.accounts.find(a => a.id === store.selectedAccountId) ?? store.accounts[0],
    [store.accounts, store.selectedAccountId]
  );

  const [symbol, setSymbol] = useState('EURUSD');
  const [side, setSide] = useState<OrderSide>('Buy');
  const [kind, setKind] = useState<OrderKind>('Market');
  const [lots, setLots] = useState(1.0);
  const [price, setPrice] = useState(1.085);
  const [stopLoss, setStopLoss] = useState(1.079);
  const [takeProfit, setTakeProfit] = useState(1.095);
  const [comment, setComment] = useState('');
  const [riskPercent, setRiskPercent] = useState(1.0);
  const [feedback, setFeedback] = useState<string | null>(null);

  // Automatic lot-size calculation based on risk % and SL distance
  const calculateRiskLots = () => {
    if (!account || !account.balance) return;
    const slDist = Math.abs((price || 1.085) - stopLoss);
    if (slDist <= 0.00001) return;
    const riskAmount = account.balance * (riskPercent / 100);
    const calculatedLots = riskAmount / (slDist * 100000);
    const clampedLots = Math.max(0.01, Math.min(50.0, Math.round(calculatedLots * 100) / 100));
    setLots(clampedLots);
    setFeedback(`Calculated ${clampedLots} lots for ${riskPercent}% risk ($${riskAmount.toFixed(2)})`);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const res = store.submitOrder({
      symbol,
      side,
      kind,
      lots,
      price: kind !== 'Market' ? price : undefined,
      stopLoss: stopLoss > 0 ? stopLoss : undefined,
      takeProfit: takeProfit > 0 ? takeProfit : undefined,
      comment,
    });
    setFeedback(res.message);
    if (res.success) {
      setTimeout(() => {
        setFeedback(null);
        onClose();
      }, 800);
    }
  };

  return (
    <Modal title="New Order Ticket" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {feedback && (
          <div className="p-2.5 bg-primary/10 border border-primary/20 text-primary text-xs rounded-lg">
            {feedback}
          </div>
        )}

        {/* Side & Kind Selection */}
        <div className="grid grid-cols-2 gap-2">
          <Button
            type="button"
            onClick={() => setSide('Buy')}
            className={`font-bold ${side === 'Buy' ? 'bg-accent-success text-white' : ''}`}
          >
            BUY
          </Button>
          <Button
            type="button"
            onClick={() => setSide('Sell')}
            className={`font-bold ${side === 'Sell' ? 'bg-accent-danger text-white' : ''}`}
          >
            SELL
          </Button>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <Button
            type="button"
            onClick={() => setKind('Market')}
            className={kind === 'Market' ? 'primary' : ''}
          >
            Market Order
          </Button>
          <Button
            type="button"
            onClick={() => setKind('Limit')}
            className={kind === 'Limit' ? 'primary' : ''}
          >
            Limit Order
          </Button>
        </div>

        {/* Symbol & Lots */}
        <div className="grid grid-cols-2 gap-3">
          <Field label="Symbol">
            <TextInput
              value={symbol}
              onChange={e => setSymbol(e.target.value.toUpperCase())}
              required
            />
          </Field>
          <Field label="Volume (Lots)">
            <TextInput
              type="number"
              step="0.01"
              min="0.01"
              max="50"
              value={lots}
              onChange={e => setLots(parseFloat(e.target.value) || 0.01)}
              required
            />
          </Field>
        </div>

        {/* Risk % Calculator */}
        <div className="p-3 bg-surface rounded-lg border border-border space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-text-muted flex items-center gap-1">
              <Calculator className="w-3.5 h-3.5" /> Risk Calculator
            </span>
            <Button
              type="button"
              onClick={calculateRiskLots}
              className="h-6 text-xs px-2"
            >
              Auto-calculate Lots
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <TextInput
              type="number"
              step="0.5"
              min="0.1"
              max="10"
              value={riskPercent}
              onChange={e => setRiskPercent(parseFloat(e.target.value) || 1.0)}
              className="w-24 text-xs"
            />
            <span className="text-xs text-text-muted">% of balance (${account?.balance.toFixed(2)})</span>
          </div>
        </div>

        {/* Price for Limit/Stop */}
        {kind !== 'Market' && (
          <Field label="Order Price">
            <TextInput
              type="number"
              step="0.0001"
              value={price}
              onChange={e => setPrice(parseFloat(e.target.value) || 0)}
              required
            />
          </Field>
        )}

        {/* Stop Loss & Take Profit */}
        <div className="grid grid-cols-2 gap-3">
          <Field label="Stop Loss">
            <TextInput
              type="number"
              step="0.0001"
              value={stopLoss}
              onChange={e => setStopLoss(parseFloat(e.target.value) || 0)}
            />
          </Field>
          <Field label="Take Profit">
            <TextInput
              type="number"
              step="0.0001"
              value={takeProfit}
              onChange={e => setTakeProfit(parseFloat(e.target.value) || 0)}
            />
          </Field>
        </div>

        <Field label="Comment">
          <TextInput
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="Optional order comment"
          />
        </Field>

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" className="primary gap-1.5 font-bold">
            <Send className="w-4 h-4" />
            Place {side} Order
          </Button>
        </div>
      </form>
    </Modal>
  );
}
