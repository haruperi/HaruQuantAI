export interface SymbolInfo {
  id: string;
  name: string;
  exchange: string;
  category: 'Forex' | 'Metals' | 'Crypto' | 'Indices' | 'Stocks';
  base: number;
  icon: string;
}
const group = (
  category: SymbolInfo['category'],
  exchange: string,
  rows: [string, string, number][],
): SymbolInfo[] =>
  rows.map(([id, name, base]) => ({
    id,
    name,
    base,
    category,
    exchange,
    icon:
      category === 'Crypto'
        ? '₿'
        : category === 'Metals'
          ? '◆'
          : category === 'Forex'
            ? '↔'
            : category === 'Indices'
              ? '▥'
              : id[0],
  }));
export const symbols: SymbolInfo[] = [
  ...group('Metals', 'SIM · Pepperstone', [
    ['XAUUSD', 'Gold Spot / U.S. Dollar', 2658],
    ['XAGUSD', 'Silver Spot / U.S. Dollar', 31.2],
    ['XPTUSD', 'Platinum', 985],
    ['XPDUSD', 'Palladium', 1050],
  ]),
  ...group('Forex', 'SIM · FX', [
    ['EURUSD', 'Euro / U.S. Dollar', 1.12],
    ['GBPUSD', 'British Pound / U.S. Dollar', 1.33],
    ['USDJPY', 'U.S. Dollar / Japanese Yen', 144],
    ['AUDUSD', 'Australian Dollar / U.S. Dollar', 0.68],
    ['USDCAD', 'U.S. Dollar / Canadian Dollar', 1.35],
    ['USDCHF', 'U.S. Dollar / Swiss Franc', 0.85],
    ['NZDUSD', 'New Zealand Dollar / U.S. Dollar', 0.62],
    ['EURGBP', 'Euro / British Pound', 0.84],
    ['EURJPY', 'Euro / Japanese Yen', 161],
    ['GBPJPY', 'British Pound / Japanese Yen', 192],
    ['AUDJPY', 'Australian Dollar / Japanese Yen', 98],
    ['EURCHF', 'Euro / Swiss Franc', 0.95],
  ]),
  ...group('Crypto', 'SIM · Crypto', [
    ['BTCUSDT', 'Bitcoin / Tether', 64000],
    ['ETHUSDT', 'Ethereum / Tether', 2650],
    ['SOLUSDT', 'Solana / Tether', 148],
    ['BNBUSDT', 'BNB / Tether', 600],
    ['XRPUSDT', 'XRP / Tether', 0.6],
    ['ADAUSDT', 'Cardano / Tether', 0.38],
    ['DOGEUSDT', 'Dogecoin / Tether', 0.12],
    ['AVAXUSDT', 'Avalanche / Tether', 28],
  ]),
  ...group('Indices', 'SIM · Index', [
    ['SPX', 'S&P 500', 5700],
    ['NDX', 'Nasdaq 100', 19900],
    ['DJI', 'Dow Jones', 42100],
    ['DAX', 'Germany 40', 18900],
    ['FTSE', 'UK 100', 8300],
    ['NIKKEI', 'Japan 225', 38000],
    ['HSI', 'Hang Seng', 19000],
    ['VIX', 'Volatility Index', 17],
  ]),
  ...group('Stocks', 'SIM · NASDAQ', [
    ['AAPL', 'Apple Inc.', 228],
    ['MSFT', 'Microsoft Corporation', 430],
    ['NVDA', 'NVIDIA Corporation', 121],
    ['AMZN', 'Amazon.com Inc.', 188],
    ['GOOGL', 'Alphabet Inc.', 165],
    ['META', 'Meta Platforms', 565],
    ['TSLA', 'Tesla Inc.', 250],
    ['NFLX', 'Netflix Inc.', 700],
    ['AMD', 'Advanced Micro Devices', 160],
    ['INTC', 'Intel Corporation', 22],
    ['COIN', 'Coinbase Global', 175],
    ['PLTR', 'Palantir Technologies', 36],
  ]),
];
export const symbolInfo = (id: string) => symbols.find((x) => x.id === id) ?? symbols[0];
