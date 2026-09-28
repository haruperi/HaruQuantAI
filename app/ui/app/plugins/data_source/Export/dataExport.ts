import { presetRange, today, validDate, type Preset } from './presentation';

export type ExportKind = 'csv' | 'mt4' | 'mt5';
export type ExportJobState = 'running' | 'paused' | 'cancelled' | 'completed' | 'failed';

export interface ExportTarget {
  id: string;
  symbol: string;
  instrument: string;
  source: string;
  timeframe: string;
  timezone: string;
  from: string;
  to: string;
  bars: number;
  category: string;
}

export interface ExportArtifact {
  name: string;
  mime: string;
  content: string;
  targetId: string;
}

export interface CsvFormat {
  name: string;
  predefined: boolean;
  header: string;
  format: string;
}

export interface CsvExportRequest {
  targets: ExportTarget[];
  from: string;
  to: string;
  timeframe: string;
  session: string;
  timezone: string;
  prefix: string;
  includeHeader: boolean;
  header: string;
  format: string;
}

export interface Mt4ExportRequest {
  target: ExportTarget;
  from: string;
  to: string;
  installation: string;
  dataFolder: string;
  server: string;
  specificationSymbol: string;
  mt4Name: string;
  timeframe: string;
  timezone: string;
  encoding: string;
  mode: 'all' | 'hst' | 'fxt';
  properties: Record<string, string>;
}

export interface Mt5ExportRequest {
  target: ExportTarget;
  from: string;
  to: string;
  timeframe: 'tick' | 'm1';
  spreadMode: 'points' | 'pips' | 'real';
  spread: number;
  timezone: string;
  filename: string;
}

export const exportTimezones = [
  ['original', 'Original'], ['UTC', 'UTC'], ['Europe/London', 'Europe/London'],
  ['Europe/Prague', 'Europe/Prague'], ['America/New_York', 'America/New_York'],
  ['America/Chicago', 'America/Chicago'], ['Asia/Tokyo', 'Asia/Tokyo'],
  ['Asia/Hong_Kong', 'Asia/Hong_Kong'], ['Australia/Sydney', 'Australia/Sydney'],
] as const;

export const exportSessions = ['No Session', 'Forex 24/5', 'CME Equity', 'US stocks', 'Metals'] as const;

export const csvTokens = [
  '[DateTime:yyyyMMdd HH:mm:ss.SSS]', '[Date:yyyyMMdd]', '[Time:HH:mm:ss]',
  '[Open]', '[High]', '[Low]', '[Close]', '[Bid]', '[Ask]', '[Volume]', '[Spread]',
  '[Symbol]', ',', ';', '\t', '[Text:]',
] as const;

