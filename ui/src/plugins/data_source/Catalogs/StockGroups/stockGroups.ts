export const stockGroupLimits = { groups: 1_000, members: 10_000, csv: 2 * 1024 * 1024, json: 5 * 1024 * 1024 };

export interface StockMembership { ticker: string; from?: string; to?: string }
export interface StockGroupDefinition {
  id: string;
  name: string;
  description: string;
  system: boolean;
  members: StockMembership[];
  origin?: 'file-import';
  originName?: string;
  originFingerprint?: string;
}
export interface StockGroupDataset {
  id: string; source: string; symbol: string; instrument: string; underlying: string;
  broker: string; brokerName: string; timeframe: string; timezone: string;
  category: string; from: string; to: string; bars: number; barType: 'start';
}
export interface StockGroupUpdateJob {
  groupIds: string[]; tickers: string[]; state: 'running'|'paused'|'completed'|'failed'|'cancelled';
  progress: number; completed: number; error?: string;
}
export interface DatasetSummaryInput { symbol: string; from?: string; to?: string; bars?: number }

export function normalizeGroupName(value: string, system = false): string {
  let name = value.trim();
  if (!name) throw new Error("Group's name must be set");
  if (system) {
    name = name.replace(/^\[+|\]+$/g, '');
    name = `[[${name}]]`;
  } else {
    if (!name.startsWith('[')) name = `[${name}`;
    if (!name.endsWith(']')) name = `${name}]`;
  }
  if (name.length > 50) throw new Error('Group name must be 50 characters or fewer.');
  return name;
}

export function validateGroup(group: StockGroupDefinition, existing: StockGroupDefinition[] = []): void {
  if (!group.id || group.id.length > 200) throw new Error('Invalid stock group identity.');
  if (normalizeGroupName(group.name, group.system) !== group.name) throw new Error('Invalid stock group name.');
  if (group.description.length > 250) throw new Error('Description must be 250 characters or fewer.');
  if (existing.some(item => item.id !== group.id && item.name.toLowerCase() === group.name.toLowerCase())) throw new Error('Name must be unique');
  if (group.members.length > stockGroupLimits.members) throw new Error('Stock group exceeds the 10,000-member limit.');
  group.members.forEach(member => validateMember(member));
}

function validIso(value: string | undefined): boolean {
  if (!value) return true;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

export function validateMember(member: StockMembership): void {
  if (!member.ticker.trim() || member.ticker.length > 50 || /[;\r\n]/.test(member.ticker)) throw new Error('Ticker must contain 1–50 characters and cannot contain semicolons.');
  if (!validIso(member.from) || !validIso(member.to)) throw new Error('Invalid membership date.');
}

function parseStockDate(value: string | undefined): string | undefined {
  const raw = value?.trim();
  if (!raw) return undefined;
  let year: number, month: number, day: number;
  let match = raw.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
  if (match) [, day, month, year] = match.map(Number);
  else {
    match = raw.match(/^(\d{4})\.(\d{2})\.(\d{2})$/);
    if (!match) return undefined;
    [, year, month, day] = match.map(Number);
  }
  const date = new Date(Date.UTC(year, month - 1, day));
  if (date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) return undefined;
  return date.toISOString().slice(0, 10);
}

export function parseStockLines(text: string): StockMembership[] {
  if (new Blob([text]).size > stockGroupLimits.csv) throw new Error('Stock list exceeds the 2 MiB limit.');
  const members = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean).map(line => {
    const cells = line.split(';');
    const member: StockMembership = { ticker: cells[0].trim() };
    const from = parseStockDate(cells[1]), to = parseStockDate(cells[2]);
    if (from) member.from = from;
    if (to) member.to = to;
    validateMember(member);
    return member;
  });
  if (!members.length) throw new Error('No stocks recognized.');
  if (members.length > stockGroupLimits.members) throw new Error('Stock group exceeds the 10,000-member limit.');
  return members;
}

function displayDate(value: string | undefined): string {
  if (!value) return '';
  const [year, month, day] = value.split('-');
  return `${day}.${month}.${year}`;
}

