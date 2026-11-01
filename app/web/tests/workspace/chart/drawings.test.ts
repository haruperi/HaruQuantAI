import { defaultCurvePoints } from '../../../workspaces/chart/src/tools/shapeTools';
import { defaultPositionPoints } from '../../../workspaces/chart/src/tools/forecasting';
import { anchoredVWAP, volumeBins } from '../../../workspaces/chart/src/tools/volumeTools';
import {
  sourceCandles,
  positionMetrics,
  positionPoints,
} from '../../../workspaces/chart/src/tools/forecasting';
import { it, expect } from 'vitest';
import { tools, patternSections } from '../../../workspaces/chart/src/tools/catalog';
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

const patternDrawing = (tool: Drawing['tool']): Drawing =>
  drawing(
    tool,
    Array.from({ length: tools[tool].anchors }, (_, i) => ({
      time: 100 + i * 40,
      price: i % 2 ? 50 : 20,
    })),
  );
it('pattern tools expose the required pivot counts and ordered labels', () => {
  const sequences: [Drawing['tool'], string[]][] = [
    ['XABCDPattern', ['X', 'A', 'B', 'C', 'D']],
    ['CypherPattern', ['X', 'A', 'B', 'C', 'D']],
    ['ABCDPattern', ['A', 'B', 'C', 'D']],
    ['TrianglePattern', ['A', 'B', 'C', 'D']],
    ['ElliottImpulse', ['0', '1', '2', '3', '4', '5']],
    ['ElliottCorrection', ['0', 'A', 'B', 'C']],
    ['ElliottTriangle', ['0', 'A', 'B', 'C', 'D', 'E']],
    ['ElliottDoubleCombo', ['0', 'W', 'X', 'Y']],
    ['ElliottTripleCombo', ['0', 'W', 'X', 'Y', 'X', 'Z']],
  ];
  for (const [id, names] of sequences) {
    expect(tools[id].anchors).toBe(names.length);
    const text = tools[id]
      .build(patternDrawing(id), projection)
      .filter((shape) => shape.kind === 'text')
      .map((shape) => shape.text);
    expect(text.slice(0, names.length)).toEqual(names);
  }
  expect(tools.HeadShoulders.anchors).toBe(7);
  expect(tools.ThreeDrives.anchors).toBe(7);
});
it('harmonic ratios are price-based and zero denominators do not invent measurements', () => {
  const d = drawing('XABCDPattern', [
    { time: 0, price: 10 },
    { time: 20, price: 30 },
    { time: 40, price: 20 },
  ]);
  expect(
    tools.XABCDPattern.build(d, projection)
      .filter((shape) => shape.kind === 'text')
      .at(-1)?.text,
  ).toBe('0.500');
  d.points[1].price = 10;
  expect(
    tools.XABCDPattern.build(d, projection)
      .filter((shape) => shape.kind === 'text')
      .at(-1)?.text,
  ).toBe('—');
  expect(
    tools.CypherPattern.build(patternDrawing('CypherPattern'), projection).length,
  ).toBeGreaterThan(tools.XABCDPattern.build(patternDrawing('XABCDPattern'), projection).length);
});
it('triangle boundaries connect alternating highs and lows and neckline joins the two neck pivots', () => {
  const triangle = tools.TrianglePattern.build(
    patternDrawing('TrianglePattern'),
    projection,
  ).filter((shape) => shape.kind === 'path');
  expect(triangle[1].points).toEqual([
    { x: 100, y: 20 },
    { x: 180, y: 20 },
  ]);
  expect(triangle[2].points).toEqual([
    { x: 140, y: 50 },
    { x: 220, y: 50 },
  ]);
  const head = tools.HeadShoulders.build(patternDrawing('HeadShoulders'), projection).filter(
    (shape) => shape.kind === 'path',
  );
  expect(head.at(-1)?.points).toEqual([
    { x: 180, y: 20 },
    { x: 260, y: 20 },
  ]);
});
it('cycle period and sine amplitude follow their anchors with bounded work', () => {
  const d = drawing('CyclicLines', [
    { time: 100, price: 20 },
    { time: 200, price: 60 },
  ]);
  const cyclic = tools.CyclicLines.build(d, projection).filter((shape) => shape.kind === 'path');
  expect(cyclic[1].points[0].x - cyclic[0].points[0].x).toBe(100);
  expect(cyclic.length).toBeLessThanOrEqual(256);
  const arcs = tools.TimeCycles.build({ ...d, tool: 'TimeCycles' }, projection).filter(
    (shape) => shape.kind === 'path',
  );
  expect(arcs[0].points).toHaveLength(33);
  const sine = tools.SineLine.build({ ...d, tool: 'SineLine' }, projection)[0];
  if (sine.kind !== 'path') throw new Error('Expected sine path');
  expect(sine.points.length).toBeLessThanOrEqual(4097);
  const crest = sine.points.reduce((best, point) =>
    Math.abs(point.x - 200) < Math.abs(best.x - 200) ? point : best,
  );
  expect(crest.y).toBeCloseTo(60, 0);
  expect(primitiveHit(sine, crest)).toBe(true);
  expect(primitiveHit(sine, { x: 5000, y: 5000 })).toBe(false);
});
it('all pattern tools support partial, coincident and reversed previews without invalid geometry', () => {
  for (const id of patternSections.flatMap((section) => section.ids)) {
    for (const points of [
      [],
      [{ time: 10, price: 20 }],
      [
        { time: 10, price: 20 },
        { time: 10, price: 20 },
      ],
      [...patternDrawing(id).points].reverse(),
    ]) {
      const shapes = tools[id].build(drawing(id, points), projection);
      expect(shapes.length).toBeGreaterThan(0);
      expect(JSON.stringify(shapes)).not.toMatch(/null|NaN/);
    }
  }
});

