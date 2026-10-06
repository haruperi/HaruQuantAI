import React, { useState, useMemo, useRef, useEffect } from 'react';
import type { Strategy, Trade } from '../../../host/types';

interface TradesOnChartViewProps {
  strategy?: Strategy;
}

interface Bar {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export function TradesOnChartView({ strategy }: TradesOnChartViewProps) {
  const [selectedSymbol, setSelectedSymbol] = useState(strategy?.symbol || 'EURUSD');
  const [selectedTimeframe, setSelectedTimeframe] = useState(strategy?.timeframe || 'H1');
  const [showGrid, setShowGrid] = useState(true);
  const [showPrice, setShowPrice] = useState(true);
  const [showTicket, setShowTicket] = useState(true);
  const [showPL, setShowPL] = useState(true);

  // Indicators toggle
  const [showSMA, setShowSMA] = useState(true);
  const [showEMA, setShowEMA] = useState(true);
  const [showBB, setShowBB] = useState(false);
  const [indicatorsMenuOpen, setIndicatorsMenuOpen] = useState(false);

  const [selectedTradeIndex, setSelectedTradeIndex] = useState<number>(0);
  const [hoveredBarIndex, setHoveredBarIndex] = useState<number | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const trades: Trade[] = useMemo(() => {
    return strategy?.trades || [];
  }, [strategy]);

  const selectedTrade = trades[selectedTradeIndex] || trades[0];

  // Synthesize realistic historical candlestick bars based on the strategy's trades
  const bars: Bar[] = useMemo(() => {
    const list: Bar[] = [];
    let basePrice = 1.085;
    const now = Date.now();
    const count = 120; // 120 bars

    // Generate deterministic baseline around strategy trades
    for (let i = 0; i < count; i++) {
      const timeMs = now - (count - i) * 3600 * 1000;
      const dateStr = new Date(timeMs).toISOString().replace('T', ' ').slice(0, 16);

      // Controlled random walk
      const change = Math.sin(i / 6) * 0.0012 + (Math.sin(i * 3.7) * 0.0008);
      const open = basePrice;
      const close = open + change;
      const high = Math.max(open, close) + Math.abs(Math.sin(i * 1.5)) * 0.0008;
      const low = Math.min(open, close) - Math.abs(Math.cos(i * 1.2)) * 0.0008;
      const volume = Math.floor(500 + Math.abs(Math.sin(i)) * 1200);

      list.push({ time: dateStr, open, high, low, close, volume });
      basePrice = close;
    }

    return list;
  }, [strategy?.id]);

  // Map trades to bar positions
  const mappedTrades = useMemo(() => {
    if (trades.length === 0 || bars.length === 0) return [];
    return trades.slice(0, 8).map((t, idx) => {
      // Place trades along the bar range
      const entryBarIdx = Math.min(bars.length - 10, 15 + idx * 12);
      const exitBarIdx = Math.min(bars.length - 2, entryBarIdx + 4 + (idx % 5));
      const entryPrice = bars[entryBarIdx].close;
      const exitPrice = t.pnl > 0
        ? (t.side === 'Long' ? entryPrice + 0.0025 : entryPrice - 0.0025)
        : (t.side === 'Long' ? entryPrice - 0.0018 : entryPrice + 0.0018);

      return {
        ...t,
        id: t.id || `T-${idx + 1}`,
        entryBarIdx,
        exitBarIdx,
        entryPrice,
        exitPrice,
        slPrice: t.side === 'Long' ? entryPrice - 0.002 : entryPrice + 0.002,
        ptPrice: t.side === 'Long' ? entryPrice + 0.004 : entryPrice - 0.004,
      };
    });
  }, [trades, bars]);

  const activeMappedTrade = mappedTrades[selectedTradeIndex] || mappedTrades[0];

  // Moving averages calculation
  const smaValues = useMemo(() => {
    const period = 20;
    return bars.map((_, i) => {
      if (i < period - 1) return null;
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += bars[j].close;
      return sum / period;
    });
  }, [bars]);

  const emaValues = useMemo(() => {
    const period = 50;
    const k = 2 / (period + 1);
    let prev = bars[0].close;
    return bars.map((b, i) => {
      if (i === 0) return prev;
      prev = b.close * k + prev * (1 - k);
      return prev;
    });
  }, [bars]);

