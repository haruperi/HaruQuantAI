import type { Dataset, Instrument } from '../../../host/types';

export const datasets: Dataset[] = [];
export const instruments: Instrument[] = [
  { symbol: 'EURUSD', name: 'Euro / US Dollar', type: 'Forex', pointValue: 100000, spread: 1.2, session: 'Forex 24/5', timezone: 'Europe/Prague' },
  { symbol: 'GBPJPY', name: 'British Pound / Yen', type: 'Forex', pointValue: 100000, spread: 2.1, session: 'Forex 24/5', timezone: 'Europe/Prague' },
  { symbol: 'XAUUSD', name: 'Gold / US Dollar', type: 'CFD', pointValue: 100, spread: 2.8, session: 'Metals', timezone: 'America/New_York' },
  { symbol: 'NQ', name: 'E-mini Nasdaq-100', type: 'Futures', pointValue: 20, spread: .25, session: 'CME Equity', timezone: 'America/Chicago' },
];
