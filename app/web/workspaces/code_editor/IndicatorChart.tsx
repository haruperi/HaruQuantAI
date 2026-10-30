import { useEffect, useRef } from 'react';
import { CandlestickSeries, ColorType, LineSeries, createChart, type UTCTimestamp } from 'lightweight-charts';
import type { IndicatorTestResultDto } from './codeEditorClient';

export function IndicatorChart({ result }: { result: IndicatorTestResultDto | null }) {
  const container = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!container.current || !result?.candlesticks.length) return;
    const chart = createChart(container.current, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: '#020617' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
    });
    const candles = chart.addSeries(CandlestickSeries);
    candles.setData(
      result.candlesticks.map((bar) => ({
        ...bar,
        time: bar.time as UTCTimestamp,
      })),
    );
    const colors = ['#a855f7', '#38bdf8', '#f59e0b', '#10b981', '#fb7185'];
    let oscillatorPane = 1;
    (result.plot_series ?? [{ name: 'Indicator', pane: 'oscillator', data: result.indicator_plots }]).forEach(
      (plot, index) => {
        const pane = plot.pane === 'main' ? 0 : oscillatorPane++;
        const series = chart.addSeries(
          LineSeries,
          {
            title: plot.name,
            color: colors[index % colors.length],
            lineWidth: 2,
          },
          pane,
        );
        series.setData(
          plot.data.map((point) =>
            point.value === undefined
              ? { time: point.time as UTCTimestamp }
              : { time: point.time as UTCTimestamp, value: point.value },
          ),
        );
      },
    );
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [result]);
  return <div ref={container} className="h-80 w-full shrink-0" aria-label="Historical candles and indicator series" />;
}
