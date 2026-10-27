import { createChart, LineSeries, type Time } from 'lightweight-charts';
import { useRef, useEffect, useState } from 'react';
import { Button, Modal } from '../../../components/ui';
import { activeExternalLines, type ExternalIndicatorDefinition } from './externalIndicators';
import { fetchExternalReview } from './externalIndicatorsApiClient';
import './externalIndicators.css';

export function ExternalIndicatorViewDialog({ item, onClose }: { item: ExternalIndicatorDefinition; onClose: () => void }) {
  const lines = activeExternalLines(item);
  const [page,setPage] = useState(0); const [hasMore,setHasMore] = useState(false); const chartRef = useRef<HTMLDivElement>(null); const [showChart,setShowChart] = useState(false);
  const [loading, setLoading] = useState(item.records.length === 0);
  const [remoteRows, setRemoteRows] = useState<Array<{ timestamp: string; values: (string | number)[] }>>([]);
  const [remoteColumns, setRemoteColumns] = useState<string[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchExternalReview(item.name, 200, page * 200)
      .then(res => {
        if (!active) return;
        const columns = res.columns && res.columns.length > 0 ? res.columns : lines.map(l => l.name);
        setRemoteColumns(columns); setHasMore(Boolean(res.pagination?.has_more));
        const mapped = (res.records || []).map(r => ({
          timestamp: r.timestamp,
          values: columns.map(c => (r.values as Record<string, number>)?.[c] ?? ''),
        }));
        setRemoteRows(mapped);
      })
      .catch(cause => {
        if (active) setError(cause instanceof Error ? cause.message : 'Unable to load observations.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [item.name,page]);

  const displayColumns = remoteColumns.length > 0 ? remoteColumns : lines.map((l, index) => l.name || `Value ${index + 1}`);

  const displayRows = remoteRows;
  useEffect(() => {
    if (!showChart || !chartRef.current || !remoteRows.length) return;
    const chart = createChart(chartRef.current,{height:300, width:chartRef.current.clientWidth});
    displayColumns.forEach((name,index) => {
      const series = chart.addSeries(LineSeries,{title:name,color:['#49b3a1','#5a9ee6','#dbaf57'][index%3]});
      const values = new Map<number,number>();
      remoteRows.forEach(row=>{const value=Number(row.values[index]); if(Number.isFinite(value)) values.set(Math.floor(Date.parse(row.timestamp)/1000),value);});
      series.setData([...values].sort(([a],[b])=>a-b).map(([time,value])=>({time:time as Time,value})));
    });
    chart.timeScale().fitContent(); const observer = new ResizeObserver(()=>chart.applyOptions({width:chartRef.current!.clientWidth})); observer.observe(chartRef.current);
    return ()=>{observer.disconnect();chart.remove();};
  },[showChart,remoteRows,remoteColumns]);

  return (
    <div className="external-flow">
      <Modal title={`View custom data for '${item.name}'`} width={800} onClose={onClose} footer={<Button onClick={onClose}>Close</Button>}>
        <div><Button disabled={loading || page===0} onClick={()=>setPage(value=>value-1)}>Previous</Button> <span>Page {page+1}</span> <Button disabled={loading || !hasMore} onClick={()=>setPage(value=>value+1)}>Next</Button> <Button onClick={()=>setShowChart(value=>!value)}>{showChart ? 'Hide chart' : 'Show chart'}</Button></div>
        {showChart && <div ref={chartRef} aria-label="Recorded indicator chart"/>}
        {loading && <p className="external-note">Loading observations...</p>}
        {error && <p className="external-error" role="alert">{error}</p>}
        {!loading && (
          <div className="external-view-grid">
            <table className="plain-table" aria-label={`Data for ${item.name}`}>
              <thead>
                <tr>
                  <th>Date</th>
                  {displayColumns.map((colName, index) => (
                    <th key={index}>{colName}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {displayRows.map((row, index) => (
                  <tr key={`${row.timestamp}-${index}`}>
                    <td>{row.timestamp}</td>
                    {row.values.map((value, vIndex) => (
                      <td key={vIndex}>{value}</td>
                    ))}
                  </tr>
                ))}
                {!displayRows.length && (
                  <tr>
                    <td colSpan={Math.max(1, displayColumns.length + 1)}>No observations recorded.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Modal>
    </div>
  );
}
