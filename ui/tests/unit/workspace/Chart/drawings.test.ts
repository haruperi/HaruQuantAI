import { it, expect } from 'vitest';
import { tools } from '../../../../src/workspace/Chart/src/tools/catalog';
import { primitiveHit } from '../../../../src/workspace/Chart/src/tools/geometry';
import { toolIds, type Drawing } from '../../../../src/workspace/Chart/src/types';
it('every requested tool produces finite geometry from market anchors', () => {
  for (const tool of toolIds) {
    const d: Drawing = {
      id: 'a',
      tool,
      points: [
        { time: 10, price: 20 },
        { time: 100, price: 80 },
        { time: 60, price: 50 },
      ],
      color: '#2962ff',
      width: 2,
      dash: false,
      opacity: 1,
      text: 'test',
      locked: false,
      hidden: false,
      extendLeft: false,
      extendRight: false,
    };
    const shapes = tools[tool].build(d, {
      point: (p) => ({ x: p.time, y: p.price }),
      width: 1000,
      height: 700,
      barMs: 1,
    });
    expect(shapes.length).toBeGreaterThan(0);
    expect(JSON.stringify(shapes)).not.toMatch(/null|NaN/);
  }
});
it('hit tests segment edges and text without selecting remote points', () => {
  const line = {
    kind: 'path' as const,
    points: [
      { x: 0, y: 0 },
      { x: 100, y: 100 },
    ],
  };
  expect(primitiveHit(line, { x: 50, y: 53 })).toBe(true);
  expect(primitiveHit(line, { x: 80, y: 20 })).toBe(false);
});
