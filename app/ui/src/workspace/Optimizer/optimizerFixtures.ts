export const optimizationModes = ['Simple optimization','Sequential optimization','Walk - Forward optimization','Walk - Forward matrix'] as const;
export type OptimizationMode = typeof optimizationModes[number];
export interface ParameterDraft {name:string; enabled:boolean; original:number; min:number; max:number; step:number}
export interface OptimizerDraft {
 mode:OptimizationMode; source:'databank'|'file'; sourceBank:string; targetBank:string; fileName:string;
 parameters:ParameterDraft[]; rangeMode:'Manual'|'Automatic'; maxOptimizations:number; store:'All'|'Best';
 wfType:string; optimizationType:'Floating'|'Fixed'; periodType:'Percent'|'Days'|'Bars'; oos:number; runs:number;
 oosStart:number; oosStop:number; oosStep:number; runsStart:number; runsStop:number; runsStep:number;
 passPercent:number; stableResults:number; stabilityRange:number; distribution:number;
}
export const optimizerDefaults:OptimizerDraft={mode:'Simple optimization',source:'databank',sourceBank:'Results',targetBank:'Optimized',fileName:'',
 parameters:[{name:'FastPeriod',enabled:true,original:12,min:8,max:16,step:2},{name:'SlowPeriod',enabled:true,original:28,min:20,max:40,step:5},{name:'StopLoss',enabled:false,original:40,min:20,max:60,step:10}],
 rangeMode:'Manual',maxOptimizations:10000,store:'All',wfType:'Rolling',optimizationType:'Floating',periodType:'Percent',oos:30,runs:5,oosStart:20,oosStop:40,oosStep:10,runsStart:3,runsStop:7,runsStep:2,passPercent:80,stableResults:5,stabilityRange:10,distribution:20};
/** Bounds validation is for editing these synthetic controls, not a backend schema. */
export function optimizerDraftError(d:OptimizerDraft):string|undefined {
 if(d.source==='file'&&!d.fileName)return 'Choose a strategy file for the local preview.';
 if(!d.parameters.some(p=>p.enabled))return 'Select at least one parameter.';
 if(d.parameters.some(p=>p.enabled&&(![p.min,p.max,p.step].every(Number.isFinite)||p.min>p.max||p.step<=0)))return 'Parameter ranges require minimum ≤ maximum and a positive step.';
 if(!Number.isFinite(d.maxOptimizations)||d.maxOptimizations<1)return 'Maximum optimizations must be positive.';
 if(d.mode.includes('Walk')&&(d.oos<=0||d.runs<1||(d.periodType==='Percent'&&d.oos>=100)))return 'Set a valid out-of-sample period and positive run count.';
 if(d.mode.endsWith('matrix')&&(![d.oosStart,d.oosStop,d.oosStep,d.runsStart,d.runsStop,d.runsStep].every(Number.isFinite)||d.oosStart<=0||d.runsStart<=0||(d.periodType==='Percent'&&d.oosStop>=100)||d.oosStart>d.oosStop||d.runsStart>d.runsStop||d.oosStep<=0||d.runsStep<=0))return 'Matrix ranges require start ≤ stop and positive steps.';
 return undefined;
}
export function parameterCombinations(parameters:ParameterDraft[]):number {
 const enabled=parameters.filter(p=>p.enabled);
 if(!enabled.length)return 0;
 return enabled.reduce((total,p)=>p.step>0&&p.max>=p.min?Math.min(1e9,total*(Math.floor((p.max-p.min)/p.step)+1)):0,1);
}
