import type { Dataset, Instrument } from '../../../host/types';

export const datasets: Dataset[] = [
  { id: 'd1', source: 'Dukascopy', symbol: 'EURUSD', timeframe: 'M1 → H1', from: '2010-01-01', to: '2026-08-31', bars: 6021431, quality: 99.8, status: 'Ready' },
  { id: 'd2', source: 'Dukascopy', symbol: 'GBPJPY', timeframe: 'M1 → H4', from: '2011-04-01', to: '2026-08-31', bars: 5518210, quality: 99.6, status: 'Ready' },
  { id: 'd3', source: 'Futures', symbol: 'NQ', timeframe: 'Tick → D1', from: '2014-01-02', to: '2026-08-31', bars: 12861244, quality: 98.9, status: 'Ready' },
  { id: 'd4', source: 'File import', symbol: 'XAUUSD', timeframe: 'M1 → H1', from: '2012-01-03', to: '2026-08-31', bars: 4882301, quality: 97.6, status: 'Ready' },
];
export const instruments: Instrument[] = [
  { symbol: 'EURUSD', name: 'Euro / US Dollar', type: 'Forex', pointValue: 100000, spread: 1.2, session: 'Forex 24/5', timezone: 'Europe/Prague' },
  { symbol: 'GBPJPY', name: 'British Pound / Yen', type: 'Forex', pointValue: 100000, spread: 2.1, session: 'Forex 24/5', timezone: 'Europe/Prague' },
  { symbol: 'XAUUSD', name: 'Gold / US Dollar', type: 'CFD', pointValue: 100, spread: 2.8, session: 'Metals', timezone: 'America/New_York' },
  { symbol: 'NQ', name: 'E-mini Nasdaq-100', type: 'Futures', pointValue: 20, spread: .25, session: 'CME Equity', timezone: 'America/Chicago' },
];
