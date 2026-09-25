import {useState} from 'react';
import {SqdModal} from '../../plugins/project/ProjectWorkbench';
export function OptimizationPresetDialog({onApply,onClose}:{onApply:(percent:number)=>void;onClose:()=>void}) {
 const [percent,setPercent]=useState(20);
 return <SqdModal title="Automatic parameter ranges" onClose={onClose}><label className="pw-form-row"><span>Range around original value (%)</span><input aria-label="Range percent" type="number" min={1} max={100} value={percent} onChange={e=>setPercent(Number(e.target.value))}/></label><p>Apply a local parameter-range preset. No optimization is run.</p><div className="pw-actions"><button className="sqd-btn" onClick={onClose}>Cancel</button><button className="sqd-btn sqd-btn-primary" disabled={percent<1||percent>100} onClick={()=>onApply(percent)}>Apply</button></div></SqdModal>;
}
