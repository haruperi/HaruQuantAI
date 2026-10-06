export function zoneOffset(zone: string, exchange = 0): number {
  if (zone === 'Local') return -new Date().getTimezoneOffset();
  if (zone === 'Exchange') return exchange;
  return Number(zone.replace('UTC', '') || 0) * 60;
}
export function timeLabel(time: number, zone: string, seconds = false): string {
  const date = new Date(time + zoneOffset(zone) * 60000);
  return date.toLocaleTimeString('en-GB', {
    timeZone: 'UTC',
    hour: '2-digit',
    minute: '2-digit',
    ...(seconds ? { second: '2-digit' } : {}),
  });
}
export function dateLabel(time: number, zone: string): string {
  return new Date(time + zoneOffset(zone) * 60000).toISOString().slice(0, 16).replace('T', ' ');
}
