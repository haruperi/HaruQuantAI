import { parseDate, splitRows } from './presentation';

export const externalIndicatorTypes = [
  { value: 1, label: 'Indicator value - price' },
  { value: 2, label: 'Indicator value - number' },
  { value: 3, label: 'Indicator value - price range' },
  { value: 10, label: 'Signal - 0 means false, anything else means true' },
] as const;
export type ExternalIndicatorType = 1 | 2 | 3 | 10;
export interface ExternalIndicatorLine { name: string; mt4: string; mt5: string; el: string }
export interface ExternalIndicatorRecord { timestamp: number; values: number[] }
export interface ExternalIndicatorDefinition {
  name: string; type: ExternalIndicatorType; values: ExternalIndicatorLine[];
  timeframe: string; dateFrom: string; dateTo: string; totalDays: number;
  records: ExternalIndicatorRecord[];
}
export type ExternalColumnType = '' | 'Date' | 'Time' | 'Date & Time' | 'Unused' | `Value ${number}`;
export interface ExternalImportFormat {
  name: string; separator: string; skipRows: number; skipColumns: number;
  dateFormat: string; columns: ExternalColumnType[]; predefined?: boolean;
}
export interface ExternalImportJob {
  canPause?: false; indicator: string; state: 'running' | 'paused' | 'cancelled' | 'failed' | 'completed';
  progress: number; records: ExternalIndicatorRecord[]; timeframe: string; ignored: number; error?: string;
}
export const emptyExternalLines = (): ExternalIndicatorLine[] => Array.from({ length: 3 }, () => ({ name: '', mt4: '', mt5: '', el: '' }));
export const externalDateFormats = ['yyyy.MM.dd', 'yyyy-MM-dd', 'ddMMyyyy', 'yyyyMMdd', 'dd.MM.yyyy', 'MM/dd/yyyy', 'yyyy-MM-dd HH:mm:ss', 'yyyy.MM.dd HH:mm:ss'];
export const externalSeparators = [{ label: 'Comma', value: ',' }, { label: 'Semicolon', value: ';' }, { label: 'Tab', value: '\t' }, { label: 'Pipe', value: '|' }, { label: 'Space', value: ' ' }];
export const builtInExternalFormats: ExternalImportFormat[] = [
  { name: 'Custom', separator: ',', skipRows: 0, skipColumns: 0, dateFormat: 'yyyy-MM-dd HH:mm:ss', columns: [], predefined: true },
];
export const externalLimits = { file: 10 * 1024 * 1024, rows: 100_000, records: 200_000, mq4: 2 * 1024 * 1024, json: 2 * 1024 * 1024 };

