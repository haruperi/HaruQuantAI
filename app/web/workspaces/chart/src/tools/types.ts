import type { Bar, Drawing, Point, XY } from '../types';
export type Primitive = (
  | { kind: 'path'; points: XY[]; closed?: boolean; fill?: boolean }
  | { kind: 'ellipse'; center: XY; rx: number; ry: number }
  | { kind: 'text'; at: XY; text: string }
  | { kind: 'badge'; at: XY; text: string; background: string }
) & {
  color?: string;
  fillOpacity?: number;
  dash?: number[];
  strokeWidth?: number;
  strokeOpacity?: number;
  lineCap?: CanvasLineCap;
};
export interface Projection {
  bars?: readonly Bar[];
  point: (p: Point) => XY;
  width: number;
  height: number;
  barMs: number;
  index?: (time: number) => number;
}
export interface Tool {
  label: string;
  anchors: number;
  group: string;
  shortcut?: string;
  build: (drawing: Drawing, projection: Projection) => Primitive[];
}
