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
export const tools: Record<ToolId, Tool> = {
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
  Sticker,
  Brush,
  Measure,
};
