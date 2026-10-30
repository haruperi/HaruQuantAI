export const sessionDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const;
export type SessionDay = typeof sessionDays[number];
export interface SessionElement { dayFrom: SessionDay; timeFrom: string; dayTo: SessionDay; timeTo: string; eod: boolean; sessionType?: string; dayOfWeek?: number | null }
export interface SessionHoliday { date_str: string; description: string }
export interface SessionDefinition { id?: string; name: string; broker: string; brokerName: string; elements: SessionElement[]; timezone?: string; description?: string; holidays?: SessionHoliday[]; isDefault?: boolean; normalizationWarnings?: string[] }
export interface CatalogSession extends SessionDefinition { id: string; timezone: string; description: string; holidays: SessionHoliday[]; isDefault: boolean }
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

function validTime(value: string): boolean { return /^(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?$/.test(value); }
function seconds(value: string): number { const [h,m,s = 0] = value.split(':').map(Number); return h * 3600 + m * 60 + s; }
export function validateElement(value: SessionElement): void {
  if (!sessionDays.includes(value.dayFrom) || !sessionDays.includes(value.dayTo) || !validTime(value.timeFrom) || !validTime(value.timeTo) || typeof value.eod !== 'boolean') throw new Error('Invalid session element.');
  if (value.dayFrom === value.dayTo && seconds(value.timeFrom) >= seconds(value.timeTo)) throw new Error('End time must be later than Start time; use the next day for overnight intervals.');
}
export function validateIntervals(elements: SessionElement[]): void {
  if (elements.length > 100) throw new Error('Too many session elements.');
  const week = 604800;
  const segments: [number, number][] = [];
  for (const value of elements) {
    validateElement(value);
    const start = sessionDays.indexOf(value.dayFrom) * 86400 + seconds(value.timeFrom);
    let end = sessionDays.indexOf(value.dayTo) * 86400 + seconds(value.timeTo);
    if (end < start) end += week;
    segments.push([start, Math.min(end, week)]);
    if (end > week) segments.push([0, end - week]);
  }
  segments.sort((a,b) => a[0] - b[0] || a[1] - b[1]);
  if (segments.some((value, i) => i > 0 && segments[i - 1][1] > value[0])) throw new Error('Session intervals overlap; lunch pauses must be gaps.');
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
  validateIntervals(value.elements);
}
export function generateMondayFriday(elements: SessionElement[]): SessionElement[] {
  if (!elements.length) throw new Error('No session defined. Please define Monday session and try again');
  const monday = elements.filter(row => row.dayFrom === 'Mon');
  if (!monday.length) throw new Error('You have to create Monday session element');
  if (monday.some(row => row.dayTo !== 'Mon' && row.dayTo !== 'Tue')) throw new Error('Monday sessions must end on Monday or Tuesday');
  const days: SessionDay[] = ['Mon','Tue','Wed','Thu','Fri'];
  const generated = days.flatMap((day,index) => monday.map((row): SessionElement => ({ ...row,
    ...(row.dayOfWeek != null ? {dayOfWeek:index} : {}), dayFrom:day,
    dayTo:row.dayTo === 'Tue' ? sessionDays[index + 1] : day })));
  return [...generated, ...elements.filter(row => row.dayFrom === 'Sat' || row.dayFrom === 'Sun')];
}
export function effectiveSessions(custom: SessionDefinition[], overrides: Record<string,SessionDefinition> = {}, removed: string[] = []): SessionDefinition[] {
  const removedSet = new Set(removed);
  const base = custom.length > 0 ? custom : seedSessions;
  return base.filter(row => !removedSet.has(row.name)).map(row => structuredClone(overrides[row.name] ?? row));
}
interface SessionsJson { version:1;kind:'sessions';sessions:SessionDefinition[] }
function jsonObject(value:unknown):value is Record<string,unknown>{return Boolean(value)&&typeof value==='object'&&!Array.isArray(value);}
export function serializeSessionsJson(items:SessionDefinition[]):string{return JSON.stringify({version:1,kind:'sessions',sessions:items.map(item=>structuredClone(item))} satisfies SessionsJson,null,2);}
export function parseSessionsJson(json:string):SessionDefinition[]{
  if(!json||new Blob([json]).size>2_000_000)throw new Error('Session JSON file is invalid or too large.');let raw:unknown;
  try{raw=JSON.parse(json);}catch{throw new Error('Select a valid Sessions JSON file.');}
  if(!jsonObject(raw)||raw.version!==1||raw.kind!=='sessions'||!Array.isArray(raw.sessions)||raw.sessions.length>10_000)throw new Error('Select a valid Sessions JSON file.');
  const names:string[]=[];return raw.sessions.map(source=>{if(!jsonObject(source)||typeof source.name!=='string'||!Array.isArray(source.elements))throw new Error('Invalid session in Sessions JSON.');
    const elements:SessionElement[]=source.elements.map(element=>{if(!jsonObject(element)||typeof element.dayFrom!=='string'||typeof element.dayTo!=='string'||typeof element.timeFrom!=='string'||typeof element.timeTo!=='string'||typeof element.eod!=='boolean')throw new Error('Invalid session element in Sessions JSON.');const value:SessionElement={dayFrom:element.dayFrom as SessionDay,dayTo:element.dayTo as SessionDay,timeFrom:element.timeFrom,timeTo:element.timeTo,eod:element.eod,...(typeof element.sessionType==='string'?{sessionType:element.sessionType}:{}),...('dayOfWeek' in element?{dayOfWeek:element.dayOfWeek as number|null}:{})};validateElement(value);return value;});
    const metadata = Object.fromEntries(['id','timezone','description','holidays','isDefault'].filter(key => key in source).map(key => [key, source[key]]));
    const value:SessionDefinition={...metadata,name:source.name,broker:typeof source.broker==='string'?source.broker:'-1',brokerName:typeof source.brokerName==='string'?source.brokerName:'Default',elements};validateSession(value,names,[value.broker],false);names.push(value.name);return value;});
}

export function serializeSessionsXml(items: SessionDefinition[]): string {
  const lines: string[] = ['<?xml version="1.0" encoding="UTF-8"?>', '<Sessions>'];
  for (const item of items) {
    lines.push(`  <Session name="${item.name}" broker="${item.broker}" timezone="UTC">`);
    for (const el of item.elements) {
      lines.push(
        `    <SessionElement startDay="${el.dayFrom}" startTime="${el.timeFrom}" endDay="${el.dayTo}" endTime="${el.timeTo}" seoc="${el.eod ? 'Yes' : 'No'}" type="Regular" />`
      );
    }
    lines.push('  </Session>');
  }
  lines.push('</Sessions>');
  return lines.join('\n');
}

export function parseSessionsXml(xml: string): SessionDefinition[] {
  if (!xml || new Blob([xml]).size > 2_000_000) throw new Error('Session XML file is invalid or too large.');
  const parser = new DOMParser();
  const doc = parser.parseFromString(xml, 'application/xml');
  const parseError = doc.querySelector('parsererror');
  if (parseError) throw new Error('Select a valid Sessions XML file.');
  const sessionNodes = doc.querySelectorAll('Session');
  if (!sessionNodes.length) throw new Error('No sessions found in Sessions XML.');
  const names: string[] = [];
  const items: SessionDefinition[] = [];
  sessionNodes.forEach((node) => {
    if (node.parentElement?.tagName.toLowerCase() === 'session') return;
    const name = node.getAttribute('name') || node.querySelector('Name')?.textContent || '';
    if (!name.trim()) return;
    const broker = node.getAttribute('broker') || node.querySelector('Broker')?.textContent || '-1';
    const brokerName = broker === '-1' ? 'Default' : `Broker ${broker}`;
    const elemNodes = node.querySelectorAll('SessionElement, Session');
    const elements: SessionElement[] = [];
    elemNodes.forEach((elem) => {
      if (elem === node) return;
      const dFrom = (elem.getAttribute('startDay') || elem.getAttribute('dayFrom') || elem.querySelector('DayOfWeek')?.textContent || 'Mon').slice(0, 3) as SessionDay;
      const tFrom = (elem.getAttribute('startTime') || elem.getAttribute('timeFrom') || elem.querySelector('StartTime')?.textContent || '00:00').slice(0, 5);
      const dTo = (elem.getAttribute('endDay') || elem.getAttribute('dayTo') || dFrom).slice(0, 3) as SessionDay;
      const tTo = (elem.getAttribute('endTime') || elem.getAttribute('timeTo') || elem.querySelector('EndTime')?.textContent || '23:59').slice(0, 5);
      const seocRaw = elem.getAttribute('seoc') || elem.getAttribute('eod') || 'Yes';
      const isEod = ['yes', 'true', '1'].includes(String(seocRaw).toLowerCase());
      elements.push({
        dayFrom: dFrom,
        timeFrom: tFrom,
        dayTo: dTo,
        timeTo: tTo,
        eod: isEod,
      });
    });
    const value: SessionDefinition = { name, broker, brokerName, elements };
    validateSession(value, names, [broker], false);
    names.push(name);
    items.push(value);
  });
  return items;
}
