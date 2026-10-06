import { sqUsageConditions } from '../../sqData';
export function EquityDataUsageConditions() { return <section className="sq-data-conditions"><h1>HaruQuantAI Data Usage Conditions</h1>{sqUsageConditions.map((text, index) => <p key={index}>{text}</p>)}</section>; }
