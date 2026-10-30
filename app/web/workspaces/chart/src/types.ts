export interface Bar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
export const intervals = [
  '1m',
  '3m',
  '5m',
  '15m',
  '30m',
  '1h',
  '2h',
  '4h',
  '8h',
  '1D',
  '1W',
  '1M',
] as const;
export type Interval = (typeof intervals)[number];
export const chartStyles = [
  'Candles',
  'Hollow Candles',
  'Bars',
  'Line',
  'Area',
  'Baseline',
  'Heikin Ashi',
] as const;
export type ChartStyle = (typeof chartStyles)[number];
export type ScaleMode = 'linear' | 'log' | 'percent' | 'indexed';
export interface Point {
  time: number;
  price: number;
}
export interface XY {
  x: number;
  y: number;
}
export const toolIds = [
  'TrendLine',
  'Ray',
  'Segment',
  'HorizontalLine',
  'VerticalLine',
  'HorizontalRay',
  'PriceLine',
  'Arrow',
  'FibRetracement',
  'FibExtension',
  'FibTimezone',
  'Pitchfork',
  'GannFan',
  'Rectangle',
  'Ellipse',
  'Triangle',
  'Polygon',
  'Circle',
  'Text',
  'AnchoredNote',
  'Sticker',
  'Brush',
  'Measure',
] as const;
export type ToolId = (typeof toolIds)[number];
export interface Drawing {
  id: string;
  tool: ToolId;
  points: Point[];
  color: string;
  width: number;
  dash: boolean;
  opacity: number;
  text: string;
  locked: boolean;
  hidden: boolean;
  extendLeft: boolean;
  extendRight: boolean;
}
export const indicatorIds = [
  'SMA',
  'EMA',
  'WMA',
  'BollingerBands',
  'VWAP',
  'RSI',
  'MACD',
  'Stochastic',
  'Volume',
  'ATR',
] as const;
export type IndicatorId = (typeof indicatorIds)[number];
export interface Indicator {
  id: string;
  kind: IndicatorId;
  period: number;
  slow: number;
  signal: number;
  deviation: number;
  color: string;
  width: number;
  opacity: number;
}
export interface Alert {
  id: string;
  symbol: string;
  condition: 'up' | 'down' | 'enter' | 'exit';
  value: number;
  upper: number;
  expires: number;
  once: boolean;
  active: boolean;
  triggers: number;
}
export interface Position {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit';
  quantity: number;
  entry: number;
  sl: number | null;
  tp: number | null;
  status: 'pending' | 'open' | 'closed' | 'canceled';
  exit: number | null;
}
export interface Settings {
  symbol: string;
  interval: Interval;
  style: ChartStyle;
  scale: ScaleMode;
  reverse: boolean;
  auto: boolean;
  theme: 'dark' | 'light';
  timezone: string;
  precision: number;
  countdown: boolean;
  magnet: boolean;
  volume: boolean;
  previousClose: boolean;
  tooltip: boolean;
  gaps: boolean;
  sessions: boolean;
  minimap: boolean;
  title: string;
  range: string;
  paneHeight: number;
}
export interface DocumentState {
  chart: Settings;
  drawings: Record<string, Drawing[]>;
  indicators: Indicator[];
}
export interface Persisted extends DocumentState {
  alerts: Alert[];
  favorites: ToolId[];
  recents: string[];
}
export type Dialog =
  'symbol' | 'indicators' | 'alert' | 'order' | 'settings' | 'drawing' | 'help' | 'delete' | null;
export interface Menu {
  x: number;
  y: number;
  target: 'chart' | 'price' | 'time' | 'drawing';
}
export interface UIState {
  tool: ToolId | 'cursor';
  cursor: 'crosshair' | 'dot' | 'arrow';
  dialog: Dialog;
  panel: 'alerts' | 'positions' | 'favorites' | null;
  selected: string | null;
  lock: boolean;
  hide: boolean;
  menu: Menu | null;
  side: 'buy' | 'sell';
  toast: string;
  saved: string;
  replay: boolean;
  replayPick: boolean;
  replayIndex: number;
  playing: boolean;
  speed: number;
}
export interface Quote {
  price: number;
  previous: number;
  time: number;
}
export const keyFor = (chart: Settings) => chart.symbol + ':' + chart.interval;
export const uid = () => crypto.randomUUID();
