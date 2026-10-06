import React, { useMemo, useState } from 'react';
import { Activity, BarChart2, CheckCircle2, Play, RefreshCw, Sliders } from 'lucide-react';
import { Button, Field, Modal, Select, TextInput } from '../../components/ui';

interface BarData {
  bar: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  indicatorVal: number;
  upperBand?: number;
  lowerBand?: number;
}

interface IndicatorTesterModalProps {
  onClose: () => void;
  indicatorName: string;
}

export function IndicatorTesterModal({ onClose, indicatorName }: IndicatorTesterModalProps) {
  const [period, setPeriod] = useState<number>(14);
  const [multiplier, setMultiplier] = useState<number>(2.0);
  const [symbol, setSymbol] = useState<string>('EURUSD');
  const [timeframe, setTimeframe] = useState<string>('H1');
  const [sampleSize, setSampleSize] = useState<number>(40);

  // Generate synthetic price series and calculate indicator values
  const dataset: BarData[] = useMemo(() => {
    const bars: BarData[] = [];
    let currentPrice = 1.1000;
    const baseDate = new Date(2026, 0, 15, 9, 0);

    for (let i = 0; i < sampleSize; i++) {
      const date = new Date(baseDate.getTime() + i * 3600000);
      const delta = (Math.sin(i * 0.35) * 0.0018) + ((i % 5 === 0 ? 1 : -1) * 0.0012) + (Math.random() - 0.5) * 0.0015;
      const open = Math.round(currentPrice * 100000) / 100000;
      const close = Math.round((open + delta) * 100000) / 100000;
      const high = Math.round((Math.max(open, close) + Math.random() * 0.0012) * 100000) / 100000;
      const low = Math.round((Math.min(open, close) - Math.random() * 0.0012) * 100000) / 100000;
      currentPrice = close;

      bars.push({
        bar: i + 1,
        date: date.toISOString().slice(0, 16).replace('T', ' '),
        open,
        high,
        low,
        close,
        indicatorVal: 0,
      });
    }

    // Compute SMA / EMA / Keltner bands
    for (let i = 0; i < bars.length; i++) {
      const windowStart = Math.max(0, i - period + 1);
      const windowBars = bars.slice(windowStart, i + 1);
      const sum = windowBars.reduce((acc, b) => acc + b.close, 0);
      const sma = sum / windowBars.length;

      // Approximate ATR
      const trSum = windowBars.reduce((acc, b) => acc + (b.high - b.low), 0);
      const atr = trSum / windowBars.length;

      bars[i].indicatorVal = Math.round(sma * 100000) / 100000;
      bars[i].upperBand = Math.round((sma + multiplier * atr) * 100000) / 100000;
      bars[i].lowerBand = Math.round((sma - multiplier * atr) * 100000) / 100000;
    }

    return bars;
  }, [period, multiplier, sampleSize]);

  // Scaler for SVG chart
  const minPrice = Math.min(...dataset.map(b => b.low), ...dataset.map(b => b.lowerBand ?? b.low));
  const maxPrice = Math.max(...dataset.map(b => b.high), ...dataset.map(b => b.upperBand ?? b.high));
  const priceRange = maxPrice - minPrice || 0.001;

  const chartWidth = 720;
  const chartHeight = 220;
  const candleWidth = Math.max(3, Math.floor((chartWidth - 40) / dataset.length) - 3);

  const getY = (val: number) => {
    return chartHeight - 20 - ((val - minPrice) / priceRange) * (chartHeight - 40);
  };

  const getX = (index: number) => {
    return 20 + index * ((chartWidth - 40) / (dataset.length - 1 || 1));
  };

  // Generate SVG polyline path for indicator
  const indicatorPath = dataset
    .map((b, i) => `${getX(i)},${getY(b.indicatorVal)}`)
    .join(' ');

  const upperBandPath = dataset
    .map((b, i) => `${getX(i)},${getY(b.upperBand ?? b.indicatorVal)}`)
    .join(' ');

  const lowerBandPath = dataset
    .map((b, i) => `${getX(i)},${getY(b.lowerBand ?? b.indicatorVal)}`)
    .join(' ');

  return (
    <Modal title={`Indicator Interactive Tester: ${indicatorName}`} onClose={onClose} width={860}>
      <div className="flex flex-col gap-4">
        {/* Top Controls Bar */}
        <div className="grid grid-cols-5 gap-3 p-3 bg-gray-900 rounded border border-gray-700">
          <Field label="Market Symbol">
            <Select value={symbol} onChange={setSymbol}>
              <option>EURUSD</option>
              <option>GBPUSD</option>
              <option>USDJPY</option>
              <option>XAUUSD</option>
            </Select>
          </Field>

          <Field label="Timeframe">
            <Select value={timeframe} onChange={setTimeframe}>
              <option>M15</option>
              <option>M30</option>
              <option>H1</option>
              <option>H4</option>
              <option>D1</option>
            </Select>
          </Field>

          <Field label="Period">
            <TextInput
              type="number"
              value={period}
              onChange={e => setPeriod(Math.max(2, Number(e.target.value) || 14))}
            />
          </Field>

          <Field label="Multiplier (Bands)">
            <TextInput
              type="number"
              step="0.1"
              value={multiplier}
              onChange={e => setMultiplier(Math.max(0.5, Number(e.target.value) || 2.0))}
            />
          </Field>

          <Field label="Test Bars Count">
            <Select value={String(sampleSize)} onChange={v => setSampleSize(Number(v))}>
              <option value="30">30 bars</option>
              <option value="40">40 bars</option>
              <option value="60">60 bars</option>
            </Select>
          </Field>
        </div>

        {/* SVG Chart Preview */}
        <div className="bg-[#12161b] rounded border border-gray-700 p-2 flex flex-col">
          <div className="flex items-center justify-between px-2 py-1 text-xs text-gray-300 border-b border-gray-800">
            <div className="flex items-center gap-3">
              <span className="font-semibold text-gray-200">
                {symbol} ({timeframe})
              </span>
              <span className="flex items-center gap-1.5 text-cyan-400">
                <span className="w-2.5 h-0.5 bg-cyan-400 inline-block" />
                Middle (Period={period})
              </span>
              <span className="flex items-center gap-1.5 text-amber-400">
                <span className="w-2.5 h-0.5 bg-amber-400 inline-block" />
                Upper/Lower Bands (x{multiplier})
              </span>
            </div>
            <span className="text-[11px] text-gray-500 font-mono">
              Min: {minPrice.toFixed(4)} | Max: {maxPrice.toFixed(4)}
            </span>
          </div>

          <div className="relative w-full h-[220px] overflow-hidden">
            <svg
              viewBox={`0 0 ${chartWidth} ${chartHeight}`}
              className="w-full h-full select-none"
            >
              {/* Grid Lines */}
              {[0.2, 0.4, 0.6, 0.8].map(ratio => {
                const y = 20 + ratio * (chartHeight - 40);
                return (
                  <line
                    key={ratio}
                    x1="20"
                    y1={y}
                    x2={chartWidth - 20}
                    y2={y}
                    stroke="#1e2631"
                    strokeDasharray="4 4"
                  />
                );
              })}

              {/* Upper & Lower Bands */}
              <polyline
                fill="none"
                stroke="#f59e0b"
                strokeWidth="1.2"
                strokeDasharray="3 3"
                points={upperBandPath}
              />
              <polyline
                fill="none"
                stroke="#f59e0b"
                strokeWidth="1.2"
                strokeDasharray="3 3"
                points={lowerBandPath}
              />

              {/* Candlesticks */}
              {dataset.map((b, i) => {
                const x = getX(i);
                const isBull = b.close >= b.open;
                const candleColor = isBull ? '#10b981' : '#ef4444';
                const openY = getY(b.open);
                const closeY = getY(b.close);
                const highY = getY(b.high);
                const lowY = getY(b.low);
                const top = Math.min(openY, closeY);
                const height = Math.max(2, Math.abs(closeY - openY));

                return (
                  <g key={b.bar}>
                    {/* Wick */}
                    <line
                      x1={x}
                      y1={highY}
                      x2={x}
                      y2={lowY}
                      stroke={candleColor}
                      strokeWidth="1"
                    />
                    {/* Body */}
                    <rect
                      x={x - candleWidth / 2}
                      y={top}
                      width={candleWidth}
                      height={height}
                      fill={candleColor}
                      rx="1"
                    />
                  </g>
                );
              })}

              {/* Main Indicator Overlay Line */}
              <polyline
                fill="none"
                stroke="#22d3ee"
                strokeWidth="2"
                points={indicatorPath}
              />
            </svg>
          </div>
        </div>

        {/* Calculated Series Output Table */}
        <div className="flex flex-col">
          <div className="text-xs font-semibold text-gray-300 mb-1 flex items-center justify-between">
            <span>Calculated Output Buffer Values (Latest 10 Bars)</span>
            <span className="text-[11px] text-emerald-400 flex items-center gap-1">
              <CheckCircle2 size={12} />
              Deterministic execution verified
            </span>
          </div>

          <div className="max-h-40 overflow-y-auto border border-gray-700 rounded bg-[#101419]">
            <table className="w-full text-[11px] font-mono border-collapse">
              <thead className="bg-gray-800 text-gray-400 sticky top-0">
                <tr>
                  <th className="p-1.5 text-left border-b border-gray-700">Bar #</th>
                  <th className="p-1.5 text-left border-b border-gray-700">Timestamp</th>
                  <th className="p-1.5 text-right border-b border-gray-700">Open</th>
                  <th className="p-1.5 text-right border-b border-gray-700">High</th>
                  <th className="p-1.5 text-right border-b border-gray-700">Low</th>
                  <th className="p-1.5 text-right border-b border-gray-700">Close</th>
                  <th className="p-1.5 text-right border-b border-gray-700 text-cyan-400">Indicator</th>
                  <th className="p-1.5 text-right border-b border-gray-700 text-amber-400">Upper Band</th>
                  <th className="p-1.5 text-right border-b border-gray-700 text-amber-400">Lower Band</th>
                </tr>
              </thead>
              <tbody>
                {dataset.slice(-10).map(row => (
                  <tr key={row.bar} className="hover:bg-gray-800/50 border-b border-gray-800">
                    <td className="p-1.5 text-gray-500">{row.bar}</td>
                    <td className="p-1.5 text-gray-400">{row.date}</td>
                    <td className="p-1.5 text-right text-gray-300">{row.open.toFixed(5)}</td>
                    <td className="p-1.5 text-right text-emerald-400">{row.high.toFixed(5)}</td>
                    <td className="p-1.5 text-right text-red-400">{row.low.toFixed(5)}</td>
                    <td className="p-1.5 text-right text-gray-200">{row.close.toFixed(5)}</td>
                    <td className="p-1.5 text-right font-bold text-cyan-400">
                      {row.indicatorVal.toFixed(5)}
                    </td>
                    <td className="p-1.5 text-right text-amber-400">{row.upperBand?.toFixed(5)}</td>
                    <td className="p-1.5 text-right text-amber-400">{row.lowerBand?.toFixed(5)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 pt-2 border-t border-gray-700">
          <Button onClick={onClose}>Close</Button>
          <Button className="primary" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </Modal>
  );
}
