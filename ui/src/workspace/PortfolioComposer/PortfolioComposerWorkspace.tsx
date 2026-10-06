import {useEffect,useState} from 'react';
import {CirclePlay,CircleStop,Zap} from 'lucide-react';
import {useAppStore} from '../../app/store';
import {demoResult,downloadText,usePreviewRun,type ResultDocument} from '../../plugins/project/ProjectWorkbench';
import {composerDefaults,composerError,serializeComposition,type ComposerDraft,type ComposerMember} from './composerModel';
import {PortfolioComposition} from './PortfolioComposition';
import {PortfolioConfiguration} from './PortfolioConfiguration';
import {PortfolioAutocomputation} from './PortfolioAutocomputation';
import {PortfolioComposerResults} from './PortfolioComposerResults';
import {PortfolioCandidatesModal} from './PortfolioCandidatesModal';
import {BuyHoldDialog,PortfolioComposerConfirm} from './PortfolioComposerDialogs';
const tabs=['Portfolio composition','Configuration - account, MM','Automatic computation'];
export function PortfolioComposerWorkspace(){
 const strategies=useAppStore(s=>s.strategies),savedMembers=useAppStore(s=>s.portfolio);
 const candidates:ComposerMember[]=strategies.map((s,i)=>({id:s.id,name:s.name,symbol:s.symbol,weight:100,selected:true,equity:s.equity.map(p=>p.value),money:i%3===0?'Risk fixed %':'Fixed size'}));
 const [draft,setDraft]=useState<ComposerDraft>(()=>({config:{...composerDefaults},members:savedMembers.flatMap(m=>{const c=candidates.find(c=>c.id===m.strategyId);return c?[{...c,weight:m.weight,selected:m.enabled}]:[];})}));
 const [tab,setTab]=useState(tabs[0]),[dialog,setDialog]=useState<'load'|'delete'|'clear'|'buy'|null>(null);
 const [result,setResult]=useState<ResultDocument|null>(null),[automatic,setAutomatic]=useState(false);
 const run=usePreviewRun(),locked=run.status==='running'||run.status==='paused',error=composerError(draft);
 useEffect(()=>{if(run.status==='complete')setResult({...demoResult('composer-preview','Portfolio composition — local preview'),portfolio:true,stockpicker:false,chartData:false});},[run.status]);
 const change=(next:ComposerDraft)=>{setDraft(next);setResult(null);};
 const members=(value:ComposerMember[])=>change({...draft,members:value});
 const start=(auto:boolean)=>{setResult(null);setAutomatic(auto);run.act('start');};
 const save=()=>downloadText('portfolio-composition.preview.json',serializeComposition(draft),'application/json');
 const savePortfolio=()=>{if(result)downloadText('portfolio-result.preview.json',JSON.stringify({format:'haruquantai.portfolio-result-preview',draft,result},null,2),'application/json');};
 return <div className="project-workspace pf-composer"><header className="sqd-dashboard-header"><div className="sqd-project-name">Portfolio Composer</div><span className="pf-preview-label">Local UI preview</span></header><div className="pf-composer-columns">
 <section className="pf-composer-settings" aria-label="Composer settings"><div className="pf-composer-controls"><button className="sqd-btn" disabled={!locked} onClick={()=>run.act('stop')}><CircleStop size={13}/>Stop</button><button className="sqd-btn sqd-btn-start" disabled={locked||!!error} onClick={()=>start(false)}><CirclePlay size={13}/>Recompute portfolio</button><button className="sqd-btn sqd-btn-primary" disabled={locked||!!error} onClick={()=>start(true)}><Zap size={13}/>Automatic computation</button></div><div className="sqd-progress" role="progressbar" aria-label="Composer progress" aria-valuenow={run.step*10} aria-valuemin={0} aria-valuemax={100}><div className="sqd-progress-bar" style={{width:`${run.step*10}%`}}/></div><div className="sqd-task-desc">Task: {run.status} · {automatic?'Automatic computation':'Recompute portfolio'} preview</div>
 <div className="pf-tabs" role="tablist" aria-label="Composer settings tabs">{tabs.map(t=><button role="tab" aria-selected={t===tab} key={t} onClick={()=>setTab(t)}>{t}</button>)}</div>
 <div className="pf-composer-form" inert={locked}>{locked&&<p role="status">Settings locked during the local preview.</p>}
 <div hidden={tab!==tabs[0]}><PortfolioComposition members={draft.members} onChange={members} onLoad={()=>setDialog('load')} onSave={save} onSavePortfolio={savePortfolio} onDelete={()=>setDialog('delete')} onClear={()=>setDialog('clear')} onBuyHold={()=>setDialog('buy')} canSavePortfolio={!!result}/></div>
 <div hidden={tab!==tabs[1]}><PortfolioConfiguration config={draft.config} members={draft.members} onChange={config=>change({...draft,config})}/></div>
 <div hidden={tab!==tabs[2]}><PortfolioAutocomputation config={draft.config} onChange={config=>change({...draft,config})}/></div>
 </div>{error&&<p className="pf-error" role="alert">{error}</p>}
 </section><section className="pf-composer-results" aria-label="Composer results"><PortfolioComposerResults result={result} automatic={automatic}/></section>
 </div>
 {dialog==='load'&&<PortfolioCandidatesModal candidates={candidates} existingIds={draft.members.map(m=>m.id)} onClose={()=>setDialog(null)} onAdd={ids=>{members([...draft.members,...candidates.filter(c=>ids.includes(c.id))]);setDialog(null);}} onImport={next=>{change(next);setDialog(null);}}/>}
 {(dialog==='delete'||dialog==='clear')&&<PortfolioComposerConfirm all={dialog==='clear'} onClose={()=>setDialog(null)} onConfirm={()=>{members(dialog==='clear'?[]:draft.members.filter(m=>!m.selected));setDialog(null);}}/>}
 {dialog==='buy'&&<BuyHoldDialog onClose={()=>setDialog(null)} onAdd={symbol=>{members([...draft.members,{id:`buy-hold-${symbol}-${crypto.randomUUID()}`,name:`Buy and Hold ${symbol}`,symbol,weight:100,selected:true,equity:[100,102,105],money:'Buy and Hold'}]);setDialog(null);}}/>}
 </div>;
}