const forecastBars = [10, 20, 30].map((close, i) => ({
  time: i * 10,
  open: close,
  high: close + 2,
  low: close - 2,
  close,
  volume: (i + 1) * 10,
}));
it('long and short drawings calculate risk/reward and flag invalid levels', () => {
  const long = drawing('LongPosition', [
    { time: 0, price: 100 },
    { time: 10, price: 90 },
    { time: 20, price: 120 },
  ]);
  const shapes = tools.LongPosition.build(long, projection);
  expect(
    shapes.some(
      (shape) => shape.kind === 'badge' && shape.text.includes('Risk/reward ratio: 2.00'),
    ),
  ).toBe(true);
  expect(shapes.filter((shape) => shape.fillOpacity === 0.28).map((shape) => shape.color)).toEqual([
    '#f23645',
    '#089981',
  ]);
  const short = {
    ...long,
    tool: 'ShortPosition' as const,
    points: [
      { time: 0, price: 100 },
      { time: 10, price: 110 },
      { time: 20, price: 80 },
    ],
  };
  expect(
    tools.ShortPosition.build(short, projection).some(
      (shape) => shape.kind === 'badge' && shape.text.includes('Risk/reward ratio: 2.00'),
    ),
  ).toBe(true);
  expect(
    tools.LongPosition.build(short, projection).some(
      (shape) => shape.kind === 'text' && shape.text.includes('opposite sides'),
    ),
  ).toBe(true);
});
it('VWAP weights typical prices by volume and excludes zero-volume bars', () => {
  const result = anchoredVWAP(forecastBars);
  expect(result[0].price).toBe(10);
  expect(result[1].price).toBeCloseTo(50 / 3);
  expect(result[2].price).toBeCloseTo(70 / 3);
  expect(anchoredVWAP(forecastBars.map((bar) => ({ ...bar, volume: 0 })))).toEqual([]);
});
it('volume bins conserve volume including flat candles and profiles disclose the estimate', () => {
  const bins = volumeBins(
    [...forecastBars, { ...forecastBars[0], high: 10, low: 10, volume: 25 }],
    32,
  );
  expect(bins.reduce((sum, bin) => sum + bin.volume, 0)).toBeCloseTo(85);
  expect(bins).toHaveLength(32);
  const d = drawing('FixedVolumeProfile', [
    { time: 0, price: 10 },
    { time: 20, price: 30 },
  ]);
  expect(
    tools.FixedVolumeProfile.build(d, { ...projection, bars: forecastBars }).some(
      (shape) => shape.kind === 'text' && shape.text.includes('OHLC estimate'),
    ),
  ).toBe(true);
  const anchored = tools.AnchoredVWAP.build(drawing('AnchoredVWAP', [{ time: 10, price: 20 }]), {
    ...projection,
    bars: forecastBars,
  });
  if (anchored[0].kind !== 'path') throw new Error('Expected VWAP path');
  expect(anchored[0].points[0]).toEqual({ x: 10, y: 20 });
});
it('bars pattern uses stable saved candles and translates them to its destination', () => {
  const d = {
    ...drawing('BarsPattern', [
      { time: 0, price: 10 },
      { time: 20, price: 30 },
      { time: 50, price: 100 },
    ]),
    sourceBars: forecastBars,
  };
  expect(sourceCandles(d, { ...projection, bars: [] })).toBe(forecastBars);
  const shapes = tools.BarsPattern.build(d, { ...projection, bars: [] });
  if (shapes[0].kind !== 'path') throw new Error('Expected candle wick');
  expect(shapes[0].points).toEqual([
    { x: 50, y: 102 },
    { x: 50, y: 98 },
  ]);
  const ghost = { ...d, tool: 'GhostFeed' as const };
  expect(tools.GhostFeed.build(ghost, projection)).toEqual(
    tools.GhostFeed.build(ghost, projection),
  );
  expect(tools.GhostFeed.build(ghost, projection).length).toBe(33);
});
it('range tools report signed price change, bars and elapsed time', () => {
  const d = drawing('DatePriceRange', [
    { time: 0, price: 100 },
    { time: 120000, price: 110 },
  ]);
  const shapes = tools.DatePriceRange.build(d, { ...projection, barMs: 60000 });
  const text = shapes
    .filter((shape) => shape.kind === 'text')
    .map((shape) => shape.text)
    .join('');
  expect(text).toContain('10.00 (10.00%)');
  expect(text).toContain('2 bars | 2.0 min');
});
it('forecasting tools render safe messages for absent data and bounded partial previews', () => {
  for (const id of [
    'AnchoredVWAP',
    'FixedVolumeProfile',
    'AnchoredVolumeProfile',
    'BarsPattern',
    'GhostFeed',
    'Sector',
    'PriceRange',
    'DateRange',
    'DatePriceRange',
  ] as const) {
    for (const points of [
      [],
      [{ time: 0, price: 10 }],
      [
        { time: 10, price: 10 },
        { time: 10, price: 10 },
      ],
    ]) {
      const shapes = tools[id].build(drawing(id, points), projection);
      expect(shapes.length).toBeGreaterThan(0);
      expect(JSON.stringify(shapes)).not.toMatch(/null|NaN/);
    }
  }
});

