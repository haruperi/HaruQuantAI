import { dataTabDefaults } from '../../plugins/project/ProjectWorkbench';
export interface RetestDraft { source: string; destination: string; selectedOnly: boolean }
export const retestDefaults:RetestDraft = {source:'Results',destination:'Retest',selectedOnly:false};
export const retestDataDefaults = {...dataTabDefaults,oosRanges:[]};
export function retestRouting(source:string,destination:string) { return source===destination?'overwrite':'copy'; }
export function retestStats(step:number):[string,string][] {
  return [['Retested strategies',`${step} / 10`],['Time per strategy','1 s'],['Strategies per hour','3,600'],['In databank','10'],['Failed',step>5?'2':'0'],['Passed',String(Math.max(0,step-(step>5?2:0)))],['Running time so far',`${step} s`],['Estimated time to finish',`${10-step} s`]];
}