export const builtInCsvFormats: readonly CsvFormat[] = [
  { name: 'Generic tick format (comma delimited)', predefined: true, header: 'DateTime,Bid,Ask,Volume', format: '[DateTime:yyyyMMdd HH:mm:ss.SSS],[Bid],[Ask],[Volume]' },
  { name: 'Generic bar format (comma delimited)', predefined: true, header: 'Date,Time,Open,High,Low,Close,Volume', format: '[Date:yyyyMMdd],[Time:HH:mm:ss],[Open],[High],[Low],[Close],[Volume]' },
  { name: 'Generic tick format (tab delimited)', predefined: true, header: 'DateTime\tBid\tAsk\tVolume', format: '[DateTime:yyyyMMdd HH:mm:ss.SSS]\t[Bid]\t[Ask]\t[Volume]' },
  { name: 'Generic bar format (tab delimited)', predefined: true, header: 'Date\tTime\tOpen\tHigh\tLow\tClose\tVolume', format: '[Date:yyyyMMdd]\t[Time:HH:mm:ss]\t[Open]\t[High]\t[Low]\t[Close]\t[Volume]' },
  { name: 'MetaTrader4 tick format', predefined: true, header: 'DateTime,Bid,Ask,Volume', format: '[DateTime:yyyy.MM.dd HH:mm:ss.SSS],[Bid],[Ask],[Volume]' },
  { name: 'MetaTrader4 bar format', predefined: true, header: 'Date,Time,Open,High,Low,Close,Volume', format: '[Date:yyyy.MM.dd],[Time:HH:mm],[Open],[High],[Low],[Close],[Volume]' },
  { name: 'Amibroker bar (aqi) format', predefined: true, header: 'Symbol,Date,Open,High,Low,Close,Volume', format: '[Symbol],[Date:yyyyMMdd],[Open],[High],[Low],[Close],[Volume]' },
  { name: 'Amibroker tick (aqi) format', predefined: true, header: 'Symbol,DateTime,Bid,Ask,Volume', format: '[Symbol],[DateTime:yyyyMMdd HH:mm:ss.SSS],[Bid],[Ask],[Volume]' },
  { name: "Birt's CSV2FXT format", predefined: true, header: 'Date,Time,Bid,Ask,Volume', format: '[Date:yyyy.MM.dd],[Time:HH:mm:ss.SSS],[Bid],[Ask],[Volume]' },
  { name: 'Forex Tester bar format', predefined: true, header: '<TICKER>,<DTYYYYMMDD>,<TIME>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>', format: '[Symbol],[Date:yyyyMMdd],[Time:HHmmss],[Open],[High],[Low],[Close],[Volume]' },
  { name: 'Forex SB bar format', predefined: true, header: 'Date,Time,Open,High,Low,Close,Volume', format: '[Date:yyyyMMdd],[Time:HHmmss],[Open],[High],[Low],[Close],[Volume]' },
  { name: 'Ninja Trader tick format', predefined: true, header: '', format: '[DateTime:yyyyMMdd HHmmss fff];[Bid];[Volume]' },
  { name: 'Ninja Trader bar format', predefined: true, header: '', format: '[DateTime:yyyyMMdd HHmmss];[Open];[High];[Low];[Close];[Volume]' },
  { name: 'Neuroshell Trader format', predefined: true, header: 'Date,Time,Open,High,Low,Close,Volume', format: '[Date:MM/dd/yyyy],[Time:HH:mm],[Open],[High],[Low],[Close],[Volume]' },
  { name: 'Tradestation bar format', predefined: true, header: 'Date,Time,Open,High,Low,Close,Volume', format: '[Date:MM/dd/yyyy],[Time:HH:mm],[Open],[High],[Low],[Close],[Volume]' },
] as const;

export const defaultMt4Properties: Record<string, string> = {
  SYMBOL: 'EURUSD', DIGITS: '5', POINT: '0.00001', SPREAD: '12', CONTRACT_SIZE: '100000',
  LOT_MIN: '0.01', LOT_MAX: '100', LOT_STEP: '0.01', STOPS_LEVEL: '0', TICK_SIZE: '0.00001',
  TICK_VALUE: '1', SWAP_LONG: '-6.8', SWAP_SHORT: '2.1', MARGIN_INITIAL: '0', MARGIN_MAINTENANCE: '0',
};

export function safeFilename(value: string): string {
  const result = value.trim().replace(/[<>:"/\\|?*\x00-\x1f]/g, '_').replace(/[. ]+$/g, '');
  if (!result || result.length > 160) throw new Error('Enter a valid file name (maximum 160 characters).');
  return result;
}

export function selectExportTargets(rows: ExportTarget[], ids: string[], mode: ExportKind): ExportTarget[] {
  const selected = rows.filter(row => ids.includes(row.id));
  if (mode === 'csv') {
    const eligible = selected.filter(row => row.bars > 0 && row.from && row.to);
    if (!eligible.length) throw new Error('You must select at least one data record with data to export.');
    return eligible;
  }
  if (selected.length !== 1) throw new Error('You must select exactly one data record.');
  const row = selected[0];
  if (!row.bars || !row.from || !row.to) throw new Error('There is no data to export.');
  const frames = row.timeframe.toUpperCase();
  if (mode === 'mt4' && !frames.includes('TICK')) throw new Error('MT4 FXT/HST export requires Tick data.');
  if (mode === 'mt5' && !(frames.startsWith('TICK') || frames.startsWith('M1'))) throw new Error('MT5 export requires Tick or M1 source data.');
  return [row];
}

export function exportRange(targets: ExportTarget[]): { from: string; to: string } {
  if (!targets.length) throw new Error('Select data to export.');
  const from = targets.map(row => row.from).filter(Boolean).sort()[0];
  const to = targets.map(row => row.to).filter(Boolean).sort().at(-1);
  if (!from || !to) throw new Error('There is no data to export.');
  return { from, to };
}

export function exportPreset(preset: Preset, range: { from: string; to: string }, from: string, to: string) {
  const next = presetRange(preset, range.from, range.from, from, to, range.to);
  return { from: next.from < range.from ? range.from : next.from, to: next.to > range.to ? range.to : next.to };
}

export function validateRange(from: string, to: string, range: { from: string; to: string }): void {
  if (!validDate(from) || !validDate(to) || from > to) throw new Error('Choose a valid date range with From on or before To.');
  if (from < range.from || to > range.to) throw new Error(`Dates must be between ${range.from} and ${range.to}.`);
}

export function validateCsvFormat(format: CsvFormat): void {
  if (!format.name.trim() || format.name.length > 80) throw new Error('Enter a format name (1–80 characters).');
  if (!format.format.trim() || format.format.length > 1000 || format.header.length > 1000) throw new Error('Enter a valid row format (maximum 1,000 characters).');
  const tokens = [...format.format.matchAll(/\[([A-Za-z]+)(?::[^\]]*)?\]/g)].map(match => match[1]);
  if (!tokens.length || tokens.some(token => !['DateTime', 'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Bid', 'Ask', 'Volume', 'Spread', 'Symbol', 'Text'].includes(token))) throw new Error('The row format contains an unsupported or missing token.');
}

export function parseMt4Properties(text: string): Record<string, string> {
  if (!text.trim() || text.length > 200_000) throw new Error('Choose a non-empty MT4 properties file smaller than 200 KB.');
  const result: Record<string, string> = {};
  for (const raw of text.replace(/^\uFEFF/, '').split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || line.startsWith(';')) continue;
    const index = line.indexOf('=');
    if (index < 1) continue;
    const key = line.slice(0, index).trim().toUpperCase();
    const value = line.slice(index + 1).trim();
    if (/^[A-Z][A-Z0-9_]{0,63}$/.test(key) && value.length <= 200) result[key] = value;
  }
  if (!Object.keys(result).length) throw new Error('No supported KEY=value properties were found.');
  return result;
}

