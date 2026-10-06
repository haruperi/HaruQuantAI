import { describe, expect, it } from 'vitest';
import { builtInFormats, detectFormat, emptyFileRecord, importedRecord, massSymbol, parseDate, parseImport, previewRows, splitRows, validateFormat } from '../../../../../src/plugins/data_source/FileImport/fileImport';
import { newInstrument } from '../../../../../src/plugins/data_source/FileImport/fileSymbols';
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
    const base = { ...emptyFileRecord('TEST', { ...newInstrument(), symbol: 'EURUSD' }, 'end'), bars: 100, from: '2020-01-01', to: '2020-12-31' };
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

// The store is tested with isolated browser storage, without any application files or network.
describe('file import persistence and lifecycle', () => {
  async function isolated() {
    const { vi } = await import('vitest'); vi.resetModules();
    const memory = new Map<string, string>();
    const storage = { getItem: (key: string) => memory.get(key) ?? null, setItem: (key: string, value: string) => { memory.set(key, value); }, removeItem: (key: string) => { memory.delete(key); } };
    vi.stubGlobal('localStorage', storage);
    const store = (await import('../../../../../src/plugins/data_source/FileImport/fileImportStore')).useFileImports;
    const result = parseImport(csv, detectFormat(csv), 'D1', false);
    const task = (symbol: string) => ({ filename: symbol + '.csv', ignored: 0, record: importedRecord(emptyFileRecord(symbol, { ...newInstrument(), symbol: 'EURUSD' }, 'start'), result, 'UTC') });
    return { store, memory, storage, task, vi };
  }
  it('commits each file atomically, stops without applying the unfinished task, persists groups', async () => {
    const { store, task } = await isolated();
    store.getState().start([task('ONE'), task('TWO')], 'UTC', 'Folder', 1, false);
    expect(() => store.getState().start([task('OTHER')], 'UTC', '', 0, false)).toThrow('active');
    for (let i = 0; i < 10; i++) store.getState().advance();
    expect(store.getState().records.map(row => row.symbol)).toEqual(['ONE']);
    store.getState().action('pause'); store.getState().advance(); expect(store.getState().job?.progress).toBe(50);
    store.getState().action('stop'); for (let i = 0; i < 10; i++) store.getState().advance();
    expect(store.getState().records.map(row => row.symbol)).toEqual(['ONE']);
    expect(store.getState().groups).toEqual([{ name: 'Folder', symbols: ['ONE'] }]);
    expect(store.getState().job?.state).toBe('cancelled');
  });
  it('recovers running jobs paused, resumes and deduplicates saved format names', async () => {
    const { store, task, vi } = await isolated();
    store.getState().saveFormat({ ...builtInFormats[0], name: 'Saved', predefined: false });
    expect(() => store.getState().saveFormat({ ...builtInFormats[0], name: 'Saved' })).toThrow('already exists');
    store.getState().start([task('ONE')], 'UTC', '', 0, false);
    vi.resetModules(); const restored = (await import('../../../../../src/plugins/data_source/FileImport/fileImportStore')).useFileImports;
    expect(restored.getState().job?.state).toBe('paused'); expect(restored.getState().formats[0].name).toBe('Saved');
    restored.getState().action('resume'); for (let i = 0; i < 20; i++) restored.getState().advance();
    expect(restored.getState().job?.state).toBe('completed'); expect(restored.getState().records[0].bars).toBe(2);
    restored.getState().deleteFormat('Saved'); expect(restored.getState().formats).toEqual([]);
  });
  it('fails a bad file without applying its partial rows; retains preceding success', async () => {
    const { store, task } = await isolated();
    store.getState().start([task('ONE'), { ...task('BAD'), error: 'Row 5: invalid date' }], 'UTC', '', 0, false);
    for (let i = 0; i < 20; i++) store.getState().advance();
    expect(store.getState().job).toMatchObject({ state: 'failed', completed: 1, error: 'BAD.csv: Row 5: invalid date' });
    expect(store.getState().records.map(row => row.symbol)).toEqual(['ONE']);
  });
  it('keeps previous storage on quota failure and fails closed on corrupt saved data', async () => {
    const { store, task, storage, memory, vi } = await isolated();
    storage.setItem = () => { throw new Error('Quota'); };
    expect(() => store.getState().start([task('ONE')], 'UTC', '', 0, false)).toThrow('Unable to save');
    expect(store.getState().job).toBeNull(); expect(store.getState().records).toEqual([]);
    memory.set('sqx-file-import-v1', '{bad'); vi.resetModules();
    const restored = (await import('../../../../../src/plugins/data_source/FileImport/fileImportStore')).useFileImports;
    expect(restored.getState().storageError).toContain('preserved');
    expect(() => restored.getState().start([task('ONE')], 'UTC', '', 0, false)).toThrow('preserved');
    expect(memory.get('sqx-file-import-v1')).toBe('{bad');
  });
});
