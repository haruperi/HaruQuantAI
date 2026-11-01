import type { Bar, ChartStyle, Settings } from '../types';
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
  settings?: Pick<Settings,
    'colorBarsByPreviousClose' | 'candleBody' | 'candleBorders' | 'candleWicks' |
    'candleUpColor' | 'candleDownColor' | 'candleBorderUpColor' | 'candleBorderDownColor' |
    'candleWickUpColor' | 'candleWickDownColor'>,
): void {
  const up = settings?.candleUpColor ?? '#089981';
  const down = settings?.candleDownColor ?? '#f23645';
  const width = Math.max(1, Math.floor((spacing * 0.7) / 2) * 2 + 1);
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

  ctx.save();
  ctx.lineWidth = 1;
  for (let i = start; i <= end; i++) {
    const bar = bars[i];
    if (!bar) continue;
    const reference = settings?.colorBarsByPreviousClose && i > 0
      ? bars[i - 1].close : bar.open;
    const rising = bar.close >= reference;
    const bodyColor = rising ? up : down;
    const borderColor = rising
      ? settings?.candleBorderUpColor ?? up
      : settings?.candleBorderDownColor ?? down;
    const wickColor = rising
      ? settings?.candleWickUpColor ?? up
      : settings?.candleWickDownColor ?? down;
    const cx = Math.round(x(i)) + .5;
    if (style === 'Bars') {
      ctx.strokeStyle = bodyColor;
      ctx.beginPath();
      ctx.moveTo(cx, y(bar.high));
      ctx.lineTo(cx, y(bar.low));
      ctx.moveTo(cx - width / 2, y(bar.open));
      ctx.lineTo(cx, y(bar.open));
      ctx.moveTo(cx, y(bar.close));
      ctx.lineTo(cx + width / 2, y(bar.close));
      ctx.stroke();
      continue;
    }
    if (settings?.candleWicks !== false) {
      ctx.strokeStyle = wickColor;
      ctx.beginPath();
      ctx.moveTo(cx, y(bar.high));
      ctx.lineTo(cx, y(bar.low));
      ctx.stroke();
    }
    const left = Math.round(x(i) - width / 2) + .5;
    const top = Math.min(y(bar.open), y(bar.close));
    const height = Math.max(1, Math.abs(y(bar.open) - y(bar.close)));
    if (settings?.candleBody !== false && !(style === 'Hollow Candles' && rising)) {
      ctx.fillStyle = bodyColor;
      ctx.fillRect(left, top, width, height);
    }
    if (settings?.candleBorders !== false) {
      ctx.strokeStyle = borderColor;
      ctx.strokeRect(left, top, width, height);
    }
  }
  ctx.restore();
}
