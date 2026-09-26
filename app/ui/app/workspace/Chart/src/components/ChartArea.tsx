import { useEffect, useRef, useState } from 'react';
import { useStore } from 'zustand';
import { X, Settings2 } from 'lucide-react';
import { useChart } from '../hooks/useChartEngine';
import { ChartEngine } from '../engine/ChartEngine';
import { MockFeed } from '../feed/MockFeed';
import { symbolInfo } from '../feed/symbols';
import { formatPrice } from '../utils/format';
import { pnl } from '../store/positions';
import { ToolButton } from './Tooltip';
export function ChartArea() {
  const { store, engine, root } = useChart(),
    s = useStore(store),
    host = useRef<HTMLDivElement>(null),
    legend = useRef<HTMLDivElement>(null),
    ohlc = useRef<HTMLDivElement>(null),
    buy = useRef<HTMLSpanElement>(null),
    sell = useRef<HTMLSpanElement>(null),
    [loading, setLoading] = useState(true);
  useEffect(() => {
    if (!host.current) return;
    const instance = new ChartEngine(host.current, store, new MockFeed());
    engine.current = instance;
    instance.onLoading = setLoading;
    instance.onReadout = (r) => {
      const c = store.getState().chart;
      const f = (v: number) => formatPrice(v, c.precision);
      if (ohlc.current) {
        ohlc.current.textContent =
          'O ' +
          f(r.bar.open) +
          '   H ' +
          f(r.bar.high) +
          '   L ' +
          f(r.bar.low) +
          '   C ' +
          f(r.bar.close) +
          '   ' +
          (r.change >= 0 ? '+' : '') +
          f(r.change) +
          ' (' +
          ((r.change / r.bar.open) * 100).toFixed(2) +
          '%)';
        ohlc.current.style.color = r.change >= 0 ? '#089981' : '#f23645';
      }
      if (buy.current) buy.current.textContent = f(r.last.close * 1.00002);
      if (sell.current) sell.current.textContent = f(r.last.close * 0.99998);
      legend.current?.querySelectorAll<HTMLElement>('[data-indicator]').forEach((node, i) => {
        node.textContent = r.indicatorValues[i] ?? '';
      });
      root.current?.querySelectorAll<HTMLElement>('[data-position-pnl]').forEach((node) => {
        const position = store.getState().positions.find((p) => p.id === node.dataset.positionPnl);
        if (position) {
          const value = pnl(
            position,
            instance.quotes.get(position.symbol)?.price ?? position.entry,
          );
          node.textContent = value.toFixed(2);
          node.style.color = value >= 0 ? '#089981' : '#f23645';
        }
      });
    };
    return () => {
      instance.destroy();
      engine.current = null;
    };
  }, [store, engine, root]);
  const symbol = symbolInfo(s.chart.symbol);
  return (
    <div className="cq-chart" aria-label="Chart" role="region">
      <div className="cq-canvas-host" ref={host} data-testid="chart-canvas-host" />
      <div className="cq-legend" ref={legend}>
        <h1>
          <span className="cq-symbol-logo">{symbol.icon}</span>
          {symbol.name}
          <span className="cq-legend-muted">
            {' '}
            · {s.chart.interval} · {symbol.exchange}
          </span>
          <span className="cq-live-dot" />
        </h1>
        <div className="cq-ohlc" ref={ohlc}>
          Loading OHLC…
        </div>
        <div className="cq-quotes">
          <button className="cq-sell" onClick={() => s.setUI({ dialog: 'order', side: 'sell' })}>
            <span ref={sell}>—</span>
            <small>SELL</small>
          </button>
          <span className="cq-spread">SIM</span>
          <button className="cq-buy" onClick={() => s.setUI({ dialog: 'order', side: 'buy' })}>
            <span ref={buy}>—</span>
            <small>BUY</small>
          </button>
        </div>
        {s.indicators.map((i) => (
          <div
            className="cq-indicator-legend"
            key={i.id}
            onContextMenu={(e) => {
              e.preventDefault();
              s.setUI({ dialog: 'indicators' });
            }}
          >
            <span data-indicator={i.id} style={{ color: i.color }}>
              {i.kind}
            </span>
            <ToolButton
              label={'Configure ' + i.kind}
              onClick={() => s.setUI({ dialog: 'indicators' })}
            >
              <Settings2 size={12} />
            </ToolButton>
            <ToolButton
              label={'Remove ' + i.kind}
              onClick={() => s.setIndicators(s.indicators.filter((x) => x.id !== i.id))}
            >
              <X size={12} />
            </ToolButton>
          </div>
        ))}
      </div>
      <div className="cq-save">
        <span className="cq-sim-tag">SIMULATED DATA</span>
        <small>{s.ui.saved}</small>
      </div>
      {loading && (
        <div className="cq-loading" role="status">
          Loading market history…
        </div>
      )}
      {s.ui.replayPick && (
        <div className="cq-hint">Click a candle to start replay · Esc to cancel</div>
      )}
      {s.ui.tool !== 'cursor' && (
        <div className="cq-hint">
          {s.ui.tool} ·{' '}
          {s.ui.tool === 'Polygon'
            ? 'Click vertices, Enter to finish'
            : 'Place anchors on the chart'}{' '}
          · Esc to cancel
        </div>
      )}
    </div>
  );
}
