export const sessionDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const;
export type SessionDay = typeof sessionDays[number];
export interface SessionElement { dayFrom: SessionDay; timeFrom: string; dayTo: SessionDay; timeTo: string; eod: boolean }
export interface SessionDefinition { name: string; broker: string; brokerName: string; elements: SessionElement[] }
export interface SessionBroker { id: string; name: string; postfix: string }

const weekday = (day: SessionDay, next: SessionDay, eod = true): SessionElement => ({ dayFrom: day, timeFrom: '00:00', dayTo: next, timeTo: '00:00', eod });
export const seedSessions: SessionDefinition[] = [
  { name: 'Forex 24/5', broker: '-1', brokerName: 'Default', elements: [weekday('Mon','Tue'),weekday('Tue','Wed'),weekday('Wed','Thu'),weekday('Thu','Fri'),weekday('Fri','Sat')] },
  { name: 'Metals', broker: '-1', brokerName: 'Default', elements: [
    { dayFrom:'Mon',timeFrom:'01:00',dayTo:'Mon',timeTo:'23:59',eod:true },
    { dayFrom:'Tue',timeFrom:'01:00',dayTo:'Tue',timeTo:'23:59',eod:true },
    { dayFrom:'Wed',timeFrom:'01:00',dayTo:'Wed',timeTo:'23:59',eod:true },
    { dayFrom:'Thu',timeFrom:'01:00',dayTo:'Thu',timeTo:'23:59',eod:true },
    { dayFrom:'Fri',timeFrom:'01:00',dayTo:'Fri',timeTo:'22:00',eod:true },
  ] },
  { name: 'CME Equity', broker: '-1', brokerName: 'Default', elements: [
    { dayFrom:'Mon',timeFrom:'17:00',dayTo:'Tue',timeTo:'16:00',eod:true },
    { dayFrom:'Tue',timeFrom:'17:00',dayTo:'Wed',timeTo:'16:00',eod:true },
    { dayFrom:'Wed',timeFrom:'17:00',dayTo:'Thu',timeTo:'16:00',eod:true },
    { dayFrom:'Thu',timeFrom:'17:00',dayTo:'Fri',timeTo:'16:00',eod:true },
    { dayFrom:'Sun',timeFrom:'17:00',dayTo:'Mon',timeTo:'16:00',eod:true },
  ] },
];

function validTime(value: string): boolean { return /^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value); }
export function validateElement(value: SessionElement): void {
  if (!sessionDays.includes(value.dayFrom) || !sessionDays.includes(value.dayTo) || !validTime(value.timeFrom) || !validTime(value.timeTo) || typeof value.eod !== 'boolean') throw new Error('Invalid session element.');
  if (value.dayFrom === value.dayTo && value.timeFrom > value.timeTo) throw new Error('Invalid times set. End time must be later than Start time and all times must be in 24h format');
}
export function finalSessionName(core: string, broker: SessionBroker): string { return core + broker.postfix; }
export function sessionCoreName(name: string, broker: SessionBroker | undefined): string { return broker?.postfix && name.endsWith(broker.postfix) ? name.slice(0, -broker.postfix.length) : name; }
export function validateSession(value: SessionDefinition, existing: string[], brokerIds: string[], strictName = true): void {
  if (!value.name.trim()) throw new Error('Session template name not filled');
  if (strictName && !/^[a-zA-Z0-9_-]+$/.test(value.name)) throw new Error('Session name cannot contain any special characters!');
  if (existing.some(name => name.toLowerCase() === value.name.toLowerCase())) throw new Error(`Session '${value.name}' already exists.`);
  if (!brokerIds.includes(value.broker)) throw new Error('Choose a valid broker profile.');
  if (!value.elements.length) throw new Error('No sessions defined');
  if (value.elements.length > 100) throw new Error('Too many session elements.');
  value.elements.forEach(validateElement);
}
export function generateMondayFriday(elements: SessionElement[]): SessionElement[] {
  if (!elements.length) throw new Error('No session defined. Please define Monday session and try again');
  const monday = elements.find(row => row.dayFrom === 'Mon' && (row.dayTo === 'Mon' || row.dayTo === 'Tue'));
  if (!monday) {
    if (elements.some(row => row.dayFrom === 'Mon')) throw new Error('No suitable Monday session found. Monday session must end on Monday or Tuesday');
    throw new Error('You have to create Monday session element');
  }
  const days: SessionDay[] = ['Mon','Tue','Wed','Thu','Fri'];
  const generated = days.map((day,index): SessionElement => ({ ...monday, dayFrom:day, dayTo:monday.dayTo === 'Tue' ? sessionDays[index + 1] : day }));
  return [...generated, ...elements.filter(row => row.dayFrom === 'Sat' || row.dayFrom === 'Sun')];
}
export function effectiveSessions(custom: SessionDefinition[], overrides: Record<string,SessionDefinition>, removed: string[]): SessionDefinition[] {
  const removedSet = new Set(removed); return [...seedSessions.filter(row => !removedSet.has(row.name)).map(row => overrides[row.name] ?? row), ...custom].map(row => structuredClone(row));
}
interface SessionsJson { version:1;kind:'sessions';sessions:SessionDefinition[] }
function jsonObject(value:unknown):value is Record<string,unknown>{return Boolean(value)&&typeof value==='object'&&!Array.isArray(value);}
export function serializeSessionsJson(items:SessionDefinition[]):string{return JSON.stringify({version:1,kind:'sessions',sessions:items.map(item=>structuredClone(item))} satisfies SessionsJson,null,2);}
export function parseSessionsJson(json:string):SessionDefinition[]{
  if(!json||new Blob([json]).size>2_000_000)throw new Error('Session JSON file is invalid or too large.');let raw:unknown;
  try{raw=JSON.parse(json);}catch{throw new Error('Select a valid Sessions JSON file.');}
  if(!jsonObject(raw)||raw.version!==1||raw.kind!=='sessions'||!Array.isArray(raw.sessions)||raw.sessions.length>10_000)throw new Error('Select a valid Sessions JSON file.');
  const names:string[]=[];return raw.sessions.map(source=>{if(!jsonObject(source)||typeof source.name!=='string'||!Array.isArray(source.elements))throw new Error('Invalid session in Sessions JSON.');
    const elements:SessionElement[]=source.elements.map(element=>{if(!jsonObject(element)||typeof element.dayFrom!=='string'||typeof element.dayTo!=='string'||typeof element.timeFrom!=='string'||typeof element.timeTo!=='string'||typeof element.eod!=='boolean')throw new Error('Invalid session element in Sessions JSON.');const value:SessionElement={dayFrom:element.dayFrom as SessionDay,dayTo:element.dayTo as SessionDay,timeFrom:element.timeFrom,timeTo:element.timeTo,eod:element.eod};validateElement(value);return value;});
    const value:SessionDefinition={name:source.name,broker:typeof source.broker==='string'?source.broker:'-1',brokerName:typeof source.brokerName==='string'?source.brokerName:'Default',elements};validateSession(value,names,[value.broker],false);names.push(value.name);return value;});
}
