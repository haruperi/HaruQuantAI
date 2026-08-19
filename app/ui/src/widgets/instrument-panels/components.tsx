import type { InstrumentValue } from "./contracts";
export function InstrumentPanels({ values }: { values: readonly InstrumentValue[] }): React.JSX.Element {
  return <section aria-labelledby="instruments-heading"><h2 id="instruments-heading">Market, portfolio, and trade instruments</h2><div className="workstation-grid">{values.map((item) => <article className={`instrument ${item.freshness}`} key={item.label}><h3>{item.label}</h3><output>{item.value ?? "Unknown"}</output><small>{item.freshness}</small></article>)}</div></section>;
}
