import { useMemo, useState } from 'react';
import { useAppStore } from '../../../app/store';
import { useAppNavigate } from '../../../app/router';
import { DatabankToolbar, type ToolbarAction } from './DatabankToolbar';
import {
  LoadRecordsDialog,
  RemovingReportsConfirm,
  RenameStrategiesDialog,
  RetestDialog,
  SaveRecordsDialog,
  SetNoteDialog,
} from './DatabankDialogs';
import { StrategyTable } from './StrategyTable';
import { useDatabankStore } from './databankStore';
import { ManageViewsDialog } from './ManageViewsDialog';
import { FilterByCorrelationModal } from './FilterByCorrelationModal';
import { CompareStrategiesModal } from './CompareStrategiesModal';

/**
 * SQX-parity databanks panel content (donor evidence SQX144-EV-000028..031):
 * light quant-tabs bank strip, donor toolbar with menu trees, centered
 * Records counter, Default - Main data grid, and the donor dialog set.
 * All data is fixture demo data; engine/export actions show explicit
 * deferred toasts and never fake success.
 */

type DialogState =
  | { kind: 'none' }
  | { kind: 'load' }
  | { kind: 'delete' }
  | { kind: 'clearAll' }
  | { kind: 'retest' }
  | { kind: 'rename' }
  | { kind: 'save'; format: string }
  | { kind: 'setNote' };

/** Mock cross-check rule used by Tools > Select > Passed/Failed. */
export function strategyPassesMockChecks(netProfit: number, trades: number, maxDrawdown: number): boolean {
  return netProfit > 0 && trades >= 80 && maxDrawdown < 30000;
}

