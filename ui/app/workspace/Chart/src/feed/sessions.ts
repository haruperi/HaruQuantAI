import { symbolInfo } from './symbols';
export function marketOpen(symbol: string, time: number): boolean {
  const category = symbolInfo(symbol).category;
  if (category === 'Crypto') return true;
  const d = new Date(time),
    day = d.getUTCDay(),
    minute = d.getUTCHours() * 60 + d.getUTCMinutes();
  if (day === 0 || day === 6) return false;
  return category === 'Stocks' || category === 'Indices'
    ? minute >= 13 * 60 + 30 && minute < 20 * 60
    : true;
}
