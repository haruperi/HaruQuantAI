import { useProjectWorkbench, type usePreviewRun, type ResultDocument } from './documents';

import {masterStats} from './portfolioMasterFixtures';
import {masterError,type MasterDraft} from './portfolioMasterModel';
export function PortfolioMasterProgress({run,draft,onChange,banks,available,result,onSettings,onResults}:{run:ReturnType<typeof usePreviewRun>;draft:MasterDraft;onChange:(v:MasterDraft)=>void;banks:string[];available:number;result:ResultDocument|null;onSettings:()=>void;onResults:()=>void}) {
const { ProjectProgress } = useProjectWorkbench();

 const summary=<div className="pf-master-summary"><h4>Search for portfolios using</h4>{(['Brute force','Genetic search'] as const).map(search=><label key={search}><input type="radio" name="pm-summary-search" checked={draft.search===search} onChange={()=>onChange({...draft,search})}/>{search}</label>)}<h4>Databanks</h4>{(['source','target'] as const).map(key=><label key={key}>{key==='source'?'Source databank':'Target databank'}<select aria-label={key==='source'?'Source databank':'Target databank'} value={draft[key]} onChange={e=>onChange({...draft,[key]:e.target.value})}>{banks.map(b=><option key={b}>{b}</option>)}</select></label>)}<label><input type="checkbox" checked={draft.selectedOnly} onChange={e=>onChange({...draft,selectedOnly:e.target.checked})}/>only selected</label><h4>Portfolio</h4><p># of strategies: {draft.min} – {draft.max}</p><p>Rank portfolios by: {draft.fitness}</p><p>Initial capital: {draft.capital.toLocaleString()}</p><p>Correlation max: {draft.correlation.max}</p><button className="sqd-link-button" onClick={onSettings}>Configure portfolio options</button></div>;
 return <ProjectProgress title="Portfolio Master" run={run} stats={masterStats(run.step)} summary={summary} result={result} onSettings={onSettings} onOpenResults={onResults} startError={masterError(draft,available)}/>;
}