function pad(value: number, length = 2): string { return String(value).padStart(length, '0'); }
function formatDate(date: Date, pattern: string): string {
  return pattern.replace(/yyyy/g, String(date.getUTCFullYear())).replace(/MM/g, pad(date.getUTCMonth() + 1))
    .replace(/dd/g, pad(date.getUTCDate())).replace(/HH/g, pad(date.getUTCHours()))
    .replace(/mm/g, pad(date.getUTCMinutes())).replace(/ss/g, pad(date.getUTCSeconds()))
    .replace(/SSS|fff/g, pad(date.getUTCMilliseconds(), 3));
}

interface Sample { date: Date; open: number; high: number; low: number; close: number; bid: number; ask: number; volume: number; spread: number }
function samples(target: ExportTarget, from: string, to: string, count = 180): Sample[] {
  const start = Date.parse(`${from}T00:00:00Z`); const end = Date.parse(`${to}T23:59:00Z`);
  const total = Math.max(1, Math.min(count, Math.floor((end - start) / 60000) + 1));
  const seed = [...target.symbol].reduce((sum, char) => sum + char.charCodeAt(0), 0);
  const base = target.category === 'Forex' ? 1 + (seed % 80) / 100 : 100 + seed % 900;
  return Array.from({ length: total }, (_, index) => {
    const wave = Math.sin((seed + index) / 7) * base * 0.002; const open = base + wave;
    const close = open + Math.cos((seed + index) / 5) * base * 0.0007;
    const spread = Math.max(base * 0.00008, 0.00001);
    return { date: new Date(start + (total === 1 ? 0 : Math.floor((end - start) * index / (total - 1)))), open,
      high: Math.max(open, close) + base * 0.0005, low: Math.min(open, close) - base * 0.0005,
      close, bid: close - spread / 2, ask: close + spread / 2, volume: 100 + (seed * (index + 3)) % 900, spread };
  });
}

function decimal(value: number): string { return value.toFixed(value < 10 ? 5 : 2); }
export function renderCsvLine(template: string, target: ExportTarget, row: Sample): string {
  return template.replace(/\[([A-Za-z]+)(?::([^\]]*))?\]/g, (_all, token: string, argument?: string) => {
    if (token === 'DateTime') return formatDate(row.date, argument || 'yyyyMMdd HH:mm:ss.SSS');
    if (token === 'Date') return formatDate(row.date, argument || 'yyyyMMdd');
    if (token === 'Time') return formatDate(row.date, argument || 'HH:mm:ss');
    if (token === 'Symbol') return target.symbol;
    if (token === 'Text') return argument ?? '';
    if (token === 'Volume') return String(row.volume);
    if (token === 'Spread') return decimal(row.spread);
    const value = row[token.toLowerCase() as keyof Sample];
    return typeof value === 'number' ? decimal(value) : '';
  });
}

