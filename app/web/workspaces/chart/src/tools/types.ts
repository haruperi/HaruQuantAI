import type { Drawing, Point, XY } from '../types';
export type Primitive =
  | { kind: 'path'; points: XY[]; closed?: boolean; fill?: boolean }
  | { kind: 'ellipse'; center: XY; rx: number; ry: number }
  | { kind: 'text'; at: XY; text: string };
export interface Projection {
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
