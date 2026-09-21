import { useEffect, useRef, useState } from 'react';
import { CandlestickSeries, ColorType, createChart, type CandlestickData, type Time } from 'lightweight-charts';
import type { ReviewRow } from './dataTools';

export function DataReviewChart({ rows, tick }: { rows: ReviewRow[]; tick: boolean }) {
  const ref = useRef<HTMLDivElement>(null); const [active, setActive] = useState<ReviewRow | null>(rows.at(-1) ?? null);
  useEffect(() => { setActive(rows.at(-1) ?? null); }, [rows]);
  useEffect(() => {
    if (!ref.current || tick || !rows.length) return;
    const chart = createChart(ref.current, { height: 365, layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#9ea7b5', fontSize: 11 },
      grid: { vertLines: { color: '#2a303a' }, horzLines: { color: '#2a303a' } }, rightPriceScale: { borderColor: '#3c4450' }, timeScale: { borderColor: '#3c4450', timeVisible: true, secondsVisible: false } });
    const series = chart.addSeries(CandlestickSeries, { upColor: '#31b38b', downColor: '#e05d68', wickUpColor: '#31b38b', wickDownColor: '#e05d68', borderVisible: false });
    const byTime = new Map<number, ReviewRow>();
    const points: CandlestickData<Time>[] = rows.map(row => { const time = Math.floor(Date.parse(row.date) / 1000); byTime.set(time, row); return { time: time as Time, open: row.open, high: row.high, low: row.low, close: row.close }; });
    series.setData(points); chart.timeScale().fitContent(); chart.subscribeCrosshairMove(param => { const value = typeof param.time === 'number' ? byTime.get(param.time) : undefined; if (value) setActive(value); });
    const observer = new ResizeObserver(([entry]) => chart.applyOptions({ width: entry.contentRect.width })); observer.observe(ref.current);
    return () => { observer.disconnect(); chart.remove(); };
  }, [rows, tick]);
  if (tick) return <div className="review-unavailable">Chart is not available for tick data.</div>;
  if (!rows.length) return <div className="review-unavailable">No data available.</div>;
  return <div className="review-chart"><aside>{active && <table><tbody><tr><th colSpan={2}>{new Date(active.date).toLocaleString()}</th></tr>{(['open','high','low','close'] as const).map(key => <tr key={key}><td>{key[0].toUpperCase() + key.slice(1)}</td><td>{active[key]}</td></tr>)}</tbody></table>}</aside><div ref={ref} className="review-chart-canvas" aria-label="Historical candlestick chart"/></div>;
}
