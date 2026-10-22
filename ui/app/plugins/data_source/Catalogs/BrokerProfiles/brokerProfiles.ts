import type { Commission, FileInstrument } from '../../FileImport/fileSymbols';
import type { SessionDefinition } from '../Sessions/sessions';

export type SpreadModel = {model: 'inherit'} | {model: 'fixed'; value: number};
export type BrokerCommission = {model: 'inherit'} | Commission;
export interface BrokerProfile {
  id:string; name:string; desc:string; postfix:string; timezone:string; mtUse:boolean;
  stockPickerUse:boolean; system:boolean; stocks:string[]; instruments:string[];
  spreadModel?:SpreadModel; commissionModel?:BrokerCommission; instrumentCount?:number; sessionCount?:number;
}
export interface BrokerUpdateJob { brokerIds:string[]; state:'running'|'paused'|'cancelled'|'completed'|'failed'; progress:number; targets:{brokerId:string;ticker:string;symbol:string}[]; error?:string }

export function normalizeBrokerName(value:string):string {
  const name=value.trim(); if(!name)throw new Error("Broker's name must be set");
  if(name.length>50)throw new Error('Broker profile name must be 50 characters or fewer.');
  return name;
}
export function validateBroker(value:BrokerProfile, existing:BrokerProfile[], originalId?:string):BrokerProfile {
  const name=normalizeBrokerName(value.name); if((value.desc??'').length>250)throw new Error('Description must be 250 characters or fewer.');
  if(typeof value.postfix!=='string'||value.postfix.length>100)throw new Error('Postfix must be 100 characters or fewer.');
  if (typeof value.timezone !== 'string' || !value.timezone.trim()) throw new Error('Choose a valid broker timezone or clock label.');
  if (value.timezone !== 'EETUS') {try {new Intl.DateTimeFormat('en',{timeZone:value.timezone}).format();} catch {throw new Error('Choose a valid broker timezone or clock label.');}}
  if(existing.some(row=>row.id!==originalId&&row.name.toLowerCase()===name.toLowerCase()))throw new Error('Name must be unique');
  validateBrokerCosts(value.spreadModel ?? {model:'inherit'},value.commissionModel ?? {model:'inherit'});
  return {...value,name,desc:value.desc??'',stocks:[...value.stocks],instruments:[...value.instruments]};
}
export function parseBrokerStocks(text:string):string[] { return text.split(/\r?\n/).map(line=>line.trim()).filter(Boolean).map(line=>line.split(';')[0].trim()).filter(Boolean); }
export function brokerCounts(profile:BrokerProfile,instruments:FileInstrument[],sessions:SessionDefinition[]){return {stocks:profile.stocks.length,instruments:profile.instrumentCount??instruments.filter(row=>row.broker===profile.id).length,sessions:profile.sessionCount??sessions.filter(row=>row.broker===profile.id).length};}
interface BrokersJson{version:1;kind:'brokers';brokers:Array<Omit<BrokerProfile,'id'|'system'|'instruments'>>}
function jsonObject(value:unknown):value is Record<string,unknown>{return Boolean(value)&&typeof value==='object'&&!Array.isArray(value);}
export function serializeBrokersJson(items:BrokerProfile[]):string{return JSON.stringify({version:1,kind:'brokers',brokers:items.map(row=>({name:row.name,desc:row.desc,postfix:row.postfix,timezone:row.timezone,mtUse:row.mtUse,stockPickerUse:row.stockPickerUse,spreadModel:row.spreadModel??{model:"inherit"},commissionModel:row.commissionModel??{model:"inherit"},stocks:[...row.stocks]}))} satisfies BrokersJson,null,2);}
export function parseBrokersJson(json:string):Omit<BrokerProfile,'id'>[]{
  if(!json||new Blob([json]).size>2_000_000)throw new Error('Cannot load brokers JSON.');let raw:unknown;try{raw=JSON.parse(json);}catch{throw new Error('Select a valid Brokers JSON file.');}
  if(!jsonObject(raw)||raw.version!==1||raw.kind!=='brokers'||!Array.isArray(raw.brokers)||!raw.brokers.length||raw.brokers.length>100)throw new Error('No Brokers found to import.');const names:string[]=[];
  return raw.brokers.map(source=>{if(!jsonObject(source)||typeof source.name!=='string'||typeof source.desc!=='string'||typeof source.postfix!=='string'||typeof source.timezone!=='string'||typeof source.mtUse!=='boolean'||typeof source.stockPickerUse!=='boolean'||!Array.isArray(source.stocks)||source.stocks.some(stock=>typeof stock!=='string'||!stock.trim()))throw new Error('Invalid broker in Brokers JSON.');
    const name=normalizeBrokerName(source.name);if(names.some(item=>item.toLowerCase()===name.toLowerCase()))throw new Error('Name must be unique');names.push(name);validateBrokerCosts(source.spreadModel??{model:'inherit'},source.commissionModel??{model:'inherit'});return {name,desc:source.desc,postfix:source.postfix,timezone:source.timezone||'UTC',mtUse:source.mtUse,stockPickerUse:source.stockPickerUse||source.stocks.length>0,system:false,stocks:[...source.stocks] as string[],instruments:[],spreadModel:(source.spreadModel??{model:'inherit'}) as SpreadModel,commissionModel:(source.commissionModel??{model:'inherit'}) as BrokerCommission};});
}
export function serializeBrokerStocksJson(stocks:string[]):string{return JSON.stringify({version:1,kind:'broker-stocks',stocks:[...stocks]},null,2);}
export function projectBrokerInstruments(items:FileInstrument[],selected:string[],broker:BrokerProfile|undefined,postfix:string):FileInstrument[]{return items.filter(row=>selected.includes(row.symbol)).map(row=>({...structuredClone(row),symbol:row.symbol+postfix,broker:broker?.id??'-1',brokerName:broker?.name??'Default',timezone:broker?.timezone||row.timezone}));}
export function projectBrokerSessions(items:SessionDefinition[],selected:string[],broker:BrokerProfile|undefined,postfix:string):SessionDefinition[]{return items.filter(row=>selected.includes(row.name)).map(row=>({...structuredClone(row),name:row.name+postfix,broker:broker?.id??'-1',brokerName:broker?.name??'Default'}));}

