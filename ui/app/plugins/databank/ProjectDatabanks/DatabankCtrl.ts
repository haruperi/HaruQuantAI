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

/** Mock cross-check rule used by Tools > Select > Passed/Failed. */
export function strategyPassesMockChecks(netProfit: number, trades: number, maxDrawdown: number): boolean {
  return netProfit > 0 && trades >= 80 && maxDrawdown < 30000;
}

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

  const current = store.strategies.find(s => s.id === store.selectedStrategyId) || selectedInBank[0];
  const activeView = databankStore.getActiveView();

  const deferred = (label: string) =>
    store.notify(`${label} deferred — UI prototype (no engine connected)`);

  const handleAction = (action: ToolbarAction, menuItem?: string) => {
    switch (action) {
      case 'load':
        openMockLoad(() => setDialog({ kind: 'load' }));
        break;
      case 'save':
        setDialog({ kind: 'save', format: menuItem || '' });
        break;
      case 'delete':
        requestDeleteConfirmation(store.selectedRows, store.notify, () => setDialog({ kind: 'delete' }));
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

  return { store, navigateTo, databankStore, dialog, setDialog, isManageViewsOpen, setIsManageViewsOpen, isFilterCorrelationOpen, setIsFilterCorrelationOpen, isCompareOpen, setIsCompareOpen, bank, bankStrategies, selectedInBank, current, activeView, deferred, handleAction, bankTooltip };
}
