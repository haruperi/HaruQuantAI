export const dataTabDefaults = {"engine":"MetaTrader5 (hedging mode)","symbol":"AUDUSD_dukascopy","timeframe":"D1","dateFrom":"2026.03.19","dateTo":"2026.09.18","oosRanges":[{"type":"IST","from":"2026.03.19","to":"2026.06.05"},{"type":"ISV","from":"2026.06.05","to":"2026.07.28"},{"type":"OOS","from":"2026.07.28","to":"2026.09.18"}]};

export interface RetestDraft { source: string; destination: string; selectedOnly: boolean }
export const retestDefaults:RetestDraft = {source:'Results',destination:'Retest',selectedOnly:false};
export const retestDataDefaults = {...dataTabDefaults,oosRanges:[]};
export function retestRouting(source:string,destination:string) { return source===destination?'overwrite':'copy'; }
export function retestStats(step:number):[string,string][] {
  return [['Retested strategies',`${step} / 10`],['Time per strategy','1 s'],['Strategies per hour','3,600'],['In databank','10'],['Failed',step>5?'2':'0'],['Passed',String(Math.max(0,step-(step>5?2:0)))],['Running time so far',`${step} s`],['Estimated time to finish',`${10-step} s`]];
}
