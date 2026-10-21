import { useEffect, useRef } from 'react';
import { CandlestickSeries, ColorType, createChart, type Time } from 'lightweight-charts';
import type { WorkspaceSnapshot } from './dataManagerWorkspaceClient';

export function DataManagerChart({ snapshot, loading, error, onRetry, selectedTime = null, onSelectTime = () => {} }: {
  snapshot: WorkspaceSnapshot | null; loading: boolean; error: string; onRetry: () => void;
  selectedTime?: number | null; onSelectTime?: (time: number) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const moveChart = useRef<(time: number) => void>(() => {});
  const rows = snapshot?.preview.rows;
  const selectBar = (time: number) => { onSelectTime(time); moveChart.current(time); };
  useEffect(() => {
    moveChart.current = () => {};
    if (!container.current || !rows?.length || loading || error) return;
    const chart = createChart(container.current, { autoSize: true, height: 260,
      layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#9ea7b5' },
      timeScale: { timeVisible: true },
    });
    const series = chart.addSeries(CandlestickSeries);
    series.setData(rows.map(row => ({ ...row, time: row.time as Time })));
    chart.timeScale().fitContent();
    chart.subscribeCrosshairMove(event => { if (typeof event.time === 'number') onSelectTime(event.time); });
    moveChart.current = time => {
      const bar = rows.find(row => row.time === time);
      if (bar) chart.setCrosshairPosition(bar.close, time as Time, series);
    };
    return () => { moveChart.current = () => {}; chart.remove(); };
  }, [rows, loading, error, onSelectTime]);
  useEffect(() => {
    if (selectedTime !== null) container.current?.parentElement?.querySelector(`[data-bar-time="${selectedTime}"]`)?.scrollIntoView({ block: 'nearest' });
  }, [selectedTime]);

  return <main className="dm-recorded-preview" aria-label="Linked recorded data preview" aria-busy={loading}>
    <header><strong>{snapshot?.selection ? `${snapshot.selection.symbol} · ${snapshot.selection.timeframe}` : 'Recorded history'}</strong>
      {snapshot?.selection && <span>{snapshot.selection.broker_name} · {snapshot.selection.timezone}</span>}
      <button onClick={onRetry} disabled={loading}>Refresh linked preview</button>
    </header>
    {loading ? <p role="status">Loading recorded history…</p> : error ? <p role="alert">{error}</p> : snapshot?.preview.state !== 'ready' ?
      <p role="status">{snapshot?.preview.reason ?? 'Select a saved dataset to view its recorded history.'}</p> : <>
        <p>Recorded bars · up to {snapshot.preview.limit} rows · UTC</p>
        <div ref={container} className="dm-recorded-chart" aria-label="Recorded candlestick chart" />
        <p aria-label="Selected recorded bar">{selectedTime === null ? 'Select a bar in the table or chart.' : `Selected bar: ${new Date(selectedTime * 1000).toISOString()}`}</p>
        <div className="dm-recorded-table"><table className="plain-table" aria-label="Recorded bars"><thead><tr>{['Time (UTC)', 'Open', 'High', 'Low', 'Close', 'Volume'].map(title => <th key={title}>{title}</th>)}</tr></thead>
          <tbody>{rows?.map(row => <tr key={row.time} data-bar-time={row.time} aria-selected={selectedTime === row.time} className={selectedTime === row.time ? 'selected' : ''}>
            <td><button onPointerDown={event => { if (event.button === 0) selectBar(row.time); }} onClick={() => selectBar(row.time)}>{new Date(row.time * 1000).toISOString()}</button></td>
            {(['open', 'high', 'low', 'close', 'volume'] as const).map(field => <td key={field}>{row[field]}</td>)}
          </tr>)}</tbody></table></div>
      </>}
  </main>;
}
