/** Core currently publishes progress and results, without fitness/memory series. */
export function EngineCharts() {
  return <div className="sqd-engine-charts">{['Databank fitness', 'Worker memory'].map(title => <section className="sqd-card" key={title}><h3>{title}</h3><p>Telemetry is unavailable from the execution owner.</p></section>)}</div>;
}
