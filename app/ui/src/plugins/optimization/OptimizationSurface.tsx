import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import {
  Rotate3d,
  Layers,
  Activity,
  Sliders,
  Maximize2,
  CheckCircle2,
  AlertTriangle,
  Info,
  RefreshCw,
} from 'lucide-react';
import type { SurfacePoint, PlateauCluster } from '../../app/types';
import { generateOptimizationGrid, projectCoordinate } from './optimizationSurfaceLogic';

interface OptimizationSurfaceProps {
  strategyName?: string;
  initialXParam?: string;
  initialYParam?: string;
  initialZMetric?: string;
}

export const OptimizationSurface: React.FC<OptimizationSurfaceProps> = ({
  strategyName = 'Strategy 1.0',
  initialXParam = 'FastPeriod',
  initialYParam = 'SlowPeriod',
  initialZMetric = 'Net Profit',
}) => {
  const [paramX, setParamX] = useState<string>(initialXParam);
  const [paramY, setParamY] = useState<string>(initialYParam);
  const [metricZ, setMetricZ] = useState<string>(initialZMetric);
  const [displayMode, setDisplayMode] = useState<'3d' | 'contour' | 'scatter'>('3d');

  // 3D Orbit & Perspective state
  const [rotX, setRotX] = useState<number>(35); // Elevation
  const [rotY, setRotY] = useState<number>(45); // Azimuth
  const [zoom, setZoom] = useState<number>(1.0);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [hoveredPoint, setHoveredPoint] = useState<SurfacePoint | null>(null);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // Available parameters and metrics
  const availableParams = ['FastPeriod', 'SlowPeriod', 'ATRPeriod', 'StopLoss', 'TargetMultiplier'];
  const availableMetrics = ['Net Profit', 'Profit Factor', 'Sharpe Ratio', 'Return / DD'];

  // Generate 2D grid matrix of surface points
  const gridSize = 15;
  const { points, grid, clusters, stats } = useMemo(() => {
    return generateOptimizationGrid(paramX, paramY, metricZ, gridSize);
  }, [gridSize, paramX, paramY, metricZ]);


  // Color mapping helper based on normalized height
  const getColor = useCallback((z: number, minZ: number, maxZ: number) => {
    const range = maxZ - minZ || 1;
    const t = Math.max(0, Math.min(1, (z - minZ) / range));

    // Colormap from cool indigo/cyan -> warm emerald -> yellow -> coral/rose
    let r = 0;
    let g = 0;
    let b = 0;

    if (t < 0.3) {
      // Deep indigo to teal
      const sub = t / 0.3;
      r = Math.round(30 + sub * 20);
      g = Math.round(50 + sub * 130);
      b = Math.round(180 + sub * 40);
    } else if (t < 0.7) {
      // Teal to emerald
      const sub = (t - 0.3) / 0.4;
      r = Math.round(50 + sub * 120);
      g = Math.round(180 + sub * 40);
      b = Math.round(220 - sub * 150);
    } else {
      // Emerald to orange/coral
      const sub = (t - 0.7) / 0.3;
      r = Math.round(170 + sub * 85);
      g = Math.round(220 - sub * 130);
      b = Math.round(70 - sub * 40);
    }

    return `rgba(${r}, ${g}, ${b}, 0.85)`;
  }, []);

  // HTML5 Canvas 3D isometric/perspective projection renderer
  const renderCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    const minZ = Math.min(...points.map((p) => p.z));
    const maxZ = Math.max(...points.map((p) => p.z));
    const rangeZ = maxZ - minZ || 1;

    // Convert angles to radians
    const radX = (rotX * Math.PI) / 180;
    const radY = (rotY * Math.PI) / 180;

    const cosX = Math.cos(radX);
    const sinX = Math.sin(radX);
    const cosY = Math.cos(radY);
    const sinY = Math.sin(radY);

    const centerX = width / 2;
    const centerY = height / 2 + 30;
    const scale = 14 * zoom;

    // Project 3D coordinate (x, y, z) into 2D canvas screen space
    const project = (i: number, j: number, zVal: number) => {
      // Center grid coordinates (-gridSize/2 .. +gridSize/2)
      const cx = (i - gridSize / 2) * scale;
      const cy = (j - gridSize / 2) * scale;
      const cz = (((zVal - minZ) / rangeZ) * 120 - 60) * zoom;

      // Yaw rotation around Z axis
      const rx1 = cx * cosY - cy * sinY;
      const ry1 = cx * sinY + cy * cosY;
      const rz1 = cz;

      // Pitch rotation around X axis
      const rx2 = rx1;
      const ry2 = ry1 * cosX - rz1 * sinX;
      const rz2 = ry1 * sinX + rz1 * cosX;

      return {
        screenX: centerX + rx2,
        screenY: centerY + ry2,
        depth: rz2,
      };
    };

    if (displayMode === '3d') {
      // Collect all quads to sort painters algorithm by depth
      interface Quad {
        p1: { screenX: number; screenY: number };
        p2: { screenX: number; screenY: number };
        p3: { screenX: number; screenY: number };
        p4: { screenX: number; screenY: number };
        avgZ: number;
        depth: number;
        pt: SurfacePoint;
      }

      const quads: Quad[] = [];

      for (let i = 0; i < gridSize - 1; i++) {
        for (let j = 0; j < gridSize - 1; j++) {
          const pt1 = grid[i][j];
          const pt2 = grid[i + 1][j];
          const pt3 = grid[i + 1][j + 1];
          const pt4 = grid[i][j + 1];

          const proj1 = project(i, j, pt1.z);
          const proj2 = project(i + 1, j, pt2.z);
          const proj3 = project(i + 1, j + 1, pt3.z);
          const proj4 = project(i, j + 1, pt4.z);

          const avgZ = (pt1.z + pt2.z + pt3.z + pt4.z) / 4;
          const avgDepth = (proj1.depth + proj2.depth + proj3.depth + proj4.depth) / 4;

          quads.push({
            p1: proj1,
            p2: proj2,
            p3: proj3,
            p4: proj4,
            avgZ,
            depth: avgDepth,
            pt: pt1,
          });
        }
      }

      // Sort quads from furthest to nearest
      quads.sort((a, b) => a.depth - b.depth);

      // Draw quads
      quads.forEach((quad) => {
        ctx.beginPath();
        ctx.moveTo(quad.p1.screenX, quad.p1.screenY);
        ctx.lineTo(quad.p2.screenX, quad.p2.screenY);
        ctx.lineTo(quad.p3.screenX, quad.p3.screenY);
        ctx.lineTo(quad.p4.screenX, quad.p4.screenY);
        ctx.closePath();

        ctx.fillStyle = getColor(quad.avgZ, minZ, maxZ);
        ctx.fill();

        ctx.strokeStyle = 'rgba(15, 23, 42, 0.4)';
        ctx.lineWidth = 0.75;
        ctx.stroke();
      });

      // Highlight best plateau peak
      const best = points.reduce((prev, curr) => (curr.z > prev.z ? curr : prev), points[0]);
      if (best) {
        const bestI = Math.round(((best.x - 5) / (50 - 5)) * (gridSize - 1));
        const bestJ = Math.round(((best.y - 20) / (120 - 20)) * (gridSize - 1));
        const bestProj = project(bestI, bestJ, best.z);

        ctx.beginPath();
        ctx.arc(bestProj.screenX, bestProj.screenY, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#fbbf24';
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        ctx.fillStyle = '#ffffff';
        ctx.font = '10px monospace';
        ctx.fillText(`Peak: ${best.z}`, bestProj.screenX + 8, bestProj.screenY - 4);
      }
    } else if (displayMode === 'contour') {
      // 2D Contour Heatmap
      const cellW = (width - 80) / gridSize;
      const cellH = (height - 80) / gridSize;
      for (let i = 0; i < gridSize; i++) {
        for (let j = 0; j < gridSize; j++) {
          const pt = grid[i][j];
          const x = 50 + i * cellW;
          const y = 40 + (gridSize - 1 - j) * cellH;

          ctx.fillStyle = getColor(pt.z, minZ, maxZ);
          ctx.fillRect(x, y, cellW - 1, cellH - 1);
        }
      }

      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px sans-serif';
      ctx.fillText(`${paramX} →`, width / 2 - 20, height - 10);
      ctx.save();
      ctx.translate(18, height / 2 + 20);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText(`${paramY} →`, 0, 0);
      ctx.restore();
    } else {
      // 2D Scatter Dot
      points.forEach((pt) => {
        const xNorm = (pt.x - 5) / 45;
        const yNorm = (pt.y - 20) / 100;
        const cx = 60 + xNorm * (width - 120);
        const cy = height - 50 - yNorm * (height - 100);

        ctx.beginPath();
        ctx.arc(cx, cy, 4, 0, Math.PI * 2);
        ctx.fillStyle = getColor(pt.z, minZ, maxZ);
        ctx.fill();
      });
    }
  }, [points, grid, rotX, rotY, zoom, displayMode, getColor, paramX, paramY]);

  useEffect(() => {
    renderCanvas();
  }, [renderCanvas]);

  // Mouse drag handlers for 3D rotation
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging) return;
    const deltaX = e.clientX - dragStart.x;
    const deltaY = e.clientY - dragStart.y;

    setRotY((prev) => (prev + deltaX * 0.8) % 360);
    setRotX((prev) => Math.max(5, Math.min(85, prev - deltaY * 0.8)));
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div className="flex flex-col h-full bg-slate-950 text-slate-100 rounded-xl overflow-hidden border border-slate-800">
      {/* Top Toolbar matching SQX ResultsOptimizationProfile */}
      <div className="h-14 px-5 bg-slate-900 border-b border-slate-800 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Rotate3d className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              Optimization Profile & 3D Surface
              <span className="text-[10px] font-normal px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                {strategyName}
              </span>
            </h2>
            <p className="text-[11px] text-slate-400">Interactive parameter landscape & plateau stability analysis</p>
          </div>
        </div>

        {/* Parameter & Metric Selectors */}
        <div className="flex items-center gap-3 text-xs">
          <div className="flex items-center gap-1.5 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700">
            <span className="text-slate-400">X-Axis:</span>
            <select
              value={paramX}
              onChange={(e) => setParamX(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer font-medium"
            >
              {availableParams.map((p) => (
                <option key={p} value={p} className="bg-slate-800">{p}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700">
            <span className="text-slate-400">Y-Axis:</span>
            <select
              value={paramY}
              onChange={(e) => setParamY(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none cursor-pointer font-medium"
            >
              {availableParams.map((p) => (
                <option key={p} value={p} className="bg-slate-800">{p}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 bg-slate-800/80 px-2.5 py-1 rounded border border-slate-700">
            <span className="text-slate-400">Z-Metric:</span>
            <select
              value={metricZ}
              onChange={(e) => setMetricZ(e.target.value)}
              className="bg-transparent text-indigo-300 focus:outline-none cursor-pointer font-medium"
            >
              {availableMetrics.map((m) => (
                <option key={m} value={m} className="bg-slate-800">{m}</option>
              ))}
            </select>
          </div>

          {/* Display Mode Toggle */}
          <div className="flex items-center border border-slate-700 rounded overflow-hidden">
            <button
              onClick={() => setDisplayMode('3d')}
              className={`px-2.5 py-1 text-xs transition ${
                displayMode === '3d' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              3D Surface
            </button>
            <button
              onClick={() => setDisplayMode('contour')}
              className={`px-2.5 py-1 text-xs transition ${
                displayMode === 'contour' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Heatmap
            </button>
            <button
              onClick={() => setDisplayMode('scatter')}
              className={`px-2.5 py-1 text-xs transition ${
                displayMode === 'scatter' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              Scatter
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: SQX Stability & % Profitable Optimizations Card */}
        <div className="w-80 border-r border-slate-800 bg-slate-900/50 p-4 flex flex-col gap-4 overflow-y-auto shrink-0">
          {/* % of Profitable Optimizations Card (matching SQX optimizationProfile.html) */}
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                % of Profitable Optimizations
              </span>
              <Info className="w-3.5 h-3.5 text-slate-500" />
            </div>

            <table className="w-full text-xs">
              <tbody className="divide-y divide-slate-800/60">
                <tr className="py-1.5 flex justify-between">
                  <td className="text-slate-400">Total optimizations</td>
                  <td className="font-mono text-slate-200 font-semibold">{stats.totalSimulations}</td>
                </tr>
                <tr className="py-1.5 flex justify-between">
                  <td className="text-slate-400">Profitable optimizations</td>
                  <td className="font-mono text-emerald-400 font-semibold">{stats.profitablePct}% ({stats.profitableCount})</td>
                </tr>
                <tr className="py-1.5 flex justify-between">
                  <td className="text-slate-400">Losing optimizations</td>
                  <td className="font-mono text-rose-400 font-semibold">{stats.losingPct}% ({stats.losingCount})</td>
                </tr>
                <tr className="py-1.5 flex justify-between">
                  <td className="text-slate-400">Zero profit</td>
                  <td className="font-mono text-slate-500">{stats.zeroPct}% ({stats.zeroCount})</td>
                </tr>
              </tbody>
            </table>

            {/* Check Rule from SQX: Check - more than 60% must be profitable */}
            <div className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
              stats.isPass ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
            }`}>
              <div className="flex items-center gap-2">
                {stats.isPass ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <AlertTriangle className="w-4 h-4 text-rose-400" />}
                <span>&gt; 60% Profitable Rule</span>
              </div>
              <span className="font-bold uppercase tracking-wide">{stats.isPass ? 'PASSED' : 'FAILED'}</span>
            </div>
          </div>

          {/* Plateau Clusters & Sensitivity Detection */}
          <div className="rounded-xl bg-slate-900 border border-slate-800 p-4 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Robustness Plateaus
              </span>
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
            </div>

            <div className="space-y-2.5">
              {clusters.map((c) => (
                <div key={c.id} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-200">{c.id === 'cluster-1' ? 'Primary Robust Plateau' : 'Secondary Cluster'}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      c.stabilityScore >= 80 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-amber-500/20 text-amber-300'
                    }`}>
                      {c.stabilityScore}/100
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-400 space-y-0.5">
                    <div>{paramX} range: <strong className="text-slate-200">{c.rangeX[0]} - {c.rangeX[1]}</strong></div>
                    <div>{paramY} range: <strong className="text-slate-200">{c.rangeY[0]} - {c.rangeY[1]}</strong></div>
                    <div>Avg {metricZ}: <strong className="text-indigo-400">{c.averageMetric}</strong> (σ {c.standardDeviation})</div>
                    <div>Profitable: <strong className="text-emerald-400">{c.profitablePercentage}%</strong></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Legend Strip */}
          <div className="p-3 rounded-lg bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400 space-y-2">
            <span className="font-medium text-slate-300">Surface Height Colormap</span>
            <div className="h-3 rounded-full bg-gradient-to-r from-blue-600 via-teal-400 via-emerald-400 to-amber-500" />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>Low / Negative</span>
              <span>Average</span>
              <span>Peak Profit</span>
            </div>
          </div>
        </div>

        {/* Right Side: Interactive 3D Canvas Projection */}
        <div className="flex-1 relative flex flex-col items-center justify-center p-4 bg-slate-950">
          <canvas
            ref={canvasRef}
            width={740}
            height={480}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            className="cursor-grab active:cursor-grabbing max-w-full max-h-full rounded-lg shadow-inner"
          />

          {/* 3D Orbit Controls Overlay */}
          <div className="absolute bottom-6 right-6 flex items-center gap-2 bg-slate-900/90 backdrop-blur border border-slate-800 px-3 py-1.5 rounded-lg text-xs text-slate-300 shadow-lg">
            <span className="text-slate-400">Azimuth: <strong className="text-slate-200 font-mono">{Math.round(rotY)}°</strong></span>
            <span className="text-slate-400">Elevation: <strong className="text-slate-200 font-mono">{Math.round(rotX)}°</strong></span>
            <button
              onClick={() => {
                setRotX(35);
                setRotY(45);
                setZoom(1.0);
              }}
              className="ml-2 px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-[11px] text-slate-200 flex items-center gap-1 transition"
            >
              <RefreshCw className="w-3 h-3" /> Reset View
            </button>
          </div>

          {/* Hint tag */}
          <div className="absolute top-6 left-6 text-xs text-slate-500 pointer-events-none">
            Click and drag to rotate surface • Pitch &amp; Yaw orbit
          </div>
        </div>
      </div>
    </div>
  );
};
