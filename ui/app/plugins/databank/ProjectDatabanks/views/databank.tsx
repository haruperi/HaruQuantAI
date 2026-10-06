import { RenameStrategiesDialog } from '../../DatabankRename/ui/module';
import { DatabankToolbar } from '../DatabankToolbar';
import {
  LoadRecordsDialog,
  RemovingReportsConfirm,
  RetestDialog,
  SaveRecordsDialog,
  SetNoteDialog,
} from '../DatabankDialogs';
import { StrategyTable } from '../StrategyTable';
import { ManageViewsDialog } from '../../ResultsDatabankViews/module';
import { FilterByCorrelationModal } from '../FilterByCorrelationModal';
import { CompareStrategiesModal } from '../CompareStrategiesModal';

import { useDatabankPanel } from '../DatabankCtrl';

/** Independently authored mock bank presentation; structural alignment only. */
export function DatabankPanel() {
  const { store, navigateTo, databankStore, dialog, setDialog, isManageViewsOpen, setIsManageViewsOpen, isFilterCorrelationOpen, setIsFilterCorrelationOpen, isCompareOpen, setIsCompareOpen, bank, bankStrategies, selectedInBank, current, activeView, deferred, handleAction, bankTooltip } = useDatabankPanel();
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
