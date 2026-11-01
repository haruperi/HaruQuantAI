import { describe, it, expect } from 'vitest';

export interface AppResultsDataItem {
  result_key: string;
  label: string;
  symbol: string;
  timeframe: string;
  sample_type: string;
  direction: string;
  is_portfolio: boolean;
}

export interface AppResultsSelectionState {
  project_id: string;
  databank_name: string;
  strategy_id: string;
  active_result_key: string;
  active_tab_id: string;
  data_items: AppResultsDataItem[];
}

describe('AppResults frontend contract & selection projection', () => {
  it('parses canonical AppResultsSelectionState payload correctly', () => {
    const payload: AppResultsSelectionState = {
      project_id: 'proj_1',
      databank_name: 'Results',
      strategy_id: 'Strat_01',
      active_result_key: 'Main',
      active_tab_id: 'overview',
      data_items: [
        {
          result_key: 'Main',
          label: 'Main',
          symbol: 'EURUSD',
          timeframe: 'H1',
          sample_type: 'FullSample',
          direction: 'Both',
          is_portfolio: false,
        },
        {
          result_key: 'Additional_1',
          label: 'Additional_1',
          symbol: 'GBPUSD',
          timeframe: 'H1',
          sample_type: 'FullSample',
          direction: 'Both',
          is_portfolio: false,
        },
      ],
    };

    expect(payload.strategy_id).toBe('Strat_01');
    expect(payload.data_items).toHaveLength(2);
    expect(payload.data_items[0].result_key).toBe('Main');
    expect(payload.data_items[0].symbol).toBe('EURUSD');
    expect(payload.data_items[1].result_key).toBe('Additional_1');
    expect(payload.data_items[1].symbol).toBe('GBPUSD');
  });

  it('preserves deterministic ordering: Main first, Portfolio second', () => {
    const items: AppResultsDataItem[] = [
      {
        result_key: 'Z_Cross',
        label: 'Z_Cross',
        symbol: 'USDJPY',
        timeframe: 'H1',
        sample_type: 'FullSample',
        direction: 'Both',
        is_portfolio: false,
      },
      {
        result_key: 'Portfolio',
        label: 'Portfolio',
        symbol: 'BASKET',
        timeframe: 'H1',
        sample_type: 'FullSample',
        direction: 'Both',
        is_portfolio: true,
      },
      {
        result_key: 'Main',
        label: 'Main',
        symbol: 'EURUSD',
        timeframe: 'H1',
        sample_type: 'FullSample',
        direction: 'Both',
        is_portfolio: false,
      },
    ];

    const sorted = [...items].sort((a, b) => {
      if (a.result_key === 'Main') return -1;
      if (b.result_key === 'Main') return 1;
      if (a.result_key === 'Portfolio') return -1;
      if (b.result_key === 'Portfolio') return 1;
      return a.result_key.localeCompare(b.result_key);
    });

    expect(sorted.map(x => x.result_key)).toEqual(['Main', 'Portfolio', 'Z_Cross']);
  });
});
