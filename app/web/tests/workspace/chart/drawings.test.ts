import { it, expect } from 'vitest';
import { tools } from '../../../workspaces/chart/src/tools/catalog';
import { primitiveHit } from '../../../workspaces/chart/src/tools/geometry';
import { toolIds, type Drawing } from '../../../workspaces/chart/src/types';
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

const drawing = (
  tool: Drawing['tool'],
  points = [
    { time: 0, price: 10 },
    { time: 10, price: 20 },
    { time: 6, price: 30 },
  ],
): Drawing => ({
  id: 'geometry',
  tool,
  points,
  color: '#2962ff',
  width: 2,
  dash: false,
  opacity: 1,
  text: '',
  locked: false,
  hidden: false,
  extendLeft: false,
  extendRight: false,
});
const projection = {
  point: (p: { time: number; price: number }) => ({ x: p.time, y: p.price }),
  width: 1000,
  height: 700,
  barMs: 1,
};
const paths = (tool: Drawing['tool']) =>
  tools[tool].build(drawing(tool), projection).filter((shape) => shape.kind === 'path');
it('extended lines extend in both directions and crossline spans the viewport', () => {
  const extended = paths('ExtendedLine')[0];
  expect(extended.points[0].x).toBeLessThan(0);
  expect(extended.points[1].x).toBeGreaterThan(1000);
  expect(paths('CrossLine').map((shape) => shape.points)).toEqual([
    [
      { x: 0, y: 10 },
      { x: 1000, y: 10 },
    ],
    [
      { x: 0, y: 0 },
      { x: 0, y: 700 },
    ],
  ]);
});
it('info line reports market deltas and trend angle measures projected screen degrees', () => {
  const info = tools.InfoLine.build(drawing('InfoLine'), projection).find(
    (shape) => shape.kind === 'text',
  );
  expect(info?.text).toContain('10.00 (100.00%) � 10 bars');
  const angle = tools.TrendAngle.build(drawing('TrendAngle'), projection).find(
    (shape) => shape.kind === 'text',
  );
  expect(angle?.text).toBe('-45.0�');
});
it('channel boundaries stay parallel, disjoint starts at the third anchor, and flat boundary is horizontal', () => {
  const parallel = paths('ParallelChannel');
  const slope = (points: { x: number; y: number }[]) =>
    (points[1].y - points[0].y) / (points[1].x - points[0].x);
  expect(slope(parallel[1].points)).toBe(slope(parallel[2].points));
  expect(primitiveHit(parallel[2], { x: 6, y: 30 })).toBe(true);
  expect(paths('DisjointChannel')[2].points[0]).toEqual({ x: 6, y: 30 });
  expect(slope(paths('FlatTopBottom')[2].points)).toBe(0);
});
it('regression fits candle closes, excludes outside bars and uses two residual standard deviations', () => {
  const bars = [10, 14, 14].map((close, time) => ({
    time,
    close,
    open: close,
    high: close,
    low: close,
    volume: 1,
  }));
  const d = drawing('RegressionTrend', [
    { time: 0, price: 999 },
    { time: 2, price: 999 },
  ]);
  const result = tools.RegressionTrend.build(d, {
    ...projection,
    bars: [...bars, { ...bars[0], time: 3, close: 999 }],
  });
  const center = result[1];
  expect(center.kind).toBe('path');
  if (center.kind !== 'path') throw new Error('Expected regression baseline');
  expect(center.points[0].y).toBeCloseTo(10 + 2 / 3);
  expect(center.points[1].y).toBeCloseTo(14 + 2 / 3);
  const upper = result[2];
  if (upper.kind !== 'path') throw new Error('Expected upper band');
  expect(upper.points[0].y - center.points[0].y).toBeCloseTo(2 * Math.sqrt(8 / 9));
  expect(tools.RegressionTrend.build(d, { ...projection, bars: [] })[0].kind).toBe('text');
  expect(
    tools.RegressionTrend.build({ ...d, points: [...d.points].reverse() }, { ...projection, bars }),
  ).toEqual(tools.RegressionTrend.build(d, { ...projection, bars }));
});
it('pitchfork variants have explicit distinct origins and inside tine spacing', () => {
  expect(paths('Pitchfork')[0].points[0]).toEqual({ x: 0, y: 10 });
  expect(paths('SchiffPitchfork')[0].points[0]).toEqual({ x: 0, y: 15 });
  expect(paths('ModifiedSchiffPitchfork')[0].points[0]).toEqual({ x: 5, y: 15 });
  expect(paths('InsidePitchfork')[1].points[0]).toEqual({ x: 9, y: 22.5 });
  expect(paths('InsidePitchfork')[2].points[0]).toEqual({ x: 7, y: 27.5 });
});
it('new geometry handles coincident and vertical anchors without nonfinite values', () => {
  for (const id of [
    'ExtendedLine',
    'ParallelChannel',
    'DisjointChannel',
    'FlatTopBottom',
    'SchiffPitchfork',
    'ModifiedSchiffPitchfork',
    'InsidePitchfork',
  ] as const) {
    for (const points of [
      [
        { time: 1, price: 10 },
        { time: 1, price: 10 },
        { time: 1, price: 10 },
      ],
      [
        { time: 1, price: 10 },
        { time: 1, price: 20 },
        { time: 3, price: 30 },
      ],
    ]) {
      const shapes = tools[id].build(drawing(id, points), projection);
      expect(JSON.stringify(shapes)).not.toMatch(/null|NaN/);
    }
  }
});

