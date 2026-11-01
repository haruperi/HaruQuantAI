import { Highlighter } from './Highlighter';
import {
  ArrowMarker,
  ArrowMarkUp,
  ArrowMarkDown,
  RotatedRectangle,
  PathTool,
  Polyline,
  Arc,
  Curve,
  DoubleCurve,
} from './shapeTools';
import {
  LongPosition,
  ShortPosition,
  PositionForecast,
  BarsPattern,
  GhostFeed,
  Sector,
} from './forecasting';
import { AnchoredVWAP, FixedVolumeProfile, AnchoredVolumeProfile } from './volumeTools';
import { PriceRange, DateRange, DatePriceRange } from './rangeTools';
import {
  XABCDPattern,
  CypherPattern,
  HeadShoulders,
  ABCDPattern,
  TrianglePattern,
  ThreeDrives,
} from './chartPatterns';
import {
  ElliottImpulse,
  ElliottCorrection,
  ElliottTriangle,
  ElliottDoubleCombo,
  ElliottTripleCombo,
} from './elliottWaves';
import { CyclicLines, TimeCycles, SineLine } from './cycles';
import {
  FibChannel,
  FibSpeedFan,
  TrendFibTime,
  FibCircles,
  FibSpiral,
  FibSpeedArcs,
  FibWedge,
  Pitchfan,
} from './fibonacciTools';
import { GannBox, GannSquareFixed, GannSquare } from './gannTools';
import { InfoLine, ExtendedLine, TrendAngle, CrossLine } from './lineVariants';
import { ParallelChannel, RegressionTrend, FlatTopBottom, DisjointChannel } from './channels';
import { SchiffPitchfork, ModifiedSchiffPitchfork, InsidePitchfork } from './pitchforkVariants';
import { TrendLine } from './TrendLine';
import { Segment } from './Segment';
import { Ray } from './Ray';
import { HorizontalLine } from './HorizontalLine';
import { VerticalLine } from './VerticalLine';
import { HorizontalRay } from './HorizontalRay';
import { PriceLine } from './PriceLine';
import { Arrow } from './Arrow';
import { FibRetracement } from './FibRetracement';
import { FibExtension } from './FibExtension';
import { FibTimezone } from './FibTimezone';
import { Pitchfork } from './Pitchfork';
import { GannFan } from './GannFan';
import { Rectangle } from './Rectangle';
import { Ellipse } from './Ellipse';
import { Triangle } from './Triangle';
import { Polygon } from './Polygon';
import { Circle } from './Circle';
import { Text } from './Text';
import { AnchoredNote } from './AnchoredNote';
import { Note, PriceNote, Pin, Table, Callout, Comment, PriceLabel, Signpost, FlagMark, Image, Post, Idea } from './textNotes';
import { Sticker } from './Sticker';
import { Brush } from './Brush';
import { Measure } from './Measure';
import type { ToolId } from '../types';
import type { Tool } from './types';
export const lineSections: { title: string; ids: ToolId[] }[] = [
  {
    title: 'Lines',
    ids: [
      'TrendLine',
      'Ray',
      'InfoLine',
      'ExtendedLine',
      'TrendAngle',
      'HorizontalLine',
      'HorizontalRay',
      'VerticalLine',
      'CrossLine',
    ],
  },
  {
    title: 'Channels',
    ids: ['ParallelChannel', 'RegressionTrend', 'FlatTopBottom', 'DisjointChannel'],
  },
  {
    title: 'Pitchforks',
    ids: ['Pitchfork', 'SchiffPitchfork', 'ModifiedSchiffPitchfork', 'InsidePitchfork'],
  },
  { title: 'Additional tools', ids: ['Segment', 'PriceLine', 'Arrow'] },
];
export const fibonacciSections: { title: string; ids: ToolId[] }[] = [
  {
    title: 'Fibonacci',
    ids: [
      'FibRetracement',
      'FibExtension',
      'FibChannel',
      'FibTimezone',
      'FibSpeedFan',
      'TrendFibTime',
      'FibCircles',
      'FibSpiral',
      'FibSpeedArcs',
      'FibWedge',
      'Pitchfan',
    ],
  },
  { title: 'Gann', ids: ['GannBox', 'GannSquareFixed', 'GannSquare', 'GannFan'] },
];
export const patternSections: { title: string; ids: ToolId[] }[] = [
  {
    title: 'Chart Patterns',
    ids: [
      'XABCDPattern',
      'CypherPattern',
      'HeadShoulders',
      'ABCDPattern',
      'TrianglePattern',
      'ThreeDrives',
    ],
  },
  {
    title: 'Elliott Waves',
    ids: [
      'ElliottImpulse',
      'ElliottCorrection',
      'ElliottTriangle',
      'ElliottDoubleCombo',
      'ElliottTripleCombo',
    ],
  },
  { title: 'Cycles', ids: ['CyclicLines', 'TimeCycles', 'SineLine'] },
];
export const forecastingSections: { title: string; ids: ToolId[] }[] = [
  {
    title: 'Forecasting',
    ids: [
      'LongPosition',
      'ShortPosition',
      'PositionForecast',
      'BarsPattern',
      'GhostFeed',
      'Sector',
    ],
  },
  { title: 'Volume-based', ids: ['AnchoredVWAP', 'FixedVolumeProfile', 'AnchoredVolumeProfile'] },
  { title: 'Measurers', ids: ['PriceRange', 'DateRange', 'DatePriceRange'] },
];
export const shapeSections: { title: string; ids: ToolId[] }[] = [
  { title: 'Brushes', ids: ['Brush', 'Highlighter'] },
  { title: 'Arrows', ids: ['ArrowMarker', 'Arrow', 'ArrowMarkUp', 'ArrowMarkDown'] },
  {
    title: 'Shapes',
    ids: [
      'Rectangle',
      'RotatedRectangle',
      'PathTool',
      'Circle',
      'Ellipse',
      'Polyline',
      'Triangle',
      'Arc',
      'Curve',
      'DoubleCurve',
    ],
  },
  { title: 'Additional tools', ids: ['Polygon'] },
];
export const tools: Record<ToolId, Tool> = {
  Highlighter,
  ArrowMarker,
  ArrowMarkUp,
  ArrowMarkDown,
  RotatedRectangle,
  PathTool,
  Polyline,
  Arc,
  Curve,
  DoubleCurve,

  LongPosition,
  ShortPosition,
  PositionForecast,
  BarsPattern,
  GhostFeed,
  Sector,
  AnchoredVWAP,
  FixedVolumeProfile,
  AnchoredVolumeProfile,
  PriceRange,
  DateRange,
  DatePriceRange,

  XABCDPattern,
  CypherPattern,
  HeadShoulders,
  ABCDPattern,
  TrianglePattern,
  ThreeDrives,
  ElliottImpulse,
  ElliottCorrection,
  ElliottTriangle,
  ElliottDoubleCombo,
  ElliottTripleCombo,
  CyclicLines,
  TimeCycles,
  SineLine,

  FibChannel,
  FibSpeedFan,
  TrendFibTime,
  FibCircles,
  FibSpiral,
  FibSpeedArcs,
  FibWedge,
  Pitchfan,
  GannBox,
  GannSquareFixed,
  GannSquare,
  InfoLine,
  ExtendedLine,
  TrendAngle,
  CrossLine,
  ParallelChannel,
  RegressionTrend,
  FlatTopBottom,
  DisjointChannel,
  SchiffPitchfork,
  ModifiedSchiffPitchfork,
  InsidePitchfork,
  TrendLine,
  Segment,
  Ray,
  HorizontalLine,
  VerticalLine,
  HorizontalRay,
  PriceLine,
  Arrow,
  FibRetracement,
  FibExtension,
  FibTimezone,
  Pitchfork,
  GannFan,
  Rectangle,
  Ellipse,
  Triangle,
  Polygon,
  Circle,
  Text,
  AnchoredNote,
  Note,
  PriceNote,
  Pin,
  Table,
  Callout,
  Comment,
  PriceLabel,
  Signpost,
  FlagMark,
  Image,
  Post,
  Idea,
  Sticker,
  Brush,
  Measure,
};
