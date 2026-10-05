import { useProjectWorkbench, type SettingsSection } from './documents';
import {useRef,useState} from 'react';

import {OptimizationParameters} from './OptimizationParameters';
import {OptimizationPresetDialog} from './OptimizationDialogs';
import {optimizationModes,optimizerDraftError,parameterCombinations,type OptimizerDraft} from './optimizerFixtures';

export function OptimizerSettings({draft,onChange,banks,locked,selectedId,onSelect}:{draft:OptimizerDraft;onChange:(d:OptimizerDraft)=>void;banks:string[];locked:boolean;selectedId:string;onSelect:(id:string)=>void}) {
const { ProjectSettings, DataTab, TradingOptionsTab, AtmTab, MoneyManagementTab, RankingTab, NotesTab, SqdFieldset } = useProjectWorkbench();

 const [preset,setPreset]=useState(false);const file=useRef<HTMLInputElement>(null);
 const patch=(v:Partial<OptimizerDraft>)=>onChange({...draft,...v});
 const wf=draft.mode.includes('Walk'),matrix=draft.mode.endsWith('matrix');
 const number=(label:string,key:keyof OptimizerDraft,min=1)=> <label className="pw-form-row"><span>{label}</span><input type="number" aria-label={label} min={min} value={Number(draft[key])} onChange={e=>patch({[key]:Number(e.target.value)})}/></label>;
 const options=<div className="sqd-tab-content pw-optimization">
  <SqdFieldset legend="What to optimize"><div className="pw-form-row"><label><input type="radio" name="optimization-source" checked={draft.source==='file'} onChange={()=>patch({source:'file'})}/> Strategy from file</label><button className="sqd-btn" disabled={draft.source!=='file'} onClick={()=>file.current?.click()}>Choose strategy</button><span>{draft.fileName||'No file selected'}</span><input ref={file} hidden aria-label="Strategy file" type="file" accept=".sqx,.json,.xml" onChange={e=>{const selected=e.target.files?.[0];if(selected)patch({fileName:selected.name});}}/></div>
   <label className="pw-form-row"><input type="radio" name="optimization-source" checked={draft.source==='databank'} onChange={()=>patch({source:'databank'})}/> All strategies in databank <select aria-label="Source databank" disabled={draft.source!=='databank'} value={draft.sourceBank} onChange={e=>patch({sourceBank:e.target.value})}>{banks.map(b=><option key={b}>{b}</option>)}</select></label>
   <label className="pw-form-row"><span>Store results in databank</span><select aria-label="Target databank" value={draft.targetBank} onChange={e=>patch({targetBank:e.target.value})}>{banks.map(b=><option key={b}>{b}</option>)}</select></label>
   {draft.source==='file'&&draft.fileName&&<p>Local preview uses the selected filename and fixture parameters; strategy contents are not executed.</p>}
  </SqdFieldset>
  <div className="pw-options"><SqdFieldset legend="Optimization settings">{optimizationModes.map(mode=><label key={mode}><input type="radio" name="optimization-mode" checked={draft.mode===mode} onChange={()=>patch({mode})}/>{mode}</label>)}<a href="https://strategyquant.com/doc/strategyquant/sequential-optimization/" target="_blank" rel="noreferrer">What is Sequential optimization?</a></SqdFieldset>
   <SqdFieldset legend={wf?'Walk-Forward settings':draft.mode==='Sequential optimization'?'Sequential Optimization conditions':'Simple optimization'}>
   {wf?<><label className="pw-form-row"><span>Walk-Forward type</span><select aria-label="Walk-Forward type" value={draft.wfType} onChange={e=>patch({wfType:e.target.value})}>{['Rolling','Anchored'].map(v=><option key={v}>{v}</option>)}</select></label><label className="pw-form-row"><span>Period type</span><select aria-label="Period type" value={draft.periodType} onChange={e=>patch({periodType:e.target.value as OptimizerDraft['periodType']})}>{['Percent','Days','Bars'].map(v=><option key={v}>{v}</option>)}</select></label>
    <div className="pw-actions">{(['Floating','Fixed'] as const).map(value=><button key={value} className="sqd-btn" aria-pressed={draft.optimizationType===value} onClick={()=>patch({optimizationType:value})}>{value}</button>)}</div>
    {matrix?<>{number('OOS start','oosStart')}{number('OOS stop','oosStop')}{number('OOS step','oosStep')}{number('Runs start','runsStart')}{number('Runs stop','runsStop')}{number('Runs step','runsStep')}</>:<>{number(draft.periodType==='Percent'?'Out of sample %':'In sample '+draft.periodType.toLowerCase(),'oos')}{number(draft.periodType==='Percent'?'Walk Forward runs':'Out of sample '+draft.periodType.toLowerCase(),'runs')}</>}</>
    :draft.mode==='Sequential optimization'?<>{number('% to pass','passPercent',0)}{number('Number of results in stable area','stableResults')}{number('Fitness stability range','stabilityRange')}</>
    :<>{(['All','Best'] as const).map(store=><label key={store}><input type="radio" name="optimization-storage" checked={draft.store===store} onChange={()=>patch({store})}/>Store {store==='All'?'all optimizations':'best optimization'}</label>)}</>}
   </SqdFieldset></div>
  <SqdFieldset legend="Parameters"><div className="pw-actions">{(['Manual','Automatic'] as const).map(rangeMode=><button className={`sqd-btn${draft.rangeMode===rangeMode?' active':''}`} key={rangeMode} onClick={()=>patch({rangeMode})}>{rangeMode}</button>)}<button className="sqd-btn" onClick={()=>setPreset(true)}>Automatic ranges</button><button className="sqd-btn" onClick={()=>patch({parameters:draft.parameters.map(p=>({...p,enabled:true}))})}>Select all</button><button className="sqd-btn" onClick={()=>patch({parameters:draft.parameters.map(p=>({...p,enabled:false}))})}>Clear selection</button></div>
   {draft.rangeMode==='Automatic'&&number('Value distribution (%)','distribution')}
   <OptimizationParameters value={draft.parameters} onChange={parameters=>patch({parameters})}/>
   {number('Max optimizations','maxOptimizations')}<p>Total combinations: {parameterCombinations(draft.parameters).toLocaleString()}</p>
  </SqdFieldset>{optimizerDraftError(draft)&&<p role="alert">{optimizerDraftError(draft)}</p>}
  {preset&&<OptimizationPresetDialog onClose={()=>setPreset(false)} onApply={percent=>{patch({rangeMode:'Automatic',distribution:percent,parameters:draft.parameters.map(p=>({...p,min:Math.max(1,Math.floor(p.original*(1-percent/100))),max:Math.ceil(p.original*(1+percent/100)),step:1}))});setPreset(false);}}/>}
 </div>;
 const base='https://strategyquant.com/doc/strategyquant/';
 const sections:SettingsSection[]=[{id:'optimization',title:'Optimization',help:'Choose strategy, optimization type and parameter ranges.',helpUrl:base+'simple-optimization/',content:options},
 {id:'data',title:'Data',help:'Configure data for optimization.',helpUrl:base+'data/',content:<DataTab/>},
 {id:'options',title:'Trading options',help:'Configure trading options.',helpUrl:base+'trading-options/',content:<TradingOptionsTab/>},
 {id:'atm',title:'ATM',help:'Advanced Trading Management',helpUrl:base+'settings-atm/',content:<AtmTab/>},
 {id:'money',title:'Money management',help:'Configure position sizing.',helpUrl:base+'money-management/',content:<MoneyManagementTab/>},
 {id:'ranking',title:'Ranking',help:'Configure optimization ranking and filtering.',helpUrl:base+'ranking-options/',content:<RankingTab task="Optimize"/>},
 {id:'notes',title:'Notes',help:'Notes about this configuration.',helpUrl:base+'notes/',content:<NotesTab/>}];
 return <ProjectSettings sections={sections} locked={locked} selectedId={selectedId} onSelect={onSelect}/>;
}
