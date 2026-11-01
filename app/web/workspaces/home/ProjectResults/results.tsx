import { useState, type CSSProperties } from 'react';
import { SqdModal } from '../../../common/project/ProjectModal';
import { useProjectBinding } from '../projectController';
import { NewAnalysisModal } from './newCustomPluginModal';
import type {ResultSection} from '../../../common/project/contracts';
import type { ResultDocument } from '../../../common/project/results/resultsModel';
import { ConditionalTabs } from '../../../common/project/results/tabs/ConditionalTabs';
import { useProjectResults } from './ResultsCtrl';
import { Puzzle, TextCursor, Trash2 } from 'lucide-react';
import { customAnalysisActions, NO_RESULT_CHOSEN, } from '../../../common/project/results/resultsFixtures';
import { SqrDropdown } from '../../../common/project/results/ResultsChrome';
import { DeleteAnalysisModal, RenameAnalysisModal, } from '../../../common/project/results/ResultsModals';
import { OverviewTab } from '../../results/ResultsOverview/module';
import { TradeListTab } from '../../results/ResultsTradeList/module';
import { EquityChartTab } from '../../results/ResultsEquityChart/module';
import { SourceCodeTab } from '../../results/ResultsSourceCode/module';
import { CustomAnalysisTab } from '../../../common/project/results/tabs/SmallTabs';
import { ProfileChartTab } from '../../results/ResultsProfileChart/module';
import { SpOverviewTab } from '../../results/ResultsSPOverview/module';
import { StrategyConfigTab } from '../../results/ResultsStrategyConfig/module';
import { TradeAnalysisTab } from '../../results/ResultsTradeAnalysis/module';
/**
 * Builder Results tab (FEAT-UI-BUILDER_RESULTS_TAB).
 *
 * Mirrors the donor RESULTS overlay app: info line, quant-tabs strip with
 * custom analysis tabs last, "+ New analysis" control, per-tab content and a
 * Reload link. The donor's page reload is adapted to a view-state reset.
 */
