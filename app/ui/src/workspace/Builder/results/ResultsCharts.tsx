import { useState } from 'react';
export function ResultsChart({ values, title = 'Equity', benchmark = false, bars = false, points = 'off', crosshair = false, trendline = false, markers = 'off', stagnation = 0, stagnationV2 = 0 }: {
    values: number[];
    title?: string;
    benchmark?: boolean;
    bars?: boolean;
    points?: string;
    crosshair?: boolean;
    trendline?: boolean;
    markers?: string;
    stagnation?: string | number;
    stagnationV2?: string | number;
}) {
    const [hover, setHover] = useState<number | null>(null);
    const min = Math.min(...values, bars || !values.length ? 0 : Infinity), max = Math.max(...values, bars || !values.length ? 0 : -Infinity);
    const y = (v: number) => 250 - (v - min) / Math.max(1, max - min) * 210;
    return <div className="sqr-mock-chart"><h3>{title}</h3><svg viewBox="0 0 900 280" role="img" aria-label={title} onMouseLeave={() => setHover(null)}>
 {[0, 1, 2, 3, 4].map(i => <g key={i}><line x1="55" x2="890" y1={40 + i * 52} y2={40 + i * 52} stroke="#555"/><text x="2" y={44 + i * 52} fill="#aaa" fontSize="11">{Math.round(max - (max - min) * i / 4)}</text></g>)}
 {bars ? values.map((v, i) => <rect key={i} x={60 + i * 820 / values.length} y={Math.min(y(0), y(v))} width={600 / values.length} height={Math.max(1, Math.abs(y(0) - y(v)))} fill="#5897d4" onMouseEnter={() => setHover(i)}/>) : <polyline points={values.map((v, i) => `${60 + i * 820 / Math.max(1, values.length - 1)},${y(v)}`).join(' ')} fill="none" stroke="#5897d4" strokeWidth="2"/>}
 {trendline && <line x1="60" y1={y(values[0])} x2="880" y2={y(values[values.length - 1])} stroke="#b882d3" strokeDasharray="6 3"/>}
 {stagnation !== 0 && <rect x={stagnation === 'out' ? 650 : 240} y="40" width="90" height="210" fill="#f0c661" opacity=".12"/>}
 {stagnationV2 !== 0 && <rect x={stagnationV2 === 'out' ? 750 : 380} y="40" width="70" height="210" fill="#ab80dd" opacity=".12"/>}
 {crosshair && hover !== null && values[hover] !== undefined && <g stroke="#bbb" strokeDasharray="3 3"><line x1={60 + hover * 820 / Math.max(1, values.length - 1)} x2={60 + hover * 820 / Math.max(1, values.length - 1)} y1="40" y2="250"/><line x1="60" x2="880" y1={y(values[hover])} y2={y(values[hover])}/></g>}
 {markers !== 'off' && values.map((v, i) => <line key={i} x1={60 + i * 820 / Math.max(1, values.length - 1)} x2={60 + i * 820 / Math.max(1, values.length - 1)} y1={y(v) - 8} y2={y(v) + (markers === 'maemfe' ? 18 : 4)} stroke="#7bbb82"/>)}
 {benchmark && <path d="M60 245 L180 230 L300 210 L450 180 L600 170 L880 100" stroke="#dca74c" fill="none"/>}
 {values.map((v, i) => <circle key={i} cx={60 + i * 820 / Math.max(1, values.length - 1)} cy={y(v)} r="5" fill={points === 'all' || (points === 'grow' && v > (values[i - 1] ?? v)) ? '#5897d4' : 'transparent'} onMouseEnter={() => setHover(i)}><title>{`${i + 1}: ${v}`}</title></circle>)}
 </svg><output>{hover === null || values[hover] === undefined ? 'Hover over the chart to inspect a value' : `${hover + 1}: ${values[hover].toFixed(2)}`}</output></div>;
}
export function TradesChart() {
    const [selected, setSelected] = useState(0);
    const [symbol, setSymbol] = useState('EURUSD / H1');
    const [zoom, setZoom] = useState(1);
    const [grid, setGrid] = useState(true);
    const [indicator, setIndicator] = useState(false);
    const [labels, setLabels] = useState<string[]>(['Price']);
    const bars = [[90, 100, 80, 110], [100, 110, 95, 120], [110, 105, 100, 125], [105, 125, 102, 130], [125, 130, 118, 140], [130, 120, 115, 138], [120, 145, 115, 152], [145, 138, 130, 155], [138, 150, 132, 158]];
    return <><div className="sqr-toolbar"><select aria-label="Chart symbol" value={symbol} onChange={e => setSymbol(e.target.value)}>{['EURUSD / H1', 'GBPUSD / H1'].map(v => <option key={v}>{v}</option>)}</select><label><input type="checkbox" checked={indicator} onChange={e => setIndicator(e.target.checked)}/>Show indicators</label><button className="sqd-btn" aria-pressed={grid} onClick={() => setGrid(!grid)}>Show grid</button><label>Zoom</label><button className="sqd-btn" aria-label="Zoom out" onClick={() => setZoom(z => Math.max(1, z - .25))}>-</button><button className="sqd-btn" onClick={() => setZoom(1)}>reset</button><button className="sqd-btn" aria-label="Zoom in" onClick={() => setZoom(z => Math.min(2, z + .25))}>+</button><label>Show/hide</label>{['Price', 'Ticket', 'Profit/Loss'].map(l => <button key={l} className="sqd-btn" aria-pressed={labels.includes(l)} onClick={() => setLabels(old => old.includes(l) ? old.filter(v => v !== l) : [...old, l])}>{l}</button>)}<button className="sqd-btn" disabled={selected === 0} onClick={() => setSelected(v => v - 1)}>Previous trade</button><button className="sqd-btn" disabled={selected === 8} onClick={() => setSelected(v => v + 1)}>Next trade</button></div><div className="sqr-mock-chart"><h3>{symbol} — stored chart preview</h3><svg viewBox={`0 0 ${900 / zoom} 280`} role="img" aria-label="Trades on chart" preserveAspectRatio="xMinYMid meet">{grid && [80, 120, 160, 200].map(y => <line key={y} x1="0" x2="900" y1={y} y2={y} stroke="#555"/>)}{bars.map(([open, close, low, high], i) => <g key={i} onClick={() => setSelected(i)}><line x1={80 + i * 85} x2={80 + i * 85} y1={270 - high} y2={270 - low} stroke={close > open ? '#66be74' : '#e57373'}/><rect x={65 + i * 85} y={270 - Math.max(open, close)} width="30" height={Math.abs(close - open)} fill={close > open ? '#66be74' : '#e57373'} stroke={i === selected ? 'white' : 'none'}/>{labels.includes('Price') && <text x={65 + i * 85} y="215" fill="#bbb">{close}</text>}{labels.includes('Ticket') && <text x={65 + i * 85} y="235" fill="#bbb">#{i + 1}</text>}{labels.includes('Profit/Loss') && <text x={65 + i * 85} y="255" fill="#bbb">{close - open}</text>}</g>)}<path d="M80 185 L335 145" stroke="#66b4df" strokeDasharray="5 4" fill="none"/>{indicator && <path d="M80 180 L200 170 L330 150 L500 145 L680 135 L810 120" stroke="#d7ad4e" fill="none"/>}</svg><p>Selected bar: {selected + 1} | Open: {bars[selected][0]} | Close: {bars[selected][1]} — mock price coordinates</p></div></>;
}
