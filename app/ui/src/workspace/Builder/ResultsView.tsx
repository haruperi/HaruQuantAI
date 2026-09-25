import { useState } from 'react';
import { Puzzle, TextCursor, Trash2 } from 'lucide-react';
import {
  builtInResultTabs,
  customAnalysisActions,
  defaultCustomAnalysisTabs,
  NO_RESULT_CHOSEN,
  orderResultTabs,
} from './results/resultsFixtures';
import { SqrDropdown } from './results/ResultsChrome';
import {
  DeleteAnalysisModal,
  NewAnalysisModal,
  RenameAnalysisModal,
} from './results/ResultsModals';
import { OverviewTab } from './results/tabs/OverviewTab';
import { TradeListTab } from './results/tabs/TradeListTab';
import { EquityChartTab } from './results/tabs/EquityChartTab';
import { SourceCodeTab } from './results/tabs/SourceCodeTab';
import {
  CustomAnalysisTab,
  ProfileChartTab,
  SpOverviewTab,
  StrategyConfigTab,
  TradeAnalysisTab,
} from './results/tabs/SmallTabs';

/**
 * Builder Results tab (FEAT-UI-BUILDER_RESULTS_TAB).
 *
 * Mirrors the donor RESULTS overlay app: info line, quant-tabs strip with
 * custom analysis tabs last, "+ New analysis" control, per-tab content and a
 * Reload link. The donor's page reload is adapted to a view-state reset.
 */
export function ResultsView() {
  const [activeId, setActiveId] = useState<string>('overview');
  const [customTabs, setCustomTabs] = useState<string[]>(defaultCustomAnalysisTabs);
  const [newOpen, setNewOpen] = useState(false);
  const [renameTarget, setRenameTarget] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);
  const [menuFor, setMenuFor] = useState<string | null>(null);
  const [resetKey, setResetKey] = useState(0);

  const tabs = orderResultTabs(builtInResultTabs, customTabs);
  const active = tabs.find(t => t.id === activeId) ?? tabs[0];

  const onReload = () => {
    setActiveId('overview');
    setMenuFor(null);
    setResetKey(k => k + 1);
  };

  const onCreate = (name: string) => {
    setCustomTabs(t => [...t, name]);
    setNewOpen(false);
    setActiveId(`custom:${name}`);
  };

  const onRename = (name: string) => {
    if (renameTarget == null) return;
    setCustomTabs(t => t.map(n => (n === renameTarget ? name : n)));
    if (activeId === `custom:${renameTarget}`) setActiveId(`custom:${name}`);
    setRenameTarget(null);
  };

  const onDelete = () => {
    if (deleteTarget == null) return;
    setCustomTabs(t => t.filter(n => n !== deleteTarget));
    if (activeId === `custom:${deleteTarget}`) setActiveId('overview');
    setDeleteTarget(null);
  };

  return (
    <div className="sqr-results" key={resetKey}>
      <div className="sqr-info-line">{NO_RESULT_CHOSEN}</div>
      <div className="sqr-tabs-header">
        {tabs.map(tab => {
          const isActive = tab.id === active.id;
          return (
            <div
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              className={`${isActive ? 'active' : ''}${tab.isCustom ? ' sqr-tab-custom' : ''}`}
              onClick={() => setActiveId(tab.id)}
            >
              {tab.isCustom && (
                <Puzzle size={11} className="sqr-custom-icon" aria-hidden="true" />
              )}
              {tab.title}
              {tab.isCustom && (
                <span
                  role="button"
                  tabIndex={0}
                  aria-label={`${tab.title} menu`}
                  className="sqr-tab-menu"
                  onClick={e => {
                    e.stopPropagation();
                    setMenuFor(menuFor === tab.id ? null : tab.id);
                  }}
                  onKeyDown={e => {
                    if (e.key === 'Enter') {
                      e.stopPropagation();
                      setMenuFor(menuFor === tab.id ? null : tab.id);
                    }
                  }}
                >
                  ≡
                </span>
              )}
              {tab.isCustom && menuFor === tab.id && (
                <SqrDropdown open onClose={() => setMenuFor(null)} className="sqr-tab-menu-list">
                  {[...customAnalysisActions]
                    .sort((a, b) => a.position - b.position)
                    .map(action => (
                      <a
                        key={action.title}
                        role="button"
                        tabIndex={0}
                        onClick={() => {
                          setMenuFor(null);
                          if (action.title === 'Rename') setRenameTarget(tab.title);
                          else setDeleteTarget(tab.title);
                        }}
                        onKeyDown={e => {
                          if (e.key === 'Enter') {
                            setMenuFor(null);
                            if (action.title === 'Rename') setRenameTarget(tab.title);
                            else setDeleteTarget(tab.title);
                          }
                        }}
                      >
                        {action.title === 'Rename' ? (
                          <TextCursor size={12} aria-hidden="true" />
                        ) : (
                          <Trash2 size={12} aria-hidden="true" />
                        )}
                        {action.title}
                      </a>
                    ))}
                </SqrDropdown>
              )}
            </div>
          );
        })}
        <div
          role="button"
          tabIndex={0}
          className="sqr-add-analysis"
          onClick={() => setNewOpen(true)}
          onKeyDown={e => e.key === 'Enter' && setNewOpen(true)}
        >
          + New analysis
        </div>
        <a
          role="button"
          tabIndex={0}
          className="sqr-reload"
          onClick={onReload}
          onKeyDown={e => e.key === 'Enter' && onReload()}
        >
          Reload
        </a>
      </div>
      <div className="sqr-tabs-body">
        {active.id === 'overview' && <OverviewTab />}
        {active.id === 'spOverview' && <SpOverviewTab />}
        {active.id === 'tradeList' && <TradeListTab />}
        {active.id === 'equityChart' && <EquityChartTab />}
        {active.id === 'tradeAnalysis' && <TradeAnalysisTab />}
        {active.id === 'profileChart' && <ProfileChartTab />}
        {active.id === 'strategyConfig' && <StrategyConfigTab />}
        {active.id === 'sourceCode' && <SourceCodeTab />}
        {active.id.startsWith('custom:') && (
          <CustomAnalysisTab name={active.title} />
        )}
      </div>
      {newOpen && (
        <NewAnalysisModal
          existingNames={customTabs}
          onClose={() => setNewOpen(false)}
          onCreate={onCreate}
        />
      )}
      {renameTarget != null && (
        <RenameAnalysisModal
          currentName={renameTarget}
          existingNames={customTabs}
          onClose={() => setRenameTarget(null)}
          onRename={onRename}
        />
      )}
      {deleteTarget != null && (
        <DeleteAnalysisModal
          name={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDelete={onDelete}
        />
      )}
    </div>
  );
}
