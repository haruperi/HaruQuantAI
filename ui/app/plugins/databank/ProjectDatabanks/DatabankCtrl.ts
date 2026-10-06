import { openSimulatedSave } from '../ResultsDatabankActions/save/module';
import { requestCompareStrategies } from '../ResultsDatabankActions/tools/compareStrategies/module';
import { handleEditItem } from '../ResultsDatabankActions/tools/edit/module';
import { requestRunCa } from '../ResultsDatabankActions/tools/runCa/module';
import { handleSelectItem, requestSetNote } from '../ResultsDatabankActions/tools/module';
export { strategyPassesMockChecks } from '../ResultsDatabankActions/tools/module';
import { getCurrentDatabankStrategy, requestClearAllConfirmation, refreshDatabank } from '../ResultsDatabankActions/module';
import { requestDeleteConfirmation } from '../ResultsDatabankActions/delete/module';
import { openMockLoad } from '../ResultsDatabankActions/load/module';
import { useMemo, useState } from 'react';
import { useAppNavigate } from '../../../host/router';
import type { ToolbarAction } from './DatabankToolbar';
import { useDatabankContext } from './DatabankService';

type DialogState =
  | { kind: 'none' }
  | { kind: 'load' }
  | { kind: 'delete' }
  | { kind: 'clearAll' }
  | { kind: 'retest' }
  | { kind: 'rename' }
  | { kind: 'save'; format: string }
  | { kind: 'setNote' };

export function useDatabankPanel() {
  const { store, databankStore } = useDatabankContext();
  const { navigateTo } = useAppNavigate();

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

  const current = getCurrentDatabankStrategy(store.strategies, store.selectedStrategyId, selectedInBank);
  const activeView = databankStore.getActiveView();

  const deferred = (label: string) =>
    store.notify(`${label} deferred — UI prototype (no engine connected)`);

  const handleAction = (action: ToolbarAction, menuItem?: string) => {
    switch (action) {
      case 'load':
        openMockLoad(() => setDialog({ kind: 'load' }));
        break;
      case 'save':
        openSimulatedSave(menuItem || '', format => setDialog({ kind: 'save', format }));
        break;
      case 'delete':
        requestDeleteConfirmation(store.selectedRows, store.notify, () => setDialog({ kind: 'delete' }));
        break;
      case 'clearAll':
        requestClearAllConfirmation(() => setDialog({ kind: 'clearAll' }));
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
        refreshDatabank(store.notify);
        break;
      case 'manageViews':
        setIsManageViewsOpen(true);
        break;
    }
  };

  const handleToolsItem = (item: string) => {
    if (handleSelectItem(item, bankStrategies, store.setRows, store.notify)) return;
    if (item === 'Set note') {
      requestSetNote(selectedInBank.length, store.notify, () => setDialog({ kind: 'setNote' }));
      return;
    }
    if (item === 'Compare') {
      requestCompareStrategies(() => setIsCompareOpen(true));
      return;
    }
    if (handleEditItem(item, deferred)) return;
    if (item === 'Run CA') { requestRunCa(deferred); return; }
    deferred(`Tools: ${item}`);
  };

  const bankTooltip = (name: string) =>
    name === 'Existing portfolio'
      ? 'Fit strategy to existing portfolio. Learn more'
      : undefined;

  return { store, navigateTo, databankStore, dialog, setDialog, isManageViewsOpen, setIsManageViewsOpen, isFilterCorrelationOpen, setIsFilterCorrelationOpen, isCompareOpen, setIsCompareOpen, bank, bankStrategies, selectedInBank, current, activeView, deferred, handleAction, bankTooltip };
}
