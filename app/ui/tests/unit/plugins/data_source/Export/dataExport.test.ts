import { beforeEach, describe, expect, it, vi } from 'vitest';
import { builtInCsvFormats, csvArtifacts, exportPreset, exportRange, mt4Manifest, mt5Artifact, parseMt4Properties, renderCsvLine, safeFilename, selectExportTargets, type ExportTarget } from '../../../../../app/plugins/data_source/Export/dataExport';

const tick: ExportTarget = { id: 'd3', symbol: 'NQ', instrument: 'NQ', source: 'Futures', timeframe: 'Tick → D1', timezone: 'America/Chicago', from: '2024-01-02', to: '2026-08-31', bars: 1000, category: 'Futures' };
const bar: ExportTarget = { id: 'd1', symbol: 'EURUSD', instrument: 'EURUSD', source: 'Dukascopy', timeframe: 'M1 → H1', timezone: 'UTC', from: '2025-01-01', to: '2025-12-31', bars: 500, category: 'Forex' };

describe('Data export contracts', () => {
  it('enforces per-export selection and data eligibility', () => {
    expect(selectExportTargets([tick, bar], ['d1', 'd3'], 'csv')).toHaveLength(2);
    expect(selectExportTargets([tick], ['d3'], 'mt4')).toEqual([tick]);
    expect(selectExportTargets([tick], ['d3'], 'mt5')).toEqual([tick]);
    expect(() => selectExportTargets([bar], ['d1'], 'mt4')).toThrow('Tick');
    expect(() => selectExportTargets([tick, bar], ['d1', 'd3'], 'mt5')).toThrow('exactly one');
    expect(() => selectExportTargets([{ ...bar, bars: 0 }], ['d1'], 'csv')).toThrow('with data');
  });

  it('clamps range presets and rejects unsafe filenames', () => {
    expect(exportRange([tick, bar])).toEqual({ from: '2024-01-02', to: '2026-08-31' });
    expect(exportPreset('allTime', exportRange([bar]), '2025-06-01', '2025-07-01')).toEqual({ from: '2025-01-01', to: '2025-12-31' });
    expect(safeFilename(' EUR/USD ')).toBe('EUR_USD');
    expect(() => safeFilename('...')).toThrow('valid file');
  });

  it('renders predefined/custom CSV tokens into bounded deterministic files', () => {
    const format = builtInCsvFormats.find(item => item.name === 'Generic bar format (comma delimited)')!;
    const files = csvArtifacts({ targets: [bar], from: bar.from, to: bar.to, timeframe: 'M1', session: 'No Session', timezone: 'original', prefix: 'sample', includeHeader: true, header: format.header, format: format.format });
    expect(files).toHaveLength(1); expect(files[0].name).toBe('sample-EURUSD-M1-No_Session.csv');
    expect(files[0].content.split('\r\n')).toHaveLength(182); expect(files[0].content).toContain('Date,Time,Open');
    expect(renderCsvLine('[Symbol],[Text:ok]', bar, { date: new Date('2025-01-01T00:00:00Z'), open: 1, high: 1, low: 1, close: 1, bid: 1, ask: 1, volume: 1, spread: 1 })).toBe('EURUSD,ok');
  });

  it('parses bounded MT4 properties and emits an honest manifest', () => {
    const properties = parseMt4Properties('# mock\nSYMBOL=GBPUSD\nDIGITS=5\nBAD KEY=x');
    expect(properties).toEqual({ SYMBOL: 'GBPUSD', DIGITS: '5' });
    const artifact = mt4Manifest({ target: tick, from: tick.from, to: tick.to, installation: 'MT4', dataFolder: 'history', server: 'Demo', specificationSymbol: 'NQ', mt4Name: 'NQ', timeframe: 'All', timezone: 'original', encoding: 'windows-1252', mode: 'all', properties });
    expect(artifact.name).toBe('NQ-mt4-export-manifest.json');
    expect(JSON.parse(artifact.content)).toMatchObject({ nativeCompatible: false, request: { nativeTargets: ['NQ.fxt', 'NQ.hst'] } });
    expect(() => parseMt4Properties('not properties')).toThrow('No supported');
  });

  it('creates MT5 Tick and M1 CSV shapes and validates real spread', () => {
    const tickFile = mt5Artifact({ target: tick, from: tick.from, to: tick.to, timeframe: 'tick', spreadMode: 'real', spread: 10, timezone: 'original', filename: 'NQ' });
    expect(tickFile.content).toMatch(/^DateTime,Bid,Ask,Last,Volume,Flags/);
    const m1File = mt5Artifact({ target: bar, from: bar.from, to: bar.to, timeframe: 'm1', spreadMode: 'pips', spread: 3, timezone: 'UTC', filename: 'EURUSD' });
    expect(m1File.content).toMatch(/^Date,Time,Open,High,Low,Close,TickVolume,Volume,Spread/);
    expect(() => mt5Artifact({ target: bar, from: bar.from, to: bar.to, timeframe: 'm1', spreadMode: 'real', spread: 3, timezone: 'UTC', filename: 'EURUSD' })).toThrow('Real spread');
  });
});

async function isolated() {
  vi.resetModules(); const memory = new Map<string, string>();
  vi.stubGlobal('localStorage', { getItem: (key: string) => memory.get(key) ?? null, setItem: (key: string, value: string) => { memory.set(key, value); } });
  return { store: (await import('../../../../../app/plugins/data_source/Export/dataExportStore')).useDataExports, memory };
}

beforeEach(() => vi.unstubAllGlobals());

it('persists custom formats and a resumable export lifecycle', async () => {
  const { store } = await isolated(); const artifact = { name: 'a.csv', mime: 'text/csv', content: 'a\r\n', targetId: 'd1' };
  store.getState().saveFormat({ name: 'Mine', predefined: false, header: 'H', format: '[Close]' });
  store.getState().start('csv', 'CSV mock export', ['d1'], [artifact], { csvFormat: 'Mine' }, false);
  store.getState().advance(); vi.resetModules();
  const restored = (await import('../../../../../app/plugins/data_source/Export/dataExportStore')).useDataExports;
  expect(restored.getState().job?.state).toBe('paused'); expect(restored.getState().formats[0].name).toBe('Mine');
  restored.getState().action('resume'); for (let i = 0; i < 10; i += 1) restored.getState().advance();
  expect(restored.getState().job?.state).toBe('completed'); expect(restored.getState().history[0].names).toEqual(['a.csv']);
});

it('fails closed on conflicts, duplicate formats and corrupt storage', async () => {
  const { store, memory } = await isolated(); const artifact = { name: 'a.csv', mime: 'text/csv', content: 'a', targetId: 'd1' };
  expect(() => store.getState().start('csv', 'CSV', ['d1'], [artifact], {}, true)).toThrow('active');
  store.getState().saveFormat({ name: 'Mine', predefined: false, header: '', format: '[Close]' });
  expect(() => store.getState().saveFormat({ name: 'Mine', predefined: false, header: '', format: '[Close]' })).toThrow('already exists');
  memory.set('haru-data-export-v1', 'bad'); vi.resetModules();
  const corrupt = (await import('../../../../../app/plugins/data_source/Export/dataExportStore')).useDataExports;
  expect(corrupt.getState().storageError).toContain('preserved'); expect(memory.get('haru-data-export-v1')).toBe('bad');
});
