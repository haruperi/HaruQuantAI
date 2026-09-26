export const formatPrice = (value: number, precision = 2) =>
  Number.isFinite(value) ? value.toFixed(precision) : '—';
