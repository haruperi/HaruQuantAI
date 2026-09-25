import { useState } from 'react';
import { useChart } from '../../hooks/useChartEngine';
import { uid, type Position } from '../../types';
import { validateOrder } from '../../store/positions';
import { Modal } from '../Modal';
export function OrderTicket() {
  const { store, engine } = useChart(),
    s = store.getState(),
    [side, setSide] = useState(s.ui.side),
    [type, setType] = useState<Position['type']>('market'),
    [quantity, setQuantity] = useState('1'),
    [price, setPrice] = useState(
      String(
        engine.current?.quotes.get(s.chart.symbol)?.price ??
          engine.current?.bars.at(-1)?.close ??
          0,
      ),
    ),
    [sl, setSL] = useState(''),
    [tp, setTP] = useState(''),
    [error, setError] = useState('');
  return (
    <Modal title="Simulated order">
      <form
        className="cq-form"
        onSubmit={(e) => {
          e.preventDefault();
          if (store.getState().ui.replay) {
            setError('Exit replay before placing simulated orders.');
            return;
          }
          const entry =
              type === 'market'
                ? (engine.current?.quotes.get(s.chart.symbol)?.price ?? Number(price))
                : Number(price),
            stop = sl ? Number(sl) : null,
            take = tp ? Number(tp) : null;
          const problem = validateOrder(Number(quantity), entry, side, stop, take);
          if (problem) {
            setError(problem);
            return;
          }
          store.getState().setPositions([
            ...store.getState().positions,
            {
              id: uid(),
              symbol: s.chart.symbol,
              side,
              type,
              quantity: Number(quantity),
              entry,
              sl: stop,
              tp: take,
              status: type === 'market' ? 'open' : 'pending',
              exit: null,
            },
          ]);
          s.setUI({
            dialog: null,
            panel: 'positions',
            toast: 'Simulated ' + side + ' order submitted.',
          });
        }}
      >
        <p className="cq-sim-note">
          {s.chart.symbol} · Paper trading only · P&L in quote currency per unit
        </p>
        <div className="cq-fields">
          <label>
            Side
            <select value={side} onChange={(e) => setSide(e.target.value as 'buy' | 'sell')}>
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
            </select>
          </label>
          <label>
            Order type
            <select value={type} onChange={(e) => setType(e.target.value as Position['type'])}>
              <option value="market">Market</option>
              <option value="limit">Limit</option>
            </select>
          </label>
        </div>
        <label>
          Quantity
          <input
            aria-label="Order quantity"
            type="number"
            step="any"
            min=".000001"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
          />
        </label>
        {type === 'limit' && (
          <label>
            Limit price
            <input
              type="number"
              step="any"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />
          </label>
        )}
        <div className="cq-fields">
          <label>
            Stop loss (optional)
            <input type="number" step="any" value={sl} onChange={(e) => setSL(e.target.value)} />
          </label>
          <label>
            Take profit (optional)
            <input type="number" step="any" value={tp} onChange={(e) => setTP(e.target.value)} />
          </label>
        </div>
        {error && <p role="alert">{error}</p>}
        <button className="cq-primary" type="submit">
          Place simulated order
        </button>
      </form>
    </Modal>
  );
}