export function validateBrokerCosts(spread: unknown, commission: unknown): void {
  if (!jsonObject(spread) || !['inherit','fixed'].includes(String(spread.model)) || (spread.model === 'inherit' && Object.keys(spread).length !== 1) || (spread.model === 'fixed' && Object.keys(spread).sort().join() !== 'model,value') ||
    (spread.model === 'fixed' && (typeof spread.value !== 'number' || !Number.isFinite(spread.value) || spread.value < 0 || spread.value > 100000))) throw new Error('Choose a valid spread model.');
  if (!jsonObject(commission)) throw new Error('Choose a valid commission model.');
  if (commission.model === 'inherit' && Object.keys(commission).length === 1) return;
  if (!['None','Per trade','Size based','Percentage based','Stockpicker'].includes(String(commission.model)) ||
    ['value','min','max'].some(key => typeof commission[key] !== 'number' || !Number.isFinite(commission[key]) || Number(commission[key]) < 0 || Number(commission[key]) > 100000) ||
    (commission.model === 'Percentage based' && Number(commission.value) > 100) || (commission.model === 'None' && commission.value !== 0) ||
    !['share','order','equity'].includes(String(commission.unit)) || !['money','equity'].includes(String(commission.minUnit)) || !['money','equity'].includes(String(commission.maxUnit)) ||
    (commission.minUnit === commission.maxUnit && Number(commission.max) > 0 && Number(commission.max) < Number(commission.min))) throw new Error('Choose valid commission values and units.');
}
