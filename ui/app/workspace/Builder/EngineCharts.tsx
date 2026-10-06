import { useState } from 'react';
import {
  ENGINE_CHART_TYPES,
  databankFitnessSeries,
  heapMemorySeries,
  type EngineChartType,
} from './fixtures';

/**
 * The two engine chart cards of the Builder Progress engine column
 * (donor evidence retained target UI; current donor equivalence unverified). Each card centers a borderless type
 * select that gains a border on hover and renders the matching demo chart.
 * The donor type list is engine-fed; only the two observed types ship here.
 */

const W = 400;
const H = 150;

function DatabankFitnessChart() {
  const toPoints = (points: number[]) =>
    points
      .map((v, i) => `${(i / (points.length - 1)) * (W - 44) + 38},${H - 20 - v * (H - 34)}`)
      .join(' ');

  return (
    <svg className="sqd-chart-svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img" aria-label="Databank fitness chart">
      {[0, 0.25, 0.5, 0.75, 1].map(t => (
        <line
          key={t}
          x1={38}
          x2={W - 6}
          y1={H - 20 - t * (H - 34)}
          y2={H - 20 - t * (H - 34)}
          className="sqd-chart-grid"
        />
      ))}
      <text x={32} y={H - 16} className="sqd-chart-label" textAnchor="end">0</text>
      <text x={32} y={H - 20 - 0.5 * (H - 34) + 4} className="sqd-chart-label" textAnchor="end">0.5</text>
      <text x={32} y={H - 20 - (H - 34) + 8} className="sqd-chart-label" textAnchor="end">1.0</text>
      {databankFitnessSeries.map(s => (
        <polyline key={s.name} points={toPoints(s.points)} fill="none" stroke={s.color} strokeWidth={1.6} />
      ))}
      <text x={38} y={H - 4} className="sqd-chart-label">12AM</text>
      <text x={(W - 6 + 38) / 2} y={H - 4} className="sqd-chart-label" textAnchor="middle">12PM</text>
      <text x={W - 6} y={H - 4} className="sqd-chart-label" textAnchor="end">12AM</text>
    </svg>
  );
}

function HeapMemoryChart() {
  const { used, maxGb } = heapMemorySeries;
  const maxY = maxGb;
  const toX = (i: number) => (i / (used.length - 1)) * (W - 44) + 38;
  const toY = (v: number) => H - 20 - (v / maxY) * (H - 34);
  const area = `38,${H - 20} ${used.map((v, i) => `${toX(i)},${toY(v)}`).join(' ')} ${W - 6},${H - 20}`;

  return (
    <svg className="sqd-chart-svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img" aria-label="Heap memory chart">
      {[0, 0.5, 1].map(t => (
        <line key={t} x1={38} x2={W - 6} y1={H - 20 - t * (H - 34)} y2={H - 20 - t * (H - 34)} className="sqd-chart-grid" />
      ))}
      <text x={32} y={H - 16} className="sqd-chart-label" textAnchor="end">0</text>
      <text x={32} y={toY(maxY / 2) + 4} className="sqd-chart-label" textAnchor="end">{(maxY / 2).toFixed(1)}</text>
      <text x={32} y={toY(maxY) + 8} className="sqd-chart-label" textAnchor="end">{maxY.toFixed(1)}</text>
      <polygon points={area} fill="#57b93f" opacity={0.45} />
      <polyline points={used.map((v, i) => `${toX(i)},${toY(v)}`).join(' ')} fill="none" stroke="#57b93f" strokeWidth={1.6} />
      <line x1={38} x2={W - 6} y1={toY(maxY * 0.92)} y2={toY(maxGb * 0.92)} stroke="#d9534f" strokeWidth={1.2} strokeDasharray="5,3" />
      <text x={38} y={H - 4} className="sqd-chart-label">9:00am</text>
      <text x={(W - 6 + 38) / 2} y={H - 4} className="sqd-chart-label" textAnchor="middle">Time</text>
      <text x={W - 6} y={H - 4} className="sqd-chart-label" textAnchor="end">10:00am</text>
    </svg>
  );
}

export function EngineCharts() {
  const [types, setTypes] = useState<[EngineChartType, EngineChartType]>([
    ENGINE_CHART_TYPES[0],
    ENGINE_CHART_TYPES[1],
  ]);

  return (
    <div className="sqd-engine-charts">
      {[0, 1].map(index => (
        <div className="sqd-chart-box" key={index}>
          <div className="sqd-chart-card">
            <div className="sqd-chart-select">
              <span>{types[index]}</span>
              <select
                aria-label={`Engine chart ${index + 1} type`}
                value={types[index]}
                onChange={e => {
                  const value = e.target.value as EngineChartType;
                  setTypes(current => (index === 0 ? [value, current[1]] : [current[0], value]));
                }}
              >
                {ENGINE_CHART_TYPES.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            {types[index] === 'Databank Fitness - IS Training' ? (
              <>
                <div className="sqd-chart-legend">
                  {databankFitnessSeries.map(s => (
                    <span key={s.name}><i style={{ background: s.color }} />{s.name}</span>
                  ))}
                </div>
                <DatabankFitnessChart />
              </>
            ) : (
              <HeapMemoryChart />
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
