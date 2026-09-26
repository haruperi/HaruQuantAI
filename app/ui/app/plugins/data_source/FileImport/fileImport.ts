import type { FileDefinition, FileInstrument } from './fileSymbols';
import { validateName } from './fileSymbols';

export const columnTypes = ['', 'Date', 'Time', 'Date & Time', 'Ask', 'Bid', 'Open', 'High', 'Low', 'Close', 'Volume', 'Unused'] as const;
export type ColumnType = typeof columnTypes[number];
export interface ImportFormat { name: string; separator: string; skipRows: number; skipColumns: number; dateFormat: string; columns: ColumnType[]; predefined?: boolean }
export const datePatterns = ['yyyy.MM.dd', 'yyyy-MM-dd', 'ddMMyyyy', 'yyyyMMdd', 'dd.MM.yyyy', 'MM/dd/yyyy', 'yyyy-MM-dd HH:mm:ss', 'yyyy.MM.dd HH:mm:ss', 'yyyy-MM-dd HH:mm:ss.SSS'];
export const timeframes = ['TICK', 'M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1', 'W1', 'MN1'];
// Labels and provider aliases from SQMANAGER/timezones.csv. Metadata only; no DST conversion.
export const timezones: string[][] = [
  [
    "EETUS",
    "(EST+07) New York Trading hours, US DST"
  ],
  [
    "EET",
    "(UTC+02) European DST"
  ],
  [
    "Etc/UCT",
    "(UTC) Coordinated Universal Time"
  ],
  [
    "Europe/London",
    "(UTC) Dublin, Edinburgh, Lisbon, London"
  ],
  [
    "America/New_York",
    "(UTC-05) New York, US & Canada, EST"
  ],
  [
    "Etc/GMT+12",
    "(UTC-12) International Date Line West"
  ],
  [
    "Etc/GMT+11",
    "(UTC-11) Coordinated Universal Time-11"
  ],
  [
    "Pacific/Honolulu",
    "(UTC-10) Hawaii"
  ],
  [
    "America/Anchorage",
    "(UTC-09) Alaska"
  ],
  [
    "America/Los_Angeles",
    "(UTC-08) Baja California"
  ],
  [
    "America/Vancouver",
    "(UTC-08) Pacific Time (US & Canada)"
  ],
  [
    "America/Phoenix",
    "(UTC-07) Arizona"
  ],
  [
    "America/Chihuahua",
    "(UTC-07) Chihuahua, La Paz, Mazatlan"
  ],
  [
    "America/Denver",
    "(UTC-07) Mountain Time (US & Canada)"
  ],
  [
    "America/Chicago",
    "(UTC-06) Central America"
  ],
  [
    "America/Winnipeg",
    "(UTC-06) Central Time (US & Canada)"
  ],
  [
    "America/Mexico_City",
    "(UTC-06) Guadalajara, Mexico City, Monterrey"
  ],
  [
    "America/Regina",
    "(UTC-06) Saskatchewan"
  ],
  [
    "America/Bogota",
    "(UTC-05) Bogota, Lima, Quito, Rio Branco"
  ],
  [
    "America/New_York",
    "(UTC-05) Eastern Time (US & Canada)"
  ],
  [
    "America/Indiana/Indianapolis",
    "(UTC-05) Indiana (East)"
  ],
  [
    "America/Caracas",
    "(UTC-04:30) Caracas"
  ],
  [
    "America/Asuncion",
    "(UTC-04) Asuncion"
  ],
  [
    "America/Halifax",
    "(UTC-04) Atlantic Time (Canada)"
  ],
  [
    "America/Cuiaba",
    "(UTC-04) Cuiaba"
  ],
  [
    "America/Manaus",
    "(UTC-04) Georgetown, La Paz, Manaus, San Juan"
  ],
  [
    "America/Santiago",
    "(UTC-04) Santiago"
  ],
  [
    "America/St_Johns",
    "(UTC-03:30) Newfoundland"
  ],
  [
    "America/Sao_Paulo",
    "(UTC-03) Brasilia"
  ],
  [
    "America/Argentina/Buenos_Aires",
    "(UTC-03) Buenos Aires"
  ],
  [
    "America/Cayenne",
    "(UTC-03) Cayenne, Fortaleza"
  ],
  [
    "America/Cayenne",
    "(UTC-03) Greenland"
  ],
  [
    "America/Montevideo",
    "(UTC-03) Montevideo"
  ],
  [
    "America/Montevideo",
    "(UTC-03) Salvador"
  ],
  [
    "Etc/GMT+2",
    "(UTC-02) Coordinated Universal Time-02"
  ],
  [
    "Atlantic/Azores",
    "(UTC-01) Azores"
  ],
  [
    "Atlantic/Cape_Verde",
    "(UTC-01) Cabo Verde Is."
  ],
  [
    "Africa/Casablanca",
    "(UTC) Casablanca"
  ],
  [
    "Atlantic/Reykjavik",
    "(UTC) Monrovia, Reykjavik"
  ],
  [
    "Europe/Vienna",
    "(UTC+01) Amsterdam, Berlin, Bern, Rome, Stockholm, Vienna"
  ],
  [
    "Europe/Prague",
    "(UTC+01) Belgrade, Bratislava, Budapest, Ljubljana, Prague"
  ],
  [
    "Europe/Paris",
    "(UTC+01) Brussels, Copenhagen, Madrid, Paris"
  ],
  [
    "Europe/Warsaw",
    "(UTC+01) Sarajevo, Skopje, Warsaw, Zagreb"
  ],
  [
    "Africa/Brazzaville",
    "(UTC+01) West Central Africa"
  ],
  [
    "Africa/Windhoek",
    "(UTC+01) Windhoek"
  ],
  [
    "Asia/Amman",
    "(UTC+02) Amman"
  ],
  [
    "Europe/Athens",
    "(UTC+02) Athens, Bucharest"
  ],
  [
    "Asia/Beirut",
    "(UTC+02) Beirut"
  ],
  [
    "Africa/Cairo",
    "(UTC+02) Cairo"
  ],
  [
    "Asia/Damascus",
    "(UTC+02) Damascus"
  ],
  [
    "Africa/Harare",
    "(UTC+02) Harare, Pretoria"
  ],
  [
    "Europe/Helsinki",
    "(UTC+02) Helsinki, Kyiv, Riga, Sofia, Tallinn, Vilnius"
  ],
  [
    "Europe/Istanbul",
    "(UTC+02) Istanbul"
  ],
  [
    "Asia/Jerusalem",
    "(UTC+02) Jerusalem"
  ],
  [
    "Europe/Kaliningrad",
    "(UTC+02) Kaliningrad (RTZ 1)"
  ],
  [
    "Africa/Tripoli",
    "(UTC+02) Tripoli"
  ],
  [
    "Asia/Baghdad",
    "(UTC+03) Baghdad"
  ],
  [
    "Asia/Kuwait",
    "(UTC+03) Kuwait, Riyadh"
  ],
  [
    "Europe/Minsk",
    "(UTC+03) Minsk"
  ],
  [
    "Europe/Moscow",
    "(UTC+03) Moscow, St. Petersburg, Volgograd (RTZ 2)"
  ],
  [
    "Europe/Kiev",
    "(UTC+03) Kiev"
  ],
  [
    "Africa/Nairobi",
    "(UTC+03) Nairobi"
  ],
  [
    "Asia/Tehran",
    "(UTC+03:30) Tehran"
  ],
  [
    "Asia/Muscat",
    "(UTC+04) Abu Dhabi, Muscat"
  ],
  [
    "Asia/Baku",
    "(UTC+04) Baku"
  ],
  [
    "Europe/Samara",
    "(UTC+04) Izhevsk, Samara (RTZ 3)"
  ],
  [
    "Asia/Tbilisi",
    "(UTC+04) Port Louis"
  ],
  [
    "Asia/Tbilisi",
    "(UTC+04) Tbilisi"
  ],
  [
    "Asia/Yerevan",
    "(UTC+04) Yerevan"
  ],
  [
    "Asia/Kabul",
    "(UTC+04:30) Kabul"
  ],
  [
    "Asia/Tashkent",
    "(UTC+05) Ashgabat, Tashkent"
  ],
  [
    "Asia/Yekaterinburg",
    "(UTC+05) Ekaterinburg (RTZ 4)"
  ],
  [
    "Asia/Karachi",
    "(UTC+05) Islamabad, Karachi"
  ],
  [
    "Asia/Kolkata",
    "(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi"
  ],
  [
    "Asia/Kolkata",
    "(UTC+05:30) Sri Jayawardenepura"
  ],
  [
    "Asia/Kathmandu",
    "(UTC+05:45) Kathmandu"
  ],
  [
    "Asia/Dhaka",
    "(UTC+06) Astana"
  ],
  [
    "Asia/Dhaka",
    "(UTC+06) Dhaka"
  ],
  [
    "Asia/Novosibirsk",
    "(UTC+06) Novosibirsk (RTZ 5)"
  ],
  [
    "Asia/Rangoon",
    "(UTC+06:30) Yangon (Rangoon)"
  ],
  [
    "Asia/Bangkok",
    "(UTC+07) Bangkok, Hanoi, Jakarta"
  ],
  [
    "Asia/Krasnoyarsk",
    "(UTC+07) Krasnoyarsk (RTZ 6)"
  ],
  [
    "Asia/Urumqi",
    "(UTC+08) Beijing, Chongqing, Hong Kong, Urumqi"
  ],
  [
    "Asia/Irkutsk",
    "(UTC+08) Irkutsk (RTZ 7)"
  ],
  [
    "Asia/Kuala_Lumpur",
    "(UTC+08) Kuala Lumpur, Singapore"
  ],
  [
    "Australia/Perth",
    "(UTC+08) Perth"
  ],
  [
    "Asia/Taipei",
    "(UTC+08) Taipei"
  ],
  [
    "Asia/Ulaanbaatar",
    "(UTC+08) Ulaanbaatar"
  ],
  [
    "Asia/Tokyo",
    "(UTC+09) Osaka, Sapporo, Tokyo"
  ],
  [
    "Asia/Seoul",
    "(UTC+09) Seoul"
  ],
  [
    "Asia/Yakutsk",
    "(UTC+09) Yakutsk (RTZ 8)"
  ],
  [
    "Australia/Adelaide",
    "(UTC+09:30) Adelaide"
  ],
  [
    "Australia/Darwin",
    "(UTC+09:30) Darwin"
  ],
  [
    "Australia/Brisbane",
    "(UTC+10) Brisbane"
  ],
  [
    "Australia/Sydney",
    "(UTC+10) Canberra, Melbourne, Sydney"
  ],
  [
    "Pacific/Guam",
    "(UTC+10) Guam, Port Moresby"
  ],
  [
    "Australia/Hobart",
    "(UTC+10) Hobart"
  ],
  [
    "Asia/Magadan",
    "(UTC+10) Magadan"
  ],
  [
    "Asia/Vladivostok",
    "(UTC+10) Vladivostok, Magadan (RTZ 9)"
  ],
  [
    "Asia/Vladivostok",
    "(UTC+11) Chokurdakh (RTZ 10)"
  ],
  [
    "Pacific/Noumea",
    "(UTC+11) Solomon Is., New Caledonia"
  ],
  [
    "Asia/Anadyr",
    "(UTC+12) Anadyr, Petropavlovsk-Kamchatsky (RTZ 11)"
  ],
  [
    "Pacific/Auckland",
    "(UTC+12) Auckland, Wellington"
  ],
  [
    "Etc/GMT-12",
    "(UTC+12) Coordinated Universal Time+12"
  ],
  [
    "Pacific/Fiji",
    "(UTC+12) Fiji"
  ],
  [
    "Pacific/Tongatapu",
    "(UTC+13) Nuku'alofa"
  ],
  [
    "Etc/GMT-13",
    "(UTC+13) Samoa"
  ],
  [
    "Pacific/Kiritimati",
    "(UTC+14) Kiritimati Island"
  ],
  [
    "UTC",
    "UTC (application alias)"
  ]
];
export const builtInFormats: ImportFormat[] = [
  { name: 'Generic OHLCV', separator: ',', skipRows: 0, skipColumns: 0, dateFormat: 'yyyy-MM-dd', columns: ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'], predefined: true },
  { name: 'MetaTrader bars', separator: ',', skipRows: 0, skipColumns: 0, dateFormat: 'yyyy.MM.dd', columns: ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'], predefined: true },
  { name: 'Generic ticks', separator: ',', skipRows: 0, skipColumns: 0, dateFormat: 'yyyy-MM-dd HH:mm:ss', columns: ['Date & Time', 'Ask', 'Bid', 'Volume'], predefined: true },
];
export const customFormat = (): ImportFormat => ({ ...builtInFormats[0], name: 'Custom', predefined: false, columns: [] });
export const limits = { file: 10 * 1024 * 1024, folder: 50 * 1024 * 1024, files: 500, rows: 100000, timestamps: 200000 };
export interface ImportResult { timestamps: number[]; from: string; to: string; bars: number; timeframe: string; ignored: number; duplicates: number; error?: string }
export interface ImportRecord extends FileDefinition { timestamps: number[]; unknownBars: number }
export interface ImportTask { filename: string; record: ImportRecord; ignored: number; error?: string }
export interface ImportJob { tasks: ImportTask[]; state: 'running' | 'paused' | 'cancelled' | 'failed' | 'completed'; progress: number; completed: number; skipped: number; group: string; error?: string }

export async function readImportFile(file: File): Promise<string> {
  if (!/\.(csv|tsv|txt)$/i.test(file.name)) throw new Error(`${file.name}: choose a CSV, TSV or text file.`);
  if (file.size > limits.file) throw new Error(`${file.name}: maximum file size is 10 MiB.`);
  const bytes = await file.arrayBuffer();
  try { return new TextDecoder('utf-8', { fatal: true }).decode(bytes).replace(/^\uFEFF/, ''); }
  catch { throw new Error(`${file.name}: only UTF-8 text is supported.`); }
}
/** Quoted delimiters, escaped quotes and quoted newlines; malformed quoting fails explicitly. */
export function splitRows(text: string, separator: string): string[][] {
  if (![',', ';', '\t', '|', ' '].includes(separator)) throw new Error('Choose a supported separator.');
  const rows: string[][] = []; let row: string[] = [], cell = '', quoted = false, closed = false;
  const push = () => { row.push(cell.trim()); if (row.length > 100) throw new Error('Maximum 100 columns per file.'); if (row.some(value => value !== '')) rows.push(row); row = []; cell = ''; closed = false; if (rows.length > limits.rows + 1000) throw new Error('File exceeds the 100,000 data-row limit.'); };
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else { quoted = false; closed = true; } } else cell += c; }
    else if (c === separator) { row.push(cell.trim()); cell = ''; closed = false; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; push(); }
    else if (c === '"' && !cell && !closed) quoted = true;
    else { if (closed && c.trim()) throw new Error('Unexpected character after a quoted field.'); cell += c; }
  }
  if (quoted) throw new Error('Unclosed quoted field.');
  if (cell || row.length) push();
  return rows;
}
export function validateFormat(format: ImportFormat, mappings = true) {
  if (!Number.isInteger(format.skipRows) || format.skipRows < 0 || format.skipRows > 1000 || !Number.isInteger(format.skipColumns) || format.skipColumns < 0 || format.skipColumns > 100) throw new Error('Skip rows must be 0â€“1000 and skip columns 0â€“100.');
  if (![',', ';', '\t', '|', ' '].includes(format.separator)) throw new Error('Choose a supported separator.');
  if (!format.dateFormat || format.dateFormat.length > 80) throw new Error('Enter a supported date format.');
  if (!mappings) return;
  if (!format.columns.length || format.columns.some(type => !type || !columnTypes.includes(type))) throw new Error('Choose a type for every preview column.');
  const used: ColumnType[] = format.columns.filter(type => type !== 'Unused');
  if (new Set(used).size !== used.length) throw new Error('Each column type can be assigned only once.');
  if ((!used.includes('Date') && !used.includes('Date & Time')) || (used.includes('Date') && used.includes('Date & Time'))) throw new Error('Map one Date or Date & Time column.');
  if (!['Open', 'High', 'Low', 'Close'].every(type => used.includes(type as ColumnType)) && !['Ask', 'Bid'].every(type => used.includes(type as ColumnType))) throw new Error('Map Open, High, Low, Close or Ask and Bid.');
}
export function previewRows(text: string, format: ImportFormat) { validateFormat(format, false); return splitRows(text, format.separator).slice(format.skipRows).map(row => row.slice(format.skipColumns)); }
export function detectFormat(text: string): ImportFormat {
  const first = text.split(/\r?\n/)[0] ?? '';
  const separator = [',', ';', '\t', '|'].sort((a, b) => first.split(b).length - first.split(a).length)[0];
  const rows = splitRows(text, separator); const header = rows[0]?.some(cell => /^(date|time|open|ask|<date>)$/i.test(cell));
  const sample = rows[header ? 1 : 0] ?? [];
  const date = sample[0] ?? '';
  let pattern = /^\d{4}\.\d/.test(date) ? 'yyyy.MM.dd' : /^\d{8}$/.test(date) ? Number(date.slice(0, 4)) > 1900 && Number(date.slice(0, 4)) < 2200 ? 'yyyyMMdd' : 'ddMMyyyy' : 'yyyy-MM-dd';
  if (date.includes(' ')) pattern += date.includes('.') && date.split(' ')[1]?.includes('.') ? ' HH:mm:ss.SSS' : ' HH:mm:ss';
  const columns: ColumnType[] = sample.length === 4 ? [date.includes(' ') ? 'Date & Time' : 'Date', 'Ask', 'Bid', 'Volume'] : sample.length === 7 ? ['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'] : sample.length === 6 ? ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'] : sample.map(() => '');
  return { name: 'Custom', separator, skipRows: header ? 1 : 0, skipColumns: 0, dateFormat: pattern, columns };
}
/** Strict calendar parsing; selected timezone is retained without pretending to convert DST. */
export function parseDate(value: string, pattern: string): number {
  const tokens = pattern.match(/yyyy|MM|dd|HH|mm|ss|SSS|./g) ?? [];
  const names: string[] = [];
  const expression = tokens.map(token => {
    if (['yyyy', 'MM', 'dd', 'HH', 'mm', 'ss', 'SSS'].includes(token)) { names.push(token); return `(\\d{${token.length}})`; }
    if (/[a-zA-Z]/.test(token)) throw new Error(`Unsupported date pattern: ${pattern}`);
    return token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }).join('');
  if (!['yyyy', 'MM', 'dd'].every(token => names.includes(token)) || new Set(names).size !== names.length) throw new Error('Date format must contain yyyy, MM and dd once.');
  const match = new RegExp(`^${expression}$`).exec(value);
  if (!match) throw new Error(`Date does not match ${pattern}`);
  const parts = Object.fromEntries(names.map((name, i) => [name, Number(match[i + 1])]));
  const stamp = Date.UTC(parts.yyyy, parts.MM - 1, parts.dd, parts.HH ?? 0, parts.mm ?? 0, parts.ss ?? 0, parts.SSS ?? 0);
  const d = new Date(stamp);
  if (parts.yyyy < 1900 || d.getUTCFullYear() !== parts.yyyy || d.getUTCMonth() !== parts.MM - 1 || d.getUTCDate() !== parts.dd || d.getUTCHours() !== (parts.HH ?? 0) || d.getUTCMinutes() !== (parts.mm ?? 0) || d.getUTCSeconds() !== (parts.ss ?? 0)) throw new Error('Invalid calendar date/time.');
  return stamp;
}
export function dateExample(pattern: string) { return pattern.replace(/yyyy|MM|dd|HH|mm|ss|SSS/g, token => ({ yyyy: '2026', MM: '09', dd: '20', HH: '14', mm: '30', ss: '00', SSS: '000' })[token]!); }
export function parseImport(text: string, format: ImportFormat, timeframe: string, ignoreErrors: boolean): ImportResult {
  validateFormat(format);
  if (!['auto', 'Intraday', ...timeframes].includes(timeframe)) throw new Error('Choose a supported timeframe.');
  const rows = previewRows(text, format); if (rows.length > limits.rows) throw new Error('File exceeds the 100,000 data-row limit.');
  let ignored = 0; const stamps: number[] = []; let error: string | undefined;
  const ticks = format.columns.includes('Ask');
  if ((timeframe === 'TICK') !== ticks && timeframe !== 'auto' && timeframe !== 'Intraday') throw new Error('Column mapping does not match the chosen tick/bar timeframe.');
  for (let index = 0; index < rows.length; index++) {
    try {
      const row = rows[index]; if (row.length !== format.columns.length) throw new Error('Column count differs from the mapping.');
      const values = Object.fromEntries(format.columns.map((type, i) => [type, row[i]]));
      let date = values['Date & Time'] ?? values.Date;
      let pattern = format.dateFormat;
      if (values.Time !== undefined) { date += ` ${values.Time}`; pattern += values.Time.length > 8 ? ' HH:mm:ss.SSS' : values.Time.length > 5 ? ' HH:mm:ss' : ' HH:mm'; }
      const stamp = parseDate(date, pattern);
      const numeric: Record<string, number> = {};
      for (const type of format.columns.filter(type => ['Open', 'High', 'Low', 'Close', 'Ask', 'Bid', 'Volume'].includes(type))) {
        if (!values[type]?.trim() || !Number.isFinite(Number(values[type]))) throw new Error(`${type} is not numeric.`);
        numeric[type] = Number(values[type]);
      }
      if (numeric.Volume < 0 || (ticks ? numeric.Ask < numeric.Bid : numeric.High < Math.max(numeric.Open, numeric.Low, numeric.Close) || numeric.Low > Math.min(numeric.Open, numeric.High, numeric.Close))) throw new Error('Inconsistent price or volume values.');
      stamps.push(stamp);
    } catch (cause) { ignored++; if (!ignoreErrors) { error = `Row ${index + format.skipRows + 1}: ${cause instanceof Error ? cause.message : 'Invalid data'}`; break; } }
  }
  const unique = [...new Set(stamps)].sort((a, b) => a - b);
  if (!unique.length && !error) error = 'No valid data records remain.';
  let detected = timeframe;
  if (timeframe === 'auto' || timeframe === 'Intraday') {
    const step = unique.length > 1 ? unique.slice(1).reduce((min, value, i) => Math.min(min, value - unique[i]), Infinity) / 60000 : 1440;
    detected = ticks ? 'TICK' : step < 5 ? 'M1' : step < 15 ? 'M5' : step < 30 ? 'M15' : step < 60 ? 'M30' : step < 240 ? 'H1' : step < 1440 ? 'H4' : 'D1';
  }
  return { timestamps: unique, from: unique.length ? new Date(unique[0]).toISOString().slice(0, 10) : '', to: unique.length ? new Date(unique.at(-1)!).toISOString().slice(0, 10) : '', bars: unique.length, timeframe: detected, ignored, duplicates: stamps.length - unique.length, error };
}
export function importedRecord(base: FileDefinition, parsed: ImportResult, timezone: string, previous?: ImportRecord, replace = false): ImportRecord {
  if (!timezones.some(([id]) => id === timezone)) throw new Error('Choose a valid timezone.');
  const timestamps = [...new Set([...(replace ? [] : previous?.timestamps ?? []), ...parsed.timestamps])].sort((a, b) => a - b);
  const unknownBars = replace ? 0 : previous?.unknownBars ?? base.bars;
  const from = [replace ? '' : previous?.from ?? base.from, parsed.from].filter(Boolean).sort()[0] ?? '';
  const to = [replace ? '' : previous?.to ?? base.to, parsed.to].filter(Boolean).sort().at(-1) ?? '';
  return { ...base, timeframe: parsed.timeframe, timezone, timestamps, unknownBars, from, to, bars: unknownBars + timestamps.length };
}
export function massSymbol(stem: string, postfix: string, existing: { symbol: string; source: string }[], policy: 'overwrite' | 'skip' | 'create'): string | null {
  let symbol = stem + postfix; validateName(symbol, []);
  const conflict = existing.find(row => row.symbol === symbol);
  if (!conflict) return symbol;
  if (policy === 'skip') return null;
  if (policy === 'overwrite') { if (conflict.source !== 'File import') throw new Error(`${symbol} belongs to ${conflict.source}; choose Skip or Create new ticker.`); return symbol; }
  let suffix = 2; while (existing.some(row => row.symbol === symbol + suffix)) suffix++;
  symbol += suffix; validateName(symbol, []); return symbol;
}
export function emptyFileRecord(symbol: string, instrument: FileInstrument, barType: 'start' | 'end'): FileDefinition {
  return { id: `file:${symbol}`, symbol, instrument: instrument.symbol, underlying: instrument.symbol, source: 'File import', connection: 'History', barType, timeframe: 'â€”', broker: instrument.broker, brokerName: instrument.brokerName, timezone: instrument.timezone, category: instrument.type, from: '', to: '', bars: 0 };
}
