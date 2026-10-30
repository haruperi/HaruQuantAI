import { describe, expect, it, vi } from 'vitest';
import { createSymbolDataClient, normalizeSymbolContract } from '../../../../workspaces/data_manager/plugins/Common/symbolContract';

describe('symbol compatibility boundary', () => {
  it('reads saved definitions and old workspace descriptors without changing symbol names', () => {
    expect(normalizeSymbolContract({
      instruments: [{ symbol: 'EURUSD', instrument: 'FX' }],
      active_tab: 'instruments', tabs: [{ id: 'instruments', title: 'Instruments' }],
    })).toEqual({
      symbols: [{ symbol: 'EURUSD', symbolDefinition: 'FX' }],
      active_tab: 'symbols', tabs: [{ id: 'symbols', title: 'Symbols' }],
    });
  });

  it('preserves existing endpoints and request keys while normalizing responses', async () => {
    const fetchFn = vi.fn().mockResolvedValue({
      ok: true, status: 200,
      json: async () => ({ status: 'success', data: { instruments: [], updated_count: 0 } }),
    });
    const client = createSymbolDataClient('/data', { baseUrl: '/api/v1', fetchFn: fetchFn as typeof fetch });
    expect(await client.post('/symbols/mass-edit', { symbol_ids: ['1'], updates: {} }))
      .toEqual({ symbols: [], updated_count: 0 });
    expect(fetchFn.mock.calls[0][0]).toBe('/api/v1/data/instruments/mass-edit');
    expect(JSON.parse(fetchFn.mock.calls[0][1].body)).toEqual({ instrument_ids: ['1'], updates: {} });
    await client.post('/symbols/refresh', { symbols: ['EURUSD'] });
    expect(JSON.parse(fetchFn.mock.calls[1][1].body)).toEqual({ symbols: ['EURUSD'] });
  });
});