export function formatStockLines(members: StockMembership[], exportMode = false): string {
  return members.map(member => {
    if (exportMode) return `${member.ticker};${displayDate(member.from)}${member.to ? `;${displayDate(member.to)}` : ''}`;
    return `${member.ticker}${member.from ? `;${displayDate(member.from)}` : ''}${member.to ? `;${displayDate(member.to)}` : ''}`;
  }).join('\n');
}

export function activeMemberships(group: StockGroupDefinition, today = new Date().toISOString().slice(0, 10)): StockMembership[] {
  return group.members.filter(member => (!member.from || member.from <= today) && (!member.to || member.to >= today));
}

export function summarizeGroup(group: StockGroupDefinition, datasets: DatasetSummaryInput[]) {
  const bySymbol = new Map(datasets.map(row => [row.symbol.toUpperCase(), row]));
  const matching = group.members.map(member => bySymbol.get(member.ticker.toUpperCase()));
  const numberOfSymbols = matching.filter(Boolean).length;
  const downloaded = matching.filter(row => row && (row.bars ?? 0) > 0 && row.to).length;
  const ranges = matching.filter((row): row is DatasetSummaryInput => Boolean(row?.from && row?.to));
  const from = ranges.map(row => row.from!).sort()[0] ?? '';
  const to = ranges.map(row => row.to!).sort().at(-1) ?? '';
  return { active: activeMemberships(group).length, total: group.members.length, numberOfSymbols, downloaded, ready: group.members.length > 0 && downloaded >= group.members.length - 3, from, to };
}

interface StockGroupsJson{version:1;kind:'stock-groups';groups:Array<{name:string;description:string;members:StockMembership[]}>}
function jsonObject(value:unknown):value is Record<string,unknown>{return Boolean(value)&&typeof value==='object'&&!Array.isArray(value);}
export function serializeStockGroupsJson(groups:StockGroupDefinition[]):string{return JSON.stringify({version:1,kind:'stock-groups',groups:groups.map(group=>({name:group.name,description:group.description,members:structuredClone(group.members)}))} satisfies StockGroupsJson,null,2);}
export function parseStockGroupsJson(json:string):StockGroupDefinition[]{
  if(!json||new Blob([json]).size>stockGroupLimits.json)throw new Error('Groups JSON file is invalid or too large.');let raw:unknown;
  try{raw=JSON.parse(json);}catch{throw new Error('Choose a valid Groups JSON file.');}
  if(!jsonObject(raw)||raw.version!==1||raw.kind!=='stock-groups'||!Array.isArray(raw.groups)||raw.groups.length>stockGroupLimits.groups)throw new Error('Choose a valid Groups JSON file.');
  const names:string[]=[];return raw.groups.map((source,index)=>{if(!jsonObject(source)||typeof source.name!=='string'||typeof source.description!=='string'||!Array.isArray(source.members))throw new Error('Invalid group in Groups JSON.');
    const name=normalizeGroupName(source.name);if(names.some(item=>item.toLowerCase()===name.toLowerCase()))throw new Error('Duplicate group in Groups JSON.');
    const members:StockMembership[]=source.members.map(value=>{if(!jsonObject(value)||typeof value.ticker!=='string'||(value.from!==undefined&&typeof value.from!=='string')||(value.to!==undefined&&typeof value.to!=='string'))throw new Error('Invalid stock in Groups JSON.');const member:StockMembership={ticker:value.ticker,...(value.from?{from:value.from}:{}),...(value.to?{to:value.to}:{})};validateMember(member);return member;});
    const group:StockGroupDefinition={id:`import:${index}:${name}`,name,description:source.description,system:false,members};validateGroup(group);names.push(name);return group;});
}
export function serializeStockMembersJson(members:StockMembership[]):string{return JSON.stringify({version:1,kind:'stock-group-members',stocks:structuredClone(members)},null,2);}

export function makeGeneratedDataset(ticker: string): StockGroupDataset {
  let hash = 0; for (const char of ticker) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return { id: `stock-group:${ticker}`, source: 'Equity', symbol: ticker, instrument: ticker, underlying: ticker,
    broker: '-1', brokerName: 'Default', timeframe: 'D1', timezone: 'UTC', category: 'Stocks', from: `${2000 + hash % 12}-01-03`,
    to: new Date().toISOString().slice(0, 10), bars: 2_500 + hash % 4_500, barType: 'start' };
}
