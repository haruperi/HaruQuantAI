import type { Tool } from './types';
import { path } from './geometry';
export const Highlighter: Tool = {
  label: 'Highlighter',
  anchors: 0,
  group: 'Shapes',
  build: (d, p) => [
    { ...path(d.points.map(p.point)), strokeWidth: 18, strokeOpacity: 0.28, lineCap: 'round' },
  ],
};
