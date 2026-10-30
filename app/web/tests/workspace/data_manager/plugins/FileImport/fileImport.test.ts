import { describe, expect, it } from 'vitest';
import { builtInFormats, detectFormat, emptyFileRecord, importedRecord, massSymbol, parseDate, parseImport, previewRows, splitRows, validateFormat } from '../../../../../workspaces/data_manager/plugins/FileImport/fileImport';
import { newSymbol } from '../../../../../workspaces/data_manager/plugins/FileImport/fileSymbols';
const csv = 'Date,Open,High,Low,Close,Volume\n2026-09-18,1,3,0,2,4\n2026-09-19,2,4,1,3,5';
describe('file import rules', () => {
  it('detects headers and delimiters; handles quoted fields, CRLF and malformed quotes', () => {
    const format = detectFormat(csv.replaceAll(',', ';'));
    expect(format.separator).toBe(';'); expect(format.skipRows).toBe(1);
    expect(previewRows(csv.replaceAll(',', ';'), format)).toHaveLength(2);
    expect(splitRows('"a,b","a""b"\r\n"two\nlines",3', ',')).toEqual([['a,b', 'a"b'], ['two\nlines', '3']]);
    expect(() => splitRows('"unfinished', ',')).toThrow('Unclosed');
    expect(() => splitRows('"done"bad,4', ',')).toThrow('Unexpected');
  });
  it('validates strict calendar dates and separates time fields', () => {
    expect(new Date(parseDate('20092026', 'ddMMyyyy')).toISOString()).toBe('2026-09-20T00:00:00.000Z');
    expect(() => parseDate('2026-02-30', 'yyyy-MM-dd')).toThrow('calendar');
    expect(() => parseDate('2026-09-20', 'YYYY-MM-dd')).toThrow('Unsupported');
    const result = parseImport('2026.09.20,12:00,1,3,0,2,4\n2026.09.20,12:01,1,3,0,2,4', builtInFormats[1], 'auto', false);
    expect(result.timeframe).toBe('M1'); expect(result.bars).toBe(2);
  });
  it('deduplicates timestamps, skips errors or fails without silently importing partial data', () => {
    const text = csv + '\n2026-09-19,2,4,1,3,5\n2026-02-30,2,4,1,3,5';
    const format = detectFormat(text);
    const ignored = parseImport(text, format, 'D1', true);
    expect(ignored).toMatchObject({ bars: 2, ignored: 1, duplicates: 1, error: undefined });
    expect(parseImport(text, format, 'D1', false).error).toContain('Row 5');
    expect(parseImport('broken,1,3,0,2,4', builtInFormats[0], 'D1', true).error).toContain('No valid');
    expect(() => validateFormat({ ...format, columns: ['Date', 'Open', 'Open'] })).toThrow('only once');
    expect(() => validateFormat({ ...format, skipRows: -1 })).toThrow('Skip');
  });
  it('parses ticks and refuses mismatched mappings or invalid quotes/prices', () => {
    const text = '2026-09-20 12:00:00,2,1,4';
    expect(parseImport(text, builtInFormats[2], 'auto', false)).toMatchObject({ bars: 1, timeframe: 'TICK' });
    expect(() => parseImport(text, builtInFormats[2], 'D1', false)).toThrow('timeframe');
    expect(parseImport('2026-09-20 12:00:00,1,2,4', builtInFormats[2], 'TICK', false).error).toContain('Inconsistent');
  });
  it('merges known timestamps without inventing seeded history and honors overwrite', () => {
    const base = { ...emptyFileRecord('TEST', { ...newSymbol(), symbol: 'EURUSD' }, 'end'), bars: 100, from: '2020-01-01', to: '2020-12-31' };
    const parsed = parseImport(csv, detectFormat(csv), 'D1', false);
    const once = importedRecord(base, parsed, 'UTC');
    expect(once.bars).toBe(102); expect(importedRecord(base, parsed, 'UTC', once).bars).toBe(102);
    expect(importedRecord(base, parsed, 'UTC', once, true)).toMatchObject({ bars: 2, unknownBars: 0, from: '2026-09-18' });
  });
  it('protects other providers and allocates deterministic numbered symbols', () => {
    const existing = [{ symbol: 'EURUSD', source: 'Dukascopy' }, { symbol: 'EURUSD2', source: 'File import' }];
    expect(() => massSymbol('EURUSD', '', existing, 'overwrite')).toThrow('Dukascopy');
    expect(massSymbol('EURUSD', '', existing, 'skip')).toBeNull();
    expect(massSymbol('EURUSD', '', existing, 'create')).toBe('EURUSD3');
    expect(massSymbol('TEST', '_import', existing, 'overwrite')).toBe('TEST_import');
  });
});

describe('file import backend lifecycle', () => {
  async function isolated() {
    const {vi} = await import('vitest'); vi.resetModules();
    const memory = new Map<string,string>();
    vi.stubGlobal('localStorage',{getItem:(key:string)=>memory.get(key)??null,setItem:(key:string,value:string)=>memory.set(key,value)});
    const store = (await import('../../../../../workspaces/data_manager/plugins/FileImport/fileImportStore')).useFileImports;
    const {sourceClient,useHistoricalSources} = await import('../../../../../workspaces/data_manager/plugins/Common/historicalSourceStore');
    const task = {filename:'EURUSD.csv',content:csv,format:detectFormat(csv),ignored:0,record:importedRecord(emptyFileRecord('EURUSD',newSymbol(),'start'),parseImport(csv,detectFormat(csv),'D1',false),'UTC')};
    return {store,task,sourceClient,useHistoricalSources,vi,memory};
  }
  it('sends actual content and tracks the accepted backend job without inventing records',async()=>{
    const {store,task,sourceClient,useHistoricalSources,vi}=await isolated();
    const post=vi.spyOn(sourceClient,'post').mockResolvedValue({job_id:'real-import',status:'QUEUED',progress:0,message:'Queued'});
    await store.getState().start([task],'UTC','',0,false);
    expect(post).toHaveBeenCalledWith('/datasets/import',expect.objectContaining({files:[expect.objectContaining({content:csv,symbol:'EURUSD'})]}));
    expect(useHistoricalSources.getState().job?.job_id).toBe('real-import');
    expect(store.getState().records).toEqual([]);expect(store.getState().job).toBeNull();
  });
  it('does not claim success when the backend rejects an upload',async()=>{
    const {store,task,sourceClient,vi}=await isolated();
    vi.spyOn(sourceClient,'post').mockRejectedValue(new Error('Import rejected'));
    await expect(store.getState().start([task],'UTC','',0,false)).rejects.toThrow('Import rejected');
    expect(store.getState().records).toEqual([]);
  });
  it('requires original file content rather than restoring synthetic results',async()=>{
    const {store,task}=await isolated();
    await expect(store.getState().start([{...task,content:undefined}],'UTC','',0,false)).rejects.toThrow('original');
    await expect(store.getState().start([task],'UTC','',0,true)).rejects.toThrow('active');
  });
  it('preserves saved format behavior independently of backend jobs',async()=>{
    const {store}=await isolated();
    store.getState().saveFormat({...builtInFormats[0],name:'Saved',predefined:false});
    expect(()=>store.getState().saveFormat({...builtInFormats[0],name:'Saved'})).toThrow('already exists');
    store.getState().deleteFormat('Saved');expect(store.getState().formats).toEqual([]);
  });
});
