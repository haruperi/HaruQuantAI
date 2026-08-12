'use client';

import React, { useEffect, useState } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import { useWorkspaceStore } from '../workspaces';
import { apiClients, unwrapData, type Watchlist, type MarketRow } from '@/clients';
import {
  Plus,
  Trash2,
  Star,
  Pencil,
  X,
  MoreVertical,
  LineChart,
  AlignJustify,
  Layers,
} from 'lucide-react';

/** Merge one watchlist item with its live quote, if loaded yet. */
interface DisplayRow {
  symbol: string;
  name: string;
  last: number | null;
  change: number | null;
  changePercent: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
}

function toDisplayRow(symbol: string, quote: MarketRow | undefined): DisplayRow {
  return {
    symbol,
    name: quote?.name ?? symbol,
    last: quote?.last ?? null,
    change: quote?.change ?? null,
    changePercent: quote?.change_percent ?? null,
    open: quote?.open ?? null,
    high: quote?.high ?? null,
    low: quote?.low ?? null,
  };
}

export const WatchlistWidget: React.FC = () => {
  const { openOrderTicket, submitOrder } = useTradingStore();
  const { orderConfirmationRequired, addWidgetToWorkspace } = useWorkspaceStore();

  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  const [quotesBySymbol, setQuotesBySymbol] = useState<Record<string, MarketRow>>({});
  const [quotesLoading, setQuotesLoading] = useState(false);

  const [activeMenuSymbol, setActiveMenuSymbol] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [newSymbol, setNewSymbol] = useState('');
  const [mutating, setMutating] = useState(false);

  // Fetch the caller's watchlists on mount. The backend seeds a curated
  // "default" watchlist on first read, so this always returns at least one.
  useEffect(() => {
    let cancelled = false;
    setStatus('loading');
    void apiClients.watchlists
      .list()
      .then((response) => {
        if (cancelled) return;
        const lists = unwrapData(response);
        setWatchlists(lists);
        const defaultList = lists.find((item) => item.is_default) ?? lists[0];
        setSelectedId(defaultList ? defaultList.watchlist_id : null);
        setStatus('ready');
      })
      .catch(() => {
        if (cancelled) return;
        setErrorMsg('Unable to load watchlists.');
        setStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = watchlists.find((item) => item.watchlist_id === selectedId) ?? null;
  const symbols = selected ? selected.items.map((item) => item.symbol) : [];

  // Fetch live quotes for exactly the selected watchlist's symbols whenever
  // the selection or its item list changes.
  useEffect(() => {
    if (symbols.length === 0) {
      setQuotesBySymbol({});
      return;
    }
    let cancelled = false;
    setQuotesLoading(true);
    void apiClients.data
      .quotes(symbols)
      .then((response) => {
        if (cancelled) return;
        const page = unwrapData(response);
        const bySymbol: Record<string, MarketRow> = {};
        for (const row of page.rows) bySymbol[row.symbol] = row;
        setQuotesBySymbol(bySymbol);
      })
      .catch(() => {
        if (cancelled) return;
        setQuotesBySymbol({});
      })
      .finally(() => {
        if (!cancelled) setQuotesLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, symbols.join(',')]);

  const replaceWatchlist = (updated: Watchlist) => {
    setWatchlists((prev) =>
      prev.map((item) => (item.watchlist_id === updated.watchlist_id ? updated : item))
    );
  };

  const handleCreate = () => {
    const name = newListName.trim();
    if (!name || mutating) return;
    setMutating(true);
    void apiClients.watchlists
      .create(name)
      .then((response) => {
        const created = unwrapData(response);
        setWatchlists((prev) => [...prev, created]);
        setSelectedId(created.watchlist_id);
        setNewListName('');
        setCreating(false);
      })
      .catch(() => {
        setErrorMsg('Unable to create watchlist.');
      })
      .finally(() => setMutating(false));
  };

  const handleRename = () => {
    const name = renameValue.trim();
    if (!selected || !name || mutating) return;
    setMutating(true);
    void apiClients.watchlists
      .update(selected.watchlist_id, { name })
      .then((response) => {
        replaceWatchlist(unwrapData(response));
        setRenaming(false);
      })
      .catch(() => setErrorMsg('Unable to rename watchlist.'))
      .finally(() => setMutating(false));
  };

  const handleSetDefault = () => {
    if (!selected || selected.is_default || mutating) return;
    setMutating(true);
    void apiClients.watchlists
      .update(selected.watchlist_id, { is_default: true })
      .then((response) => {
        const updated = unwrapData(response);
        setWatchlists((prev) =>
          prev.map((item) =>
            item.watchlist_id === updated.watchlist_id
              ? updated
              : { ...item, is_default: false }
          )
        );
      })
      .catch(() => setErrorMsg('Unable to set default watchlist.'))
      .finally(() => setMutating(false));
  };

  const handleDelete = () => {
    if (!selected || selected.is_default || mutating) return;
    setMutating(true);
    void apiClients.watchlists
      .remove(selected.watchlist_id)
      .then(() => {
        setWatchlists((prev) => {
          const remaining = prev.filter((item) => item.watchlist_id !== selected.watchlist_id);
          const fallback = remaining.find((item) => item.is_default) ?? remaining[0] ?? null;
          setSelectedId(fallback ? fallback.watchlist_id : null);
          return remaining;
        });
      })
      .catch(() => setErrorMsg('Unable to delete watchlist.'))
      .finally(() => setMutating(false));
  };

  const handleAddSymbol = () => {
    const symbol = newSymbol.trim().toUpperCase();
    if (!selected || !symbol || mutating) return;
    if (symbols.includes(symbol)) {
      setNewSymbol('');
      return;
    }
    setMutating(true);
    void apiClients.watchlists
      .update(selected.watchlist_id, { symbols: [...symbols, symbol] })
      .then((response) => {
        replaceWatchlist(unwrapData(response));
        setNewSymbol('');
      })
      .catch(() => setErrorMsg('Unable to add symbol.'))
      .finally(() => setMutating(false));
  };

  const handleRemoveSymbol = (symbol: string) => {
    if (!selected || mutating) return;
    setMutating(true);
    void apiClients.watchlists
      .update(selected.watchlist_id, {
        symbols: symbols.filter((item) => item !== symbol),
      })
      .then((response) => replaceWatchlist(unwrapData(response)))
      .catch(() => setErrorMsg('Unable to remove symbol.'))
      .finally(() => setMutating(false));
  };

  const rows = symbols.map((symbol) => toDisplayRow(symbol, quotesBySymbol[symbol]));

  const fmt = (value: number | null): string => (value === null ? '—' : value.toFixed(5));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Watchlist Top Header Controls */}
      <div style={{ padding: '8px 12px', background: 'var(--cme-navy-dark)', borderBottom: '1px solid var(--cme-navy-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontWeight: 700, fontSize: '11px', color: 'var(--text-muted)' }}>WATCHLIST:</span>
          {!renaming && (
            <select
              className="form-select"
              value={selectedId ?? ''}
              onChange={(e) => setSelectedId(e.target.value)}
              style={{ padding: '2px 6px', fontSize: '11px' }}
            >
              {watchlists.map((item) => (
                <option key={item.watchlist_id} value={item.watchlist_id}>
                  {item.name}
                  {item.is_default ? ' (default)' : ''}
                </option>
              ))}
            </select>
          )}
          {renaming && (
            <>
              <input
                className="form-select"
                autoFocus
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleRename();
                  if (e.key === 'Escape') setRenaming(false);
                }}
                style={{ padding: '2px 6px', fontSize: '11px', width: '140px' }}
              />
              <button className="btn-cme btn-primary btn-sm" onClick={handleRename} disabled={mutating}>
                Save
              </button>
            </>
          )}
          {selected && !renaming && (
            <>
              <button
                className="btn-cme btn-outline btn-sm"
                title="Rename watchlist"
                style={{ padding: '2px 4px' }}
                onClick={() => {
                  setRenameValue(selected.name);
                  setRenaming(true);
                }}
              >
                <Pencil size={12} />
              </button>
              <button
                className="btn-cme btn-outline btn-sm"
                title={selected.is_default ? 'Already the default' : 'Set as default'}
                style={{ padding: '2px 4px', opacity: selected.is_default ? 0.4 : 1 }}
                disabled={selected.is_default || mutating}
                onClick={handleSetDefault}
              >
                <Star size={12} />
              </button>
              <button
                className="btn-cme btn-outline btn-sm"
                title={selected.is_default ? 'Cannot delete the default watchlist' : 'Delete watchlist'}
                style={{ padding: '2px 4px', opacity: selected.is_default ? 0.4 : 1 }}
                disabled={selected.is_default || mutating}
                onClick={handleDelete}
              >
                <Trash2 size={12} />
              </button>
            </>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {selected && (
            <>
              <input
                className="form-select"
                placeholder="Add symbol…"
                value={newSymbol}
                onChange={(e) => setNewSymbol(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAddSymbol();
                }}
                style={{ padding: '2px 6px', fontSize: '11px', width: '100px' }}
              />
              <button className="btn-cme btn-outline btn-sm" onClick={handleAddSymbol} disabled={mutating}>
                <Plus size={12} /> ADD
              </button>
            </>
          )}
          {!creating && (
            <button className="btn-cme btn-primary btn-sm" onClick={() => setCreating(true)}>
              <Plus size={12} /> CREATE NEW
            </button>
          )}
          {creating && (
            <>
              <input
                className="form-select"
                autoFocus
                placeholder="Watchlist name…"
                value={newListName}
                onChange={(e) => setNewListName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleCreate();
                  if (e.key === 'Escape') setCreating(false);
                }}
                style={{ padding: '2px 6px', fontSize: '11px', width: '140px' }}
              />
              <button className="btn-cme btn-primary btn-sm" onClick={handleCreate} disabled={mutating}>
                Save
              </button>
            </>
          )}
        </div>
      </div>

      {errorMsg && (
        <div style={{ padding: '4px 12px', color: 'var(--financial-negative, #ff4975)', fontSize: '11px' }}>
          {errorMsg}
        </div>
      )}

      {/* Main Watchlist Items Table */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {status === 'loading' && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted, #718294)' }}>
            Loading watchlists…
          </div>
        )}
        {status === 'error' && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--financial-negative, #ff4975)' }}>
            {errorMsg}
          </div>
        )}
        {status === 'ready' && rows.length === 0 && (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted, #718294)' }}>
            No symbols in this watchlist. Add one above.
          </div>
        )}
        {status === 'ready' && rows.length > 0 && (
          <table className="cme-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Last Price</th>
                <th>Change</th>
                <th>Open</th>
                <th>High</th>
                <th>Low</th>
                <th style={{ textAlign: 'center' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => {
                const isUp = (p.change ?? 0) > 0;
                const isDown = (p.change ?? 0) < 0;
                const priceClass = isUp ? 'price-up' : isDown ? 'price-down' : 'price-flat';
                const changeCell =
                  p.change === null || p.changePercent === null
                    ? '—'
                    : `${isUp ? '+' : ''}${p.change.toFixed(5)} (${p.changePercent.toFixed(2)}%)`;

                return (
                  <tr key={p.symbol}>
                    <td style={{ fontWeight: 600, color: 'var(--cme-blue-bright)' }}>{p.symbol}</td>
                    <td className={priceClass}>{fmt(p.last)}</td>
                    <td className={priceClass}>{quotesLoading ? '…' : changeCell}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.open)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.high)}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>{fmt(p.low)}</td>
                    <td style={{ textAlign: 'center', position: 'relative' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                        <button
                          className="btn-cme btn-outline btn-sm"
                          onClick={() => {
                            if (!orderConfirmationRequired) {
                              submitOrder({ symbol: p.symbol, side: 'BUY', qty: 1, orderType: 'Market' });
                            } else {
                              openOrderTicket({ symbol: p.symbol, side: 'BUY', type: 'Market' });
                            }
                          }}
                        >
                          TRADE
                        </button>
                        <button
                          className="btn-cme btn-outline btn-sm"
                          style={{ padding: '2px 4px' }}
                          onClick={() => setActiveMenuSymbol(activeMenuSymbol === p.symbol ? null : p.symbol)}
                        >
                          <MoreVertical size={14} />
                        </button>
                        <button
                          className="btn-cme btn-outline btn-sm"
                          title="Remove from watchlist"
                          style={{ padding: '2px 4px' }}
                          onClick={() => handleRemoveSymbol(p.symbol)}
                        >
                          <X size={14} />
                        </button>
                      </div>

                      {activeMenuSymbol === p.symbol && (
                        <div className="markets-row-menu">
                          <div
                            className="sidebar-menu-item"
                            onClick={() => {
                              addWidgetToWorkspace('chart', `${p.symbol} Chart`, p.symbol);
                              setActiveMenuSymbol(null);
                            }}
                          >
                            <LineChart size={14} /> Chart
                          </div>
                          <div
                            className="sidebar-menu-item"
                            onClick={() => {
                              addWidgetToWorkspace('priceLadder', `${p.symbol} DOM`, p.symbol);
                              setActiveMenuSymbol(null);
                            }}
                          >
                            <AlignJustify size={14} /> Price Ladder
                          </div>
                          <div
                            className="sidebar-menu-item"
                            onClick={() => {
                              addWidgetToWorkspace('optionsGrid', `${p.symbol} Options`, p.symbol);
                              setActiveMenuSymbol(null);
                            }}
                          >
                            <Layers size={14} /> Options
                          </div>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
