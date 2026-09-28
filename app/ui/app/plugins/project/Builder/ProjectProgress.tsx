import {CircleStop,CirclePause,CirclePlay} from 'lucide-react';
import { useState, type ReactNode } from 'react';
import { SqdModal } from './ProjectModal';
import { ResultsChart } from './results/ResultsCharts';
import { downloadText, type ResultDocument } from './results/resultsModel';
import type { usePreviewRun } from './projectFixtures';

export function ProjectProgress({title, run, stats, summary, result, onOpenResults, onSettings, startError}: {
  title:string; run:ReturnType<typeof usePreviewRun>; stats:[string,string][];
  summary:ReactNode; result:ResultDocument|null; onOpenResults:()=>void;
  onSettings:()=>void; startError?:string;
}) {
  const [detail,setDetail]=useState<string|null>(null);
  const [sample,setSample]=useState('Full');
  const running=run.status==='running';
  return <div className="sqd-dashboard"><div className="sqd-flex pw-progress">
    <section className="pw-engine">
      <div className="sqd-card pw-controls">
        <button className="sqd-btn" disabled={run.status==='idle'} onClick={()=>run.act('stop')}><CircleStop size={13} className="sqd-ico-stop"/>Stop</button>
        <button className="sqd-btn" disabled={!running} onClick={()=>run.act('pause')}><CirclePause size={13} className="sqd-ico-pause"/>Pause</button>
        <button className="sqd-btn sqd-btn-start" disabled={running||!!startError} onClick={()=>run.act('start')}><CirclePlay size={13}/>{run.status==='paused'?'Resume':'Start'}</button>
        <button className="sqd-btn" onClick={()=>setDetail('Project configuration')}>Config</button>
      </div>
      {startError&&<p role="alert">{startError}</p>}
      <div className="sqd-progress" role="progressbar" aria-label={`${title} progress`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={run.step*10}>
        <div className="sqd-progress-bar" style={{width:`${run.step*10}%`}}/>
      </div>
      <div className="sqd-task-desc">Task: {title} · <span role="status">{run.status}</span> · Local UI preview</div>
      <div className="sqd-log-card"><div className="sqd-log-scroll">{run.log.map((line,i)=><div key={i}>{line}</div>)}</div>
        <div className="sqd-log-buttons"><button className="sqd-btn" onClick={run.clearLog}>Clear log</button>
          <label><input type="checkbox" checked={run.clearOnStart} onChange={e=>run.setClearOnStart(e.target.checked)}/> Clear on start</label>
          <button className="sqd-btn" onClick={()=>downloadText(`${title.toLowerCase()}-preview.log`,run.log.join('\n'))}>Save log</button></div>
      </div>
      <div className="sqd-card sqd-stats-card"><table className="sqd-stats-table"><tbody>{stats.map(([label,value])=><tr key={label}><td>{label}:</td><td>{value}</td><td><button className="sqd-link-button" aria-label={`${label} details`} onClick={()=>setDetail(label)}>Detailed</button></td></tr>)}</tbody></table></div>
      <ResultsChart values={[0,2,3,2,5,4,6,8,7,10].slice(0,Math.max(1,run.step))} title="Task progress / local preview"/>
    </section>
    <section className="pw-summary"><h3>Settings summary</h3><div inert={running||run.status==='paused'}>{summary}</div><button className="sqd-btn" onClick={()=>onSettings()}>Full settings</button></section>
    <section className="sqd-results-wrap pw-results"><div className="sqd-result-card"><button className="sqd-result-title" onClick={onOpenResults} disabled={!result}>{result?`Selected strategy: ${result.name}`:'No results so far'}</button>
      {result&&<div className="sqd-result-body"><div className="sqd-btn-group">{['Full','IS','OOS'].map(s=><button key={s} className={sample===s?'active':''} onClick={()=>setSample(s)}>{s}</button>)}</div>
        <ResultsChart values={sample==='Full'?result.equity:sample==='IS'?result.equity.slice(0,16):result.equity.slice(16)} title={`Equity / ${sample}`}/><button className="sqd-btn" onClick={onOpenResults}>Open Results</button></div>}
    </div></section>
    {detail&&<SqdModal title={detail} onClose={()=>setDetail(null)}><p>Local {title} preview</p><table className="sqr-data-table"><tbody>{stats.map(([k,v])=><tr key={k}><th>{k}</th><td>{v}</td></tr>)}</tbody></table><button className="sqd-btn" onClick={()=>{setDetail(null);onSettings();}}>Open Full settings</button></SqdModal>}
  </div></div>;
}
