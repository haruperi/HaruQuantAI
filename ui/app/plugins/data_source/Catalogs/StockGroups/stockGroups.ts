export const stockGroupLimits = { groups: 1_000, members: 50_000, csv: 20 * 1024 * 1024, json: 20 * 1024 * 1024 };

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
    name = `[${name.replace(/^[\[\]]+|[\[\]]+$/g, '')}]`;
    if(!name.slice(1,-1).trim())throw new Error("Group's name must be set");
  }
  if (name.length > 50) throw new Error('Group name must be 50 characters or fewer.');
  return name;
}

export function validateGroup(group: StockGroupDefinition, existing: StockGroupDefinition[] = []): void {
  if (!group.id || group.id.length > 200) throw new Error('Invalid stock group identity.');
  if (normalizeGroupName(group.name, group.system) !== group.name) throw new Error('Invalid stock group name.');
  if (group.description.length > 250) throw new Error('Description must be 250 characters or fewer.');
  if (existing.some(item => item.id !== group.id && item.name.toLowerCase() === group.name.toLowerCase())) throw new Error('Name must be unique');
  if (group.members.length > stockGroupLimits.members) throw new Error('Stock group exceeds the 50,000-member limit.');
  group.members.forEach(member => validateMember(member));
}

function validIso(value: string | undefined): boolean {
  if (!value) return true;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.getTime()) && date.toISOString().slice(0, 10) === value;
}

export function validateMember(member: StockMembership): void {
  if (!member.ticker.trim() || member.ticker.length > 50 || /[;\u0000-\u001f\u007f]/.test(member.ticker)) throw new Error('Ticker must contain 1–50 characters and cannot contain semicolons.');
  if (!validIso(member.from) || !validIso(member.to)) throw new Error('Invalid membership date.');
  if(member.from && member.to && member.from>member.to)throw new Error('Membership end must not precede its start.');
}

function parseStockDate(value: string | undefined): string | undefined {
  const raw = value?.trim();
  if (!raw) return undefined;
  if(/^\d{4}-\d{2}-\d{2}$/.test(raw)){if(!validIso(raw))throw new Error('Invalid membership date.');return raw;}
  let year: number, month: number, day: number;
  let match = raw.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
  if (match) [, day, month, year] = match.map(Number);
  else {
    match = raw.match(/^(\d{4})\.(\d{2})\.(\d{2})$/);
    if (!match) throw new Error('Invalid membership date.');
    [, year, month, day] = match.map(Number);
  }
  const date = new Date(0);date.setUTCFullYear(year,month-1,day);date.setUTCHours(0,0,0,0);
  if (date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) throw new Error('Invalid membership date.');
  return date.toISOString().slice(0, 10);
}

export function parseStockLines(text: string): StockMembership[] {
  if (new Blob([text]).size > stockGroupLimits.csv) throw new Error('Stock list exceeds the 20 MiB limit.');
  const members = text.split(/\r?\n/).map(line => line.trim()).filter(Boolean).map(line => {
    const cells = line.split(';');
    if(cells.length>3)throw new Error('Membership has too many fields.');
    const member: StockMembership = { ticker: cells[0].trim() };
    const from = parseStockDate(cells[1]), to = parseStockDate(cells[2]);
    if (from) member.from = from;
    if (to) member.to = to;
    validateMember(member);
    return member;
  });
  if (members.length > stockGroupLimits.members) throw new Error('Stock group exceeds the 50,000-member limit.');
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
    return `${member.ticker}${member.from || member.to ? `;${displayDate(member.from)}` : ''}${member.to ? `;${displayDate(member.to)}` : ''}`;
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
  return { active: activeMemberships(group).length, total: group.members.length, numberOfSymbols, downloaded, ready: group.members.length > 0 && downloaded >= group.members.length, from, to };
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

export function serializeStockGroupsXml(groups: StockGroupDefinition[]): string {
  let xml = '<?xml version="1.0" encoding="UTF-8"?>\n<Groups>\n';
  for (const group of groups) {
    xml += `  <Group name="${escapeXml(group.name)}">\n`;
    xml += `    <Desc>${escapeXml(group.description || '')}</Desc>\n`;
    xml += '    <Stocks>\n';
    for (const member of group.members) {
      let stockTag = `      <Stock name="${escapeXml(member.ticker)}"`;
      if (member.from) stockTag += ` from="${member.from}"`;
      if (member.to) stockTag += ` to="${member.to}"`;
      stockTag += '/>\n';
      xml += stockTag;
    }
    xml += '    </Stocks>\n';
    xml += '  </Group>\n';
  }
  xml += '</Groups>\n';
  return xml;
}

function unescapeXml(str: string): string {
  return str
    .replace(/&apos;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&gt;/g, '>')
    .replace(/&lt;/g, '<')
    .replace(/&amp;/g, '&');
}

export function parseStockGroupsXml(xmlText: string): StockGroupDefinition[] {
  if (!xmlText || new Blob([xmlText]).size > stockGroupLimits.json) {
    throw new Error('Groups XML file is invalid or too large.');
  }
  if (!/<Groups\b[^>]*>/i.test(xmlText) || !/<\/Groups>/i.test(xmlText)) {
    throw new Error('Choose a valid Groups XML file.');
  }

  const groupRegex = /<Group\b([^>]*)>([\s\S]*?)<\/Group>/gi;
  const groups: StockGroupDefinition[] = [];
  const names: string[] = [];
  let groupMatch: RegExpExecArray | null;

  while ((groupMatch = groupRegex.exec(xmlText)) !== null) {
    if (groups.length >= stockGroupLimits.groups) {
      throw new Error('Choose a valid Groups XML file.');
    }
    const attrs = groupMatch[1];
    const inner = groupMatch[2];
    const nameMatch = /name=(["'])(.*?)\1/i.exec(attrs);
    if (!nameMatch) {
      throw new Error('Choose a valid Groups XML file.');
    }
    const name = normalizeGroupName(unescapeXml(nameMatch[2]));
    if (names.some(item => item.toLowerCase() === name.toLowerCase())) {
      throw new Error('Duplicate group in Groups XML.');
    }
    const descMatch = /<Desc\b[^>]*>([\s\S]*?)<\/Desc>/i.exec(inner);
    const description = descMatch ? unescapeXml(descMatch[1].trim()) : '';

    const members: StockMembership[] = [];
    const stockRegex = /<Stock\b([^>]*)\/?>/gi;
    let stockMatch: RegExpExecArray | null;
    while ((stockMatch = stockRegex.exec(inner)) !== null) {
      const stockAttrs = stockMatch[1];
      const stockNameMatch = /name=(["'])(.*?)\1/i.exec(stockAttrs);
      if (!stockNameMatch) continue;
      const ticker = unescapeXml(stockNameMatch[2].trim());
      const fromMatch = /from=(["'])(.*?)\1/i.exec(stockAttrs);
      const toMatch = /to=(["'])(.*?)\1/i.exec(stockAttrs);
      const from = parseStockDate(fromMatch ? fromMatch[2] : undefined);
      const to = parseStockDate(toMatch ? toMatch[2] : undefined);
      const member: StockMembership = { ticker, ...(from ? { from } : {}), ...(to ? { to } : {}) };
      validateMember(member);
      members.push(member);
    }
    const group: StockGroupDefinition = {
      id: `import:${groups.length}:${name}`,
      name,
      description,
      system: false,
      members,
    };
    validateGroup(group);
    names.push(name);
    groups.push(group);
  }

  if (groups.length === 0) {
    throw new Error('Choose a valid Groups XML file.');
  }

  return groups;
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
