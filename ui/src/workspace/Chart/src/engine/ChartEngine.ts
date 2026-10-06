import type { Bar, Drawing, Point, Quote, XY } from '../types';
import { keyFor, uid } from '../types';
import type { ChartStore } from '../store/chartStore';
import type { MarketDataAdapter } from '../feed/adapter';
import { bucket, nextBucket, resample } from '../feed/resample';
import { marketOpen } from '../feed/sessions';
import { clamp, priceToY, yToPrice, niceTicks, zoomAt, transformPrice } from './scales';
import { paintSeries, heikinAshi } from './candles';
import { tools } from '../tools/catalog';
import { paint, primitiveHit } from '../tools/geometry';
import type { Projection } from '../tools/types';
import { indicators } from '../indicators/catalog';
import { IndicatorRuntime } from '../indicators/renderers';
import type { Series } from '../indicators/types';
import { triggered } from '../store/alerts';
import { advancePosition } from '../store/positions';
import { replayStep } from '../store/replay';
import { dateLabel, timeLabel } from '../utils/time';
import { formatPrice } from '../utils/format';

export interface Readout {
  bar: Bar;
  last: Bar;
  change: number;
  countdown: string;
  closed: boolean;
  indicatorValues: string[];
}
interface Pane {
  configId: string;
  top: number;
  height: number;
  min: number;
  max: number;
  series: Series[];
  color: string;
}
export class ChartEngine {
  readonly canvases: HTMLCanvasElement[] = [];
  readonly quotes = new Map<string, Quote>();
  bars: Bar[] = [];
  visible: Bar[] = [];
  spacing = 8;
  offset = 0;
  width = 0;
  height = 0;
  plotWidth = 0;
  plotHeight = 0;
  mainHeight = 0;
  min = 1;
  max = 2;
  private manual: [number, number] | null = null;
  private resize: ResizeObserver;
  private frame = 0;
  private dirty = 7;
  private disposed = false;
  private dpr = 1;
  private abort?: AbortController;
  private unsubscribe: () => void;
  private stopFeed?: () => void;
  private stops = new Map<string, () => void>();
  private timer: ReturnType<typeof setInterval>;
  private lastSignature = '';
  private indicatorKey = '';
  private indicatorCache: Series[][] = [];
  private indicatorRuntimes = new Map<string, { signature: string; runtime: IndicatorRuntime }>();
  private panes: Pane[] = [];
  private paneRanges = new Map<string, [number, number]>();
  private scalePane: Pane | null = null;
  private pointer: XY | null = null;
  private down: XY | null = null;
  private initialOffset = 0;
  private initialRange: [number, number] = [0, 1];
  private gesture: 'pan' | 'price' | 'time' | 'draw' | 'move' | 'resize' | 'pane' | null = null;
  private preview: Drawing | null = null;
  private original: Drawing | null = null;
  private handle = -1;
  private moving = false;
  private touches = new Map<number, XY>();
  private pinch = 0;
  private points: Point[] = [];
  private loading = false;
  private barsVersion = 0;
  private tickAt = 0;
  private latestReplay = 0;
  private liveViewport: { spacing: number; offset: number } | null = null;
  private initialSpacing = 8;
  private ha: Bar[] = [];
  private haVersion = -1;
  private clickClose: string | null = null;
  private positionChips: { id: string; y: number }[] = [];
  private removers: (() => void)[] = [];
  onReadout?: (value: Readout) => void;
  onLoading?: (loading: boolean) => void;
  constructor(
    readonly host: HTMLDivElement,
    readonly store: ChartStore,
    readonly feed: MarketDataAdapter,
    readonly now: () => number = Date.now,
  ) {
    for (let i = 0; i < 3; i++) {
      const canvas = document.createElement('canvas');
      canvas.setAttribute('aria-hidden', 'true');
      Object.assign(canvas.style, {
        position: 'absolute',
        inset: '0',
        width: '100%',
        height: '100%',
        pointerEvents: i === 2 ? 'auto' : 'none',
      });
      host.append(canvas);
      this.canvases.push(canvas);
    }
    const input = this.canvases[2];
    input.setAttribute('data-testid', 'chart-input');
    input.style.touchAction = 'none';
    const listen = <K extends keyof HTMLElementEventMap>(
      event: K,
      fn: (e: HTMLElementEventMap[K]) => void,
      options?: AddEventListenerOptions,
    ) => {
      input.addEventListener(event, fn, options);
      this.removers.push(() => input.removeEventListener(event, fn));
    };
    listen('pointerdown', (e) => this.pointerDown(e));
    listen('pointermove', (e) => this.pointerMove(e));
    listen('pointerup', (e) => this.pointerUp(e));
    listen('pointercancel', () => this.cancel());
    listen('pointerleave', () => {
      if (!this.down) {
        this.pointer = null;
        this.invalidate(4);
      }
    });
    listen(
      'wheel',
      (e) => {
        e.preventDefault();
        const p = this.local(e);
        this.zoom(Math.exp(-e.deltaY * 0.0015), p.x);
      },
      { passive: false },
    );
    listen('dblclick', () => {
      if (this.store.getState().ui.tool === 'Polygon') this.finish();
      else this.reset();
    });
    listen('contextmenu', (e) => {
      e.preventDefault();
      const p = this.local(e),
        hit = this.hit(p);
      if (hit) this.store.getState().setUI({ selected: hit.id });
      this.store.getState().setUI({
        menu: {
          x: p.x,
          y: p.y,
          target: hit
            ? 'drawing'
            : p.x > this.plotWidth
              ? 'price'
              : p.y > this.plotHeight
                ? 'time'
                : 'chart',
        },
      });
    });
    this.resize = new ResizeObserver(() => this.size());
    this.resize.observe(host);
    this.size();
    this.unsubscribe = store.subscribe((s, previous) => {
      const signature = s.chart.symbol + ':' + s.chart.interval + ':' + s.chart.range;
      if (signature !== this.lastSignature) {
        this.lastSignature = signature;
        void this.load();
      }
      if (s.chart.auto && !previous.chart.auto) this.manual = null;
      if (!s.chart.auto && previous.chart.auto && !this.manual) this.manual = [this.min, this.max];
      if (s.chart.scale !== previous.chart.scale || s.chart.reverse !== previous.chart.reverse)
        this.manual = null;
      if (s.chart.gaps !== previous.chart.gaps) this.reset();
      if (s.chart.symbol !== previous.chart.symbol) this.watchSymbols();
      if (s.ui.replayIndex !== previous.ui.replayIndex || s.ui.replay !== previous.ui.replay) {
        if (s.ui.replay && !previous.ui.replay)
          this.liveViewport = { spacing: this.spacing, offset: this.offset };
        this.updateVisible();
        if (!s.ui.replay && this.liveViewport) {
          this.spacing = this.liveViewport.spacing;
          this.offset = this.liveViewport.offset;
          this.liveViewport = null;
        } else this.scrollLast();
        this.haVersion = -1;
      }
      if (s.ui.tool !== previous.ui.tool) {
        this.points = [];
        this.preview = null;
      }
      if (s.alerts !== previous.alerts || s.positions !== previous.positions) this.watchSymbols();
      this.invalidate(7);
    });
    this.lastSignature =
      store.getState().chart.symbol +
      ':' +
      store.getState().chart.interval +
      ':' +
      store.getState().chart.range;
    this.timer = setInterval(() => {
      const s = store.getState();
      if (s.alerts.some((a) => a.active && a.expires <= this.now()))
        s.setAlerts(s.alerts.map((a) => (a.expires <= this.now() ? { ...a, active: false } : a)));
      if (s.ui.replay && s.ui.playing && this.now() - this.latestReplay >= 1000 / s.ui.speed) {
        this.latestReplay = this.now();
        this.step(1);
      }
      this.invalidate(4);
    }, 100);
    void this.load();
    this.watchSymbols();
  }
  private local(e: { clientX: number; clientY: number }): XY {
    const r = this.host.getBoundingClientRect();
    return {
      x: ((e.clientX - r.left) * this.width) / r.width,
      y: ((e.clientY - r.top) * this.height) / r.height,
    };
  }
  private size() {
    this.width = this.host.clientWidth;
    this.height = this.host.clientHeight;
    this.plotWidth = Math.max(1, this.width - 64);
    this.plotHeight = Math.max(1, this.height - 28);
    this.dpr = window.devicePixelRatio || 1;
    for (const c of this.canvases) {
      c.width = Math.round(this.width * this.dpr);
      c.height = Math.round(this.height * this.dpr);
    }
    if (!this.offset) this.reset();
    this.invalidate(7);
  }
  private invalidate(flags: number) {
    this.dirty |= flags;
    if (!this.frame && !this.disposed)
      this.frame = requestAnimationFrame(() => {
        this.frame = 0;
        this.render();
      });
  }
  private rangeStart(): number {
    const now = this.now(),
      range = this.store.getState().chart.range;
    const days: Record<string, number> = {
      '1D': 1,
      '5D': 5,
      '1M': 30,
      '3M': 90,
      '6M': 180,
      '1Y': 365,
      '5Y': 1826,
      All: 1826,
    };
    return range === 'YTD'
      ? Date.UTC(new Date(now).getUTCFullYear(), 0, 1)
      : now - (days[range] ?? 1) * 86400000;
  }
  async load() {
    this.abort?.abort();
    this.stopFeed?.();
    this.abort = new AbortController();
    const controller = this.abort,
      s = this.store.getState();
    this.loading = true;
    this.onLoading?.(true);
    this.host.dataset.loading = 'true';
    try {
      const now = this.now();
      const base = await this.feed.history(
        s.chart.symbol,
        Math.min(now - 32 * 86400000, this.rangeStart()),
        now,
        controller.signal,
      );
      if (controller.signal.aborted || this.disposed) return;
      this.bars = resample(base, s.chart.interval);
      this.barsVersion++;
      this.updateVisible();
      this.reset();
      this.stopFeed = this.feed.subscribe(s.chart.symbol, '1m', (minute) => {
        if (this.disposed || controller.signal.aborted) return;
        this.quote(s.chart.symbol, minute.close, minute.time);
        const time = bucket(minute.time, s.chart.interval),
          last = this.bars.at(-1);
        // Only the current interval is rebuilt; older historical buckets stay immutable.
        const start = time;
        let index = base.length - 1;
        while (index >= 0 && base[index].time > minute.time) index--;
        if (base[index]?.time !== minute.time) index = -1;
        if (index >= 0) base[index] = { ...minute };
        else if (!base.length || minute.time > base.at(-1)!.time) base.push({ ...minute });
        else return;
        let begin = base.length - 1;
        while (begin > 0 && base[begin - 1].time >= start) begin--;
        const aggregate = resample(base.slice(begin), s.chart.interval).at(-1);
        if (!aggregate) return;
        if (last?.time === time) this.bars[this.bars.length - 1] = aggregate;
        else if (!last || time > last.time) {
          const following = this.offset + this.bars.length * this.spacing < this.plotWidth + 100;
          this.bars.push(aggregate);
          if (following) this.offset -= this.spacing;
        }
        this.barsVersion++;
        if (!this.store.getState().ui.replay) this.updateVisible();
        this.invalidate(7);
      });
    } catch (error) {
      if (!controller.signal.aborted)
        this.store
          .getState()
          .setUI({ toast: error instanceof Error ? error.message : 'History unavailable' });
    } finally {
      if (!controller.signal.aborted) {
        this.loading = false;
        this.host.dataset.loading = 'false';
        this.onLoading?.(false);
        this.invalidate(7);
      }
    }
  }
  async quoteFor(symbol: string): Promise<number> {
    let value: number | undefined;
    const stop = this.feed.subscribe(symbol, '1m', (bar) => {
      value = bar.close;
    });
    stop();
    if (value !== undefined) return value;
    const history = await this.feed.history(
      symbol,
      this.now() - 7 * 86400000,
      this.now(),
      this.abort?.signal,
    );
    const last = history.at(-1);
    if (!last) throw new Error('No quote is available for this simulated session.');
    return last.close;
  }
  private watchSymbols() {
    const s = this.store.getState(),
      wanted = new Set([
        ...s.alerts.filter((a) => a.active).map((a) => a.symbol),
        ...s.positions
          .filter((p) => p.status === 'open' || p.status === 'pending')
          .map((p) => p.symbol),
      ]);
    wanted.delete(s.chart.symbol);
    for (const [symbol, stop] of this.stops)
      if (!wanted.has(symbol)) {
        stop();
        this.stops.delete(symbol);
      }
    for (const symbol of wanted)
      if (!this.stops.has(symbol)) {
        this.stops.set(symbol, () => {});
        const stop = this.feed.subscribe(symbol, '1m', (b) => this.quote(symbol, b.close, b.time));
        this.stops.set(symbol, stop);
      }
  }
  private quote(symbol: string, price: number, time: number) {
    const previous = this.quotes.get(symbol)?.price ?? price;
    this.quotes.set(symbol, { price, previous, time });
    if (symbol === this.store.getState().chart.symbol && price !== previous)
      this.tickAt = this.now();
    const s = this.store.getState();
    if (s.ui.replay) return;
    const alerts = s.alerts.map((a) => {
      if (a.symbol !== symbol) return a;
      if (triggered(a, previous, price, this.now())) {
        s.setUI({
          toast: 'Alert · ' + symbol + ' crossed ' + formatPrice(a.value, s.chart.precision),
        });
        return { ...a, triggers: a.triggers + 1, active: !a.once };
      }
      return a.active && this.now() >= a.expires ? { ...a, active: false } : a;
    });
    if (alerts.some((a, i) => a !== s.alerts[i])) s.setAlerts(alerts);
    const positions = s.positions.map((p) => (p.symbol === symbol ? advancePosition(p, price) : p));
    if (positions.some((p, i) => p !== s.positions[i])) s.setPositions(positions);
  }
  private updateVisible() {
    const s = this.store.getState();
    this.visible = s.ui.replay ? this.bars.slice(0, s.ui.replayIndex + 1) : this.bars;
    this.indicatorKey = '';
  }
  reset() {
    this.manual = null;
    this.paneRanges.clear();
    const state = this.store.getState();
    if (!state.chart.auto) this.store.setState({ chart: { ...state.chart, auto: true } });
    const start = this.rangeStart();
    const first = Math.max(
      0,
      this.visible.findIndex((b) => b.time >= start),
    );
    const count = Math.max(30, (this.x(this.visible.length - 1) - this.x(first)) / this.spacing);
    this.spacing = clamp((this.plotWidth - 80) / count, 0.2, 50);
    this.scrollLast();
    this.invalidate(7);
  }
  scrollLast() {
    this.offset += this.plotWidth - 80 - this.x(this.visible.length - 1);
    this.invalidate(7);
  }
  zoom(factor: number, x = this.plotWidth / 2) {
    const z = zoomAt(x, this.spacing, this.offset, factor);
    this.spacing = z.spacing;
    this.offset = z.offset;
    this.invalidate(7);
  }
  setWindow(fraction: number) {
    const index = Math.round((this.visible.length - 1) * clamp(fraction, 0, 1));
    this.offset += this.plotWidth / 2 - this.x(index);
    this.invalidate(7);
  }
  addPriceLine(y: number) {
    const drawing = this.makeDrawing([
      { time: this.visible.at(-1)?.time ?? this.now(), price: this.price(y) },
    ]);
    drawing.tool = 'PriceLine';
    this.store.getState().setDrawings([...this.drawings(), drawing]);
    this.store.getState().setUI({ selected: drawing.id });
  }
  step(delta: number) {
    const s = this.store.getState(),
      index = replayStep(s.ui.replayIndex, delta, this.bars.length);
    s.setUI({ replayIndex: index, playing: index === this.bars.length - 1 ? false : s.ui.playing });
  }
  cancel() {
    this.points = [];
    this.preview = null;
    this.down = null;
    this.gesture = null;
    this.original = null;
    this.touches.clear();
    this.store.getState().setUI({ tool: 'cursor', menu: null });
    this.invalidate(6);
  }
  private x(i: number): number {
    if (this.store.getState().chart.gaps) return i * this.spacing + this.offset;
    const first = this.visible[0]?.time ?? 0;
    const duration = this.barMs();
    return (
      (((this.visible[i]?.time ?? first + i * duration) - first) / duration) * this.spacing +
      this.offset
    );
  }
  private barMs(): number {
    const i = this.store.getState().chart.interval;
    return (
      nextBucket(this.visible[0]?.time ?? this.now(), i) -
      bucket(this.visible[0]?.time ?? this.now(), i)
    );
  }
  private indexAt(x: number): number {
    if (this.store.getState().chart.gaps) return (x - this.offset) / this.spacing;
    const time = (this.visible[0]?.time ?? 0) + ((x - this.offset) / this.spacing) * this.barMs();
    return this.indexTime(time);
  }
  private indexTime(time: number): number {
    let lo = 0,
      hi = this.visible.length - 1;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (this.visible[mid].time < time) lo = mid + 1;
      else hi = mid;
    }
    if (!this.visible.length) return 0;
    if (time > this.visible.at(-1)!.time)
      return this.visible.length - 1 + (time - this.visible.at(-1)!.time) / this.barMs();
    if (time < this.visible[0].time) return (time - this.visible[0].time) / this.barMs();
    if (lo > 0 && this.visible[lo].time !== time)
      return (
        lo -
        1 +
        (time - this.visible[lo - 1].time) / (this.visible[lo].time - this.visible[lo - 1].time)
      );
    return lo;
  }
  private y(price: number) {
    const c = this.store.getState().chart;
    return (
      12 +
      priceToY(price, this.min, this.max, this.mainHeight - 24, c.scale, c.reverse, this.anchor())
    );
  }
  private anchor() {
    return (
      this.visible[Math.max(0, Math.floor(this.indexAt(0)))]?.close ?? this.visible[0]?.close ?? 1
    );
  }
  private price(y: number) {
    const c = this.store.getState().chart;
    return yToPrice(
      y - 12,
      this.min,
      this.max,
      this.mainHeight - 24,
      c.scale,
      c.reverse,
      this.anchor(),
    );
  }
  private point(p: XY): Point {
    const i = this.indexAt(p.x),
      near = Math.round(i),
      bar = this.visible[clamp(near, 0, this.visible.length - 1)],
      c = this.store.getState().chart;
    let price = this.price(p.y);
    if (c.magnet && bar)
      price = [bar.open, bar.high, bar.low, bar.close].reduce((a, b) =>
        Math.abs(this.y(a) - p.y) < Math.abs(this.y(b) - p.y) ? a : b,
      );
    const index = c.magnet ? near : i,
      low = Math.floor(index),
      fraction = index - low;
    const a = this.visible[low]?.time ?? (this.visible[0]?.time ?? 0) + low * this.barMs(),
      b = this.visible[low + 1]?.time ?? a + this.barMs();
    return { time: a + (b - a) * fraction, price };
  }
  private projection(): Projection {
    return {
      point: (p) => ({
        x: this.store.getState().chart.gaps
          ? this.indexTime(p.time) * this.spacing + this.offset
          : ((p.time - (this.visible[0]?.time ?? 0)) / this.barMs()) * this.spacing + this.offset,
        y: this.y(p.price),
      }),
      width: this.plotWidth,
      height: this.mainHeight,
      barMs: this.barMs(),
      index: (time) => this.indexTime(time),
    };
  }
  private drawings() {
    const s = this.store.getState();
    return s.drawings[keyFor(s.chart)] ?? [];
  }
  private hit(p: XY): Drawing | null {
    if (this.store.getState().ui.hide) return null;
    const projection = this.projection();
    return (
      [...this.drawings()]
        .reverse()
        .find(
          (d) =>
            !d.hidden && tools[d.tool].build(d, projection).some((shape) => primitiveHit(shape, p)),
        ) ?? null
    );
  }
  private pointerDown(e: PointerEvent) {
    if (e.button !== 0) return;
    const p = this.local(e);
    this.touches.set(e.pointerId, p);
    this.canvases[2].setPointerCapture(e.pointerId);
    if (this.touches.size === 2) {
      const [a, b] = [...this.touches.values()];
      this.pinch = Math.hypot(a.x - b.x, a.y - b.y);
      this.gesture = null;
      return;
    }
    this.store.getState().setUI({ menu: null });
    this.down = p;
    this.moving = false;
    this.initialOffset = this.offset;
    this.initialSpacing = this.spacing;
    this.initialRange = [this.min, this.max];
    const s = this.store.getState();
    if (s.ui.replayPick) {
      s.setUI({
        replay: true,
        replayPick: false,
        replayIndex: clamp(Math.round(this.indexAt(p.x)), 0, this.bars.length - 1),
      });
      this.down = null;
      return;
    }
    this.clickClose =
      p.x > this.plotWidth
        ? (this.positionChips.find((v) => Math.abs(v.y - p.y) < 10)?.id ?? null)
        : null;
    if (this.clickClose && s.ui.replay) {
      this.clickClose = null;
      this.down = null;
      return;
    }
    if (this.clickClose) return;
    if (Math.abs(p.y - this.mainHeight) < 5 && this.panes.length) {
      this.gesture = 'pane';
      return;
    }
    if (p.x > this.plotWidth) {
      this.scalePane =
        this.panes.find((pane) => p.y >= pane.top && p.y < pane.top + pane.height) ?? null;
      if (this.scalePane) this.initialRange = [this.scalePane.min, this.scalePane.max];
      this.gesture = 'price';
      return;
    }
    if (p.y > this.plotHeight) {
      this.gesture = 'time';
      return;
    }
    if (s.ui.tool !== 'cursor') {
      this.gesture = 'draw';
      const point = this.point(p);
      if (s.ui.tool === 'Brush') this.points = [point];
      else this.points.push(point);
      this.preview = this.makeDrawing(this.points);
      if (tools[s.ui.tool].anchors === 1) this.finish();
      return;
    }
    const selected = this.drawings().find((d) => d.id === s.ui.selected);
    this.handle =
      selected && !selected.locked && !selected.hidden && !s.ui.lock && !s.ui.hide
        ? selected.points.findIndex((a) => {
            const b = this.projection().point(a);
            return Math.hypot(b.x - p.x, b.y - p.y) < 9;
          })
        : -1;
    const hit = this.handle >= 0 ? selected : this.hit(p);
    if (hit) {
      s.setUI({ selected: hit.id });
      if (!hit.locked && !s.ui.lock) {
        this.original = structuredClone(hit);
        this.preview = structuredClone(hit);
        this.gesture = this.handle >= 0 ? 'resize' : 'move';
      }
      return;
    }
    s.setUI({ selected: null });
    this.gesture = 'pan';
  }
  private pointerMove(e: PointerEvent) {
    const p = this.local(e);
    this.pointer = p;
    if (this.touches.has(e.pointerId)) this.touches.set(e.pointerId, p);
    if (this.touches.size === 2) {
      const [a, b] = [...this.touches.values()],
        distance = Math.hypot(a.x - b.x, a.y - b.y);
      if (this.pinch) this.zoom(distance / this.pinch, (a.x + b.x) / 2);
      this.pinch = distance;
      return;
    }
    const s = this.store.getState();
    if (!this.down) {
      if (this.points.length && s.ui.tool !== 'cursor')
        this.preview = this.makeDrawing([...this.points, this.point(p)]);
      this.invalidate(4);
      return;
    }
    const dx = p.x - this.down.x,
      dy = p.y - this.down.y;
    this.moving ||= Math.hypot(dx, dy) > 3;
    if (this.gesture === 'pan' || this.gesture === 'time') {
      if (e.shiftKey && this.gesture === 'time') {
        const next = zoomAt(
          this.down.x,
          this.initialSpacing,
          this.initialOffset,
          Math.exp(dx * 0.002),
        );
        this.spacing = next.spacing;
        this.offset = next.offset;
      } else this.offset = this.initialOffset + dx;
      this.invalidate(7);
    }
    if (this.gesture === 'price') {
      const span = this.initialRange[1] - this.initialRange[0],
        center = (this.initialRange[1] + this.initialRange[0]) / 2;
      const factor = Math.exp(dy * (e.shiftKey ? 0.02 : 0.005));
      if (this.scalePane)
        this.paneRanges.set(this.scalePane.configId, [
          center - (span * factor) / 2,
          center + (span * factor) / 2,
        ]);
      else {
        this.manual = [
          Math.max(0.0000001, center - (span * factor) / 2),
          center + (span * factor) / 2,
        ];
        this.store.setState({ chart: { ...s.chart, auto: false } });
      }
      this.invalidate(7);
    }
    if (this.gesture === 'pane') {
      const h = clamp(this.plotHeight - p.y, 40, 300);
      this.store.setState({ chart: { ...s.chart, paneHeight: h } });
      this.invalidate(7);
    }
    if (this.gesture === 'draw' && s.ui.tool !== 'cursor') {
      if (s.ui.tool === 'Brush') {
        this.points.push(this.point(p));
        this.preview = this.makeDrawing(this.points);
      } else this.preview = this.makeDrawing([...this.points, this.point(p)]);
      this.invalidate(4);
    }
    if ((this.gesture === 'move' || this.gesture === 'resize') && this.original) {
      const a = this.point(this.down),
        b = this.point(p);
      this.preview = {
        ...this.original,
        points: this.original.points.map((v, i) =>
          this.gesture === 'resize'
            ? i === this.handle
              ? b
              : v
            : { time: v.time + b.time - a.time, price: v.price + b.price - a.price },
        ),
      };
      this.invalidate(6);
    }
  }
  private pointerUp(e: PointerEvent) {
    this.touches.delete(e.pointerId);
    if (this.touches.size) {
      this.pinch = 0;
      this.down = null;
      return;
    }
    const s = this.store.getState();
    if (this.clickClose) {
      s.setPositions(
        s.positions.map((p) =>
          p.id === this.clickClose
            ? {
                ...p,
                status: p.status === 'pending' ? 'canceled' : 'closed',
                exit: this.quotes.get(p.symbol)?.price ?? p.entry,
              }
            : p,
        ),
      );
      this.clickClose = null;
    }
    if (this.gesture === 'draw' && s.ui.tool !== 'cursor') {
      const tool = tools[s.ui.tool];
      if (s.ui.tool === 'Brush') this.finish();
      else if (tool.anchors === 2 && this.moving) {
        this.points.push(this.point(this.local(e)));
        this.finish();
      } else if (tool.anchors > 0 && this.points.length >= tool.anchors) this.finish();
    }
    if ((this.gesture === 'move' || this.gesture === 'resize') && this.preview && this.moving) {
      const next = this.preview;
      s.setDrawings(this.drawings().map((d) => (d.id === next.id ? next : d)));
    }
    if (this.gesture !== 'draw') this.preview = null;
    this.down = null;
    this.gesture = null;
    this.original = null;
    this.invalidate(7);
  }
  private makeDrawing(points: Point[]): Drawing {
    const tool = this.store.getState().ui.tool;
    return {
      id: uid(),
      tool: tool === 'cursor' ? 'TrendLine' : tool,
      points: points.map((p) => ({ ...p })),
      color: '#2962ff',
      width: 2,
      dash: false,
      opacity: 1,
      text: '',
      locked: false,
      hidden: false,
      extendLeft: false,
      extendRight: false,
    };
  }
  finish() {
    if (!this.preview || !this.points.length) return;
    const s = this.store.getState(),
      tool = tools[this.preview.tool];
    if (tool.anchors && this.points.length < tool.anchors) return;
    if (!tool.anchors && this.points.length < (this.preview.tool === 'Polygon' ? 3 : 2)) return;
    const drawing = { ...this.preview, points: this.points.map((p) => ({ ...p })) };
    s.setDrawings([...this.drawings(), drawing]);
    this.points = [];
    this.preview = null;
    s.setUI({
      tool: 'cursor',
      selected: drawing.id,
      ...(['Text', 'AnchoredNote', 'Sticker'].includes(drawing.tool)
        ? { dialog: 'drawing' as const }
        : {}),
    });
    this.invalidate(7);
  }
  private context(layer: number) {
    const ctx = this.canvases[layer].getContext('2d')!;
    ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    ctx.clearRect(0, 0, this.width, this.height);
    ctx.font = '11px -apple-system, Trebuchet MS, sans-serif';
    return ctx;
  }
  private render() {
    if (this.disposed || !this.width || !this.height) return;
    const started = performance.now(),
      flags = this.dirty;
    this.dirty = 0;
    const s = this.store.getState(),
      c = s.chart,
      bars = this.visible;
    const dark = c.theme === 'dark',
      bg = dark ? '#131722' : '#ffffff',
      fg = dark ? '#d1d4dc' : '#131722',
      muted = '#787b86',
      grid = dark ? 'rgba(42,46,57,0.6)' : '#e6e8ed';
    const start = clamp(Math.floor(this.indexAt(0)) - 1, 0, Math.max(0, bars.length - 1)),
      end = clamp(Math.ceil(this.indexAt(this.plotWidth)) + 1, 0, Math.max(0, bars.length - 1));
    const paneConfigs = s.indicators.filter((i) => indicators[i.kind].pane);
    const paneCount = paneConfigs.length + (c.volume ? 1 : 0);
    const paneHeight = Math.min(
      c.paneHeight === 100 && paneConfigs.length === 0 ? this.plotHeight * 0.15 : c.paneHeight,
      Math.max(12, (this.plotHeight - 120) / Math.max(1, paneCount)),
    );
    this.mainHeight = Math.max(100, this.plotHeight - paneCount * paneHeight);
    if (flags & 1) {
      const ctx = this.context(0);
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, this.width, this.height);
      if (!bars.length) {
        ctx.fillStyle = muted;
        ctx.fillText(
          this.loading ? 'Loading deterministic market history…' : 'No bars in this session',
          32,
          120,
        );
        return;
      }
      let low = Infinity,
        high = -Infinity;
      for (let i = start; i <= end; i++) {
        low = Math.min(low, bars[i].low);
        high = Math.max(high, bars[i].high);
      }
      const pad = Math.max((high - low) * 0.1, high * 0.0001);
      [this.min, this.max] = this.manual ?? [Math.max(0.0000001, low - pad), high + pad];
      ctx.strokeStyle = grid;
      ctx.lineWidth = 1;
      ctx.fillStyle = muted;
      for (const tick of niceTicks(
        this.min,
        this.max,
        Math.max(3, Math.floor(this.mainHeight / 65)),
      )) {
        const y = Math.round(this.y(tick)) + 0.5;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(this.plotWidth, y);
        ctx.stroke();
        const value = transformPrice(tick, c.scale, this.anchor());
        ctx.fillText(
          c.scale === 'log'
            ? formatPrice(tick, c.precision)
            : formatPrice(value, c.scale === 'percent' ? 2 : c.precision) +
                (c.scale === 'percent' ? '%' : ''),
          this.plotWidth + 6,
          y + 4,
        );
      }
      const step = Math.max(1, Math.ceil(85 / this.spacing));
      for (let i = Math.ceil(start / step) * step; i <= end; i += step) {
        const bar = bars[i];
        if (!bar) continue;
        const x = Math.round(this.x(i)) + 0.5;
        if (x < 0 || x > this.plotWidth) continue;
        ctx.strokeStyle = grid;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, this.plotHeight);
        ctx.stroke();
        ctx.fillStyle = muted;
        const boundary =
          i > 0 &&
          Math.floor(bar.time / 86400000) !==
            Math.floor(bars[Math.max(0, i - step)].time / 86400000);
        ctx.font = (boundary ? 'bold ' : '') + '11px Trebuchet MS';
        ctx.fillText(
          step * this.barMs() > 86400000 || boundary
            ? new Date(bar.time).toISOString().slice(5, 10)
            : timeLabel(bar.time, c.timezone),
          x - 16,
          this.plotHeight + 18,
        );
      }
      ctx.font = '11px Trebuchet MS';
      if (c.sessions) {
        ctx.setLineDash([2, 4]);
        for (let i = Math.max(1, start); i <= end; i++)
          if (Math.floor(bars[i].time / 86400000) !== Math.floor(bars[i - 1].time / 86400000)) {
            ctx.beginPath();
            ctx.moveTo(this.x(i), 0);
            ctx.lineTo(this.x(i), this.plotHeight);
            ctx.stroke();
          }
        ctx.setLineDash([]);
      }
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, 0, this.plotWidth, this.mainHeight);
      ctx.clip();
      if (c.style === 'Heikin Ashi' && this.haVersion !== this.barsVersion) {
        this.ha = heikinAshi(bars);
        this.haVersion = this.barsVersion;
      }
      paintSeries(
        ctx,
        c.style === 'Heikin Ashi' ? this.ha : bars,
        start,
        end,
        (i) => this.x(i),
        (p) => this.y(p),
        this.spacing,
        c.style,
        this.mainHeight,
      );
      const ik = String(this.barsVersion) + ':' + bars.length + JSON.stringify(s.indicators);
      if (this.indicatorKey !== ik) {
        this.indicatorKey = ik;
        const active = new Set(s.indicators.map((i) => i.id));
        for (const id of this.indicatorRuntimes.keys())
          if (!active.has(id)) this.indicatorRuntimes.delete(id);
        this.indicatorCache = s.indicators.map((i) => {
          const signature = [i.kind, i.period, i.slow, i.signal, i.deviation].join(':');
          let entry = this.indicatorRuntimes.get(i.id);
          if (!entry || entry.signature !== signature) {
            entry = { signature, runtime: new IndicatorRuntime(i) };
            this.indicatorRuntimes.set(i.id, entry);
          }
          return entry.runtime.update(bars);
        });
      }
      this.panes = [];
      let paneTop = this.mainHeight;
      s.indicators.forEach((config, index) => {
        const series = this.indicatorCache[index] ?? [];
        if (indicators[config.kind].pane) {
          const vals = series.flatMap((line) =>
            line.slice(start, end + 1).filter((v): v is number => v !== null),
          );
          const min =
              config.kind === 'RSI' || config.kind === 'Stochastic' ? 0 : Math.min(0, ...vals),
            max =
              config.kind === 'RSI' || config.kind === 'Stochastic' ? 100 : Math.max(1, ...vals);
          this.panes.push({
            configId: config.id,
            top: paneTop,
            height: paneHeight,
            min,
            max,
            series,
            color: config.color,
          });
          paneTop += paneHeight;
        } else
          this.paintIndicator(
            ctx,
            series,
            start,
            end,
            (p) => this.y(p),
            config.color,
            config.width,
            config.opacity,
          );
      });
      ctx.restore();
      if (c.volume) {
        this.panes.push({
          configId: 'volume',
          top: paneTop,
          height: paneHeight,
          min: 0,
          max: Math.max(1, ...bars.slice(start, end + 1).map((b) => b.volume)),
          series: [bars.map((b) => b.volume)],
          color: '#787b86',
        });
      }
      for (const pane of this.panes) {
        const manual = this.paneRanges.get(pane.configId);
        if (manual) [pane.min, pane.max] = manual;
        ctx.strokeStyle = grid;
        ctx.beginPath();
        ctx.moveTo(0, pane.top + 0.5);
        ctx.lineTo(this.width, pane.top + 0.5);
        ctx.stroke();
        const y = (v: number) =>
          pane.top +
          pane.height -
          10 -
          ((v - pane.min) / (pane.max - pane.min || 1)) * (pane.height - 25);
        const config = s.indicators.find((i) => i.id === pane.configId);
        ctx.fillStyle = muted;
        ctx.fillText(config?.kind ?? 'Volume', 12, pane.top + 16);
        for (const tick of niceTicks(pane.min, pane.max, 3)) {
          ctx.fillText(formatPrice(tick, 1), this.plotWidth + 5, y(tick) + 4);
        }
        ctx.save();
        ctx.beginPath();
        ctx.rect(0, pane.top, this.plotWidth, pane.height);
        ctx.clip();
        if (pane.configId === 'volume' || config?.kind === 'Volume') {
          ctx.globalAlpha = config?.opacity ?? 0.5;
          for (let i = start; i <= end; i++) {
            ctx.fillStyle =
              config?.color ?? (bars[i].close >= bars[i].open ? '#089981' : '#f23645');
            ctx.fillRect(
              this.x(i) - this.spacing * 0.35,
              y(bars[i].volume),
              Math.max(1, this.spacing * 0.7 * (config?.width ?? 1)),
              pane.top + pane.height - y(bars[i].volume),
            );
          }
          ctx.globalAlpha = 1;
        } else
          this.paintIndicator(
            ctx,
            pane.series,
            start,
            end,
            y,
            pane.color,
            config?.width ?? 1,
            config?.opacity ?? 1,
          );
        ctx.restore();
        const lastValue = pane.series[0]?.at(-1);
        if (lastValue !== null && lastValue !== undefined) {
          const chipY = clamp(y(lastValue), pane.top + 10, pane.top + pane.height - 10);
          ctx.fillStyle = pane.color;
          ctx.fillRect(this.plotWidth, chipY - 9, 64, 18);
          ctx.fillStyle = '#fff';
          ctx.fillText(formatPrice(lastValue, 2), this.plotWidth + 4, chipY + 4);
        }
      }
      ctx.fillStyle = muted;
      ctx.font = 'bold 14px Trebuchet MS';
      ctx.fillText('TradingView-clone', 14, this.mainHeight - 18);
      ctx.strokeStyle = grid;
      ctx.beginPath();
      ctx.moveTo(this.plotWidth + 0.5, 0);
      ctx.lineTo(this.plotWidth + 0.5, this.height);
      ctx.moveTo(0, this.plotHeight + 0.5);
      ctx.lineTo(this.width, this.plotHeight + 0.5);
      ctx.stroke();
    }
    if (flags & 3) {
      const ctx = this.context(1);
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, 0, this.plotWidth, this.mainHeight);
      ctx.clip();
      if (!s.ui.hide)
        for (const drawing of this.drawings()) {
          if (drawing.hidden || this.preview?.id === drawing.id) continue;
          this.paintDrawing(ctx, drawing, drawing.id === s.ui.selected);
        }
      ctx.restore();
    }
    const ctx = this.context(2);
    const last = bars.at(-1);
    if (!last) return;
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, this.plotWidth, this.mainHeight);
    ctx.clip();
    if (this.preview) this.paintDrawing(ctx, this.preview, true);
    ctx.restore();
    const chip = (price: number, text: string, color: string, dash = [3, 3]) => {
      const y = this.y(price);
      if (y < 0 || y > this.mainHeight) return;
      ctx.strokeStyle = color;
      ctx.setLineDash(dash);
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(this.plotWidth, y);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = color;
      ctx.fillRect(this.plotWidth, y - 10, 64, 20);
      ctx.fillStyle = '#fff';
      ctx.fillText(text, this.plotWidth + 4, y + 4);
    };
    const quote = this.quotes.get(c.symbol);
    const direction = quote ? quote.price >= quote.previous : last.close >= last.open;
    const liveColor = direction ? '#089981' : '#f23645';
    chip(last.close, formatPrice(last.close, c.precision), liveColor);
    if (!s.ui.replay && this.now() - this.tickAt < 180) {
      ctx.save();
      ctx.globalAlpha = 0.18 * (1 - (this.now() - this.tickAt) / 180);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(this.plotWidth, this.y(last.close) - 10, 64, 20);
      ctx.fillStyle = liveColor;
      const lastX = this.x(bars.length - 1);
      if (lastX >= 0 && lastX < this.plotWidth)
        ctx.fillRect(
          lastX - 4,
          this.y(last.high) - 5,
          8,
          Math.abs(this.y(last.low) - this.y(last.high)) + 10,
        );
      ctx.restore();
    }
    const remaining = Math.max(0, nextBucket(last.time, c.interval) - this.now()),
      countdown =
        Math.floor(remaining / 60000)
          .toString()
          .padStart(2, '0') +
        ':' +
        Math.floor((remaining / 1000) % 60)
          .toString()
          .padStart(2, '0');
    if (c.countdown && !s.ui.replay) {
      ctx.fillStyle = muted;
      ctx.fillText(
        marketOpen(c.symbol, this.now()) ? countdown : 'Closed',
        this.plotWidth + 8,
        this.y(last.close) + 24,
      );
    }
    if (c.previousClose && bars.length > 1)
      chip(
        bars[bars.length - 2].close,
        'Prev ' + formatPrice(bars[bars.length - 2].close, c.precision),
        muted,
      );
    this.positionChips = [];
    for (const a of s.alerts)
      if (a.symbol === c.symbol && a.active)
        chip(a.value, '♧ ' + formatPrice(a.value, c.precision), '#ff9800');
    for (const p of s.positions)
      if (p.symbol === c.symbol && (p.status === 'open' || p.status === 'pending')) {
        const color = p.side === 'buy' ? '#2962ff' : '#f23645';
        chip(
          p.entry,
          (p.status === 'pending' ? 'LMT ' : '× ') +
            formatPrice((last.close - p.entry) * p.quantity * (p.side === 'buy' ? 1 : -1), 2),
          color,
        );
        this.positionChips.push({ id: p.id, y: this.y(p.entry) });
        if (p.sl) chip(p.sl, 'SL', '#f23645');
        if (p.tp) chip(p.tp, 'TP', '#089981');
      }
    let hover = last;
    if (this.pointer && this.pointer.x < this.plotWidth && this.pointer.y < this.mainHeight) {
      const point = this.point(this.pointer),
        px = c.magnet ? this.projection().point(point) : this.pointer,
        index = clamp(Math.round(this.indexAt(px.x)), 0, bars.length - 1);
      hover = bars[index] ?? last;
      if (s.ui.cursor !== 'arrow') {
        ctx.strokeStyle = muted;
        ctx.setLineDash([4, 4]);
        if (s.ui.cursor === 'crosshair') {
          ctx.beginPath();
          ctx.moveTo(px.x, 0);
          ctx.lineTo(px.x, this.plotHeight);
          ctx.moveTo(0, px.y);
          ctx.lineTo(this.plotWidth, px.y);
          ctx.stroke();
        } else {
          ctx.beginPath();
          ctx.arc(px.x, px.y, 3, 0, Math.PI * 2);
          ctx.fillStyle = fg;
          ctx.fill();
        }
        ctx.setLineDash([]);
        ctx.fillStyle = '#363a45';
        ctx.fillRect(this.plotWidth, px.y - 10, 64, 20);
        ctx.fillRect(clamp(px.x - 65, 0, this.plotWidth - 130), this.plotHeight, 140, 24);
        ctx.fillStyle = '#fff';
        ctx.fillText(formatPrice(point.price, c.precision), this.plotWidth + 4, px.y + 4);
        ctx.fillText(
          dateLabel(hover.time, c.timezone),
          clamp(px.x - 62, 3, this.plotWidth - 127),
          this.plotHeight + 16,
        );
      }
      if (c.tooltip) {
        ctx.fillStyle = dark ? '#1e222d' : '#f1f3f6';
        ctx.fillRect(
          clamp(px.x + 15, 0, this.plotWidth - 190),
          clamp(px.y + 15, 0, this.mainHeight - 45),
          185,
          35,
        );
        ctx.fillStyle = fg;
        ctx.fillText(
          'O ' +
            formatPrice(hover.open, c.precision) +
            '  C ' +
            formatPrice(hover.close, c.precision),
          clamp(px.x + 23, 8, this.plotWidth - 182),
          clamp(px.y + 35, 20, this.mainHeight - 25),
        );
      }
    }
    const index = bars.indexOf(hover);
    this.onReadout?.({
      bar: hover,
      last,
      change: hover.close - hover.open,
      countdown,
      closed: !marketOpen(c.symbol, this.now()),
      indicatorValues: s.indicators.map(
        (i, n) =>
          i.kind +
          ' ' +
          (this.indicatorCache[n] ?? [])
            .map((line) => (line[index] === null ? '—' : formatPrice(line[index] ?? NaN, 2)))
            .join(' / '),
      ),
    });
    this.host.dataset.visibleBars = String(end - start + 1);
    this.host.dataset.renderMs = (performance.now() - started).toFixed(2);
    this.host.dataset.barCount = String(bars.length);
    this.host.dataset.drawings = String(this.drawings().length);
  }
  private paintIndicator(
    ctx: CanvasRenderingContext2D,
    series: Series[],
    start: number,
    end: number,
    y: (v: number) => number,
    color: string,
    width: number,
    opacity: number,
  ) {
    ctx.save();
    ctx.globalAlpha = opacity;
    ctx.lineWidth = width;
    series.forEach((line, n) => {
      ctx.strokeStyle = n === 0 ? color : n === 1 ? '#ff9800' : '#ab47bc';
      ctx.beginPath();
      let connected = false;
      for (let i = start; i <= end; i++) {
        const v = line[i];
        if (v === null || v === undefined) {
          connected = false;
          continue;
        }
        if (connected) ctx.lineTo(this.x(i), y(v));
        else ctx.moveTo(this.x(i), y(v));
        connected = true;
      }
      ctx.stroke();
    });
    ctx.restore();
  }
  private paintDrawing(ctx: CanvasRenderingContext2D, d: Drawing, selected: boolean) {
    ctx.save();
    ctx.strokeStyle = d.color;
    ctx.fillStyle = d.color;
    ctx.lineWidth = d.width;
    ctx.globalAlpha = d.opacity;
    ctx.font = (d.tool === 'Sticker' ? '24' : '12') + 'px Trebuchet MS';
    ctx.setLineDash(d.dash ? [6, 4] : []);
    paint(ctx, tools[d.tool].build(d, this.projection()));
    if (d.text && !['Text', 'AnchoredNote', 'Sticker', 'PriceLine'].includes(d.tool)) {
      const p = this.projection().point(d.points[0]);
      ctx.fillText(d.text, p.x + 5, p.y - 8);
    }
    ctx.setLineDash([]);
    if (selected && !d.locked)
      for (const anchor of d.points) {
        const p = this.projection().point(anchor);
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
        ctx.fillStyle = '#fff';
        ctx.fill();
        ctx.stroke();
      }
    ctx.restore();
  }
  destroy() {
    this.disposed = true;
    this.abort?.abort();
    this.stopFeed?.();
    for (const stop of this.stops.values()) stop();
    this.unsubscribe();
    clearInterval(this.timer);
    cancelAnimationFrame(this.frame);
    this.resize.disconnect();
    this.removers.forEach((fn) => fn());
    this.canvases.forEach((c) => c.remove());
  }
}
