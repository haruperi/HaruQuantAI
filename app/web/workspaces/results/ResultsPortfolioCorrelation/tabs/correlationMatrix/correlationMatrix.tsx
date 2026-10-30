/** The existing precomputed two-market matrix; no correlation calculation. */
export function CorrelationMatrix({ period }: { period: string }) {
  return <><h3>Portfolio correlation / {period}</h3><table className="sqr-data-table"><thead><tr><th>Market</th><th>EURUSD</th><th>GBPUSD</th></tr></thead><tbody><tr><th>EURUSD</th><td>1.00</td><td>{period === 'Day' ? '0.42' : '0.36'}</td></tr><tr><th>GBPUSD</th><td>{period === 'Day' ? '0.42' : '0.36'}</td><td>1.00</td></tr></tbody></table></>;
}
