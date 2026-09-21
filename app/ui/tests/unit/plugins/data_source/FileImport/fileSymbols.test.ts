import { describe, expect, it } from 'vitest';
import { canonicalInstrument, commissionModels, defaultCommission, newInstrument, validateInstrument, validateName } from '../../../../../src/plugins/data_source/FileImport/fileSymbols';
describe('file symbol rules', () => {
  it('accepts the donor name pattern and rejects empty, invalid and duplicate names', () => {
    validateName('EURUSD_1@feed.:$', []);
    for (const name of ['', 'bad name', '../bad/name']) expect(() => validateName(name, [])).toThrow();
    expect(() => validateName('EURUSD', ['EURUSD'])).toThrow('already exists');
  });
  it('uses donor defaults and validates numerical and swap bounds', () => {
    expect(newInstrument().pointValue).toBe(100000);
    expect(newInstrument('Futures').tickSize).toBe(0.1);
    const value = { ...newInstrument(), symbol: 'TEST' };
    validateInstrument(value, [], ['-1']);
    for (const patch of [{ multiplier: 0 }, { spread: NaN }, { tickSize: -1 }, { broker: 'missing' }]) expect(() => validateInstrument({ ...value, ...patch }, [], ['-1'])).toThrow();
    expect(() => validateInstrument({ ...value, swap: { ...value.swap, rolloutHour: '25:00' } }, [], ['-1'])).toThrow('swap');
  });
  it('validates all bundled commission models and keeps canonical JSON objects', () => {
    for (const model of commissionModels) {
      const value = { ...newInstrument(), symbol: 'TEST', commission: defaultCommission(model) };
      validateInstrument(value, [], ['-1']);
      const json = canonicalInstrument(value);
      expect(json.swap.rolloutHour).toBe('23:00');
      expect(json.commission.model).toBe(model);
      expect(Object.keys(json).sort()).toEqual(['broker','brokerName','commission','minDistance','multiplier','name','pointValue','sizeStep','slippage','spread','swap','symbol','tickSize','tickStep','timezone','type'].sort());
    }
    expect(() => validateInstrument({ ...newInstrument(), symbol: 'TEST', commission: { ...defaultCommission('Percentage based'), value: 101 } }, [], ['-1'])).toThrow('commission');
  });
});
