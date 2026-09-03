'use client';

import React, { useEffect, useRef, useState } from 'react';
import { useWorkspaceStore } from '../workspaces';
import { ApiClientError, apiClients, unwrapData, type Watchlist } from '@/clients';
import {
  filterSymbols,
  loadSymbolUniverse,
  resolveSourceSymbol,
} from './symbolUniverse';
import { emitWatchlistsChanged } from './watchlistEvents';
import {
  Plus,
  Trash2,
  Star,
  Pencil,
  X,
  ChevronUp,
  ChevronDown,
  ArrowUp,
  ArrowDown,
  Info,
} from 'lucide-react';

type SortDirection = 'asc' | 'desc';

/** Widget status includes the explicit gateway-unavailable state (D-UI §4.8). */
type WatchlistStatus = 'loading' | 'ready' | 'error' | 'unavailable';

export const WatchlistWidget: React.FC = () => {
  const { addWidgetToWorkspace } = useWorkspaceStore();

  const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [status, setStatus] = useState<WatchlistStatus>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  const [creating, setCreating] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [renaming, setRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [newSymbol, setNewSymbol] = useState('');
  const [mutating, setMutating] = useState(false);

  const [sortBySymbol, setSortBySymbol] = useState<SortDirection | null>(null);

  const [universe, setUniverse] = useState<string[]>([]);
  const [universeStatus, setUniverseStatus] = useState<'loading' | 'ready' | 'error'>(
    'loading'
  );
  const [universeErrorMsg, setUniverseErrorMsg] = useState('');
  const [suggestOpen, setSuggestOpen] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const suggestionIdPrefix = useRef(`symbol-suggestion-${Math.random().toString(36).slice(2, 8)}`);

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
      .catch((cause: unknown) => {
        if (cancelled) return;
        if (cause instanceof ApiClientError && cause.status === 503) {
          setErrorMsg('The watchlist gateway is unavailable.');
          setStatus('unavailable');
        } else {
          setErrorMsg('Unable to load watchlists.');
          setStatus('error');
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    void loadSymbolUniverse()
      .then((symbols) => {
        if (cancelled) return;
        setUniverse(symbols);
        setUniverseStatus('ready');
      })
      .catch(() => {
        if (cancelled) return;
        setUniverseStatus('error');
        setUniverseErrorMsg('Symbol directory unavailable. Cannot verify instruments.');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const tradableSymbols = new Set(universe);

  const selected = watchlists.find((item) => item.watchlist_id === selectedId) ?? null;
  const symbols = selected ? selected.items.map((item) => item.symbol) : [];

  const replaceWatchlist = (updated: Watchlist) => {
    setWatchlists((prev) =>
      prev.map((item) => (item.watchlist_id === updated.watchlist_id ? updated : item))
    );
    emitWatchlistsChanged();
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
        emitWatchlistsChanged();
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
        emitWatchlistsChanged();
      })
      .catch(() => setErrorMsg('Unable to delete watchlist.'))
      .finally(() => setMutating(false));
  };

  const closeSuggestions = () => {
    setSuggestOpen(false);
    setHighlight(-1);
  };

  const addSymbol = (candidate: string) => {
    if (!selected || mutating) return;
    if (universeStatus !== 'ready') {
      setErrorMsg('Symbol directory unavailable. Cannot verify this instrument.');
      return;
    }
    const symbol = resolveSourceSymbol(universe, candidate);
    if (!symbol) {
      setErrorMsg('Select an exact symbol from the connected source.');
      return;
    }
    setErrorMsg('');
    closeSuggestions();
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

  const handleAddSymbol = () => addSymbol(newSymbol);

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

  const moveSymbol = (symbol: string, direction: 'up' | 'down') => {
    if (!selected || mutating) return;
    const index = symbols.indexOf(symbol);
    const target = direction === 'up' ? index - 1 : index + 1;
    if (index === -1 || target < 0 || target >= symbols.length) return;
    const reordered = [...symbols];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    setMutating(true);
    void apiClients.watchlists
      .update(selected.watchlist_id, { symbols: reordered })
      .then((response) => replaceWatchlist(unwrapData(response)))
      .catch(() => setErrorMsg('Unable to reorder symbols.'))
      .finally(() => setMutating(false));
  };

  const toggleSortSymbol = () => {
    if (sortBySymbol === null) {
      setSortBySymbol('asc');
    } else if (sortBySymbol === 'asc') {
      setSortBySymbol('desc');
    } else {
      setSortBySymbol(null);
    }
  };

  const suggestions = suggestOpen
    ? filterSymbols(universe, newSymbol).filter((symbol) => !symbols.includes(symbol))
    : [];

  const handleSymbolKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (!suggestOpen) {
        setSuggestOpen(true);
        return;
      }
      setHighlight((prev) => (suggestions.length === 0 ? -1 : (prev + 1) % suggestions.length));
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlight((prev) =>
        suggestions.length === 0 ? -1 : prev <= 0 ? suggestions.length - 1 : prev - 1
      );
      return;
    }
    if (event.key === 'Escape') {
      closeSuggestions();
      return;
    }
    if (event.key === 'Tab' && suggestions.length > 0) {
      event.preventDefault();
      setNewSymbol(
        highlight >= 0 && suggestions[highlight]
          ? suggestions[highlight]
          : suggestions[0]
      );
      closeSuggestions();
      return;
    }
    if (event.key === 'Enter') {
      // A highlighted suggestion wins over the raw text, so completing and
      // committing is one keystroke rather than two.
      addSymbol(highlight >= 0 && suggestions[highlight] ? suggestions[highlight] : newSymbol);
    }
  };

  const handleReorderList = (direction: 'up' | 'down') => {
    if (!selected || mutating) return;
    const index = watchlists.findIndex((w) => w.watchlist_id === selected.watchlist_id);
    const target = direction === 'up' ? index - 1 : index + 1;
    if (index === -1 || target < 0 || target >= watchlists.length) return;
    setMutating(true);
    void apiClients.watchlists
      .update(selected.watchlist_id, { sort_order: target })
      .then((response) => replaceWatchlist(unwrapData(response)))
      .catch(() => setErrorMsg('Unable to reorder watchlist.'))
      .finally(() => setMutating(false));
  };

  const displaySymbols =
    sortBySymbol === null
      ? symbols
      : [...symbols].sort((a, b) =>
          sortBySymbol === 'asc' ? a.localeCompare(b) : b.localeCompare(a)
        );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', backgroundColor: 'var(--cme-navy-dark, #0b1426)', color: 'var(--text-primary, #e2e8f0)', fontFamily: 'var(--font-sans, inherit)' }}>
      {/* Top Header Controls */}
      <div style={{ padding: '12px 16px', background: 'var(--cme-navy-surface, #132238)', borderBottom: '1px solid var(--cme-navy-border, #1e3a5f)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: '#ffffff', letterSpacing: '0.02em', display: 'flex', alignItems: 'center', gap: '6px' }}>
            NEW WATCHLIST
          </h2>
          <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted, #718294)' }}>
            WATCHLIST:
          </span>
          {!renaming && (
            <select
              className="form-select"
              aria-label="Select watchlist"
              value={selectedId ?? ''}
              onChange={(e) => setSelectedId(e.target.value)}
              style={{ padding: '4px 8px', fontSize: '12px', minWidth: '130px' }}
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
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <input
                className="form-select"
                autoFocus
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleRename();
                  if (e.key === 'Escape') setRenaming(false);
                }}
                style={{ padding: '3px 6px', fontSize: '12px', width: '130px' }}
              />
              <button className="btn-cme btn-primary btn-sm" onClick={handleRename} disabled={mutating}>
                Save
              </button>
            </div>
          )}
          {selected && !renaming && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                className="btn-cme btn-outline btn-sm"
                title="Rename watchlist"
                style={{ padding: '3px 6px' }}
                onClick={() => {
                  setRenameValue(selected.name);
                  setRenaming(true);
                }}
              >
                <Pencil size={13} />
              </button>
              <button
                className="btn-cme btn-outline btn-sm"
                title="Move watchlist up"
                aria-label="Move watchlist up"
                style={{ padding: '3px 6px' }}
                disabled={mutating || watchlists.findIndex((w) => w.watchlist_id === selected.watchlist_id) === 0}
                onClick={() => handleReorderList('up')}
              >
                <ArrowUp size={13} />
              </button>
              <button
                className="btn-cme btn-outline btn-sm"
                title="Move watchlist down"
                aria-label="Move watchlist down"
                style={{ padding: '3px 6px' }}
                disabled={mutating || watchlists.findIndex((w) => w.watchlist_id === selected.watchlist_id) === watchlists.length - 1}
                onClick={() => handleReorderList('down')}
              >
                <ArrowDown size={13} />
              </button>
              <button
                className="btn-cme btn-outline btn-sm"
                title={selected.is_default ? 'Already the default' : 'Set as default'}
                style={{ padding: '3px 6px', opacity: selected.is_default ? 0.4 : 1 }}
                disabled={selected.is_default || mutating}
                onClick={handleSetDefault}
              >
                <Star size={13} />
              </button>
              <button
                className="btn-cme btn-outline btn-sm"
                title={selected.is_default ? 'Cannot delete the default watchlist' : 'Delete watchlist'}
                style={{ padding: '3px 6px', opacity: selected.is_default ? 0.4 : 1 }}
                disabled={selected.is_default || mutating}
                onClick={handleDelete}
              >
                <Trash2 size={13} />
              </button>
            </div>
          )}
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          {selected && (
            <>
              <div style={{ position: 'relative' }}>
                <input
                  className="form-select"
                  placeholder="Add symbol…"
                  aria-label="Add symbol"
                  role="combobox"
                  aria-expanded={suggestions.length > 0}
                  aria-controls={`${suggestionIdPrefix.current}-listbox`}
                  aria-autocomplete="list"
                  aria-activedescendant={
                    highlight >= 0 ? `${suggestionIdPrefix.current}-${highlight}` : undefined
                  }
                  autoComplete="off"
                  value={newSymbol}
                  title={
                    universeStatus === 'ready'
                      ? `${universe.length} instruments available from the connected source`
                      : universeStatus === 'error'
                        ? 'Instrument universe unavailable'
                        : 'Loading the instrument universe…'
                  }
                  onChange={(e) => {
                    setNewSymbol(e.target.value);
                    setSuggestOpen(true);
                    setHighlight(-1);
                  }}
                  onFocus={() => setSuggestOpen(true)}
                  onBlur={() => window.setTimeout(closeSuggestions, 0)}
                  onKeyDown={handleSymbolKeyDown}
                  style={{ padding: '3px 6px', fontSize: '11px', width: '100px' }}
                />
                {suggestions.length > 0 && (
                  <ul
                    id={`${suggestionIdPrefix.current}-listbox`}
                    role="listbox"
                    aria-label="Symbol suggestions"
                    style={{
                      position: 'absolute',
                      top: 'calc(100% + 2px)',
                      left: 0,
                      zIndex: 30,
                      margin: 0,
                      padding: '2px',
                      listStyle: 'none',
                      minWidth: '150px',
                      maxHeight: '220px',
                      overflowY: 'auto',
                      background: 'var(--cme-navy-surface, #132238)',
                      border: '1px solid var(--cme-navy-border, #1e3a5f)',
                      borderRadius: '4px',
                      boxShadow: '0 6px 18px rgba(0, 0, 0, 0.45)',
                    }}
                  >
                    {suggestions.map((symbol, index) => (
                      <li
                        key={symbol}
                        id={`${suggestionIdPrefix.current}-${index}`}
                        role="option"
                        aria-selected={index === highlight}
                        // mousedown, not click: blur would close the list first.
                        onMouseDown={(e) => {
                          e.preventDefault();
                          addSymbol(symbol);
                        }}
                        onMouseEnter={() => setHighlight(index)}
                        style={{
                          padding: '4px 8px',
                          fontSize: '11px',
                          fontWeight: 600,
                          cursor: 'pointer',
                          borderRadius: '3px',
                          color:
                            index === highlight
                              ? '#ffffff'
                              : 'var(--text-primary, #e2e8f0)',
                          backgroundColor:
                            index === highlight ? 'rgba(0, 163, 255, 0.18)' : 'transparent',
                        }}
                      >
                        {symbol}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <button className="btn-cme btn-outline btn-sm" onClick={handleAddSymbol} disabled={mutating || universeStatus !== 'ready'} style={{ fontSize: '11px' }}>
                <Plus size={13} /> ADD
              </button>
            </>
          )}
          {!creating && (
            <button className="btn-cme btn-primary btn-sm" onClick={() => setCreating(true)} style={{ fontSize: '11px', fontWeight: 600 }}>
              <Plus size={13} /> CREATE NEW
            </button>
          )}
          {creating && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
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
                style={{ padding: '3px 6px', fontSize: '11px', width: '130px' }}
              />
              <button className="btn-cme btn-primary btn-sm" onClick={handleCreate} disabled={mutating}>
                Save
              </button>
            </div>
          )}
        </div>
      </div>

      {(errorMsg ||
        (status === 'ready' && universeStatus === 'error' && universeErrorMsg)) && (
        <div role="alert" style={{ padding: '6px 16px', color: 'var(--financial-negative, #ff4975)', fontSize: '12px', backgroundColor: 'rgba(255, 73, 117, 0.1)', borderBottom: '1px solid rgba(255, 73, 117, 0.2)' }}>
          {errorMsg ||
            (status === 'ready' && universeStatus === 'error' ? universeErrorMsg : '')}
        </div>
      )}
      {/* Main Content Area */}
      <div style={{ flex: 1, overflow: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '20px' }}>

        {/* SECTION 1: Your Watchlists */}
        <div style={{ background: 'var(--cme-navy-surface, #132238)', border: '1px solid var(--cme-navy-border, #1e3a5f)', borderRadius: '6px', padding: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '6px', color: '#ffffff' }}>
              Your Watchlist <Info size={13} style={{ color: 'var(--text-muted, #718294)', cursor: 'pointer' }} />
            </h3>
          </div>

          {status === 'loading' && (
            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted, #718294)', fontSize: '12px' }}>
              Loading watchlists…
            </div>
          )}
          {status === 'error' && (
            <div style={{ padding: '16px', textAlign: 'center', color: 'var(--financial-negative, #ff4975)', fontSize: '12px' }}>
              {errorMsg}
            </div>
          )}
          {status === 'unavailable' && (
            <div role="alert" style={{ padding: '16px', textAlign: 'center', color: 'var(--financial-negative, #ff4975)', fontSize: '12px' }}>
              {errorMsg} No watchlists are shown until the gateway returns.
            </div>
          )}
          {status === 'ready' && watchlists.length === 0 && (
            <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted, #718294)', border: '1px dashed var(--cme-navy-border, #1e3a5f)', borderRadius: '4px' }}>
              <p style={{ margin: '0 0 12px 0', fontSize: '13px' }}>You currently have no Watchlists created</p>
              <button className="btn-cme btn-primary btn-sm" onClick={() => setCreating(true)}>
                CREATE NEW
              </button>
            </div>
          )}

          {status === 'ready' && watchlists.length > 0 && selected && (
            <div>
              {/* Watchlists Tab / Pills */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px', borderBottom: '1px solid var(--cme-navy-border, #1e3a5f)', paddingBottom: '10px' }}>
                {watchlists.map((wl) => {
                  const isSelected = wl.watchlist_id === selectedId;
                  return (
                    <button
                      key={wl.watchlist_id}
                      onClick={() => setSelectedId(wl.watchlist_id)}
                      style={{
                        padding: '6px 12px',
                        fontSize: '12px',
                        fontWeight: isSelected ? 700 : 500,
                        borderRadius: '4px',
                        border: isSelected ? '1px solid var(--cme-blue-bright, #00a3ff)' : '1px solid var(--cme-navy-border, #1e3a5f)',
                        backgroundColor: isSelected ? 'rgba(0, 163, 255, 0.15)' : 'transparent',
                        color: isSelected ? '#ffffff' : 'var(--text-muted, #718294)',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        transition: 'all 0.15s ease',
                      }}
                    >
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', border: isSelected ? '2px solid var(--cme-blue-bright, #00a3ff)' : '1px solid var(--text-muted)', backgroundColor: isSelected ? 'var(--cme-blue-bright, #00a3ff)' : 'transparent' }} />
                      {wl.name}
                      {wl.is_default && <span style={{ fontSize: '10px', color: '#f0b429' }}>★</span>}
                      <span style={{ fontSize: '10px', opacity: 0.7, backgroundColor: 'rgba(255, 255, 255, 0.08)', borderRadius: '8px', padding: '1px 5px' }}>
                        {wl.items.length}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Symbol Cards / List */}
              {displaySymbols.length === 0 ? (
                <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted, #718294)', fontSize: '12px' }}>
                  No symbols in this watchlist. Add one using the controls above.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {/* Table structure preserved for semantic sorting/testing assertions (FR-UI-043/044) */}
                  <table className="cme-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead>
                      <tr>
                        <th style={{ padding: '4px 8px', textAlign: 'left' }}>
                          <button
                            className="btn-cme btn-outline btn-sm"
                            onClick={toggleSortSymbol}
                            style={{ padding: '2px 6px', fontSize: '10px', display: 'inline-flex', alignItems: 'center', gap: '3px' }}
                            title="Sort by Symbol"
                          >
                            Symbol
                            {sortBySymbol && (sortBySymbol === 'asc' ? <ChevronUp size={11} /> : <ChevronDown size={11} />)}
                          </button>
                        </th>
                        <th style={{ padding: '4px 8px', textAlign: 'left' }}>Class</th>
                        <th style={{ padding: '4px 8px', textAlign: 'right' }}>Management</th>
                      </tr>
                    </thead>
                    <tbody>
                      {displaySymbols.map((symbol) => {
                        const notTradable =
                          universeStatus === 'ready' && !tradableSymbols.has(symbol);
                        const assetClass =
                          selected.items.find((item) => item.symbol === symbol)?.asset_class ||
                          'Unavailable';
                        const index = symbols.indexOf(symbol);
                        const reorderDisabled = mutating || sortBySymbol !== null;

                        return (
                          <tr key={symbol} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                            <td style={{ padding: '8px 10px', fontWeight: 600, color: 'var(--cme-blue-bright, #00a3ff)', fontSize: '13px' }}>
                              {symbol}
                              {notTradable && (
                                <span
                                  style={{ marginLeft: '8px', fontSize: '9px', fontWeight: 700, color: 'var(--cme-warning-yellow, #f0b429)', border: '1px solid var(--cme-warning-yellow, #f0b429)', borderRadius: '3px', padding: '1px 4px' }}
                                  title="Not found in the tradable instrument directory"
                                >
                                  NOT TRADABLE
                                </span>
                              )}
                            </td>
                            <td style={{ padding: '8px 10px', fontSize: '12px' }}>
                              {assetClass}
                            </td>
                            <td style={{ padding: '8px 10px', textAlign: 'right' }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                                <button
                                  className="btn-cme btn-outline btn-sm"
                                  style={{ padding: '2px 6px' }}
                                  title="Move up"
                                  disabled={reorderDisabled || index <= 0}
                                  onClick={() => moveSymbol(symbol, 'up')}
                                >
                                  <ArrowUp size={12} />
                                </button>
                                <button
                                  className="btn-cme btn-outline btn-sm"
                                  style={{ padding: '2px 6px' }}
                                  title="Move down"
                                  disabled={reorderDisabled || index >= symbols.length - 1}
                                  onClick={() => moveSymbol(symbol, 'down')}
                                >
                                  <ArrowDown size={12} />
                                </button>
                                <button
                                  className="btn-cme btn-outline btn-sm"
                                  title="Remove from watchlist"
                                  style={{ padding: '2px 6px' }}
                                  onClick={() => handleRemoveSymbol(symbol)}
                                >
                                  <X size={13} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer Controls */}
      <div style={{ padding: '12px 16px', background: 'var(--cme-navy-surface, #132238)', borderTop: '1px solid var(--cme-navy-border, #1e3a5f)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '10px' }}>
        <button className="btn-cme btn-outline btn-sm" style={{ padding: '6px 14px', fontSize: '11px', fontWeight: 600 }}>
          SAVE A COPY
        </button>
        <button
          className="btn-cme btn-primary btn-sm"
          onClick={() => addWidgetToWorkspace('watchlist', selected?.name ?? 'Watchlist')}
          style={{ padding: '6px 14px', fontSize: '11px', fontWeight: 600 }}
        >
          ADD TO WORKSPACE
        </button>
      </div>
    </div>
  );
};
