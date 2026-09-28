import { describe, expect, it } from 'vitest';
import { discoverTD, validateTD } from '../../../../../app/plugins/DataSource/TickDownloader/tickDownloader';
describe('TickDownloader discovery and validation', () => {
  it('prefers installation tickdata folders and deduplicates file-backed symbols', () => {
    expect(discoverTD(['TD/tickdata/EURUSD/2020/a.bin', 'TD/tickdata/EURUSD/2020/b.bin', 'TD/tickdata/GBPUSD/a.bin', 'TD/bin/app.exe']).symbols).toEqual(['EURUSD', 'GBPUSD']);
  });
  it('supports a directly selected data folder and ignores root files', () => {
    expect(discoverTD(['tickdata/EURUSD/data.bin', 'tickdata/readme.txt']).symbols).toEqual(['EURUSD']);
    expect(discoverTD(['empty/readme.txt']).symbols).toEqual([]);
  });
  it('bounds discovery and rejects invalid relative paths', () => {
    expect(() => discoverTD([])).toThrow();
    expect(() => discoverTD(['TD/../secret'])).toThrow();
    expect(() => discoverTD(['TD/a/x', 'Other/b/x'])).toThrow();
    expect(() => discoverTD(Array(20001).fill('TD/a/x'))).toThrow('20,000');
  });
  it('rejects missing selection, unknown symbols and duplicate names', () => {
    const request = { folder: 'TD', symbols: ['EURUSD'], postfix: '' };
    expect(() => validateTD(request, ['EURUSD'], ['EURUSD'])).toThrow('postfix');
    expect(() => validateTD({ ...request, symbols: [] }, ['EURUSD'], [])).toThrow('at least one');
    expect(() => validateTD(request, ['GBPUSD'], [])).toThrow('chosen folder');
    expect(() => validateTD({ ...request, postfix: '_TD' }, ['EURUSD'], ['EURUSD'])).not.toThrow();
  });
});