it('position sizing and reference badges use independent width and explicit projected amounts', () => {
  const d = {
    ...drawing('LongPosition', [
      { time: 0, price: 100 },
      { time: 10, price: 90 },
      { time: 20, price: 120 },
    ]),
    positionSizing: { accountSize: 1000, riskPercent: 25 },
  };
  expect(positionMetrics(d)).toMatchObject({
    quantity: 25,
    riskAmount: 250,
    rewardAmount: 500,
    ratio: 2,
  });
  expect(positionPoints(d)).toEqual([
    { time: 0, price: 100 },
    { time: 0, price: 90 },
    { time: 0, price: 120 },
    { time: 20, price: 100 },
  ]);
  const shapes = tools.LongPosition.build(d, projection);
  const badges = shapes.filter((shape) => shape.kind === 'badge');
  expect(badges[0].text).toContain('Amount: 1500.00');
  expect(badges[1].text).toContain('Amount: 750.00');
  expect(badges[2].text).toContain('Projected P&L: 500.00, Qty: 25.00');
  expect(JSON.stringify(shapes)).not.toContain('Closed');
  expect(shapes.some((shape) => shape.dash?.length === 2)).toBe(true);
  expect(shapes.filter((shape) => shape.fillOpacity === 0.28)).toHaveLength(2);
});