export function ProjectResults({ result, extraSections=[], embedded=false, visibleTabIds, emptyMessage=NO_RESULT_CHOSEN }: {
    embedded?:boolean;
    visibleTabIds?:readonly string[];
    emptyMessage?:string;
    extraSections?:ResultSection[];
    result: ResultDocument | null;
}) {
    const binding = useProjectBinding();
    const [analysisName, setAnalysisName] = useState('');
    const { activeId, setActiveId, customTabs, newOpen, setNewOpen, renameTarget, setRenameTarget, deleteTarget, setDeleteTarget, menuFor, setMenuFor, resetKey, tabs, active, onReload, onCreate, onRename, onDelete } = useProjectResults(result, extraSections, visibleTabIds);
    return (<div className={`sqr-results${embedded ? ' sqr-embedded' : ''}`} key={resetKey} style={binding ? { position: 'relative', flex: 1, minHeight: 0,
        '--sqx-panel': 'var(--panel)', '--sqx-card': 'var(--panel)',
        '--sqx-tab-bg': 'var(--panel2)', '--sqx-tab-border': 'var(--line)',
        '--sqx-text': 'var(--text)', '--sqx-info-line': 'var(--muted)',
      } as CSSProperties : undefined}>
      <div className="sqr-info-line">{result ? `${result.name} — Main backtest | Local mock results` : emptyMessage}</div>
      <div className="sqr-tabs-header" role="tablist" aria-label="Result views">
        {tabs.map(tab => {
            const isActive = tab.id === active.id;
            return (<div key={tab.id} role="tab" aria-label={tab.title} tabIndex={0} onKeyDown={e => { if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                setActiveId(tab.id);
            } }} aria-selected={isActive} className={`${isActive ? 'active' : ''}${tab.isCustom ? ' sqr-tab-custom' : ''}`} onClick={() => setActiveId(tab.id)}>
              {tab.isCustom && (<Puzzle size={11} className="sqr-custom-icon" aria-hidden="true"/>)}
              {tab.title}
              {tab.isCustom && (<span role="button" tabIndex={0} aria-label={`${tab.title} menu`} className="sqr-tab-menu" onClick={e => {
                        e.stopPropagation();
                        setMenuFor(menuFor === tab.id ? null : tab.id);
                    }} onKeyDown={e => {
                        if (e.key === 'Enter') {
                            e.stopPropagation();
                            setMenuFor(menuFor === tab.id ? null : tab.id);
                        }
                    }}>
                  ≡
                </span>)}
              {tab.isCustom && menuFor === tab.id && (<SqrDropdown open onClose={() => setMenuFor(null)} className="sqr-tab-menu-list">
                  {[...customAnalysisActions]
                        .sort((a, b) => a.position - b.position)
                        .map(action => (<a key={action.title} role="button" tabIndex={0} onClick={() => {
                            setMenuFor(null);
                            if (action.title === 'Rename')
                                setRenameTarget(tab.title);
                            else
                                setDeleteTarget(tab.title);
                        }} onKeyDown={e => {
                            if (e.key === 'Enter') {
                                setMenuFor(null);
                                if (action.title === 'Rename')
                                    setRenameTarget(tab.title);
                                else
                                    setDeleteTarget(tab.title);
                            }
                        }}>
                        {action.title === 'Rename' ? (<TextCursor size={12} aria-hidden="true"/>) : (<Trash2 size={12} aria-hidden="true"/>)}
                        {action.title}
                      </a>))}
                </SqrDropdown>)}
            </div>);
        })}
        <div role="button" tabIndex={0} className="sqr-add-analysis" onClick={() => setNewOpen(true)} onKeyDown={e => e.key === 'Enter' && setNewOpen(true)}>
          + New analysis
        </div>
        <a role="button" tabIndex={0} className="sqr-reload" onClick={onReload} onKeyDown={e => e.key === 'Enter' && onReload()}>
          Reload
        </a>
      </div>
      <div className="sqr-tabs-body" key={result?.id ?? 'empty'}>
        {Object.entries({ overview: <OverviewTab result={result}/>, spOverview: <SpOverviewTab result={result}/>, tradeList: <TradeListTab result={result}/>, equityChart: <EquityChartTab result={result}/>, tradeAnalysis: <TradeAnalysisTab result={result}/>, profileChart: <ProfileChartTab result={result}/>, strategyConfig: <StrategyConfigTab result={result}/>, sourceCode: <SourceCodeTab result={result}/> }).map(([id, content]) => <div key={id} hidden={active.id !== id} className="sqr-panel-slot">{content}</div>)}
        {['monteCarloTests', 'tradesOnChart', 'stockpicker', 'correlation'].includes(active.id) && result && <ConditionalTabs id={active.id} result={result}/>}
        {extraSections.map(section=><div key={section.id} hidden={active.id!==section.id} className="sqr-panel-slot">{section.content}</div>)}
        {active.id.startsWith('custom:') && (binding ? <div className="sqr-content"><h3>{active.title}</h3><p>This analysis definition is saved. No analysis provider is configured.</p></div> : <CustomAnalysisTab name={active.title} result={result}/>)}
      </div>
      {newOpen && (binding ? <SqdModal title="Create custom analysis" onClose={() => setNewOpen(false)}>
        <p>Save a named analysis definition in this project. An analysis provider can be configured separately.</p>
        <label>Name<input aria-label="Name of custom plugin tab" className="sqd-input" value={analysisName} onChange={event => setAnalysisName(event.target.value)} /></label>
        <button className="sqd-btn" disabled={binding.state.busy || !analysisName.trim() || customTabs.includes(analysisName.trim())} onClick={() => void onCreate(analysisName.trim())}>Create</button>
      </SqdModal> : <NewAnalysisModal existingNames={customTabs} onClose={() => setNewOpen(false)} onCreate={onCreate}/>)}
      {renameTarget != null && (<RenameAnalysisModal currentName={renameTarget} existingNames={customTabs} onClose={() => setRenameTarget(null)} onRename={onRename}/>)}
      {deleteTarget != null && (<DeleteAnalysisModal name={deleteTarget} onClose={() => setDeleteTarget(null)} onDelete={onDelete}/>)}
    </div>);
}
