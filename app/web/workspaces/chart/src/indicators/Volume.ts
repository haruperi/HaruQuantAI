import type { IndicatorDefinition } from './types';
export const Volume: IndicatorDefinition = {
  step: (b, _c, i) => ({ values: [b[i].volume], state: [] }),
  name: 'Volume',
  pane: true,
  period: 1,
  calculate: (b) => [b.map((x) => x.volume)],
};
