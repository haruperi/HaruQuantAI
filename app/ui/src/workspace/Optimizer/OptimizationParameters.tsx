import type {ParameterDraft} from './optimizerFixtures';
export function OptimizationParameters({value,onChange}:{value:ParameterDraft[];onChange:(value:ParameterDraft[])=>void}) {
 const update=(index:number,patch:Partial<ParameterDraft>)=>onChange(value.map((p,i)=>i===index?{...p,...patch}:p));
 return <table className="pw-parameters"><thead><tr>{['Use','Parameter','Original','Start','Stop','Step'].map(k=><th key={k}>{k}</th>)}</tr></thead><tbody>
 {value.map((p,i)=><tr key={p.name}><td><input type="checkbox" aria-label={`Use ${p.name}`} checked={p.enabled} onChange={e=>update(i,{enabled:e.target.checked})}/></td><th>{p.name}</th><td>{p.original}</td>
 {(['min','max','step'] as const).map(k=><td key={k}><input type="number" aria-label={`${p.name} ${k}`} value={p[k]} disabled={!p.enabled} onChange={e=>update(i,{[k]:Number(e.target.value)})}/></td>)}</tr>)}
 </tbody></table>;
}
