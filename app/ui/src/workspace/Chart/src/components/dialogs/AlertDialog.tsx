import { useRef, useState } from 'react';
import { useChart } from '../../hooks/useChartEngine';
import { uid, type Alert } from '../../types';
import { symbols } from '../../feed/symbols';
import { Modal } from '../Modal';
export function AlertDialog() {
  const { store, engine } = useChart(),
    s = store.getState(),
    [symbol, setSymbol] = useState(s.chart.symbol),
    [condition, setCondition] = useState<Alert['condition']>('up'),
    [value, setValue] = useState(
      String(engine.current?.quotes.get(symbol)?.price ?? engine.current?.bars.at(-1)?.close ?? 0),
    ),
    [upper, setUpper] = useState(''),
    [once, setOnce] = useState(true),
    [expires, setExpires] = useState(new Date(Date.now() + 86400000).toISOString().slice(0, 16)),
    [error, setError] = useState('');
  const request = useRef(0);
  const usePrice = async (next: string) => {
    const revision = ++request.current;
    try {
      const price = await engine.current?.quoteFor(next);
      if (revision === request.current && price !== undefined) setValue(String(price));
    } catch (error) {
      if (revision === request.current)
        setError(error instanceof Error ? error.message : 'Quote unavailable.');
    }
  };
  return (
    <Modal title="Create alert">
      <form
        className="cq-form"
        onSubmit={(e) => {
          e.preventDefault();
          const price = Number(value),
            high = Number(upper),
            expiry = Date.parse(expires + 'Z');
          if (
            !Number.isFinite(price) ||
            price <= 0 ||
            !Number.isFinite(expiry) ||
            expiry <= Date.now() ||
            (['enter', 'exit'].includes(condition) && (!Number.isFinite(high) || high <= price))
          ) {
            setError('Use a positive price, a valid upper channel bound, and a future expiration.');
            return;
          }
          store.getState().setAlerts([
            ...store.getState().alerts,
            {
              id: uid(),
              symbol,
              condition,
              value: price,
              upper: ['enter', 'exit'].includes(condition) ? high : price,
              expires: expiry,
              once,
              active: true,
              triggers: 0,
            },
          ]);
          s.setUI({ dialog: null, panel: 'alerts' });
        }}
      >
        <label>
          Symbol
          <select
            value={symbol}
            onChange={(e) => {
              setSymbol(e.target.value);
              void usePrice(e.target.value);
            }}
          >
            {symbols.map((x) => (
              <option key={x.id}>{x.id}</option>
            ))}
          </select>
        </label>
        <label>
          Condition
          <select
            value={condition}
            onChange={(e) => setCondition(e.target.value as Alert['condition'])}
          >
            <option value="up">Crossing up</option>
            <option value="down">Crossing down</option>
            <option value="enter">Entering channel</option>
            <option value="exit">Exiting channel</option>
          </select>
        </label>
        <label>
          Price / lower bound
          <input
            aria-label="Alert price"
            type="number"
            step="any"
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        </label>
        <button type="button" onClick={() => void usePrice(symbol)}>
          Use current simulated price
        </button>
        {['enter', 'exit'].includes(condition) && (
          <label>
            Upper bound
            <input
              type="number"
              step="any"
              value={upper}
              onChange={(e) => setUpper(e.target.value)}
            />
          </label>
        )}
        <label>
          Expiration (UTC)
          <input
            type="datetime-local"
            value={expires}
            onChange={(e) => setExpires(e.target.value)}
          />
        </label>
        <label className="cq-check">
          <input type="checkbox" checked={once} onChange={(e) => setOnce(e.target.checked)} />
          Trigger once
        </label>
        {error && <p role="alert">{error}</p>}
        <button className="cq-primary" type="submit">
          Create simulated alert
        </button>
      </form>
    </Modal>
  );
}
