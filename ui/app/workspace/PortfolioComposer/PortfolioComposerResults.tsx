import { useProjectWorkbench, type ResultDocument, type ResultSection } from './documents';
import {useState} from 'react';

export function PortfolioComposerResults({result,automatic}:{result:ResultDocument|null;automatic:boolean}){
const { ProjectResults, ResultsChart } = useProjectWorkbench();

 const [filter,setFilter]=useState('All');
 const log=[['2025-01-03','Opened','Example order opened at configured weight.'],['2025-01-04','Skipped','Example order skipped: insufficient free margin.'],['2025-01-05','Closed','Example order closed.']];
 const extra:ResultSection[]=result?[{id:'pc-log',title:'Log',position:99,content:<div className="sqr-content"><label className="pf-row"><span>Actions</span><select aria-label="Log actions" value={filter} onChange={e=>setFilter(e.target.value)}>{['All','Opened','Skipped','Closed'].map(v=><option key={v}>{v}</option>)}</select></label><table className="sqr-data-table"><thead><tr><th>Date</th><th>Action</th><th>Local fixture detail</th></tr></thead><tbody>{log.filter(row=>filter==='All'||row[1]===filter).map(row=><tr key={row[0]}>{row.map(v=><td key={v}>{v}</td>)}</tr>)}</tbody></table></div>}]:[];
 if(result&&automatic)extra.push({id:'pc-simulations',title:'Automatic computation simulations',position:999,content:<div className="sqr-content"><ResultsChart title="Automatic computation simulations — local fixture" values={[1.1,1.5,1.3,1.8,2.1,1.7,2.2]} bars/><p>Displayed points are fixed examples, not optimization output.</p></div>});
 return <ProjectResults result={result} extraSections={extra} embedded visibleTabIds={['overview','tradeList','equityChart','tradeAnalysis','correlation']} emptyMessage="No portfolio result. Select strategies and click Recompute portfolio."/>;
}
