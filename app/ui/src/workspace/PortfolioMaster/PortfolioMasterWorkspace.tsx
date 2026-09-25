import {useEffect,useState} from 'react';
import {useAppStore} from '../../app/store';
import {ProjectFrame,ProjectResults,demoResult,usePreviewRun,type ResultDocument} from '../../plugins/project/ProjectWorkbench';
import {masterDefaults,type MasterDraft} from './portfolioMasterModel';
import {masterResult} from './portfolioMasterFixtures';
import {PortfolioMasterProgress} from './PortfolioMasterProgress';
import {PortfolioMasterSettings} from './PortfolioMasterSettings';
export function PortfolioMasterWorkspace(){
 const panel=useAppStore(s=>s.tab),setPanel=useAppStore(s=>s.setTab),banks=useAppStore(s=>s.databanks);
 const strategies=useAppStore(s=>s.strategies),selectedId=useAppStore(s=>s.selectedStrategyId),selectedRows=useAppStore(s=>s.selectedRows);
 const [draft,setDraft]=useState(()=>({...structuredClone(masterDefaults),source:banks[0]?.name??'Results',target:banks[1]?.name??'Results'}));
 const [result,setResult]=useState<ResultDocument|null>(null);const run=usePreviewRun();
 useEffect(()=>{const selected=strategies.find(s=>s.id===selectedId);if(selected)setResult(demoResult(selected.id,selected.name));},[selectedId,strategies]);
 useEffect(()=>{if(run.status==='complete')setResult(masterResult());},[run.status]);
 const change=(next:MasterDraft)=>{setDraft(next);setResult(null);};
 const sourceIds=banks.find(b=>b.name===draft.source)?.strategyIds??[];
 const available=sourceIds.filter(id=>!draft.selectedOnly||selectedRows.includes(id)).length;
 const locked=run.status==='running'||run.status==='paused';
 return <ProjectFrame title="Portfolio Master" panel={panel} onPanelChange={setPanel} running={locked}>
 <div className="pw-panel" hidden={panel!=='progress'}><PortfolioMasterProgress run={run} draft={draft} onChange={change} banks={banks.map(b=>b.name)} available={available} result={result} onSettings={()=>setPanel('settings')} onResults={()=>setPanel('results')}/></div>
 <div className="pw-panel" hidden={panel!=='settings'}><PortfolioMasterSettings draft={draft} onChange={change} banks={banks.map(b=>b.name)} available={available} locked={locked}/></div>
 <div className="pw-panel" hidden={panel!=='results'}><ProjectResults result={result}/></div>
 </ProjectFrame>;
}
export {PortfolioMasterWorkspace as PortfolioMaster};
