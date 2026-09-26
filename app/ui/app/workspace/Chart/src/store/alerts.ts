import type { Alert } from '../types';
export function triggered(a: Alert, previous: number, price: number, now: number): boolean {
  if (!a.active || now >= a.expires) return false;
  if (a.condition === 'up') return previous < a.value && price >= a.value;
  if (a.condition === 'down') return previous > a.value && price <= a.value;
  const was = previous >= a.value && previous <= a.upper,
    inside = price >= a.value && price <= a.upper;
  return a.condition === 'enter' ? !was && inside : was && !inside;
}
