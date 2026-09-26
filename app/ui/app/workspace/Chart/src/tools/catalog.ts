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
export const tools: Record<ToolId, Tool> = {
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
