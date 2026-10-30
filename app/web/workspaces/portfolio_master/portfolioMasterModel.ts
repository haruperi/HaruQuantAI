export interface MasterFilter { id:number; metric:string; comparison:string; value:number }
export interface MasterDraft {
 search:'Brute force'|'Genetic search'; dateRange:'Full available'|'Limited'; from:string; to:string;
 inSample:number; reverse:boolean; min:number; max:number; limit:number; fitness:string; sectorLimit:number;
 source:string; target:string; selectedOnly:boolean; capital:number; overrideMoney:boolean; money:string;
 population:number; generations:number; restart:boolean; stagnation:number; continuous:boolean;
 correlation:{period:string;type:string;sample:string;empty:boolean;max:number;negative:boolean}; filters:MasterFilter[];
}
export const masterDefaults:MasterDraft={search:'Brute force',dateRange:'Full available',from:'2020-01-01',to:'2025-12-31',inSample:70,reverse:false,min:2,max:8,limit:100,fitness:'Return / Drawdown',sectorLimit:3,source:'Results',target:'Last generation',selectedOnly:false,capital:10000,overrideMoney:false,money:'Fixed size',population:100,generations:700,restart:true,stagnation:500,continuous:false,correlation:{period:'Day',type:'Profit / Loss',sample:'In Sample',empty:false,max:0.3,negative:true},filters:[]};
/** Editing constraints for a local preview, not a quantitative schema. */
export function masterError(d:MasterDraft,available:number):string|undefined {
 if(!Number.isInteger(d.min)||!Number.isInteger(d.max)||d.min<2||d.max<d.min)return 'Portfolio size requires min ≥ 2 and max ≥ min.';
 if(available<d.min)return 'Select enough source strategies to match the minimum portfolio size.';
 if(!Number.isFinite(d.capital)||d.capital<=0||d.limit<1)return 'Initial capital and maximum stored portfolios must be positive.';
 if(d.inSample<1||d.inSample>99)return 'In Sample part must be between 1 and 99%.';
 if(d.dateRange==='Limited'&&(!d.from||!d.to||d.from>d.to))return 'Enter a valid data range with start before end.';
 if(d.correlation.max<0||d.correlation.max>1)return 'Maximum correlation must be between 0 and 1.';
 if(d.search==='Genetic search'&&(d.population<10||d.generations<10||d.stagnation<10))return 'Genetic settings require at least 10 population, generations and stagnation generations.';
 return undefined;
}
