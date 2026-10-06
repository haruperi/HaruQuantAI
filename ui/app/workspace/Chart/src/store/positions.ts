import type { Position } from '../types';
export const pnl = (p: Position, price: number) =>
  ((p.exit ?? price) - p.entry) * p.quantity * (p.side === 'buy' ? 1 : -1);
export function advancePosition(p: Position, price: number): Position {
  if (p.status === 'closed' || p.status === 'canceled') return p;
  if (p.status === 'pending') {
    if (p.side === 'buy' ? price > p.entry : price < p.entry) return p;
    return advancePosition({ ...p, status: 'open', entry: price }, price);
  }
  const stop = p.sl !== null && (p.side === 'buy' ? price <= p.sl : price >= p.sl);
  const take = p.tp !== null && (p.side === 'buy' ? price >= p.tp : price <= p.tp);
  return stop || take ? { ...p, status: 'closed', exit: price } : p;
}
export function validateOrder(
  quantity: number,
  entry: number,
  side: 'buy' | 'sell',
  sl: number | null,
  tp: number | null,
): string {
  if (!Number.isFinite(quantity) || quantity <= 0 || !Number.isFinite(entry) || entry <= 0)
    return 'Enter a positive quantity and price.';
  if (
    sl !== null &&
    (!Number.isFinite(sl) || sl <= 0 || (side === 'buy' ? sl >= entry : sl <= entry))
  )
    return 'Stop loss must be beyond entry on the loss side.';
  if (
    tp !== null &&
    (!Number.isFinite(tp) || tp <= 0 || (side === 'buy' ? tp <= entry : tp >= entry))
  )
    return 'Take profit must be beyond entry on the profit side.';
  return '';
}
