import {useState} from 'react';
import {useAppStore} from '../../app/store';
import {ProjectFrame,ProjectResults,demoResult,usePreviewRun} from '../../plugins/project/ProjectWorkbench';
import {RetesterSettings} from './RetesterSettings';
import {RetesterProgress} from './RetesterProgress';
import {retestDefaults} from './retesterFixtures';
export function RetesterWorkspace(){
 const panel=useAppStore(s=>s.tab),setPanel=useAppStore(s=>s.setTab);
 const banks=useAppStore(s=>s.databanks),selected=useAppStore(s=>s.strategies.find(v=>v.id===s.selectedStrategyId));
 const selectionCount=useAppStore(s=>s.selectedRows.length);
 const [draft,setDraft]=useState(()=>({...retestDefaults,source:banks[0]?.name??'Results',destination:banks[1]?.name??'Results'}));
 const [settingsSection,setSettingsSection]=useState('data');
 const openSettings=(section='data')=>{setSettingsSection(section);setPanel('settings');};
 const run=usePreviewRun();const result=selected?demoResult(selected.id,selected.name):null;
 return <ProjectFrame title="Retester" panel={panel} onPanelChange={setPanel} running={run.status==='running'||run.status==='paused'}>
  <div className="pw-panel" hidden={panel!=='progress'}><RetesterProgress run={run} draft={draft} onChange={setDraft} banks={banks.map(b=>b.name)} result={result} selectionCount={selectionCount} onResults={()=>setPanel('results')} onSettings={openSettings}/></div>
  <div className="pw-panel" hidden={panel!=='settings'}><RetesterSettings selectedId={settingsSection} onSelect={setSettingsSection} locked={run.status==='running'||run.status==='paused'}/></div>
  <div className="pw-panel" hidden={panel!=='results'}><ProjectResults result={result}/></div>
 </ProjectFrame>;
}
