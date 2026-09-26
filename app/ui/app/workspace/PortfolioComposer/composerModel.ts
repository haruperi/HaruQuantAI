export interface ComposerMember { id:string; name:string; symbol:string; weight:number; selected:boolean; equity:number[]; money:string }
export interface ComposerConfig {range:'Full available'|'Limited';from:string;to:string;capital:number;leverage:number;fitness:string;simulations:number;riskFree:number}
export interface ComposerDraft {members:ComposerMember[];config:ComposerConfig}
export const composerDefaults:ComposerConfig={range:'Full available',from:'2020-01-01',to:'2025-12-31',capital:100000,leverage:1,fitness:'Sharpe ratio',simulations:10,riskFree:0.7};
export function composerError(d:ComposerDraft):string|undefined {
 const selected=d.members.filter(m=>m.selected);
 if(!selected.length)return 'Select at least one strategy to recompute the portfolio.';
 if(selected.some(m=>!Number.isFinite(m.weight)||m.weight<0))return 'Selected strategy weights must be non-negative numbers.';
 if(!Number.isFinite(d.config.capital)||d.config.capital<=0||!Number.isFinite(d.config.leverage)||d.config.leverage<=0)return 'Initial capital and leverage must be positive.';
 if(!Number.isInteger(d.config.simulations)||d.config.simulations<1||!Number.isFinite(d.config.riskFree)||d.config.riskFree<0||d.config.riskFree>1)return 'Set positive simulations and a risk free rate between 0 and 1.';
 if(d.config.range==='Limited'&&(!d.config.from||!d.config.to||d.config.from>d.config.to))return 'Enter a valid data range with start before end.';
 return undefined;
}
/** Move selected rows one position while preserving their relative order. */
export function moveMembers(members:ComposerMember[],direction:-1|1):ComposerMember[] {
 const next=[...members];
 const indexes=Array.from({length:next.length},(_,i)=>i);if(direction===1)indexes.reverse();
 for(const i of indexes){const j=i+direction;if(next[i].selected&&j>=0&&j<next.length&&!next[j].selected)[next[i],next[j]]=[next[j],next[i]];}
 return next;
}
export function serializeComposition(draft:ComposerDraft):string{return JSON.stringify({format:'haruquantai.portfolio-ui-preview',version:1,...draft},null,2);}
/** Accept only our own bounded preview document; never interpret native SQX data. */
export function parseComposition(text:string):ComposerDraft {
 const d=JSON.parse(text) as Record<string,unknown>;
 if(d?.format!=='haruquantai.portfolio-ui-preview'||d.version!==1||!Array.isArray(d.members)||d.members.length>500||!d.config||typeof d.config!=='object')throw new Error('Choose a HaruQuantAI portfolio preview JSON file. Native SQX import is unavailable in this UI prototype.');
 const c=d.config as Record<string,unknown>;
 if(!['Full available','Limited'].includes(String(c.range))||!['from','to','fitness'].every(k=>typeof c[k]==='string')||!['capital','leverage','simulations','riskFree'].every(k=>typeof c[k]==='number'&&Number.isFinite(c[k])))throw new Error('Invalid preview configuration.');
 const ids=new Set<string>();
 for(const value of d.members){
  if(!value||typeof value!=='object')throw new Error('Invalid preview member.');
  const m=value as Record<string,unknown>;
  if(!['id','name','symbol','money'].every(k=>typeof m[k]==='string')||typeof m.selected!=='boolean'||typeof m.weight!=='number'||!Number.isFinite(m.weight)||m.weight<0||!Array.isArray(m.equity)||m.equity.length>10000||m.equity.some(v=>typeof v!=='number'||!Number.isFinite(v))||ids.has(String(m.id)))throw new Error('Invalid or duplicate preview member.');
  ids.add(String(m.id));
 }
 return {config:{range:c.range as ComposerConfig['range'],from:String(c.from),to:String(c.to),capital:Number(c.capital),leverage:Number(c.leverage),fitness:String(c.fitness),simulations:Number(c.simulations),riskFree:Number(c.riskFree)},members:d.members.map(m=>({id:String(m.id),name:String(m.name),symbol:String(m.symbol),money:String(m.money),weight:Number(m.weight),selected:Boolean(m.selected),equity:[...m.equity]}))};
}
