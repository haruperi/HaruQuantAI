import { useProjectWorkbench, type ResultDocument, type ResultSection } from './documents';
import {useState} from 'react';

import {WalkForwardMatrixView} from './WalkForwardMatrixView';
import type {OptimizationMode} from './optimizerFixtures';

function OptimizationProfile(){
const { ResultsChart } = useProjectWorkbench();

 const [metric,setMetric]=useState('Net profit');
 return <div className="sqr-content"><h3>% of Profitable Optimizations</h3><table className="sqr-data-table"><tbody>{[['Total optimizations','100','100%'],['Profitable optimizations','78','78%'],['Losing optimizations','20','20%'],['Zero profit','2','2%']].map(row=><tr key={row[0]}>{row.map(v=><td key={v}>{v}</td>)}</tr>)}</tbody></table><label className="pw-form-row">Metric <select value={metric} onChange={e=>setMetric(e.target.value)}>{['Net profit','Drawdown','Profit factor'].map(v=><option key={v}>{v}</option>)}</select></label><ResultsChart title={`${metric} / local optimization profile`} values={metric==='Net profit'?[100,160,230,280,250,190]:metric==='Drawdown'?[120,80,60,70,95,140]:[1.1,1.4,1.8,2.1,1.9,1.3]} bars/></div>;
}
function SequentialResults(){
const { ResultsChart } = useProjectWorkbench();

 const [parameter,setParameter]=useState('FastPeriod'),[applied,setApplied]=useState(false);
 return <div className="sqr-content"><h3>RESULT: PASSED — local fixture</h3><label className="pw-form-row">By parameter <select value={parameter} onChange={e=>setParameter(e.target.value)}>{['FastPeriod','SlowPeriod','StopLoss'].map(v=><option key={v}>{v}</option>)}</select></label><button className="sqd-btn" disabled={applied} onClick={()=>setApplied(true)}>{applied?'Optimized values applied to local preview':'Apply optimized values into strategy'}</button>{applied&&<p role="status">Local preview value: FastPeriod 14, SlowPeriod 30. Databank strategy unchanged.</p>}<ResultsChart title={parameter} values={parameter==='FastPeriod'?[10,18,30,35,28,16]:[8,13,22,32,30,21]} bars/></div>;
}
export function OptimizerResults({result,mode}:{result:ResultDocument|null;mode:OptimizationMode}) {
const { ProjectResults } = useProjectWorkbench();

 const extras:ResultSection[]=result?[{id:'optimization-profile',title:'Optimization profile',position:11,content:<OptimizationProfile/>}]:[];
 if(result&&mode==='Sequential optimization')extras.push({id:'sequential',title:'Sequential Optimization Results',position:12,content:<SequentialResults/>});
 if(result&&mode.includes('Walk'))extras.push({id:'wf',title:mode.endsWith('matrix')?'Walk-Forward matrix':'Walk-Forward results',position:13,content:<WalkForwardMatrixView matrix={mode.endsWith('matrix')}/>});
 return <ProjectResults result={result} extraSections={extras}/>;
}