const isType = (value: number): value is ExternalIndicatorType => externalIndicatorTypes.some(item => item.value === value);
export function externalTypeLabel(value: ExternalIndicatorType): string { return externalIndicatorTypes.find(item => item.value === value)?.label ?? ''; }
export function activeExternalLines(item: Pick<ExternalIndicatorDefinition, 'values'>): ExternalIndicatorLine[] { return item.values.filter(line => line.name.trim()); }
export function validateExternalDefinition(item: ExternalIndicatorDefinition, existing: string[] = []): void {
  item.name = item.name.trim();
  if (!item.name) throw new Error('Name cannot be empty');
  if (item.name.length > 128) throw new Error('Name must be 128 characters or fewer.');
  if (existing.some(name => name.toLowerCase() === item.name.toLowerCase())) throw new Error(`Custom data with name '${item.name}' already exists.`);
  if (!isType(item.type)) throw new Error('Choose a valid return type.');
  if (!Array.isArray(item.values) || item.values.length !== 3) throw new Error('Exactly three indicator value lines are required.');
  const names: string[] = [];
  for (const line of item.values) {
    if (!line || ['name', 'mt4', 'mt5', 'el'].some(key => typeof line[key as keyof ExternalIndicatorLine] !== 'string')) throw new Error('Invalid indicator value line.');
    line.name = line.name.trim();
    if (!/^[a-zA-Z0-9]*$/.test(line.name)) throw new Error('Value name cannot contain any special characters!');
    if ([line.name, line.mt4, line.mt5, line.el].some(value => value.length > 500)) throw new Error('Indicator value fields must be 500 characters or fewer.');
    if (line.name && names.includes(line.name)) throw new Error('Value names must be unique!');
    if (line.name) names.push(line.name);
  }
  if (!names.length) throw new Error('At least one value must be specified!');
  if (!Array.isArray(item.records) || item.records.length > externalLimits.records) throw new Error('Invalid indicator records.');
  const count = names.length;
  item.records.forEach((row, index) => {
    if (!Number.isFinite(row.timestamp) || row.values.length !== count || row.values.some(value => !Number.isFinite(value)) || (index && row.timestamp <= item.records[index - 1].timestamp)) throw new Error('Invalid indicator records.');
  });
}
export function validateExternalFormat(format: ExternalImportFormat, valueCount: number, mappings = true): void {
  if (!format.name.trim() || format.name.length > 80) throw new Error('Name cannot be empty');
  if (!externalSeparators.some(item => item.value === format.separator)) throw new Error('Choose a supported separator.');
  if (!Number.isInteger(format.skipRows) || format.skipRows < 0 || format.skipRows > 1000 || !Number.isInteger(format.skipColumns) || format.skipColumns < 0 || format.skipColumns > 100) throw new Error('Skip rows must be 0–1000 and skip columns 0–100.');
  if (!format.dateFormat || format.dateFormat.length > 80) throw new Error('Enter a supported date format.');
  if (!mappings) return;
  if (!format.columns.length || format.columns.some(type => !type)) throw new Error('Select type for each column.');
  const used = format.columns.filter(type => type !== 'Unused');
  if (new Set(used).size !== used.length) throw new Error('Each column type can be assigned only once.');
  const hasDate = used.includes('Date'), hasDateTime = used.includes('Date & Time');
  if (hasDate === hasDateTime) throw new Error('Map one Date or Date & Time column.');
  for (let index = 1; index <= valueCount; index++) if (!used.includes(`Value ${index}`)) throw new Error(`Map Value ${index}.`);
}
export async function readExternalFile(file: File): Promise<string> {
  if (!/\.(csv|tsv|txt)$/i.test(file.name)) throw new Error('Choose a CSV, TSV or text data file.');
  if (file.size > externalLimits.file) throw new Error('Maximum data file size is 10 MiB.');
  try { return new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer()).replace(/^\uFEFF/, ''); }
  catch { throw new Error('Only UTF-8 text data files are supported.'); }
}
export function externalPreview(text: string, format: ExternalImportFormat): string[][] {
  validateExternalFormat(format, 0, false);
  return splitRows(text, format.separator).slice(format.skipRows).map(row => row.slice(format.skipColumns));
}
export function detectExternalFormat(text: string, valueCount: number): ExternalImportFormat {
  const first = text.split(/\r?\n/)[0] ?? '';
  const separator = [',', ';', '\t', '|'].sort((a, b) => first.split(b).length - first.split(a).length)[0];
  const rows = splitRows(text, separator); const header = rows[0]?.some(cell => /^(date|time|value)/i.test(cell));
  const sample = rows[header ? 1 : 0] ?? []; const firstCell = sample[0] ?? '';
  let dateFormat = /^\d{4}\.\d/.test(firstCell) ? 'yyyy.MM.dd' : /^\d{8}$/.test(firstCell) ? 'yyyyMMdd' : 'yyyy-MM-dd';
  if (firstCell.includes(' ')) dateFormat += ' HH:mm:ss';
  const dateColumns: ExternalColumnType[] = firstCell.includes(' ') ? ['Date & Time'] : sample[1]?.includes(':') ? ['Date', 'Time'] : ['Date'];
  return { name: 'Custom', separator, skipRows: header ? 1 : 0, skipColumns: 0, dateFormat, columns: [...dateColumns, ...Array.from({ length: valueCount }, (_, i): ExternalColumnType => `Value ${i + 1}`), ...Array.from({ length: Math.max(0, sample.length - dateColumns.length - valueCount) }, (): ExternalColumnType => 'Unused')], predefined: true };
}
export function parseExternalData(text: string, format: ExternalImportFormat, valueCount: number, ignoreErrors: boolean): { records: ExternalIndicatorRecord[]; ignored: number; timeframe: string } {
  validateExternalFormat(format, valueCount); const rows = externalPreview(text, format);
  if (rows.length > externalLimits.rows) throw new Error('File exceeds the 100,000 data-row limit.');
  const parsed: ExternalIndicatorRecord[] = []; let ignored = 0;
  for (let index = 0; index < rows.length; index++) {
    try {
      const row = rows[index]; if (row.length !== format.columns.length) throw new Error('Column count differs from the mapping.');
      const values = Object.fromEntries(format.columns.map((type, column) => [type, row[column]]));
      let date = values['Date & Time'] ?? values.Date ?? ''; let pattern = format.dateFormat;
      if (values.Time !== undefined) { date += ` ${values.Time}`; pattern += values.Time.length > 5 ? ' HH:mm:ss' : ' HH:mm'; }
      const result = Array.from({ length: valueCount }, (_, i) => Number(values[`Value ${i + 1}`]));
      if (result.some(value => !Number.isFinite(value))) throw new Error('Indicator value is not numeric.');
      parsed.push({ timestamp: parseDate(date, pattern), values: result });
    } catch (cause) {
      ignored++;
      if (!ignoreErrors) throw new Error(`Row ${index + format.skipRows + 1}: ${cause instanceof Error ? cause.message : 'Invalid data'}`);
    }
  }
  const unique = [...new Map(parsed.map(row => [row.timestamp, row])).values()].sort((a, b) => a.timestamp - b.timestamp);
  if (!unique.length) throw new Error('No valid data records remain.');
  const step = unique.length > 1 ? unique.slice(1).reduce((min, row, i) => Math.min(min, row.timestamp - unique[i].timestamp), Infinity) / 60000 : 1440;
  const timeframe = step < 5 ? 'M1' : step < 15 ? 'M5' : step < 30 ? 'M15' : step < 60 ? 'M30' : step < 240 ? 'H1' : step < 1440 ? 'H4' : step < 10080 ? 'D1' : 'W1';
  return { records: unique, ignored, timeframe };
}
export function summarizeExternal(item: ExternalIndicatorDefinition): ExternalIndicatorDefinition {
  if (!item.records.length) return { ...item, timeframe: '—', dateFrom: '', dateTo: '', totalDays: 0 };
  const dateFrom = new Date(item.records[0].timestamp).toISOString().slice(0, 10), dateTo = new Date(item.records.at(-1)!.timestamp).toISOString().slice(0, 10);
  return { ...item, dateFrom, dateTo, totalDays: Math.floor((item.records.at(-1)!.timestamp - item.records[0].timestamp) / 86_400_000) + 1 };
}
export function recognizeMq4(filename: string, source: string): ExternalIndicatorDefinition {
  if (!/\.mq4$/i.test(filename)) throw new Error('Select an MQ4 indicator file.');
  if (new Blob([source]).size > externalLimits.mq4) throw new Error('Maximum MQ4 file size is 2 MiB.');
  const bufferMatch = source.match(/#property\s+indicator_buffers\s+(\d+)/i); const declared = Number(bufferMatch?.[1] ?? 0);
  const labels = new Map<number, string>();
  for (const match of source.matchAll(/#property\s+indicator_label(\d+)\s+"([^"]+)"/gi)) labels.set(Number(match[1]) - 1, match[2]);
  for (const match of source.matchAll(/SetIndexLabel\s*\(\s*(\d+)\s*,\s*"([^"]+)"/gi)) labels.set(Number(match[1]), match[2]);
  const bound = [...source.matchAll(/SetIndexBuffer\s*\(\s*(\d+)\s*,\s*([A-Za-z_]\w*)/gi)].map(match => ({ index: Number(match[1]), name: match[2] }));
  const count = Math.max(declared, labels.size, bound.length); if (!count) throw new Error('Failed to recognize custom indicator from file. Reason: no output buffers found');
  if (count > 3) throw new Error('Recognized indicator has more than three output lines.');
  const values = emptyExternalLines(); const used = new Set<string>();
  for (let index = 0; index < count; index++) { const fallback = bound.find(item => item.index === index)?.name?.replace(/(?:Ext)?(?:Buffer)?$/gi, '') || `Value${index + 1}`; const raw = labels.get(index) || fallback; const base = raw.replace(/[^a-zA-Z0-9]/g, '').slice(0, 76) || `Value${index + 1}`; let name = base; let suffix = 2; while (used.has(name)) name = `${base}${suffix++}`; used.add(name); values[index].name = name; values[index].mt4 = `iCustom(Symbol(), Period(), "${filename.replace(/\.mq4$/i, '')}", ${index}, shift)`; }
  const item: ExternalIndicatorDefinition = { name: filename.replace(/\.mq4$/i, '').trim(), type: 2, values, timeframe: '—', dateFrom: '', dateTo: '', totalDays: 0, records: [] }; validateExternalDefinition(item); return item;
}
interface ExternalIndicatorsJson{version:1;kind:'external-indicators';indicators:Array<Pick<ExternalIndicatorDefinition,'name'|'type'|'values'>>}
function jsonObject(value:unknown):value is Record<string,unknown>{return Boolean(value)&&typeof value==='object'&&!Array.isArray(value);}
export function serializeExternalIndicatorsJson(items:ExternalIndicatorDefinition[]):string{return JSON.stringify({version:1,kind:'external-indicators',indicators:items.map(item=>({name:item.name,type:item.type,values:structuredClone(item.values)}))} satisfies ExternalIndicatorsJson,null,2);}
export function parseExternalIndicatorsJson(json:string):ExternalIndicatorDefinition[]{
  if(!json||new Blob([json]).size>externalLimits.json)throw new Error('External indicators JSON file is invalid or too large.');let raw:unknown;
  try{raw=JSON.parse(json);}catch{throw new Error('Select a valid ExternalIndicators JSON file.');}
  if(!jsonObject(raw)||raw.version!==1||raw.kind!=='external-indicators'||!Array.isArray(raw.indicators)||raw.indicators.length>10_000)throw new Error('Select a valid ExternalIndicators JSON file.');
  const names:string[]=[];return raw.indicators.map(source=>{if(!jsonObject(source)||typeof source.name!=='string'||typeof source.type!=='number'||!Array.isArray(source.values))throw new Error('Invalid indicator in ExternalIndicators JSON.');
    const values=structuredClone(source.values) as ExternalIndicatorLine[];const item:ExternalIndicatorDefinition={name:source.name,type:source.type as ExternalIndicatorType,values,timeframe:'—',dateFrom:'',dateTo:'',totalDays:0,records:[]};validateExternalDefinition(item,names);names.push(item.name);return item;});
}