it('one-click position defaults mirror a one-percent stop and equal target', () => {
  expect(defaultPositionPoints({ time: 1000, price: 100 }, false, 10)).toEqual([
    { time: 1000, price: 100 },
    { time: 1000, price: 99 },
    { time: 1000, price: 101 },
    { time: 1080, price: 100 },
  ]);
  expect(
    defaultPositionPoints({ time: 1000, price: 100 }, true, 10).map((point) => point.price),
  ).toEqual([100, 101, 99, 100]);
});

it('rotated rectangles retain perpendicular adjacent edges and their original first edge', () => {
  const shape = tools.RotatedRectangle.build(drawing('RotatedRectangle'), projection)[0];
  if (shape.kind !== 'path') throw new Error('Expected rectangle');
  const [a, b, c] = shape.points;
  expect(a).toEqual({ x: 0, y: 10 });
  expect(b).toEqual({ x: 10, y: 20 });
  expect((b.x - a.x) * (c.x - b.x) + (b.y - a.y) * (c.y - b.y)).toBeCloseTo(0);
});
it('paths have an arrowhead while polylines stay open, and marks are single-anchor tools', () => {
  expect(tools.PathTool.build(drawing('PathTool'), projection)).toHaveLength(2);
  const polyline = tools.Polyline.build(drawing('Polyline'), projection);
  expect(polyline).toHaveLength(1);
  if (polyline[0].kind !== 'path') throw new Error('Expected polyline');
  expect(polyline[0].closed).toBe(false);
  expect(tools.ArrowMarkUp.anchors).toBe(1);
  expect(tools.ArrowMarkDown.anchors).toBe(1);
});
it('highlighter produces a broad translucent rounded stroke and hit tests its width', () => {
  const shape = tools.Highlighter.build(
    drawing('Highlighter', [
      { time: 0, price: 10 },
      { time: 100, price: 10 },
    ]),
    projection,
  )[0];
  expect(shape).toMatchObject({ strokeWidth: 18, strokeOpacity: 0.28, lineCap: 'round' });
  expect(primitiveHit(shape, { x: 50, y: 19 })).toBe(true);
  expect(primitiveHit(shape, { x: 50, y: 30 })).toBe(false);
});
it('Bezier curves reach their endpoints and control handles change the bend', () => {
  const first = { time: 0, price: 100 },
    last = { time: 100, price: 120 };
  for (const [id, double] of [
    ['Curve', false],
    ['DoubleCurve', true],
  ] as const) {
    const points = defaultCurvePoints(first, last, double);
    const shapes = tools[id].build(drawing(id, points), projection);
    const shape = shapes[0];
    if (shape.kind !== 'path') throw new Error('Expected curve');
    expect(shape.points[0]).toEqual({ x: 0, y: 100 });
    expect(shape.points.at(-1)).toEqual({ x: 100, y: 120 });
    const changed = points.map((point, i) =>
      i === 2 ? { ...point, price: point.price + 50 } : point,
    );
    expect(tools[id].build(drawing(id, changed), projection)).not.toEqual(shapes);
    expect(shape.points.length).toBeLessThanOrEqual(97);
  }
});
it('arcs pass through their bend anchor and partial or coincident shapes stay finite', () => {
  const arc = tools.Arc.build(
    drawing('Arc', [
      { time: 0, price: 10 },
      { time: 20, price: 10 },
      { time: 10, price: 20 },
    ]),
    projection,
  )[0];
  expect(primitiveHit(arc, { x: 10, y: 20 })).toBe(true);
  for (const id of [
    'RotatedRectangle',
    'Curve',
    'DoubleCurve',
    'Arc',
    'ArrowMarker',
    'ArrowMarkUp',
    'ArrowMarkDown',
    'PathTool',
    'Polyline',
    'Highlighter',
  ] as const) {
    for (const points of [
      [],
      [{ time: 10, price: 20 }],
      [
        { time: 10, price: 20 },
        { time: 10, price: 20 },
      ],
    ]) {
      expect(JSON.stringify(tools[id].build(drawing(id, points), projection))).not.toMatch(
        /NaN|null/,
      );
    }
  }
});
