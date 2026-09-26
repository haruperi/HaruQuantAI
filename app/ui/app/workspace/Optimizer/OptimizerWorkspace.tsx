import {useState} from 'react';
import {useAppStore} from '../../host/store';
import {ProjectFrame,demoResult,usePreviewRun} from '../../plugins/project/ProjectWorkbench';
import {OptimizerSettings} from './OptimizerSettings';
import {OptimizerProgress} from './OptimizerProgress';
import {OptimizerResults} from './OptimizerResults';
import {optimizerDefaults} from './optimizerFixtures';
export function OptimizerWorkspace(){
 const panel=useAppStore(s=>s.tab),setPanel=useAppStore(s=>s.setTab);
 const banks=useAppStore(s=>s.databanks),selected=useAppStore(s=>s.strategies.find(v=>v.id===s.selectedStrategyId));
 const [draft,setDraft]=useState(()=>({...structuredClone(optimizerDefaults),sourceBank:banks[0]?.name??'Results',targetBank:banks[1]?.name??'Results'}));
 const [settingsSection,setSettingsSection]=useState('optimization');
 const openSettings=(section='optimization')=>{setSettingsSection(section);setPanel('settings');};
 const run=usePreviewRun();const result=selected?demoResult(selected.id,selected.name):null;
 return <ProjectFrame title="Optimizer" panel={panel} onPanelChange={setPanel} running={run.status==='running'||run.status==='paused'}>
  <div className="pw-panel" hidden={panel!=='progress'}><OptimizerProgress run={run} draft={draft} onChange={setDraft} result={result} onResults={()=>setPanel('results')} onSettings={openSettings}/></div>
  <div className="pw-panel" hidden={panel!=='settings'}><OptimizerSettings selectedId={settingsSection} onSelect={setSettingsSection} draft={draft} onChange={setDraft} banks={banks.map(b=>b.name)} locked={run.status==='running'||run.status==='paused'}/></div>
  <div className="pw-panel" hidden={panel!=='results'}><OptimizerResults result={result} mode={draft.mode}/></div>
 </ProjectFrame>;
}