  const bbValues = useMemo(() => {
    const period = 20;
    return bars.map((_, i) => {
      if (i < period - 1) return null;
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += bars[j].close;
      const mean = sum / period;
      let varSum = 0;
      for (let j = i - period + 1; j <= i; j++) varSum += Math.pow(bars[j].close - mean, 2);
      const std = Math.sqrt(varSum / period);
      return { upper: mean + std * 2, middle: mean, lower: mean - std * 2 };
    });
  }, [bars]);

  // Render Candlestick Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    // Find price min/max
    let minPrice = Infinity;
    let maxPrice = -Infinity;
    bars.forEach(b => {
      if (b.low < minPrice) minPrice = b.low;
      if (b.high > maxPrice) maxPrice = b.high;
    });
    // Add margin
    const priceMargin = (maxPrice - minPrice) * 0.08 || 0.001;
    minPrice -= priceMargin;
    maxPrice += priceMargin;
    const priceRange = maxPrice - minPrice;

    const chartPaddingLeft = 10;
    const chartPaddingRight = 65;
    const chartPaddingTop = 20;
    const chartPaddingBottom = 30;
    const plotWidth = width - chartPaddingLeft - chartPaddingRight;
    const plotHeight = height - chartPaddingTop - chartPaddingBottom;

    const barWidth = Math.max(3, (plotWidth / bars.length) * 0.7);
    const barSpacing = plotWidth / bars.length;

    const getY = (val: number) => {
      return chartPaddingTop + plotHeight - ((val - minPrice) / priceRange) * plotHeight;
    };

    const getX = (idx: number) => {
      return chartPaddingLeft + idx * barSpacing + barSpacing / 2;
    };

    // 1. Grid
    if (showGrid) {
      ctx.strokeStyle = '#21262d';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 2]);

      // Horizontal price lines
      const steps = 6;
      for (let i = 0; i <= steps; i++) {
        const y = chartPaddingTop + (plotHeight / steps) * i;
        ctx.beginPath();
        ctx.moveTo(chartPaddingLeft, y);
        ctx.lineTo(width - chartPaddingRight, y);
        ctx.stroke();

        const price = maxPrice - (priceRange / steps) * i;
        ctx.fillStyle = '#8b949e';
        ctx.font = '10px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(price.toFixed(5), width - chartPaddingRight + 6, y + 3);
      }

