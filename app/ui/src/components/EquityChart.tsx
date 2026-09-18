import { useEffect, useRef } from 'react';
import { AreaSeries, ColorType, createChart, LineSeries, type Time } from 'lightweight-charts';
import type { EquityPoint } from '../app/types';

export function EquityChart({ data, height = 280, drawdown = false }: { data: EquityPoint[]; height?: number; drawdown?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => { if (!ref.current) return; const chart = createChart(ref.current, { height, layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#9ea7b5', fontSize: 11 }, grid: { vertLines: { color: '#2a303a' }, horzLines: { color: '#2a303a' } }, rightPriceScale: { borderColor: '#3c4450' }, timeScale: { borderColor: '#3c4450', timeVisible: false } });
    if (drawdown) { const series = chart.addSeries(LineSeries, { color: '#ee6677', lineWidth: 2 }); series.setData(data.map(x => ({ time: x.time as Time, value: -x.drawdown }))); }
    else { const series = chart.addSeries(AreaSeries, { lineColor: '#32b5e7', topColor: 'rgba(50,181,231,.32)', bottomColor: 'rgba(50,181,231,.02)', lineWidth: 2 }); series.setData(data.map(x => ({ time: x.time as Time, value: x.value }))); }
    chart.timeScale().fitContent(); const observer = new ResizeObserver(([entry]) => chart.applyOptions({ width: entry.contentRect.width })); observer.observe(ref.current); return () => { observer.disconnect(); chart.remove(); }; }, [data, height, drawdown]);
  return <div ref={ref} className="chart"/>;
}
