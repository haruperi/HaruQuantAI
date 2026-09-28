import { useProjectWorkbench, type ResultDocument, type usePreviewRun } from './documents';

import {optimizationModes,optimizerDraftError,type OptimizerDraft} from './optimizerFixtures';
export function OptimizerProgress({run,draft,onChange,result,onResults,onSettings}:{run:ReturnType<typeof usePreviewRun>;draft:OptimizerDraft;onChange:(d:OptimizerDraft)=>void;result:ResultDocument|null;onResults:()=>void;onSettings:(section?:string)=>void}) {
const { ProjectProgress } = useProjectWorkbench();

 const summary=<><h4>Backtest options</h4><p>Data: local EURUSD / H1 fixture</p><div className="pw-actions">{[["data","Data"],["options","Trading options"],["money","Money management"]].map(([id,label])=><button key={id} className="sqd-link-button" onClick={()=>onSettings(id)}>{label}</button>)}</div><h4>Optimization</h4><div className="pw-mode-buttons" role="group" aria-label="Optimization type">{optimizationModes.map((mode,i)=><button key={mode} className="sqd-btn" aria-pressed={draft.mode===mode} onClick={()=>onChange({...draft,mode})}>{['Simple','Sequential','Walk-forward','Walk-forward matrix'][i]}</button>)}</div><p>Source: {draft.source==='file'?draft.fileName||'No file selected':draft.sourceBank}</p><p>Target: {draft.targetBank}</p><p>Parameters: {draft.parameters.filter(p=>p.enabled).map(p=>p.name).join(', ')||'None selected'}</p><button className="sqd-link-button" onClick={()=>onSettings("optimization")}>Configure optimization</button></>;
 return <ProjectProgress title="Optimizer" run={run} stats={[["Total steps","10"],["Step",String(run.step)],["Running time so far",`${run.step} s`],["Estimated time to finish",`${10-run.step} s`]]} summary={summary} result={result} onSettings={onSettings} onOpenResults={onResults} startError={optimizerDraftError(draft)}/>;
}
