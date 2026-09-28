import { useProjectWorkbench, type ResultDocument, type usePreviewRun } from './documents';

import {retestRouting,retestStats,type RetestDraft} from './retesterFixtures';
export function RetesterProgress({run,draft,onChange,banks,result,onResults,onSettings,selectionCount}:{run:ReturnType<typeof usePreviewRun>;draft:RetestDraft;onChange:(v:RetestDraft)=>void;banks:string[];result:ResultDocument|null;onResults:()=>void;onSettings:(section?:string)=>void;selectionCount:number}) {
const { ProjectProgress } = useProjectWorkbench();

 const summary=<><h4>Backtest options</h4><p>Data: local EURUSD / H1 fixture</p><div className="pw-actions">{[["data","Data"],["options","Trading options"],["money","Money management"]].map(([id,label])=><button key={id} className="sqd-link-button" onClick={()=>onSettings(id)}>{label}</button>)}</div><h4>Databanks</h4>
 <label>Source databank <select aria-label="Source databank" value={draft.source} onChange={e=>onChange({...draft,source:e.target.value})}>{banks.map(b=><option key={b}>{b}</option>)}</select></label>
 <label><input type="checkbox" checked={draft.selectedOnly} onChange={e=>onChange({...draft,selectedOnly:e.target.checked})}/> Retest only selected</label>
 <label>Target databank <select aria-label="Target databank" value={draft.destination} onChange={e=>onChange({...draft,destination:e.target.value})}>{banks.map(b=><option key={b}>{b}</option>)}</select></label>
 <p>{retestRouting(draft.source,draft.destination)==='copy'?'Copy preview: original results remain in the source databank.':'Overwrite preview: the source and target databanks are the same.'}</p><h4>Cross checks (robustness)</h4><button className="sqd-link-button" onClick={()=>onSettings("checks")}>Configure cross checks</button></>;
 return <ProjectProgress title="Retester" run={run} stats={retestStats(run.step)} summary={summary} result={result} onOpenResults={onResults} onSettings={onSettings} startError={draft.selectedOnly&&selectionCount===0?'Select strategies in the databank before starting.':undefined}/>;
}
