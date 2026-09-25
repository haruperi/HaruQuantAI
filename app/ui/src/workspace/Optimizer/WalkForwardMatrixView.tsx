import {useState} from 'react';
import {ResultsChart} from '../../plugins/project/ProjectWorkbench';
export function WalkForwardMatrixView({matrix=true}:{matrix?:boolean}={}){
 const [cell,setCell]=useState([0,0]);
 const scores=[[72,81,76],[79,88,83],[70,84,80]];
 return <div className="sqr-content"><h3>{matrix?'Walk-Forward matrix':'Walk-Forward results'} — local fixture</h3>{matrix&&<table className="pw-matrix"><thead><tr><th>Runs / OOS</th>{[20,30,40].map(v=><th key={v}>{v}%</th>)}</tr></thead><tbody>{[3,5,7].map((r,i)=><tr key={r}><th>{r}</th>{scores[i].map((score,j)=><td key={j}><button aria-label={`${r} runs ${[20,30,40][j]} percent`} aria-pressed={cell[0]===i&&cell[1]===j} onClick={()=>setCell([i,j])}>{score}%</button></td>)}</tr>)}</tbody></table>}<p>Selected: {[3,5,7][cell[0]]} runs / {[20,30,40][cell[1]]}% OOS · Mock score {scores[cell[0]][cell[1]]}%</p><ResultsChart title="Walk-forward equity" values={cell[0]===0?[10000,10200,10100,10500,10800]:[10000,10100,10400,10600,11200]}/></div>;
}
