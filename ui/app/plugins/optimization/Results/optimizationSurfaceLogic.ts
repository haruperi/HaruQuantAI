import type { SurfacePoint, PlateauCluster } from './presentation';

export interface OptimizationGridResult {
  points: SurfacePoint[];
  grid: SurfacePoint[][];
  clusters: PlateauCluster[];
  stats: {
    totalSimulations: number;
    profitableCount: number;
    profitablePct: number;
    losingCount: number;
    losingPct: number;
    zeroCount: number;
    zeroPct: number;
    averageMetric: string;
    isPass: boolean;
  };
}

export function generateOptimizationGrid(
  xParam: string = 'FastPeriod',
  yParam: string = 'SlowPeriod',
  zMetric: string = 'Net Profit',
  gridSize: number = 15
): OptimizationGridResult {
  const rawPoints: SurfacePoint[] = [];
  const matrix: SurfacePoint[][] = [];

  const xMin = 5;
  const xMax = 50;
  const yMin = 20;
  const yMax = 120;

  let profitableCount = 0;
  let losingCount = 0;
  let zeroCount = 0;
  let totalMetric = 0;

  for (let i = 0; i < gridSize; i++) {
    const row: SurfacePoint[] = [];
    const xVal = Math.round(xMin + (i / (gridSize - 1)) * (xMax - xMin));

    for (let j = 0; j < gridSize; j++) {
      const yVal = Math.round(yMin + (j / (gridSize - 1)) * (yMax - yMin));

      // Synthetic landscape with broad plateau
      const normX = (xVal - 22) / 10;
      const normY = (yVal - 58) / 25;
      const dist = Math.sqrt(normX * normX + normY * normY);

      const plateauBase = Math.exp(-dist * dist * 0.7);
      const secondaryPeak = 0.4 * Math.exp(-Math.pow(normX - 1.5, 2) - Math.pow(normY + 1.2, 2));
      const roughness = Math.sin(i * 1.8) * Math.cos(j * 1.8) * 0.08;
      const rawZ = plateauBase + secondaryPeak + roughness - 0.22;

      let zValue = 0;
      if (zMetric === 'Net Profit') {
        zValue = Math.round(rawZ * 12500);
      } else if (zMetric === 'Profit Factor') {
        zValue = Number(Math.max(0.4, 1.0 + rawZ * 1.8).toFixed(2));
      } else if (zMetric === 'Sharpe Ratio') {
        zValue = Number(Math.max(-0.5, 0.8 + rawZ * 2.2).toFixed(2));
      } else {
        zValue = Number(Math.max(0.2, 1.2 + rawZ * 3.5).toFixed(2));
      }

      if (zValue > 0) profitableCount++;
      else if (zValue < 0) losingCount++;
      else zeroCount++;

      totalMetric += zValue;

      const pt: SurfacePoint = {
        x: xVal,
        y: yVal,
        z: zValue,
        xParam,
        yParam,
        zMetric,
      };

      row.push(pt);
      rawPoints.push(pt);
    }
    matrix.push(row);
  }

  const totalSimulations = gridSize * gridSize;
  const profitablePct = Number(((profitableCount / totalSimulations) * 100).toFixed(1));
  const losingPct = Number(((losingCount / totalSimulations) * 100).toFixed(1));
  const zeroPct = Number(((zeroCount / totalSimulations) * 100).toFixed(1));

  const plateauClusters: PlateauCluster[] = [
    {
      id: 'cluster-1',
      centerParamX: 22,
      centerParamY: 58,
      rangeX: [16, 30],
      rangeY: [42, 75],
      averageMetric: zMetric === 'Net Profit' ? 8420 : 2.15,
      standardDeviation: zMetric === 'Net Profit' ? 420 : 0.12,
      stabilityScore: 92,
      profitablePercentage: 96.5,
    },
    {
      id: 'cluster-2',
      centerParamX: 38,
      centerParamY: 30,
      rangeX: [32, 44],
      rangeY: [24, 40],
      averageMetric: zMetric === 'Net Profit' ? 4180 : 1.54,
      standardDeviation: zMetric === 'Net Profit' ? 860 : 0.28,
      stabilityScore: 74,
      profitablePercentage: 78.0,
    },
  ];

  return {
    points: rawPoints,
    grid: matrix,
    clusters: plateauClusters,
    stats: {
      totalSimulations,
      profitableCount,
      profitablePct,
      losingCount,
      losingPct,
      zeroCount,
      zeroPct,
      averageMetric: (totalMetric / totalSimulations).toFixed(1),
      isPass: profitablePct >= 60,
    },
  };
}

export function projectCoordinate(
  i: number,
  j: number,
  zVal: number,
  gridSize: number,
  minZ: number,
  maxZ: number,
  rotX: number,
  rotY: number,
  zoom: number,
  width: number,
  height: number
) {
  const rangeZ = maxZ - minZ || 1;
  const radX = (rotX * Math.PI) / 180;
  const radY = (rotY * Math.PI) / 180;

  const cosX = Math.cos(radX);
  const sinX = Math.sin(radX);
  const cosY = Math.cos(radY);
  const sinY = Math.sin(radY);

  const centerX = width / 2;
  const centerY = height / 2 + 30;
  const scale = 14 * zoom;

  const cx = (i - gridSize / 2) * scale;
  const cy = (j - gridSize / 2) * scale;
  const cz = (((zVal - minZ) / rangeZ) * 120 - 60) * zoom;

  const rx1 = cx * cosY - cy * sinY;
  const ry1 = cx * sinY + cy * cosY;
  const rz1 = cz;

  const rx2 = rx1;
  const ry2 = ry1 * cosX - rz1 * sinX;
  const rz2 = ry1 * sinX + rz1 * cosX;

  return {
    screenX: centerX + rx2,
    screenY: centerY + ry2,
    depth: rz2,
  };
}
