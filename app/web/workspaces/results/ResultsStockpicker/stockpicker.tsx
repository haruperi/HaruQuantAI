/** Current stockpicker fixture table; no stored-log retrieval. */
export function StockpickerTab() {
  return <div className="sqr-tab"><div className="sqr-toolbar"/><div className="sqr-content"><table className="sqr-data-table"><thead><tr><th>Date</th><th>Symbol</th><th>Score</th><th>Action</th></tr></thead><tbody>{['AAPL', 'MSFT', 'NVDA'].map((s, i) => <tr key={s}><td>2025.06.03</td><td>{s}</td><td>{90 - i * 10}</td><td>Selected</td></tr>)}</tbody></table><p className="sqd-gen-help">Precomputed local UI fixture. No analysis is executed.</p></div></div>;
}
