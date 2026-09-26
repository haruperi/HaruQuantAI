import { describe, expect, it } from 'vitest';
import { catalogue, categories, filterCatalogue, parseCatalogue } from '../../../../../app/plugins/data_source/Dukascopy/dukascopy';
describe('Dukascopy donor catalogue', () => {
  it('loads every symbol in source order and preserves distinct date ranges', () => {
    expect(catalogue).toHaveLength(725);
    expect(catalogue.slice(0, 3).map(row => row.symbol)).toEqual(['AUDUSD', 'EURUSD', 'GBPUSD']);
    expect(catalogue.find(row => row.symbol === 'AUDCAD')).toMatchObject({ dateFrom: '2006-01-03', dateFromM1: '2007-03-13', fullCategory: 'Forex - Crosses' });
    expect(new Set(catalogue.map(row => row.symbol)).size).toBe(725);
  });
  it('filters names and categories without reordering', () => {
    expect(filterCatalogue('aud', 'Forex - Majors').map(row => row.symbol)).toEqual(['AUDUSD']);
    expect(filterCatalogue('no-such-symbol', '')).toEqual([]);
    expect(categories.slice(0, 3)).toEqual([{ value: '', name: 'All' }, { value: 'Forex', name: 'Forex - All' }, { value: 'Forex - Majors', name: 'Forex - Majors' }]);
  });
  it('rejects malformed catalogue rows', () => {
    expect(() => parseCatalogue('broken')).toThrow();
    expect(() => parseCatalogue('X;X;Forex;Majors;31.02.2020;01.01.2020;5;1;2;3;4;3')).toThrow();
  });
});
