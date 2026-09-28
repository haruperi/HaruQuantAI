import { useEffect, useRef, useState } from 'react';
import { CandlestickSeries, ColorType, createChart, type CandlestickData, type Time } from 'lightweight-charts';
import type { ReviewCandle } from './actionsClient';

export function DataReviewChart({ candles, isTick }: { candles: ReviewCandle[]; isTick?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState<ReviewCandle | null>(candles.at(-1) ?? null);

  useEffect(() => {
    setActive(candles.at(-1) ?? null);
  }, [candles]);

  useEffect(() => {
    if (!ref.current || isTick || !candles.length) return;
    const chart = createChart(ref.current, {
      height: 365,
      layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#9ea7b5', fontSize: 11 },
      grid: { vertLines: { color: '#2a303a' }, horzLines: { color: '#2a303a' } },
      rightPriceScale: { borderColor: '#3c4450' },
      timeScale: { borderColor: '#3c4450', timeVisible: true, secondsVisible: false },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#31b38b',
      downColor: '#e05d68',
      wickUpColor: '#31b38b',
      wickDownColor: '#e05d68',
      borderVisible: false,
    });

    const byTime = new Map<number, ReviewCandle>();
    const points: CandlestickData<Time>[] = candles.map(candle => {
      const timeSec = Math.floor(candle.time / 1000);
      byTime.set(timeSec, candle);
      return {
        time: timeSec as Time,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
      };
    });

    series.setData(points);
    chart.timeScale().fitContent();

    chart.subscribeCrosshairMove(param => {
      const val = typeof param.time === 'number' ? byTime.get(param.time) : undefined;
      if (val) setActive(val);
    });

    const observer = new ResizeObserver(([entry]) => chart.applyOptions({ width: entry.contentRect.width }));
    observer.observe(ref.current);

    return () => {
      observer.disconnect();
      chart.remove();
    };
  }, [candles, isTick]);

  if (isTick) return <div className="review-unavailable">Chart is not available for tick data.</div>;
  if (!candles.length) return <div className="review-unavailable">No data available.</div>;

  return (
    <div className="review-chart">
      <aside>
        {active && (
          <table>
            <tbody>
              <tr>
                <th colSpan={2}>{new Date(active.time).toLocaleString()}</th>
              </tr>
              {(['open', 'high', 'low', 'close', 'volume'] as const).map(key => (
                <tr key={key}>
                  <td>{key[0].toUpperCase() + key.slice(1)}</td>
                  <td>{typeof active[key] === 'number' ? active[key].toLocaleString() : active[key]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </aside>
      <div ref={ref} className="review-chart-canvas" aria-label="Historical candlestick chart" />
    </div>
  );
}