export function csvArtifacts(request: CsvExportRequest): ExportArtifact[] {
  const range = exportRange(request.targets); validateRange(request.from, request.to, range);
  if (!exportTimezones.some(([id]) => id === request.timezone) || !exportSessions.includes(request.session as typeof exportSessions[number])) throw new Error('Choose a valid session and timezone.');
  const namePrefix = safeFilename(request.prefix);
  validateCsvFormat({ name: 'Current', predefined: false, header: request.header, format: request.format });
  return request.targets.map(target => {
    const rows = samples(target, request.from, request.to).map(row => renderCsvLine(request.format, target, row));
    const content = [...(request.includeHeader && request.header ? [request.header] : []), ...rows].join('\r\n') + '\r\n';
    const suffix = `${target.symbol}-${request.timeframe}-${request.session.replace(/\s+/g, '_')}.csv`;
    return { name: `${namePrefix}-${safeFilename(suffix)}`, mime: 'text/csv;charset=utf-8', content, targetId: target.id };
  });
}

export function mt4Manifest(request: Mt4ExportRequest): ExportArtifact {
  const range = exportRange([request.target]); validateRange(request.from, request.to, range);
  if (!request.installation || !request.dataFolder || !request.server) throw new Error('Select the MT4 installation, data folder, and server.');
  if (!['all', 'hst', 'fxt'].includes(request.mode) || !['All', 'M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'].includes(request.timeframe)) throw new Error('Choose valid MT4 export options.');
  const symbol = safeFilename(request.mt4Name);
  const nativeTargets = request.mode === 'all' ? [`${symbol}.fxt`, `${symbol}.hst`] : [`${symbol}.${request.mode}`];
  const content = JSON.stringify({ kind: 'HaruQuantAI MT4 mock export manifest', nativeCompatible: false,
    notice: 'No FXT or HST binary was generated. A backend MT4 writer is required.', createdAt: new Date().toISOString(),
    request: { ...request, target: { id: request.target.id, symbol: request.target.symbol }, nativeTargets } }, null, 2);
  return { name: `${symbol}-mt4-export-manifest.json`, mime: 'application/json;charset=utf-8', content, targetId: request.target.id };
}

export function mt5Artifact(request: Mt5ExportRequest): ExportArtifact {
  const range = exportRange([request.target]); validateRange(request.from, request.to, range);
  if (request.target.timeframe.toUpperCase().startsWith('M1') && request.timeframe !== 'm1') throw new Error('Tick export is unavailable for M1 source data.');
  if (request.spreadMode === 'real' && !request.target.timeframe.toUpperCase().includes('TICK')) throw new Error('Real spread requires Tick source data.');
  if (!Number.isFinite(request.spread) || request.spread < 0 || request.spread > 1000) throw new Error('Spread must be between 0 and 1,000.');
  const filename = `${safeFilename(request.filename)}.csv`;
  const generated = samples(request.target, request.from, request.to);
  const lines = request.timeframe === 'tick'
    ? ['DateTime,Bid,Ask,Last,Volume,Flags', ...generated.map(row => `${formatDate(row.date, 'yyyy.MM.dd HH:mm:ss.SSS')},${decimal(row.bid)},${decimal(row.ask)},${decimal(row.close)},${row.volume},6`)]
    : ['Date,Time,Open,High,Low,Close,TickVolume,Volume,Spread', ...generated.map(row => `${formatDate(row.date, 'yyyy.MM.dd')},${formatDate(row.date, 'HH:mm')},${decimal(row.open)},${decimal(row.high)},${decimal(row.low)},${decimal(row.close)},${row.volume},${row.volume},${request.spreadMode === 'real' ? Math.round(row.spread * 100000) : request.spread}`)];
  return { name: filename, mime: 'text/csv;charset=utf-8', content: lines.join('\r\n') + '\r\n', targetId: request.target.id };
}

export function downloadExportArtifacts(artifacts: ExportArtifact[]): void {
  for (const artifact of artifacts) {
    const url = URL.createObjectURL(new Blob([artifact.content], { type: artifact.mime }));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = artifact.name; anchor.hidden = true;
    document.body.append(anchor); anchor.click(); anchor.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

export { today };