it('Fibonacci channel places the 1 level through the third anchor and fans preserve ratios', () => {
  const channel = tools.FibChannel.build(drawing('FibChannel'), projection);
  const levels = channel.filter((shape) => shape.kind === 'path');
  const one = levels[6];
  expect(primitiveHit(one, { x: 6, y: 30 })).toBe(true);
  const fan = tools.FibSpeedFan.build(drawing('FibSpeedFan'), projection).filter(
    (shape) => shape.kind === 'path',
  );
  expect(fan).toHaveLength(6);
  const last = fan.at(-1)!;
  expect(primitiveHit(last, { x: 10, y: 20 })).toBe(true);
});
it('Fibonacci time tools distinguish sequence spacing from third-anchor trend projections', () => {
  const time = tools.FibTimezone.build(drawing('FibTimezone'), projection).filter(
    (shape) => shape.kind === 'path',
  );
  expect(time.map((shape) => shape.points[0].x)).toEqual([0, 10, 20, 30, 50, 80, 130, 210]);
  const trend = tools.TrendFibTime.build(drawing('TrendFibTime'), projection).filter(
    (shape) => shape.kind === 'path',
  );
  expect(trend[1].points[0].x).toBe(6);
  expect(trend[3].points[0].x).toBe(16);
});
it('retracements calculate price ratios before nonlinear projection and honor both extensions', () => {
  const d = { ...drawing('FibRetracement'), extendLeft: true, extendRight: true };
  const shapes = tools.FibRetracement.build(d, {
    ...projection,
    point: (p) => ({ x: p.time, y: Math.log(p.price) }),
  });
  const half = shapes.filter((shape) => shape.kind === 'path')[3];
  expect(half.points[0]).toEqual({ x: 0, y: Math.log(15) });
  expect(half.points[1].x).toBe(1000);
});
it('trend extensions project the measured price move from the third anchor', () => {
  const shapes = tools.FibExtension.build(drawing('FibExtension'), projection);
  const levels = shapes.filter((shape) => shape.kind === 'path').slice(1);
  expect(levels[0].points[0].y).toBe(30);
  expect(levels[6].points[0].y).toBeCloseTo(46.18);
});
it('Fibonacci curves have bounded samples and golden spiral reaches its radius anchor', () => {
  const spiral = paths('FibSpiral')[0];
  expect(spiral.points).toHaveLength(257);
  // theta=0 at sample 2/3 of the six-pi range, within one sampling step.
  const radius = Math.hypot(10, 10);
  const radii = spiral.points.map((p) => Math.hypot(p.x, p.y - 10));
  const quarterTurn = 256 / 12;
  const i = 128,
    j = i + Math.round(quarterTurn);
  expect(radii[j] / radii[i]).toBeCloseTo(((1 + Math.sqrt(5)) / 2) ** ((j - i) / quarterTurn));
  expect(radii.some((r) => Math.abs(r - radius) < 1)).toBe(true);
  for (const id of ['FibCircles', 'FibSpeedArcs', 'FibWedge'] as const) {
    const curves = paths(id);
    expect(curves.every((shape) => shape.points.length <= 97)).toBe(true);
    const point = curves.at(-1)!.points[20];
    expect(primitiveHit(curves.at(-1)!, point)).toBe(true);
    expect(primitiveHit(curves.at(-1)!, { x: 10000, y: 10000 })).toBe(false);
  }
});
it('Gann box, square and fixed square have distinct calibrated geometry', () => {
  const d = drawing('GannSquareFixed', [
    { time: 0, price: 10 },
    { time: 40, price: 30 },
  ]);
  const fixed = tools.GannSquareFixed.build(d, projection)[0];
  if (fixed.kind !== 'path') throw new Error('Expected fixed-square outline');
  expect(fixed.points[2]).toEqual({ x: 40, y: 50 });
  const square = tools.GannSquare.build({ ...d, tool: 'GannSquare' }, projection)[0];
  if (square.kind !== 'path') throw new Error('Expected square outline');
  expect(square.points[2]).toEqual({ x: 40, y: 30 });
  expect(paths('GannBox').length).toBeLessThan(paths('GannSquare').length);
  expect(paths('GannFan')).toHaveLength(9);
});
it('all Fibonacci and Gann tools stay finite with coincident and reversed anchors', () => {
  for (const id of toolIds.filter((id) => tools[id].group === 'Fibonacci')) {
    for (const points of [
      [
        { time: 1, price: 10 },
        { time: 1, price: 10 },
        { time: 1, price: 10 },
      ],
      [
        { time: 30, price: 40 },
        { time: 10, price: 20 },
        { time: 20, price: 10 },
      ],
    ]) {
      const shapes = tools[id].build(drawing(id, points), projection);
      expect(shapes.length).toBeGreaterThan(0);
      expect(JSON.stringify(shapes)).not.toMatch(/null|NaN/);
    }
  }
});
