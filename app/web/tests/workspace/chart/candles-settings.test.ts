import { expect, it } from 'vitest';
import { paintSeries } from '../../../workspaces/chart/src/engine/candles';
import { defaults } from '../../../workspaces/chart/src/store/chartStore';

const bars = [
  { time: 0, open: 100, high: 110, low: 95, close: 105, volume: 1 },
  { time: 1, open: 100, high: 107, low: 98, close: 102, volume: 1 },
];

function draw(change: Partial<typeof defaults>) {
  const calls: string[] = [];
  const ctx = {
    fillStyle: '', strokeStyle: '', lineWidth: 1,
    save() {}, restore() {}, beginPath() {}, moveTo() {}, lineTo() {},
    stroke() { calls.push('wick:' + this.strokeStyle); },
    fillRect() { calls.push('body:' + this.fillStyle); },
    strokeRect() { calls.push('border:' + this.strokeStyle); },
  };
  paintSeries(ctx as unknown as CanvasRenderingContext2D, bars, 0, 1, (i) => i * 30, (value) => 200 - value, 10, 'Candles', 150, {
    ...defaults, ...change,
  });
  return calls;
}

it('uses distinct colors for candle bodies borders and wicks', () => {
  const calls = draw({
    colorBarsByPreviousClose: true,
    candleUpColor: '#123456', candleDownColor: '#654321',
    candleWickUpColor: '#abcdef', candleWickDownColor: '#fedcba',
    candleBorderUpColor: '#111111', candleBorderDownColor: '#222222',
  });
  expect(calls).toContain('body:#123456');
  expect(calls).toContain('border:#111111');
  expect(calls).toContain('wick:#abcdef');
  expect(calls).toContain('body:#654321');
  expect(calls).toContain('border:#222222');
  expect(calls).toContain('wick:#fedcba');
});

it('compares candle direction against previous close when requested', () => {
  const without = draw({ colorBarsByPreviousClose: false });
  const withPrevious = draw({ colorBarsByPreviousClose: true });
  expect(without.filter((x) => x.startsWith('body:'))).toEqual(['body:#089981', 'body:#089981']);
  expect(withPrevious.filter((x) => x.startsWith('body:'))).toEqual(['body:#089981', 'body:#f23645']);
});

it('honors visibility of candle bodies borders and wicks', () => {
  expect(draw({ candleBody: false, candleBorders: false, candleWicks: false })).toEqual([]);
  expect(draw({ candleBody: false, candleBorders: true, candleWicks: false }))
    .toEqual(['border:#089981', 'border:#089981']);
});
