import { describe, expect, it } from 'vitest';
import {
  applyMassPatch,
  effectiveInstruments,
  newInstrument,
  parseInstrumentsJson,
  serializeInstrumentsJson,
  type InstrumentBroker,
} from '../../../../../../src/plugins/data_source/Catalogs/Instruments/instruments';

const brokers: InstrumentBroker[] = [
  { id: '-1', name: 'Default', postfix: '', timezone: 'UTC' },
  { id: 'demo', name: 'Demo & Broker', postfix: '_demo', timezone: 'EST+07' },
];

describe('instrument management rules', () => {
  it('composes seed overrides, custom instruments, and removals', () => {
    const custom = { ...newInstrument('Stock'), symbol: 'CUSTOM', name: 'Custom' };
    const seed = effectiveInstruments([], {}, [])[0];
    const overridden = { ...seed, spread: seed.spread + 2 };
    const result = effectiveInstruments([custom], { [seed.symbol]: overridden }, ['GBPJPY']);
    expect(result.find(item => item.symbol === seed.symbol)?.spread).toBe(overridden.spread);
    expect(result.some(item => item.symbol === 'GBPJPY')).toBe(false);
    expect(result.find(item => item.symbol === 'CUSTOM')?.type).toBe('Stock');
  });

  it('applies only enabled mass-edit fields without mutating the source', () => {
    const source = { ...newInstrument(), symbol: 'SOURCE', spread: 1, slippage: 2 };
    const value = { ...source, spread: 9, slippage: 10, commission: { ...source.commission, model: 'Per trade' as const, value: 4 } };
    const result = applyMassPatch(source, { fields: { spread: true, commission: true }, value });
    expect(result.spread).toBe(9);
    expect(result.slippage).toBe(2);
    expect(result.commission).toEqual(value.commission);
    expect(source.spread).toBe(1);
  });

  it('round trips complete JSON and maps broker metadata by identity', () => {
    const item = {
      ...newInstrument('Stock'), symbol: 'AB_demo', name: 'A & B < test', broker: 'demo',
      brokerName: 'Demo & Broker', timezone: 'EST+07',
      commission: { model: 'Stockpicker' as const, value: 0.0035, unit: 'share', min: 0.35, minUnit: 'money', max: 1, maxUnit: 'equity' },
      swap: { use: true, type: 'percent' as const, long: -1.5, short: 0.5, tripleSwapOn: 'FRIDAY', rolloutHour: '22:30' },
    };
    const json = serializeInstrumentsJson([item], brokers);
    expect(JSON.parse(json)).toMatchObject({version:1,kind:'instruments',brokers:[{name:'Demo & Broker'}]});
    expect(parseInstrumentsJson(json, brokers)).toEqual([item]);
  });

  it('rejects malformed, wrong-kind, empty, and duplicate JSON before mutation', () => {
    for (const json of ['', '{', '{}', '{"version":1,"kind":"sessions","instruments":[]}', '{"version":1,"kind":"instruments","brokers":[],"instruments":[]}']) {
      expect(() => parseInstrumentsJson(json, brokers)).toThrow();
    }
    const first = { ...newInstrument(), symbol: 'DUP' };
    const duplicateJson = serializeInstrumentsJson([first, { ...first, symbol: 'dup' }], brokers);
    expect(() => parseInstrumentsJson(duplicateJson, brokers)).toThrow('already exists');
  });
});
