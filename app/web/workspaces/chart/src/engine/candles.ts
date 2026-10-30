import type { Bar, ChartStyle } from '../types';
export function heikinAshi(bars: readonly Bar[]): Bar[] {
  let prev: Bar | undefined;
  return bars.map((b) => {
    const close = (b.open + b.high + b.low + b.close) / 4,
      open = prev ? (prev.open + prev.close) / 2 : (b.open + b.close) / 2;
    prev = {
      ...b,
      open,
      close,
      high: Math.max(b.high, open, close),
      low: Math.min(b.low, open, close),
    };
    return prev;
  });
}
export function paintSeries(
  ctx: CanvasRenderingContext2D,
  bars: readonly Bar[],
  start: number,
  end: number,
  x: (i: number) => number,
  y: (p: number) => number,
  spacing: number,
  style: ChartStyle,
  bottom: number,
): void {
  const up = '#089981',
    down = '#f23645',
    width = Math.max(1, Math.floor((spacing * 0.7) / 2) * 2 + 1);
  if (['Line', 'Area', 'Baseline'].includes(style)) {
    const first = bars[start];
    if (!first) return;
    ctx.beginPath();
    for (let i = start; i <= end; i++) {
      const b = bars[i];
      if (!b) continue;
      if (i === start) ctx.moveTo(x(i), y(b.close));
      else ctx.lineTo(x(i), y(b.close));
    }
    ctx.strokeStyle = '#2962ff';
    ctx.lineWidth = 1.6;
    ctx.stroke();
    if (style === 'Area') {
      ctx.lineTo(x(end), bottom);
      ctx.lineTo(x(start), bottom);
      ctx.closePath();
      const g = ctx.createLinearGradient(0, 0, 0, bottom);
      g.addColorStop(0, '#2962ff66');
      g.addColorStop(1, '#2962ff02');
      ctx.fillStyle = g;
      ctx.fill();
    }
    if (style === 'Baseline') {
      const baseline = y(first.close);
      for (const [color, top, height] of [
        [up, 0, baseline],
        [down, baseline, bottom - baseline],
      ] as const) {
        ctx.save();
        ctx.beginPath();
        ctx.rect(0, top, ctx.canvas.width, height);
        ctx.clip();
        ctx.beginPath();
        for (let i = start; i <= end; i++) {
          if (i === start) ctx.moveTo(x(i), y(bars[i].close));
          else ctx.lineTo(x(i), y(bars[i].close));
        }
        ctx.strokeStyle = color;
        ctx.stroke();
        ctx.lineTo(x(end), baseline);
        ctx.lineTo(x(start), baseline);
        ctx.closePath();
        ctx.fillStyle = color + '22';
        ctx.fill();
        ctx.restore();
      }
    }
    return;
  }
  for (const rising of [true, false]) {
    ctx.strokeStyle = rising ? up : down;
    ctx.fillStyle = ctx.strokeStyle;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = start; i <= end; i++) {
      const b = bars[i];
      if (!b || b.close >= b.open !== rising) continue;
      const cx = Math.round(x(i)) + 0.5;
      ctx.moveTo(cx, y(b.high));
      ctx.lineTo(cx, y(b.low));
      if (style === 'Bars') {
        ctx.moveTo(cx - width / 2, y(b.open));
        ctx.lineTo(cx, y(b.open));
        ctx.moveTo(cx, y(b.close));
        ctx.lineTo(cx + width / 2, y(b.close));
      }
    }
    ctx.stroke();
    if (style === 'Bars') continue;
    ctx.beginPath();
    for (let i = start; i <= end; i++) {
      const b = bars[i];
      if (!b || b.close >= b.open !== rising) continue;
      const top = Math.min(y(b.open), y(b.close)),
        height = Math.max(1, Math.abs(y(b.open) - y(b.close)));
      ctx.rect(Math.round(x(i) - width / 2) + 0.5, top, width, height);
    }
    if (style === 'Hollow Candles' && rising) ctx.stroke();
    else ctx.fill();
  }
}