export function DatabankPanel() {
  const store = useAppStore();
  const { navigateTo } = useAppNavigate();
  const databankStore = useDatabankStore();

  const [dialog, setDialog] = useState<DialogState>({ kind: 'none' });
  const [isManageViewsOpen, setIsManageViewsOpen] = useState(false);
  const [isFilterCorrelationOpen, setIsFilterCorrelationOpen] = useState(false);
  const [isCompareOpen, setIsCompareOpen] = useState(false);

  const bank = store.databanks.find(b => b.id === store.selectedBankId) || store.databanks[0];

  const bankStrategies = useMemo(
    () => store.strategies.filter(s => bank?.strategyIds.includes(s.id)),
    [store.strategies, bank]
  );

  const selectedInBank = useMemo(
    () => bankStrategies.filter(s => store.selectedRows.includes(s.id)),
    [bankStrategies, store.selectedRows]
  );

  const current = store.strategies.find(s => s.id === store.selectedStrategyId) || selectedInBank[0];
  const activeView = databankStore.getActiveView();

  const deferred = (label: string) =>
    store.notify(`${label} deferred — UI prototype (no engine connected)`);

  const handleAction = (action: ToolbarAction, menuItem?: string) => {
    switch (action) {
      case 'load':
        setDialog({ kind: 'load' });
        break;
      case 'save':
        setDialog({ kind: 'save', format: menuItem || '' });
        break;
      case 'delete':
        if (!store.selectedRows.length) {
          store.notify('You have to select at least one strategy to delete');
          break;
        }
        setDialog({ kind: 'delete' });
        break;
      case 'clearAll':
        setDialog({ kind: 'clearAll' });
        break;
      case 'retest':
        if (!store.selectedRows.length) {
          store.notify('You have to select at least one strategy');
          break;
        }
        setDialog({ kind: 'retest' });
        break;
      case 'rename':
        if (!selectedInBank.length) {
          store.notify('You have to select at least one strategy');
          break;
        }
        setDialog({ kind: 'rename' });
        break;
      case 'filterByCorrelation':
        setIsFilterCorrelationOpen(true);
        break;
      case 'portfolio':
        deferred(`Portfolio: ${menuItem}`);
        break;
      case 'tools':
        handleToolsItem(menuItem || '');
        break;
      case 'refresh':
        store.notify('Databank reloaded');
        break;
      case 'manageViews':
        setIsManageViewsOpen(true);
        break;
    }
  };

  const handleToolsItem = (item: string) => {
    if (item === 'Select:Passed' || item === 'Select:Failed') {
      const passed = item === 'Select:Passed';
      const ids = bankStrategies
        .filter(s => strategyPassesMockChecks(s.metrics.netProfit, s.metrics.trades, s.metrics.maxDrawdown) === passed)
        .map(s => s.id);
      store.setRows(ids);
      store.notify(`${passed ? 'Passed' : 'Failed'} strategies selected (${ids.length})`);
      return;
    }
    if (item === 'Set note') {
      if (!selectedInBank.length) {
        store.notify('You have to select at least one strategy');
        return;
      }
      setDialog({ kind: 'setNote' });
      return;
    }
    if (item === 'Compare') {
      setIsCompareOpen(true);
      return;
    }
    deferred(`Tools: ${item}`);
  };

  const bankTooltip = (name: string) =>
    name === 'Existing portfolio'
      ? 'Fit strategy to existing portfolio. Learn more'
      : undefined;

  return (
    <div className="sqx-panel">
      <div className="sqx-tabs" role="tablist" aria-label="Databanks">
        {store.databanks.map(b => (
          <button
            type="button"
            key={b.id}
            role="tab"
            aria-selected={b.id === bank?.id}
            className={`sqx-tab${b.id === bank?.id ? ' active' : ''}`}
            title={bankTooltip(b.name)}
            onClick={() => store.setBank(b.id)}
          >
            {b.name}
            {b.name === 'Existing portfolio' && <span className="sqx-tab-help" aria-hidden="true">ⓘ</span>}
          </button>
        ))}
      </div>

      <DatabankToolbar
        records={bankStrategies.length}
        selectedCount={selectedInBank.length}
        viewNames={databankStore.views.map(v => v.name)}
        activeView={activeView.name}
        onViewChange={name => {
          const view = databankStore.views.find(v => v.name === name);
          if (view) databankStore.setActiveView(view.id);
        }}
        onAction={handleAction}
      />

      <div className="sqx-grid-area">
        {bankStrategies.length === 0 ? (
          <div className="sqx-empty">No results in databank.</div>
        ) : (
          <StrategyTable
            data={bankStrategies}
            selectedId={store.selectedStrategyId}
            selectedRows={store.selectedRows}
            onSelect={store.selectStrategy}
            onRows={store.setRows}
            onActivate={id => {
              if (['builder', 'retester', 'optimizer', 'portfolio'].includes(store.module)) {
                // Commit both route fields together so selection cannot restore a stale tab.
                navigateTo(store.module, { tab: 'results', strategyId: id });
              } else {
                store.selectStrategy(id);
              }
            }}
            activeView={activeView}
          />
        )}
      </div>

      {dialog.kind === 'load' && (
        <LoadRecordsDialog
          onFinished={() => {
            setDialog({ kind: 'none' });
            store.notify('Databank reloaded');
          }}
        />
      )}

      {dialog.kind === 'delete' && (
        <RemovingReportsConfirm
          message={`Are you sure you want to remove selected reports (${store.selectedRows.length})?`}
          onConfirm={() => store.deleteStrategies(store.selectedRows)}
          onClose={() => setDialog({ kind: 'none' })}
        />
      )}

      {dialog.kind === 'clearAll' && bank && (
        <RemovingReportsConfirm
          message="Are you sure you want to clear all the reports from this databank?"
          onConfirm={() => {
            store.deleteStrategies(bank.strategyIds);
            store.notify('Databank cleared');
          }}
          onClose={() => setDialog({ kind: 'none' })}
        />
      )}

      {dialog.kind === 'retest' && (
        <RetestDialog
          onMove={remove => {
            if (remove) store.deleteStrategies(store.selectedRows);
            store.notify(
              remove
                ? `Moved ${store.selectedRows.length} strategies to Retester (demo)`
                : `Copied ${store.selectedRows.length} strategies to Retester (demo)`
            );
          }}
          onClose={() => setDialog({ kind: 'none' })}
        />
      )}

      {dialog.kind === 'save' && (
        <SaveRecordsDialog
          format={dialog.format}
          onSave={() => deferred(`Save: ${dialog.format}`)}
          onClose={() => setDialog({ kind: 'none' })}
        />
      )}

      {dialog.kind === 'rename' && (
        <RenameStrategiesDialog
          count={selectedInBank.length}
          currentName={selectedInBank[0]?.name ?? ''}
          onRename={({ name, prefix, postfix }) => {
            for (const s of selectedInBank) {
              const next = name ?? `${prefix ?? ''}${s.name}${postfix ?? ''}`;
              store.renameStrategy(s.id, next, s.note || '');
            }
            store.notify(`Renamed ${selectedInBank.length} strateg${selectedInBank.length === 1 ? 'y' : 'ies'}`);
          }}
          onClose={() => setDialog({ kind: 'none' })}
        />
      )}

      {dialog.kind === 'setNote' && (
        <SetNoteDialog
          currentNote={selectedInBank[0]?.note ?? ''}
          onSetNote={note => {
            for (const s of selectedInBank) store.renameStrategy(s.id, s.name, note);
            store.notify(`Note set on ${selectedInBank.length} strateg${selectedInBank.length === 1 ? 'y' : 'ies'}`);
          }}
          onClose={() => setDialog({ kind: 'none' })}
        />
      )}

      <div className="sqx-dialog-scope">
        <ManageViewsDialog
          isOpen={isManageViewsOpen}
          onClose={() => setIsManageViewsOpen(false)}
        />
        <FilterByCorrelationModal
          isOpen={isFilterCorrelationOpen}
          onClose={() => setIsFilterCorrelationOpen(false)}
          strategies={bankStrategies}
          onApplyFilter={(keepIds, removedIds) => {
            if (removedIds.length === 0) return;
            store.deleteStrategies(removedIds);
            store.notify(
              `Correlation filter applied: removed ${removedIds.length} correlated strategies (kept ${keepIds.length})`
            );
          }}
        />
        <CompareStrategiesModal
          isOpen={isCompareOpen}
          onClose={() => setIsCompareOpen(false)}
          strategies={bankStrategies}
          initialStrategyId1={store.selectedRows[0] || store.selectedStrategyId}
          initialStrategyId2={store.selectedRows[1] || undefined}
        />
      </div>
    </div>
  );
}
