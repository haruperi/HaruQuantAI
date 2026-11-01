import type { Tool } from './types';
import { pitchfork } from './pitchforkVariants';
export const Pitchfork: Tool = {
  label: 'Pitchfork',
  anchors: 3,
  group: 'Trend',
  build: (d, p) => pitchfork(d, p, 'standard'),
};
