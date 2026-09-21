import React, { useMemo, useState } from 'react';
import {
  Copy,
  Download,
  Filter,
  FolderInput,
  MoreHorizontal,
  Search,
  Settings2,
  Trash2,
  SlidersHorizontal,
  GitCompare,
} from 'lucide-react';
import { useAppStore } from '../../../app/store';
import { Button, IconButton, Modal, TextInput } from '../../../components/ui';
import { StrategyTable } from './StrategyTable';
import { useDatabankStore } from './databankStore';
import { ManageViewsDialog } from './ManageViewsDialog';
import { FilterByCorrelationModal } from './FilterByCorrelationModal';
import { CompareStrategiesModal } from './CompareStrategiesModal';

export function DatabankPanel() {
  const store = useAppStore();
  const databankStore = useDatabankStore();

  const [query, setQuery] = useState('');
  const [dialog, setDialog] = useState<'move' | 'rename' | 'delete' | null>(null);
  const [isManageViewsOpen, setIsManageViewsOpen] = useState(false);
  const [isFilterCorrelationOpen, setIsFilterCorrelationOpen] = useState(false);
  const [isCompareStrategiesOpen, setIsCompareStrategiesOpen] = useState(false);

  const [target, setTarget] = useState('retest');
  const [copy, setCopy] = useState(true);
  const [name, setName] = useState('');
  const [note, setNote] = useState('');

  const bank = store.databanks.find(b => b.id === store.selectedBankId) || store.databanks[0];
  const activeView = databankStore.getActiveView();

  const bankStrategies = useMemo(() => {
    return store.strategies.filter(s => bank?.strategyIds.includes(s.id));
  }, [store.strategies, bank]);

  const data = useMemo(() => {
    return bankStrategies.filter(s =>
      `${s.name} ${s.symbol} ${s.timeframe}`.toLowerCase().includes(query.toLowerCase())
    );
  }, [bankStrategies, query]);

  const current = store.strategies.find(s => s.id === store.selectedStrategyId);

  const openRename = () => {
    if (!current) return;
    setName(current.name);
    setNote(current.note || '');
    setDialog('rename');
  };

  const handleApplyCorrelationFilter = (
    keepIds: string[],
    removedIds: string[]
  ) => {
    if (removedIds.length === 0) return;
    store.deleteStrategies(removedIds);
    store.notify(
      `Correlation filter applied: removed ${removedIds.length} correlated strategies (kept ${keepIds.length})`
    );
  };

  return (
    <div className="databank-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* SQX Databank Section Header */}
      <div
        className="databank-sqx-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '6px 12px',
          background: 'var(--surface-color, #161b22)',
          borderBottom: '1px solid var(--border-color, #2d333b)',
          fontSize: 12,
          fontWeight: 600,
          color: 'var(--text-color, #c9d1d9)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: '#58a6ff', letterSpacing: '0.5px' }}>DATABANKS:</span>
          <span>{store.databanks.length}</span>
          <span style={{ color: 'var(--border-color, #30363d)' }}>|</span>
          <span style={{ color: '#3fb950', letterSpacing: '0.5px' }}>TOTAL STRATEGIES:</span>
          <span>{store.strategies.length}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted, #8b949e)' }}>Active Bank:</span>
          <span style={{ color: '#f0883e', fontWeight: 600 }}>{bank?.name}</span>
          <span style={{ fontSize: 11, color: '#8b949e' }}>({bankStrategies.length})</span>
        </div>
      </div>

      {/* Databank Tabs */}
      <div className="bank-tabs">
        {store.databanks.map(b => (
          <button
            key={b.id}
            className={b.id === bank.id ? 'active' : ''}
            onClick={() => store.setBank(b.id)}
          >
            {b.name}
            <small>{b.strategyIds.length}</small>
          </button>
        ))}
        <button
          className="add-bank"
          title="Add new databank"
          onClick={() => store.notify('New databank created')}
        >
          ＋
        </button>
      </div>

      {/* Toolbar with Views and Operations */}
      <div className="bank-toolbar" style={{ flexWrap: 'wrap', gap: 6, padding: '6px 8px' }}>
        {/* Search */}
        <div className="search">
          <Search size={14} />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search strategies (name, symbol, TF)..."
          />
        </div>

        {/* View Selector + Gear Button (Manage Views) */}
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted, #8b949e)' }}>View:</span>
          <select
            className="text-input"
            style={{ width: 170, height: 26, fontSize: 11, padding: '2px 6px' }}
            value={databankStore.activeViewId}
            onChange={e => databankStore.setActiveView(e.target.value)}
          >
            {databankStore.views.map(v => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
          <IconButton
            title="Manage views & columns (SQX Views Dialog)"
            onClick={() => setIsManageViewsOpen(true)}
          >
            <SlidersHorizontal size={14} />
          </IconButton>
        </div>

        <div style={{ width: 1, height: 20, background: 'var(--border-color, #2d333b)', margin: '0 2px' }} />

        {/* Move / Rename */}
        <Button
          disabled={!store.selectedRows.length}
          onClick={() => setDialog('move')}
          style={{ padding: '3px 8px', fontSize: 11 }}
        >
          <FolderInput size={13} /> Move / copy
        </Button>

        <Button
          disabled={!current}
          onClick={openRename}
          style={{ padding: '3px 8px', fontSize: 11 }}
        >
          <Settings2 size={13} /> Rename & notes
        </Button>

        {/* Filter by correlation modal button */}
        <Button
          title="Filter out correlated strategies"
          onClick={() => setIsFilterCorrelationOpen(true)}
          style={{ padding: '3px 8px', fontSize: 11 }}
        >
          <Filter size={13} /> Filter by correlation
        </Button>

        {/* Compare strategies modal button */}
        <Button
          title="Compare 2 strategies side-by-side"
          disabled={bankStrategies.length < 2}
          onClick={() => setIsCompareStrategiesOpen(true)}
          style={{ padding: '3px 8px', fontSize: 11 }}
        >
          <GitCompare size={13} /> Compare strategies
        </Button>

        {/* Action icons */}
        <IconButton
          title="Export selected"
          onClick={() =>
            store.notify(
              `${store.selectedRows.length || bankStrategies.length} strategy artifacts exported`
            )
          }
        >
          <Download size={14} />
        </IconButton>

        <IconButton
          title="Delete selected strategies"
          disabled={!store.selectedRows.length}
          onClick={() => setDialog('delete')}
        >
          <Trash2 size={14} />
        </IconButton>

        <IconButton title="More actions">
          <MoreHorizontal size={15} />
        </IconButton>

        <span className="row-count" style={{ marginLeft: 'auto', fontSize: 11 }}>
          {data.length} shown · {store.selectedRows.length} selected
        </span>
      </div>

      {/* Main Virtualized Dynamic Table */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <StrategyTable
          data={data}
          selectedId={store.selectedStrategyId}
          selectedRows={store.selectedRows}
          onSelect={store.selectStrategy}
          onRows={store.setRows}
          activeView={activeView}
        />
      </div>

      {/* Modals */}
      {dialog === 'move' && (
        <Modal
          title="Move or copy strategies"
          onClose={() => setDialog(null)}
          footer={
            <>
              <Button onClick={() => setDialog(null)}>Cancel</Button>
              <Button
                className="primary"
                onClick={() => {
                  store.moveStrategies(store.selectedRows, target, copy);
                  store.notify(
                    `${copy ? 'Copied' : 'Moved'} strategies to ${
                      store.databanks.find(b => b.id === target)?.name
                    }`
                  );
                  setDialog(null);
                }}
              >
                {copy ? <Copy size={14} /> : <FolderInput size={14} />} {copy ? 'Copy' : 'Move'}
              </Button>
            </>
          }
        >
          <p className="dialog-note">
            The selected {store.selectedRows.length} strategies will{' '}
            {copy ? 'remain in the source databank.' : 'be removed from the source databank.'}
          </p>
          <label className="field">
            <span>Target databank</span>
            <select
              className="text-input"
              value={target}
              onChange={e => setTarget(e.target.value)}
            >
              {store.databanks
                .filter(b => b.id !== bank.id)
                .map(b => (
                  <option value={b.id} key={b.id}>
                    {b.name}
                  </option>
                ))}
            </select>
          </label>
          <label className="check">
            <input type="radio" checked={copy} onChange={() => setCopy(true)} /> Copy strategies
          </label>
          <label className="check">
            <input type="radio" checked={!copy} onChange={() => setCopy(false)} /> Move strategies
          </label>
        </Modal>
      )}

      {dialog === 'rename' && current && (
        <Modal
          title="Strategy name and notes"
          onClose={() => setDialog(null)}
          footer={
            <>
              <Button onClick={() => setDialog(null)}>Cancel</Button>
              <Button
                className="primary"
                disabled={!name.trim()}
                onClick={() => {
                  store.renameStrategy(current.id, name.trim(), note);
                  setDialog(null);
                }}
              >
                Save
              </Button>
            </>
          }
        >
          <label className="field">
            <span>Name</span>
            <TextInput value={name} onChange={e => setName(e.target.value)} autoFocus />
          </label>
          <label className="field">
            <span>Notes</span>
            <textarea
              className="text-input textarea"
              value={note}
              onChange={e => setNote(e.target.value)}
            />
          </label>
        </Modal>
      )}

      {dialog === 'delete' && (
        <Modal
          title="Delete selected strategies?"
          onClose={() => setDialog(null)}
          footer={
            <>
              <Button onClick={() => setDialog(null)}>Cancel</Button>
              <Button
                className="danger"
                onClick={() => {
                  store.deleteStrategies(store.selectedRows);
                  setDialog(null);
                }}
              >
                Delete permanently
              </Button>
            </>
          }
        >
          <p>
            This removes {store.selectedRows.length} selected strategies from every databank. This
            action cannot be undone.
          </p>
        </Modal>
      )}

      {/* SQX Manage Views Dialog */}
      <ManageViewsDialog
        isOpen={isManageViewsOpen}
        onClose={() => setIsManageViewsOpen(false)}
      />

      {/* SQX Filter by Correlation Modal */}
      <FilterByCorrelationModal
        isOpen={isFilterCorrelationOpen}
        onClose={() => setIsFilterCorrelationOpen(false)}
        strategies={bankStrategies}
        onApplyFilter={handleApplyCorrelationFilter}
      />

      {/* SQX Compare Strategies Modal */}
      <CompareStrategiesModal
        isOpen={isCompareStrategiesOpen}
        onClose={() => setIsCompareStrategiesOpen(false)}
        strategies={bankStrategies}
        initialStrategyId1={store.selectedRows[0] || store.selectedStrategyId}
        initialStrategyId2={store.selectedRows[1] || undefined}
      />
    </div>
  );
}
