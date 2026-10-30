import { useState } from 'react';
import { useStore } from 'zustand';
import { Search } from 'lucide-react';
import { useChart } from '../../hooks/useChartEngine';
import { symbols } from '../../feed/symbols';
import { fuzzy } from '../../utils/search';
import { Modal } from '../Modal';
export function SymbolSearch() {
  const { store } = useChart(),
    s = useStore(store),
    [query, setQuery] = useState(''),
    [category, setCategory] = useState('All'),
    [index, setIndex] = useState(0);
  const results = symbols.filter(
    (x) =>
      (category === 'All' || x.category === category) &&
      fuzzy(query, x.id + ' ' + x.name + ' ' + x.exchange),
  );
  return (
    <Modal title="Symbol search">
      <div className="cq-search">
        <Search size={18} />
        <input
          autoFocus
          aria-label="Search symbols"
          placeholder="Search symbol, company, or market"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIndex(0);
          }}
          onKeyDown={(e) => {
            if (e.key === 'ArrowDown') {
              e.preventDefault();
              setIndex((i) => Math.min(results.length - 1, i + 1));
            }
            if (e.key === 'ArrowUp') {
              e.preventDefault();
              setIndex((i) => Math.max(0, i - 1));
            }
            if (e.key === 'Enter' && results[index]) s.selectSymbol(results[index].id);
          }}
        />
      </div>
      <div className="cq-tabs">
        {['All', 'Forex', 'Metals', 'Crypto', 'Indices', 'Stocks'].map((c) => (
          <button
            key={c}
            className={category === c ? 'cq-active' : ''}
            onClick={() => {
              setCategory(c);
              setIndex(0);
            }}
          >
            {c}
          </button>
        ))}
      </div>
      {!query && (
        <div className="cq-recents">
          <small>RECENT</small>
          {s.recents.map((r) => (
            <button key={r} onClick={() => s.selectSymbol(r)}>
              {r}
            </button>
          ))}
        </div>
      )}
      <div className="cq-symbol-list" role="listbox" aria-label="Symbols">
        {results.map((x, i) => (
          <button
            role="option"
            aria-selected={i === index}
            key={x.id}
            className={i === index ? 'cq-highlight' : ''}
            onClick={() => s.selectSymbol(x.id)}
          >
            <span className="cq-symbol-logo">{x.icon}</span>
            <strong>{x.id}</strong>
            <span>{x.name}</span>
            <small>
              {x.category} · {x.exchange}
            </small>
          </button>
        ))}
        {!results.length && <p>No matching symbols.</p>}
      </div>
    </Modal>
  );
}