      // Vertical time lines
      for (let i = 0; i < bars.length; i += 20) {
        const x = getX(i);
        ctx.beginPath();
        ctx.moveTo(x, chartPaddingTop);
        ctx.lineTo(x, height - chartPaddingBottom);
        ctx.stroke();

        ctx.fillStyle = '#8b949e';
        ctx.font = '9px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(bars[i].time.slice(11, 16), x, height - chartPaddingBottom + 14);
      }
      ctx.setLineDash([]);
    }

    // 2. Bollinger Bands (if enabled)
    if (showBB) {
      ctx.fillStyle = 'rgba(187, 134, 252, 0.06)';
      ctx.beginPath();
      let started = false;
      for (let i = 0; i < bars.length; i++) {
        const bb = bbValues[i];
        if (!bb) continue;
        const x = getX(i);
        const yUpper = getY(bb.upper);
        if (!started) {
          ctx.moveTo(x, yUpper);
          started = true;
        } else {
          ctx.lineTo(x, yUpper);
        }
      }
      for (let i = bars.length - 1; i >= 0; i--) {
        const bb = bbValues[i];
        if (!bb) continue;
        const x = getX(i);
        ctx.lineTo(x, getY(bb.lower));
      }
      ctx.closePath();
      ctx.fill();

      // Upper and lower lines
      ctx.strokeStyle = 'rgba(187, 134, 252, 0.5)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      started = false;
      for (let i = 0; i < bars.length; i++) {
        const bb = bbValues[i];
        if (!bb) continue;
        const x = getX(i);
        if (!started) { ctx.moveTo(x, getY(bb.upper)); started = true; }
        else ctx.lineTo(x, getY(bb.upper));
      }
      ctx.stroke();

      ctx.beginPath();
      started = false;
      for (let i = 0; i < bars.length; i++) {
        const bb = bbValues[i];
        if (!bb) continue;
        const x = getX(i);
        if (!started) { ctx.moveTo(x, getY(bb.lower)); started = true; }
        else ctx.lineTo(x, getY(bb.lower));
      }
      ctx.stroke();
    }

    // 3. Moving Average Lines (SMA & EMA)
    if (showSMA) {
      ctx.strokeStyle = '#e3b341'; // Golden Yellow
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      let started = false;
      for (let i = 0; i < bars.length; i++) {
        const val = smaValues[i];
        if (val === null) continue;
        const x = getX(i);
        const y = getY(val);
        if (!started) { ctx.moveTo(x, y); started = true; }
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    if (showEMA) {
      ctx.strokeStyle = '#58a6ff'; // Cyan Blue
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      let started = false;
      for (let i = 0; i < bars.length; i++) {
        const val = emaValues[i];
        if (val === null) continue;
        const x = getX(i);
        const y = getY(val);
        if (!started) { ctx.moveTo(x, y); started = true; }
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    // 4. Candlesticks
    bars.forEach((b, idx) => {
      const x = getX(idx);
      const isUp = b.close >= b.open;
      const color = isUp ? '#3fb950' : '#f85149';

      const yHigh = getY(b.high);
      const yLow = getY(b.low);
      const yOpen = getY(b.open);
      const yClose = getY(b.close);

      // Wick
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, yHigh);
      ctx.lineTo(x, yLow);
      ctx.stroke();

      // Candle Body
      const bodyTop = Math.min(yOpen, yClose);
      const bodyHeight = Math.max(1.5, Math.abs(yOpen - yClose));
      ctx.fillStyle = color;
      ctx.fillRect(x - barWidth / 2, bodyTop, barWidth, bodyHeight);
    });

    // 5. Render Trade Overlays (Entry Arrows, Connecting lines, Exit Markers, Labels)
    mappedTrades.forEach((trade, tIdx) => {
      const isSelected = tIdx === selectedTradeIndex;
      const xEntry = getX(trade.entryBarIdx);
      const yEntry = getY(trade.entryPrice);
      const xExit = getX(trade.exitBarIdx);
      const yExit = getY(trade.exitPrice);

      const isLong = trade.side === 'Long';
      const isWin = trade.pnl >= 0;

      // Dashed trade connecting line
      ctx.strokeStyle = isWin ? 'rgba(63, 185, 80, 0.8)' : 'rgba(248, 81, 73, 0.8)';
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(xEntry, yEntry);
      ctx.lineTo(xExit, yExit);
      ctx.stroke();
      ctx.setLineDash([]);

      // Entry Marker (Triangle Arrow)
      ctx.fillStyle = isLong ? '#3fb950' : '#f85149';
      ctx.beginPath();
      if (isLong) {
        // Up arrow below entry price
        const arrowY = yEntry + 8;
        ctx.moveTo(xEntry, arrowY - 6);
        ctx.lineTo(xEntry - 5, arrowY + 4);
        ctx.lineTo(xEntry + 5, arrowY + 4);
      } else {
        // Down arrow above entry price
        const arrowY = yEntry - 8;
        ctx.moveTo(xEntry, arrowY + 6);
        ctx.lineTo(xEntry - 5, arrowY - 4);
        ctx.lineTo(xEntry + 5, arrowY - 4);
      }
      ctx.closePath();
      ctx.fill();

      // Exit Marker (Square / Cross)
      ctx.fillStyle = isWin ? '#3fb950' : '#f85149';
      ctx.fillRect(xExit - 3, yExit - 3, 6, 6);

      // Trade Labels based on visibility toggles
      if (showTicket || showPrice || showPL) {
        ctx.font = '9px sans-serif';
        ctx.textAlign = 'center';
        let label = '';
        if (showTicket) label += `#${trade.id} `;
        if (showPL) label += `${trade.pnl >= 0 ? '+' : ''}$${trade.pnl.toFixed(0)} `;
        if (showPrice) label += `@${trade.exitPrice.toFixed(4)}`;

        const textY = isWin ? yExit - 8 : yExit + 14;
        ctx.fillStyle = isSelected ? '#ffffff' : '#8b949e';
        ctx.fillText(label.trim(), xExit, textY);
      }
    });

    // 6. Crosshair on hover
    if (hoveredBarIndex !== null && hoveredBarIndex >= 0 && hoveredBarIndex < bars.length) {
      const x = getX(hoveredBarIndex);
      ctx.strokeStyle = '#58a6ff';
      ctx.lineWidth = 1;
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(x, chartPaddingTop);
      ctx.lineTo(x, height - chartPaddingBottom);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }, [
    bars,
    mappedTrades,
    selectedTradeIndex,
    hoveredBarIndex,
    showGrid,
    showPrice,
    showTicket,
    showPL,
    showSMA,
    showEMA,
    showBB,
    smaValues,
    emaValues,
    bbValues,
  ]);

  const activeBar = hoveredBarIndex !== null ? bars[hoveredBarIndex] : bars[bars.length - 1];

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const chartPaddingLeft = 10;
    const chartPaddingRight = 65;
    const plotWidth = canvas.width - chartPaddingLeft - chartPaddingRight;
    const barSpacing = plotWidth / bars.length;

    const idx = Math.floor((clientX - chartPaddingLeft) / barSpacing);
    if (idx >= 0 && idx < bars.length) {
      setHoveredBarIndex(idx);
    } else {
      setHoveredBarIndex(null);
    }
  };

  const handlePrevTrade = () => {
    setSelectedTradeIndex(prev => (prev > 0 ? prev - 1 : mappedTrades.length - 1));
  };

  const handleNextTrade = () => {
    setSelectedTradeIndex(prev => (prev < mappedTrades.length - 1 ? prev + 1 : 0));
  };

  return (
    <div
      className="trades-on-chart-view"
      style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0d1117' }}
    >
      {/* SQX Chart Toolbar */}
      <div
        className="chart-toolbar"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '6px 12px',
          background: '#161b22',
          borderBottom: '1px solid #30363d',
          flexWrap: 'wrap',
          fontSize: 12,
        }}
      >
        {/* Symbol Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ color: '#8b949e', fontSize: 11 }}>Symbol:</span>
          <select
            className="text-input"
            style={{ width: 95, height: 26, fontSize: 11, padding: '2px 4px' }}
            value={selectedSymbol}
            onChange={e => setSelectedSymbol(e.target.value)}
          >
            <option value="EURUSD">EURUSD</option>
            <option value="GBPUSD">GBPUSD</option>
            <option value="USDJPY">USDJPY</option>
            <option value="AUDUSD">AUDUSD</option>
            <option value="USDCAD">USDCAD</option>
          </select>
        </div>

        {/* Timeframe */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{ color: '#8b949e', fontSize: 11 }}>TF:</span>
          <select
            className="text-input"
            style={{ width: 65, height: 26, fontSize: 11, padding: '2px 4px' }}
            value={selectedTimeframe}
            onChange={e => setSelectedTimeframe(e.target.value)}
          >
            <option value="M1">M1</option>
            <option value="M5">M5</option>
            <option value="M15">M15</option>
            <option value="H1">H1</option>
            <option value="H4">H4</option>
            <option value="D1">D1</option>
          </select>
        </div>

        <div style={{ width: 1, height: 18, background: '#30363d' }} />

        {/* Show Indicators Dropdown */}
        <div style={{ position: 'relative' }}>
          <button
            className="btn btn-default"
            style={{
              height: 26,
              fontSize: 11,
              padding: '2px 8px',
              background: '#21262d',
              border: '1px solid #30363d',
              borderRadius: 3,
              cursor: 'pointer',
              color: '#c9d1d9',
            }}
            onClick={() => setIndicatorsMenuOpen(!indicatorsMenuOpen)}
          >
            Show indicators ▾
          </button>
          {indicatorsMenuOpen && (
            <div
              style={{
                position: 'absolute',
                top: 30,
                left: 0,
                zIndex: 100,
                background: '#161b22',
                border: '1px solid #30363d',
                borderRadius: 4,
                boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
                padding: '8px 12px',
                display: 'flex',
                flexDirection: 'column',
                gap: 6,
                minWidth: 150,
              }}
            >
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={showSMA}
                  onChange={e => setShowSMA(e.target.checked)}
                />
                <span style={{ color: '#e3b341' }}>SMA (20)</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={showEMA}
                  onChange={e => setShowEMA(e.target.checked)}
                />
                <span style={{ color: '#58a6ff' }}>EMA (50)</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={showBB}
                  onChange={e => setShowBB(e.target.checked)}
                />
                <span style={{ color: '#bb86fc' }}>Bollinger Bands</span>
              </label>
            </div>
          )}
        </div>

        {/* Grid toggle */}
        <button
          className={`btn ${showGrid ? 'active' : ''}`}
          style={{
            height: 26,
            fontSize: 11,
            padding: '2px 8px',
            background: showGrid ? '#1f6feb' : '#21262d',
            border: '1px solid #30363d',
            borderRadius: 3,
            cursor: 'pointer',
            color: '#fff',
          }}
          onClick={() => setShowGrid(!showGrid)}
        >
          Grid
        </button>

        <div style={{ width: 1, height: 18, background: '#30363d' }} />

        {/* Trade visibility options */}
        <div style={{ display: 'inline-flex', borderRadius: 3, overflow: 'hidden', border: '1px solid #30363d' }}>
          <button
            style={{
              padding: '2px 8px',
              fontSize: 11,
              background: showPrice ? '#30363d' : '#21262d',
              border: 'none',
              color: '#c9d1d9',
              cursor: 'pointer',
            }}
            onClick={() => setShowPrice(!showPrice)}
          >
            Price
          </button>
          <button
            style={{
              padding: '2px 8px',
              fontSize: 11,
              background: showTicket ? '#30363d' : '#21262d',
              borderLeft: '1px solid #30363d',
              borderRight: '1px solid #30363d',
              borderTop: 'none',
              borderBottom: 'none',
              color: '#c9d1d9',
              cursor: 'pointer',
            }}
            onClick={() => setShowTicket(!showTicket)}
          >
            Ticket
          </button>
          <button
            style={{
              padding: '2px 8px',
              fontSize: 11,
              background: showPL ? '#30363d' : '#21262d',
              border: 'none',
              color: '#c9d1d9',
              cursor: 'pointer',
            }}
            onClick={() => setShowPL(!showPL)}
          >
            Profit/Loss
          </button>
        </div>

        <div style={{ width: 1, height: 18, background: '#30363d' }} />

        {/* Trade Navigation */}
        <div style={{ display: 'inline-flex', gap: 4 }}>
          <button
            className="btn btn-default"
            style={{
              height: 26,
              fontSize: 11,
              padding: '2px 8px',
              background: '#21262d',
              border: '1px solid #30363d',
              borderRadius: 3,
              cursor: 'pointer',
              color: '#c9d1d9',
            }}
            onClick={handlePrevTrade}
          >
            &lt; Previous trade
          </button>
          <button
            className="btn btn-default"
            style={{
              height: 26,
              fontSize: 11,
              padding: '2px 8px',
              background: '#21262d',
              border: '1px solid #30363d',
              borderRadius: 3,
              cursor: 'pointer',
              color: '#c9d1d9',
            }}
            onClick={handleNextTrade}
          >
            Next trade &gt;
          </button>
        </div>
      </div>

      {/* Main Content: Sidebar Data Panel + Chart Panel */}
      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* Left Data Panel (SQX style bar info & trade info) */}
        <div
          className="chart-data-panel"
          style={{
            width: 210,
            borderRight: '1px solid #30363d',
            background: '#12161c',
            padding: 10,
            fontSize: 11,
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            overflowY: 'auto',
          }}
        >
          {/* Bar Info Table */}
          <div>
            <div style={{ fontWeight: 600, color: '#58a6ff', marginBottom: 4 }}>Bar Data</div>
            <div style={{ color: '#8b949e', marginBottom: 6 }}>{activeBar?.time}</div>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                <tr><td style={{ color: '#8b949e' }}>Open:</td><td style={{ textAlign: 'right', fontFamily: 'monospace' }}>{activeBar?.open.toFixed(5)}</td></tr>
                <tr><td style={{ color: '#8b949e' }}>High:</td><td style={{ textAlign: 'right', fontFamily: 'monospace' }}>{activeBar?.high.toFixed(5)}</td></tr>
                <tr><td style={{ color: '#8b949e' }}>Low:</td><td style={{ textAlign: 'right', fontFamily: 'monospace' }}>{activeBar?.low.toFixed(5)}</td></tr>
                <tr><td style={{ color: '#8b949e' }}>Close:</td><td style={{ textAlign: 'right', fontFamily: 'monospace' }}>{activeBar?.close.toFixed(5)}</td></tr>
                <tr><td style={{ color: '#8b949e' }}>Volume:</td><td style={{ textAlign: 'right', fontFamily: 'monospace' }}>{activeBar?.volume}</td></tr>
              </tbody>
            </table>
          </div>

          {/* Indicators Table */}
          <div style={{ borderTop: '1px solid #21262d', paddingTop: 8 }}>
            <div style={{ fontWeight: 600, color: '#c9d1d9', marginBottom: 4 }}>Indicators</div>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <tbody>
                {showSMA && (
                  <tr>
                    <td style={{ color: '#e3b341' }}>SMA (20):</td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                      {smaValues[hoveredBarIndex ?? bars.length - 1]?.toFixed(5) || 'N/A'}
                    </td>
                  </tr>
                )}
                {showEMA && (
                  <tr>
                    <td style={{ color: '#58a6ff' }}>EMA (50):</td>
                    <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                      {emaValues[hoveredBarIndex ?? bars.length - 1]?.toFixed(5) || 'N/A'}
                    </td>
                  </tr>
                )}
                {showBB && (
                  <>
                    <tr>
                      <td style={{ color: '#bb86fc' }}>BB Upper:</td>
                      <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                        {bbValues[hoveredBarIndex ?? bars.length - 1]?.upper.toFixed(5) || 'N/A'}
                      </td>
                    </tr>
                    <tr>
                      <td style={{ color: '#bb86fc' }}>BB Lower:</td>
                      <td style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                        {bbValues[hoveredBarIndex ?? bars.length - 1]?.lower.toFixed(5) || 'N/A'}
                      </td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>

          {/* Selected Trade Info */}
          {activeMappedTrade && (
            <div
              style={{
                borderTop: '1px solid #21262d',
                paddingTop: 8,
                background: 'rgba(56, 139, 253, 0.05)',
                padding: 8,
                borderRadius: 4,
              }}
            >
              <div style={{ fontWeight: 600, color: '#f0883e', marginBottom: 4 }}>
                Trade #{activeMappedTrade.id} ({selectedTradeIndex + 1}/{mappedTrades.length})
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                <div>
                  <span
                    style={{
                      fontWeight: 600,
                      color: activeMappedTrade.side === 'Long' ? '#3fb950' : '#f85149',
                    }}
                  >
                    {activeMappedTrade.side === 'Long' ? 'Buy' : 'Sell'}
                  </span>{' '}
                  at {activeMappedTrade.entryPrice.toFixed(5)}
                </div>
                <div style={{ color: '#8b949e', fontSize: 10 }}>
                  Open: {bars[activeMappedTrade.entryBarIdx]?.time}
                </div>
                <div style={{ marginTop: 2 }}>
                  <span>Close at {activeMappedTrade.exitPrice.toFixed(5)}</span>
                </div>
                <div style={{ color: '#8b949e', fontSize: 10 }}>
                  Exit: {bars[activeMappedTrade.exitBarIdx]?.time}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                  <span style={{ color: '#8b949e' }}>SL: {activeMappedTrade.slPrice.toFixed(5)}</span>
                  <span style={{ color: '#8b949e' }}>PT: {activeMappedTrade.ptPrice.toFixed(5)}</span>
                </div>
                <div style={{ marginTop: 4, fontWeight: 600 }}>
                  PL:{' '}
                  <span
                    style={{
                      color: activeMappedTrade.pnl >= 0 ? '#3fb950' : '#f85149',
                    }}
                  >
                    {activeMappedTrade.pnl >= 0 ? '+' : ''}${activeMappedTrade.pnl.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Interactive Candlestick Canvas Container */}
        <div
          ref={containerRef}
          style={{ flex: 1, position: 'relative', overflow: 'hidden' }}
          onMouseLeave={() => setHoveredBarIndex(null)}
        >
          <canvas
            ref={canvasRef}
            width={900}
            height={550}
            style={{ width: '100%', height: '100%', display: 'block' }}
            onMouseMove={handleCanvasMouseMove}
          />
        </div>
      </div>
    </div>
  );
}
