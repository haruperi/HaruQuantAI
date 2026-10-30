import { describe, expect, it } from 'vitest';
import {
  applyMassPatch,
  effectiveSymbols,
  newSymbol,
  parseSymbolsJson,
  serializeSymbolsJson,
  type SymbolBroker,
} from '../../../../../../workspaces/data_manager/plugins/Catalogs/Symbols/symbols';

const brokers: SymbolBroker[] = [
  { id: '-1', name: 'Default', postfix: '', timezone: 'UTC' },
  { id: 'demo', name: 'Demo & Broker', postfix: '_demo', timezone: 'EST+07' },
];

describe('symbol management rules', () => {
  it('composes seed overrides, custom symbols, and removals', () => {
    const custom = { ...newSymbol('Stock'), symbol: 'CUSTOM', name: 'Custom' };
    const seed = effectiveSymbols([], {}, [])[0];
    const overridden = { ...seed, spread: seed.spread + 2 };
    const result = effectiveSymbols([custom], { [seed.symbol]: overridden }, ['GBPJPY']);
    expect(result.find(item => item.symbol === seed.symbol)?.spread).toBe(overridden.spread);
    expect(result.some(item => item.symbol === 'GBPJPY')).toBe(false);
    expect(result.find(item => item.symbol === 'CUSTOM')?.type).toBe('Stock');
  });

  it('applies only enabled mass-edit fields without mutating the source', () => {
    const source = { ...newSymbol(), symbol: 'SOURCE', spread: 1, slippage: 2 };
    const value = { ...source, spread: 9, slippage: 10, commission: { ...source.commission, model: 'Per trade' as const, value: 4 } };
    const result = applyMassPatch(source, { fields: { spread: true, commission: true }, value });
    expect(result.spread).toBe(9);
    expect(result.slippage).toBe(2);
    expect(result.commission).toEqual(value.commission);
    expect(source.spread).toBe(1);
  });

  it('round trips complete JSON and maps broker metadata by identity', () => {
    const item = {
      ...newSymbol('Stock'), symbol: 'AB_demo', name: 'A & B < test', broker: 'demo',
      brokerName: 'Demo & Broker', timezone: 'EST+07',
      commission: { model: 'Stockpicker' as const, value: 0.0035, unit: 'share', min: 0.35, minUnit: 'money', max: 1, maxUnit: 'equity' },
      swap: { use: true, type: 'percent' as const, long: -1.5, short: 0.5, tripleSwapOn: 'FRIDAY', rolloutHour: '22:30' },
    };
    const json = serializeSymbolsJson([item], brokers);
    expect(JSON.parse(json)).toMatchObject({version:1,kind:'symbols',brokers:[{name:'Demo & Broker'}]});
    expect(parseSymbolsJson(json, brokers)).toEqual([item]);
  });

  it('rejects malformed, wrong-kind, empty, and duplicate JSON before mutation', () => {
    for (const json of ['', '{', '{}', '{"version":1,"kind":"sessions","symbols":[]}', '{"version":1,"kind":"symbols","brokers":[],"symbols":[]}']) {
      expect(() => parseSymbolsJson(json, brokers)).toThrow();
    }
    const first = { ...newSymbol(), symbol: 'DUP' };
    const duplicateJson = serializeSymbolsJson([first, { ...first, symbol: 'dup' }], brokers);
    expect(() => parseSymbolsJson(duplicateJson, brokers)).toThrow('already exists');
  });

  it('starts the authoritative store without browser fixtures', async () => {
    const { useSymbols } = await import('../../../../../../workspaces/data_manager/plugins/Catalogs/Symbols/symbolsStore');
    useSymbols.getState().reset();
    expect(useSymbols.getState().symbols).toEqual([]);
    expect(useSymbols.getState().loaded).toBe(false);
  });
});
