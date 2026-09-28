/** Owner-local presentation/resource documents; no backend execution authority. */
export interface SurfacePoint {
  x: number;
  y: number;
  z: number;
  xParam: string;
  yParam: string;
  zMetric: string;
}

export interface PlateauCluster {
  id: string;
  centerParamX: number;
  centerParamY: number;
  rangeX: [number, number];
  rangeY: [number, number];
  averageMetric: number;
  standardDeviation: number;
  stabilityScore: number;
  profitablePercentage: number;
}
