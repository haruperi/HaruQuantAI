import { useProjectWorkbench, type ResultDocument } from './documents';

export function masterResult():ResultDocument {
const { demoResult } = useProjectWorkbench();
return {...demoResult('portfolio-preview','Portfolio 001 — local preview'),portfolio:true,stockpicker:false,chartData:false};}
export function masterStats(step:number):[string,string][] {return [['Portfolios tested',String(step*24)],['Portfolios accepted',String(step)],['In databank','0 (preview only)'],['Running time so far',`${step} s`],['Estimated time to finish',`${10-step} s`]];}
