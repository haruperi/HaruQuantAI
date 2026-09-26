import {useState} from 'react';
import {SqdModal} from '../../plugins/project/ProjectWorkbench';
export function PortfolioComposerConfirm({all,onConfirm,onClose}:{all:boolean;onConfirm:()=>void;onClose:()=>void}){return <SqdModal title={all?'Clear all strategies':'Delete selected strategies'} onClose={onClose} footer={<><button className="sqd-btn" onClick={onClose}>Cancel</button><button className="sqd-btn" onClick={onConfirm}>{all?'Clear all':'Delete'}</button></>}><p>Remove {all?'all':'the selected'} strategies from this local composition?</p></SqdModal>;}
export function BuyHoldDialog({onAdd,onClose}:{onAdd:(symbol:string)=>void;onClose:()=>void}){
 const [symbol,setSymbol]=useState('SPY');
 return <SqdModal title="Buy and Hold strategy" width={600} onClose={onClose} footer={<><button className="sqd-btn" onClick={onClose}>Close</button><button className="sqd-btn sqd-btn-primary" onClick={()=>onAdd(symbol)}>Add</button></>}><p>A long-term stock or ETF holding strategy.</p><strong>Use only in combination with Stockpicker strategies.</strong><label className="pf-row"><span>Symbol</span><select aria-label="Buy and Hold symbol" value={symbol} onChange={e=>setSymbol(e.target.value)}>{['SPY','QQQ','DIA'].map(v=><option key={v}>{v}</option>)}</select></label><p className="pf-hint">Symbols and strategy records are local examples.</p></SqdModal>;
}
