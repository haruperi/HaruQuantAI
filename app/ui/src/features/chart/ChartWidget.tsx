'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  apiClients,
  BAR_TIMEFRAMES,
  unwrapData,
  type BarSeries,
  type BarTimeframe,
  type IndicatorSeries,
  type IndicatorSpec,
  type MarketRow,
} from '../../clients';
import { useTradingStore } from '../../store/useTradingStore';
import { useWorkspaceStore } from '../workspaces';
import type { OrderSide, Product } from '../../types/market';
import {
  filterSymbols,
  loadSymbolUniverse,
  resolveSourceSymbol,
} from '../watchlists/symbolUniverse';
import {
  PlusCircle,
  Slash,
  Minus,
  Type,
  Smile,
  Trash2,
  Settings,
  Maximize2,
  Camera,
  RotateCcw,
  RotateCw,
  Search,
  SlidersHorizontal,
  Ruler,
  Magnet,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  Calendar,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  CandlestickChart,
  LineChart as LineChartIcon,
  BarChart2,
  Activity,
  Star,
  X,
  Grid,
  TrendingUp,
  TrendingDown,
  Check,
  Crosshair,
  MousePointer,
  Eraser,
  ZoomIn,
  Link,
  Paintbrush,
  Layers,
  Share2,
  CircleDot,
  GripVertical,
  MoreHorizontal
} from 'lucide-react';

const renderChartIcon = (type: string) => {
  if (['Bars', 'HLC bars'].includes(type)) return <BarChart2 size={14} />;
  if (['Line', 'Line with markers', 'Step line', 'Kagi'].includes(type)) return <LineChartIcon size={14} />;
  if (['Area', 'HLC area', 'Baseline'].includes(type)) return <Activity size={14} />;
  if (['Columns'].includes(type)) return <Grid size={14} />;
  if (['Renko', 'Line break', 'Point & figure'].includes(type)) return <TrendingUp size={14} />;
  return <CandlestickChart size={14} />;
};

const FREEHAND_TOOLS = new Set(['brush', 'highlighter', 'path', 'polyline', 'curve', 'doublecurve']);
const ARROW_TOOLS = new Set(['arrowmarker', 'arrowline', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright']);
const PATTERN_TOOLS = new Set([
  'xabcd', 'cypher', 'abcd', 'headandshoulders', 'trianglepattern', 'threedrives',
  'elliott12345', 'elliottabc', 'elliottabcde', 'elliottwxy', 'elliottwxyxz'
]);
const TEXT_TOOLS = new Set([
  'text', 'anchoredtext', 'note', 'pricenote', 'callout', 'comment', 'pricelabel',
  'signpost', 'flagmark'
]);

const drawArrowHead = (ctx: CanvasRenderingContext2D, fromX: number, fromY: number, toX: number, toY: number, color: string, size = 9) => {
  const angle = Math.atan2(toY - fromY, toX - fromX);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(toX, toY);
  ctx.lineTo(toX - size * Math.cos(angle - Math.PI / 6), toY - size * Math.sin(angle - Math.PI / 6));
  ctx.lineTo(toX - size * Math.cos(angle + Math.PI / 6), toY - size * Math.sin(angle + Math.PI / 6));
  ctx.closePath();
  ctx.fill();
};

const drawPolyline = (ctx: CanvasRenderingContext2D, points: { x: number; y: number }[] = []) => {
  if (points.length < 2) return;
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  points.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
  ctx.stroke();
};

const renderDrawingShape = (ctx: CanvasRenderingContext2D, shape: any, chartWidth: number, chartHeight: number, _priceMin: number, priceRange: number, priceMax: number, symbolDigits: number = 2) => {
  if (!shape) return;
  const { tool, startX, startY, endX, endY, text, emoji, points = [] } = shape;
  const color = shape.color || '#3cc8ff';
  const strokeWidth = shape.lineWidth || 2;
  const isDashed = shape.lineStyle === 'dashed';

  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = strokeWidth;
  if (isDashed) ctx.setLineDash([6, 6]);

  if (tool === 'trendline' || tool === 'select' || !tool) {
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.arc(startX, startY, strokeWidth + 2, 0, 2 * Math.PI);
    ctx.arc(endX, endY, strokeWidth + 2, 0, 2 * Math.PI);
    ctx.fill();
  } else if (tool === 'extendedline') {
    const dx = endX - startX || 1;
    const dy = endY - startY;
    ctx.beginPath();
    ctx.moveTo(startX - dx * 100, startY - dy * 100);
    ctx.lineTo(endX + dx * 100, endY + dy * 100);
    ctx.stroke();
  } else if (tool === 'ray' || tool === 'horizontalray') {
    const dx = endX - startX || 1;
    const dy = tool === 'horizontalray' ? 0 : endY - startY;
    const scale = (chartWidth - startX) / dx;
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(chartWidth, startY + dy * scale);
    ctx.stroke();
  } else if (ARROW_TOOLS.has(tool)) {
    let targetX = endX;
    let targetY = endY;
    if (tool === 'arrowup') targetY = startY - Math.max(24, Math.abs(endY - startY));
    if (tool === 'arrowdown') targetY = startY + Math.max(24, Math.abs(endY - startY));
    if (tool === 'arrowleft') targetX = startX - Math.max(24, Math.abs(endX - startX));
    if (tool === 'arrowright') targetX = startX + Math.max(24, Math.abs(endX - startX));
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(targetX, targetY);
    ctx.stroke();
    drawArrowHead(ctx, startX, startY, targetX, targetY, color, tool === 'arrowmarker' ? 12 : 9);
  } else if (tool === 'infoline' || tool === 'trendangle') {
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();
    const priceStart = priceMax - (startY / chartHeight) * priceRange;
    const priceEnd = priceMax - (endY / chartHeight) * priceRange;
    const diff = priceEnd - priceStart;
    const pct = (diff / priceStart) * 100;
    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;

    ctx.fillStyle = '#112b4a';
    ctx.fillRect(midX - 50, midY - 14, 100, 20);
    ctx.strokeStyle = color;
    ctx.strokeRect(midX - 50, midY - 14, 100, 20);
    ctx.fillStyle = diff >= 0 ? '#00e473' : '#ff003d';
    ctx.font = 'bold 10px "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${diff >= 0 ? '+' : ''}${diff.toFixed(symbolDigits)} (${pct.toFixed(2)}%)`, midX, midY + 1);
  } else if (tool === 'horizontalline') {
    ctx.beginPath();
    ctx.moveTo(0, startY);
    ctx.lineTo(chartWidth, startY);
    ctx.stroke();
  } else if (tool === 'verticalline') {
    ctx.beginPath();
    ctx.moveTo(startX, 0);
    ctx.lineTo(startX, chartHeight);
    ctx.stroke();
  } else if (tool === 'crossline') {
    ctx.beginPath();
    ctx.moveTo(0, startY);
    ctx.lineTo(chartWidth, startY);
    ctx.moveTo(startX, 0);
    ctx.lineTo(startX, chartHeight);
    ctx.stroke();
  } else if (['parallelchannel', 'flattopbottom', 'regressiontrend', 'disjointchannel'].includes(tool)) {
    const h = endY - startY;
    ctx.fillStyle = `${color}22`;
    ctx.fillRect(startX, startY, endX - startX, h);
    ctx.strokeRect(startX, startY, endX - startX, h);
    ctx.beginPath();
    if (tool === 'flattopbottom') {
      ctx.moveTo(startX, startY + h / 2);
      ctx.lineTo(endX, startY + h / 2);
    } else {
      ctx.moveTo(startX, startY + h * 0.25);
      ctx.lineTo(endX, startY + h * 0.75);
      ctx.moveTo(startX, startY + h * 0.5);
      ctx.lineTo(endX, startY + h * 0.5);
    }
    ctx.stroke();
  } else if (['pitchfork', 'schiffpitchfork', 'modifiedschiff', 'insidepitchfork'].includes(tool)) {
    const midY = (startY + endY) / 2;
    const spread = Math.max(22, Math.abs(endY - startY) / 2);
    const offset = tool === 'schiffpitchfork' ? spread * 0.35 : tool === 'modifiedschiff' ? -spread * 0.35 : 0;
    [-1, 0, 1].forEach((lane) => {
      ctx.beginPath();
      ctx.moveTo(startX, startY + offset);
      ctx.lineTo(endX, midY + lane * spread);
      ctx.stroke();
    });
  } else if (tool === 'fib' || tool === 'fibextension') {
    const levels = [
      { ratio: 0, color: '#718294', bg: 'rgba(156, 39, 176, 0.18)' },
      { ratio: 0.236, color: '#ff4975', bg: 'rgba(255, 152, 0, 0.18)' },
      { ratio: 0.382, color: '#ff9800', bg: 'rgba(0, 228, 115, 0.18)' },
      { ratio: 0.5, color: '#00e473', bg: 'rgba(60, 200, 255, 0.18)' },
      { ratio: 0.618, color: '#3cc8ff', bg: 'rgba(0, 110, 182, 0.18)' },
      { ratio: 0.786, color: '#9c27b0', bg: 'rgba(8, 29, 55, 0.4)' },
      { ratio: 1, color: '#718294', bg: 'transparent' }
    ];
    const dy = endY - startY;

    // Draw Shaded Bands between Levels
    for (let i = 0; i < levels.length - 1; i++) {
      const y1 = startY + dy * levels[i].ratio;
      const y2 = startY + dy * levels[i + 1].ratio;
      const bandTop = Math.min(y1, y2);
      const bandH = Math.abs(y2 - y1);
      ctx.fillStyle = levels[i].bg;
      ctx.fillRect(startX, bandTop, endX - startX, bandH);
    }

    // Draw Dashed Trend Line between Start and End points
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = color;
    ctx.lineWidth = strokeWidth;
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw Level Lines and Price Labels
    levels.forEach((lvl) => {
      const ly = startY + dy * lvl.ratio;
      ctx.strokeStyle = lvl.color;
      ctx.lineWidth = strokeWidth;
      ctx.beginPath();
      ctx.moveTo(startX, ly);
      ctx.lineTo(endX, ly);
      ctx.stroke();

      const lvlPrice = priceMax - (ly / chartHeight) * priceRange;
      ctx.fillStyle = lvl.color;
      ctx.font = 'bold 10px "Segoe UI", Roboto, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(`${lvl.ratio} (${lvlPrice.toFixed(symbolDigits)})`, startX + 4, ly - 3);
    });

    // Draw Blue Circular Anchor Dots
    ctx.fillStyle = color;
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(startX, startY, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(endX, endY, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
  } else if (['fibchannel', 'fibtimezone', 'fibfan', 'trendbasedfibtime', 'fibcircles', 'fibspiral', 'fibarcs', 'fibwedge', 'pitchfan'].includes(tool)) {
    const dx = endX - startX || 80;
    const dy = endY - startY || 80;
    const ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1];
    if (tool === 'fibtimezone' || tool === 'trendbasedfibtime') {
      [0, 1, 2, 3, 5, 8, 13].forEach((ratio) => {
        const x = startX + (dx / 3) * ratio;
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, chartHeight);
        ctx.stroke();
      });
    } else if (tool === 'fibcircles' || tool === 'fibarcs' || tool === 'fibspiral') {
      const radius = Math.hypot(dx, dy);
      ratios.slice(1).forEach((ratio, index) => {
        ctx.beginPath();
        if (tool === 'fibarcs') {
          ctx.arc(startX, startY, radius * ratio, -Math.PI / 2, Math.PI / 2);
        } else if (tool === 'fibspiral') {
          ctx.arc(startX, startY, radius * ratio, index * 0.65, index * 0.65 + Math.PI * 1.3);
        } else {
          ctx.ellipse(startX, startY, Math.abs(dx) * ratio, Math.abs(dy) * ratio, 0, 0, Math.PI * 2);
        }
        ctx.stroke();
      });
    } else if (tool === 'fibwedge') {
      ratios.slice(1).forEach((ratio) => {
        ctx.beginPath();
        ctx.arc(startX, startY, Math.hypot(dx, dy) * ratio, 0, Math.atan2(dy, dx));
        ctx.stroke();
      });
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, startY);
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.stroke();
    } else {
      ratios.forEach((ratio) => {
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, startY + dy * ratio);
        ctx.stroke();
      });
    }
  } else if (['gannbox', 'gannsquarefixed', 'gannsquare'].includes(tool)) {
    ctx.strokeRect(startX, startY, endX - startX, endY - startY);
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(endX, endY);
    ctx.moveTo(endX, startY);
    ctx.lineTo(startX, endY);
    ctx.stroke();
  } else if (tool === 'gannfan') {
    [0.125, 0.25, 0.5, 1, 2, 4, 8].forEach((ratio) => {
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, startY + (endY - startY) * ratio);
      ctx.stroke();
    });
  } else if (tool === 'longposition' || tool === 'shortposition') {
    const isLong = tool === 'longposition';
    const midY = (startY + endY) / 2;
    const topH = Math.abs(midY - startY) || 30;
    const botH = Math.abs(endY - midY) || 30;

    ctx.fillStyle = 'rgba(0, 228, 115, 0.25)';
    ctx.fillRect(startX, isLong ? startY : midY, endX - startX || 120, isLong ? topH : botH);
    ctx.strokeStyle = '#00e473';
    ctx.lineWidth = strokeWidth;
    ctx.strokeRect(startX, isLong ? startY : midY, endX - startX || 120, isLong ? topH : botH);

    ctx.fillStyle = 'rgba(255, 0, 61, 0.25)';
    ctx.fillRect(startX, isLong ? midY : startY, endX - startX || 120, isLong ? botH : topH);
    ctx.strokeStyle = '#ff003d';
    ctx.strokeRect(startX, isLong ? midY : startY, endX - startX || 120, isLong ? botH : topH);

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 10px "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`${isLong ? 'Long' : 'Short'} Position (R/R: 2.00)`, startX + (endX - startX || 120) / 2, midY + 3);
  } else if (['forecast', 'barspattern', 'ghostfeed', 'projection', 'anchoredvwap', 'fixedrangevolumeprofile'].includes(tool)) {
    const width = endX - startX || 120;
    const height = endY - startY || 70;
    if (tool === 'fixedrangevolumeprofile') {
      const bars = [0.45, 0.72, 0.92, 0.65, 1, 0.58, 0.35];
      bars.forEach((ratio, index) => {
        const barHeight = Math.max(4, Math.abs(height) / bars.length - 2);
        const y = startY + (height / bars.length) * index;
        ctx.fillStyle = index % 2 ? 'rgba(255,73,117,0.28)' : 'rgba(60,200,255,0.28)';
        ctx.fillRect(startX, y, width * ratio, barHeight);
      });
      ctx.strokeRect(startX, startY, width, height);
    } else if (tool === 'anchoredvwap') {
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.stroke();
      ctx.setLineDash([4, 4]);
      [-16, 16].forEach((offset) => {
        ctx.beginPath();
        ctx.moveTo(startX, startY + offset);
        ctx.lineTo(endX, endY + offset);
        ctx.stroke();
      });
      ctx.setLineDash([]);
    } else {
      const projectionPoints = [
        { x: startX, y: startY },
        { x: startX + width * 0.25, y: startY + height * 0.65 },
        { x: startX + width * 0.5, y: startY + height * 0.25 },
        { x: startX + width * 0.75, y: startY + height * 0.8 },
        { x: endX, y: endY }
      ];
      if (tool === 'ghostfeed') ctx.setLineDash([6, 5]);
      drawPolyline(ctx, projectionPoints);
      ctx.setLineDash([]);
      drawArrowHead(ctx, projectionPoints[3].x, projectionPoints[3].y, endX, endY, color);
    }
  } else if (['pricerange', 'daterange', 'dateandpricerange'].includes(tool)) {
    const w = endX - startX;
    const h = endY - startY;
    ctx.fillStyle = `${color}22`;
    ctx.fillRect(startX, startY, w, h);
    ctx.strokeRect(startX, startY, w, h);
    const priceStart = priceMax - (startY / chartHeight) * priceRange;
    const priceEnd = priceMax - (endY / chartHeight) * priceRange;
    const bars = Math.max(1, Math.round(Math.abs(w) / 12));
    const label = tool === 'pricerange'
      ? `${(priceEnd - priceStart).toFixed(symbolDigits)} (${(((priceEnd - priceStart) / priceStart) * 100).toFixed(2)}%)`
      : tool === 'daterange'
        ? `${bars} bars`
        : `${bars} bars, ${(priceEnd - priceStart).toFixed(symbolDigits)}`;
    ctx.fillStyle = '#112b4a';
    ctx.fillRect((startX + endX) / 2 - 55, (startY + endY) / 2 - 12, 110, 24);
    ctx.fillStyle = '#ffffff';
    ctx.font = '600 10px "Roboto Mono", monospace';
    ctx.textAlign = 'center';
    ctx.fillText(label, (startX + endX) / 2, (startY + endY) / 2 + 3);
  } else if (PATTERN_TOOLS.has(tool)) {
    const width = endX - startX || 150;
    const height = endY - startY || 90;
    const definitions = {
      headandshoulders: [[0, .75], [.18, .35], [.34, .72], [.5, .05], [.66, .72], [.82, .35], [1, .75]],
      trianglepattern: [[0, .2], [.2, .8], [.4, .3], [.6, .7], [.8, .4], [1, .55]],
      elliott12345: [[0, .8], [.2, .25], [.38, .58], [.62, .08], [.78, .48], [1, 0]],
      elliottabc: [[0, .2], [.38, .85], [.68, .4], [1, .9]],
      elliottabcde: [[0, .15], [.2, .8], [.4, .25], [.6, .72], [.8, .38], [1, .62]],
      elliottwxy: [[0, .2], [.25, .8], [.5, .38], [.75, .88], [1, .45]],
      elliottwxyxz: [[0, .15], [.18, .8], [.36, .35], [.54, .82], [.72, .4], [.86, .75], [1, .5]],
      threedrives: [[0, .75], [.16, .2], [.32, .72], [.5, .08], [.66, .65], [.84, 0], [1, .55]],
      default: [[0, .72], [.2, .12], [.4, .62], [.62, .25], [.8, .8], [1, .18]]
    };
    const normalized = (definitions as Record<string, number[][]>)[tool] || definitions.default;
    const patternPoints = normalized.map(([x, y]: number[]) => ({ x: startX + width * x, y: startY + height * y }));
    drawPolyline(ctx, patternPoints);
    ctx.fillStyle = color;
    ctx.font = '600 10px "Roboto Mono", monospace';
    patternPoints.forEach((point: { x: number; y: number }, index: number) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillText(String(index + 1), point.x + 4, point.y - 4);
    });
  } else if (tool === 'cycliclines' || tool === 'timecycles') {
    const step = Math.max(18, Math.abs(endX - startX) / 6);
    for (let x = Math.min(startX, endX); x <= Math.max(startX, endX); x += step) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, chartHeight);
      ctx.stroke();
    }
  } else if (tool === 'sineline') {
    const width = endX - startX || 160;
    const amplitude = Math.max(15, Math.abs(endY - startY) / 2);
    ctx.beginPath();
    for (let i = 0; i <= 80; i++) {
      const x = startX + (width * i) / 80;
      const y = startY + Math.sin((i / 80) * Math.PI * 4) * amplitude;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
  } else if (FREEHAND_TOOLS.has(tool)) {
    if (tool === 'highlighter') {
      ctx.globalAlpha = 0.35;
      ctx.lineWidth = Math.max(8, strokeWidth * 5);
    }
    drawPolyline(ctx, points.length > 1 ? points : [{ x: startX, y: startY }, { x: endX, y: endY }]);
    ctx.globalAlpha = 1;
  } else if (tool === 'rectangle' || tool === 'rotatedrectangle') {
    ctx.fillStyle = `${color}22`;
    if (tool === 'rotatedrectangle') {
      const cx = (startX + endX) / 2;
      const cy = (startY + endY) / 2;
      const width = Math.hypot(endX - startX, endY - startY);
      const height = Math.max(34, width * 0.45);
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(Math.atan2(endY - startY, endX - startX));
      ctx.fillRect(-width / 2, -height / 2, width, height);
      ctx.strokeRect(-width / 2, -height / 2, width, height);
      ctx.restore();
    } else {
      ctx.fillRect(startX, startY, endX - startX, endY - startY);
      ctx.strokeRect(startX, startY, endX - startX, endY - startY);
    }
  } else if (tool === 'circle' || tool === 'ellipse') {
    const rx = Math.abs(endX - startX) / 2;
    const ry = tool === 'circle' ? rx : Math.abs(endY - startY) / 2;
    ctx.fillStyle = `${color}22`;
    ctx.beginPath();
    ctx.ellipse(startX + rx, startY + ry, rx || 10, ry || 10, 0, 0, 2 * Math.PI);
    ctx.fill();
    ctx.stroke();
  } else if (tool === 'triangle') {
    ctx.fillStyle = `${color}22`;
    ctx.beginPath();
    ctx.moveTo((startX + endX) / 2, startY);
    ctx.lineTo(endX, endY);
    ctx.lineTo(startX, endY);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  } else if (tool === 'arc') {
    const cx = (startX + endX) / 2;
    const cy = (startY + endY) / 2;
    ctx.beginPath();
    ctx.arc(cx, cy, Math.max(12, Math.hypot(endX - startX, endY - startY) / 2), Math.PI, 2 * Math.PI);
    ctx.stroke();
  } else if (TEXT_TOOLS.has(tool)) {
    ctx.font = 'bold 11px "Segoe UI", Roboto, sans-serif';
    const labels = {
      anchoredtext: 'Anchored Text', note: 'Trading Note', pricenote: 'Price Note',
      callout: 'Callout', comment: 'Comment', pricelabel: 'Price Label',
      signpost: 'Signpost', flagmark: 'Flag'
    };
    const label = text || (labels as Record<string, string>)[tool] || 'Text';
    const labelWidth = Math.max(72, ctx.measureText(label).width + 18);
    ctx.fillStyle = '#112b4a';
    ctx.fillRect(startX - 5, startY - 14, labelWidth, 24);
    ctx.strokeStyle = color;
    ctx.strokeRect(startX - 5, startY - 14, labelWidth, 24);
    if (tool === 'callout' || tool === 'signpost' || tool === 'flagmark') {
      ctx.beginPath();
      ctx.moveTo(startX, startY + 10);
      ctx.lineTo(endX, endY);
      ctx.stroke();
    }
    ctx.fillStyle = color;
    ctx.textAlign = 'left';
    ctx.fillText(label, startX, startY + 2);
  } else if (tool === 'pin') {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(startX, startY - 7, 6, 0, 2 * Math.PI);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(startX, startY - 1);
    ctx.lineTo(startX, startY + 12);
    ctx.stroke();
  } else if (tool === 'table') {
    const width = Math.max(90, Math.abs(endX - startX));
    const height = Math.max(54, Math.abs(endY - startY));
    ctx.strokeRect(startX, startY, width, height);
    for (let i = 1; i < 3; i++) {
      ctx.beginPath(); ctx.moveTo(startX + (width * i) / 3, startY); ctx.lineTo(startX + (width * i) / 3, startY + height); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(startX, startY + (height * i) / 3); ctx.lineTo(startX + width, startY + (height * i) / 3); ctx.stroke();
    }
  } else if (tool === 'emoji' || tool === 'icon') {
    ctx.font = '22px sans-serif';
    ctx.fillText(emoji || '😊', startX, startY);
  } else if (tool === 'measure' || tool === 'pricerange' || tool === 'daterange') {
    const w = endX - startX;
    const h = endY - startY;
    ctx.fillStyle = `${color}22`;
    ctx.fillRect(startX, startY, w, h);
    ctx.strokeRect(startX, startY, w, h);

    ctx.fillStyle = '#112b4a';
    ctx.fillRect((startX + endX) / 2 - 50, (startY + endY) / 2 - 12, 100, 24);
    ctx.strokeStyle = color;
    ctx.strokeRect((startX + endX) / 2 - 50, (startY + endY) / 2 - 12, 100, 24);
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 10px "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(`14 bars, $12.50`, (startX + endX) / 2, (startY + endY) / 2 + 3);
  }

  ctx.restore();
};

export interface BarData {
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  /** ISO-8601 UTC bar-open instant exactly as the broker reported it. */
  timestamp: string;
  /** Time-axis label derived from `timestamp` for the active timeframe. */
  time: string;
  /** Count of broker bar slots missing immediately before this bar. */
  missingBarsBefore?: number;
}

export interface VisibleBarRange {
  start: number;
  end: number;
}

/** Bound chart work to the clipped viewport while retaining the newest bar. */
export function visibleBarRange(
  barCount: number,
  plotWidth: number,
  candleWidth: number,
  panOffset: number
): VisibleBarRange {
  const start = Math.max(0, Math.floor(-panOffset / candleWidth));
  const end = Math.min(barCount, Math.ceil((plotWidth - panOffset) / candleWidth));
  if (end > start) return { start, end };
  const capacity = Math.min(barCount, Math.ceil(plotWidth / candleWidth) + 1);
  return panOffset >= plotWidth
    ? { start: 0, end: capacity }
    : { start: Math.max(0, barCount - capacity), end: barCount };
}

/**
 * Timeframes the runtime broker can serve, grouped for the toolbar menu.
 *
 * These are Data's canonical keys, so the value the user picks is the value
 * sent to the broker — there is no intermediate label the backend would reject.
 */
const TIMEFRAME_LABELS: Record<BarTimeframe, string> = {
  M1: '1 minute',
  M5: '5 minutes',
  M15: '15 minutes',
  M30: '30 minutes',
  H1: '1 hour',
  H4: '4 hours',
  D1: '1 day',
  W1: '1 week',
  MN1: '1 month',
};

const TIMEFRAME_GROUPS: Record<BarTimeframe, 'MINUTES' | 'HOURS' | 'DAYS'> = {
  M1: 'MINUTES',
  M5: 'MINUTES',
  M15: 'MINUTES',
  M30: 'MINUTES',
  H1: 'HOURS',
  H4: 'HOURS',
  D1: 'DAYS',
  W1: 'DAYS',
  MN1: 'DAYS',
};

const TIMEFRAME_MENU = (['MINUTES', 'HOURS', 'DAYS'] as const).map((heading) => ({
  heading,
  items: BAR_TIMEFRAMES.filter((key) => TIMEFRAME_GROUPS[key] === heading).map((key) => ({
    key,
    label: TIMEFRAME_LABELS[key],
  })),
}));

const INTRADAY_TIMEFRAMES = new Set<BarTimeframe>(['M1', 'M5', 'M15', 'M30', 'H1', 'H4']);
const TIMEFRAME_MILLISECONDS: Record<BarTimeframe, number> = {
  M1: 60_000,
  M5: 300_000,
  M15: 900_000,
  M30: 1_800_000,
  H1: 3_600_000,
  H4: 14_400_000,
  D1: 86_400_000,
  W1: 604_800_000,
  // Month lengths vary; this is used only as a conservative discontinuity threshold.
  MN1: 2_419_200_000,
};

/**
 * Extremes of one bar field, without spreading the array into `Math.min/max`.
 *
 * A spread passes one argument per element, which overflows the call stack at
 * roughly 130k arguments — and a backtest-scale window is well past that
 * (MT5 holds 178k H1 bars for USDJPY alone), so the spread form would throw
 * before drawing a single candle.
 */
export function barExtent(
  bars: BarData[],
  from: number,
  to: number
): { min: number; max: number } {
  let min = Infinity;
  let max = -Infinity;
  for (let i = from; i < to; i++) {
    const bar = bars[i];
    if (bar.low < min) min = bar.low;
    if (bar.high > max) max = bar.high;
  }
  return { min, max };
}

/** Largest volume across a bar range, spread-free for the same reason. */
export function maxVolume(bars: BarData[], from: number, to: number): number {
  let max = 0;
  for (let i = from; i < to; i++) {
    if (bars[i].volume > max) max = bars[i].volume;
  }
  return max || 1;
}

/** Label one bar-open instant for the time axis of the active timeframe. */
function formatBarLabel(timestamp: string, timeframe: BarTimeframe): string {
  const at = new Date(timestamp);
  if (Number.isNaN(at.getTime())) return '';
  return INTRADAY_TIMEFRAMES.has(timeframe)
    ? at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
    : at.toISOString().split('T')[0];
}

/**
 * Project one broker bar series into the shape the canvas renders.
 *
 * A bar missing any OHLC value is dropped rather than defaulted: a zero close
 * would collapse the price scale and read as a real crash.
 */
export function toChartBars(series: BarSeries | null | undefined, timeframe: BarTimeframe): BarData[] {
  if (!series) return [];
  let invalidSlots = 0;
  let previousTimestamp: number | null = null;
  return series.bars.reduce<BarData[]>((rows, bar) => {
    if (
      bar.time === null ||
      bar.open === null ||
      bar.high === null ||
      bar.low === null ||
      bar.close === null
    ) {
      invalidSlots += 1;
      return rows;
    }
    const timestamp = new Date(bar.time).getTime();
    const interval = TIMEFRAME_MILLISECONDS[timeframe];
    const inferredMissing =
      previousTimestamp !== null && Number.isFinite(timestamp)
        ? Math.max(0, Math.round((timestamp - previousTimestamp) / interval) - 1)
        : 0;
    const missingBarsBefore = Math.max(invalidSlots, inferredMissing);
    rows.push({
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
      volume: bar.volume ?? 0,
      timestamp: bar.time,
      time: formatBarLabel(bar.time, timeframe),
      ...(missingBarsBefore > 0 ? { missingBarsBefore } : {}),
    });
    invalidSlots = 0;
    previousTimestamp = Number.isFinite(timestamp) ? timestamp : null;
    return rows;
  }, []);
}

const DRAWING_STORAGE_PREFIX = 'haruquantai.chart.drawings.v1';

function drawingStorageKey(symbol: string): string {
  return `${DRAWING_STORAGE_PREFIX}:${symbol}`;
}

function isStoredDrawing(value: unknown): value is Record<string, unknown> {
  if (typeof value !== 'object' || value === null) return false;
  const drawing = value as Record<string, unknown>;
  return (
    (typeof drawing.id === 'string' || typeof drawing.id === 'number') &&
    typeof drawing.tool === 'string' &&
    typeof drawing.startX === 'number' &&
    typeof drawing.startY === 'number' &&
    typeof drawing.endX === 'number' &&
    typeof drawing.endY === 'number'
  );
}

function loadStoredDrawings(symbol: string): any[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(drawingStorageKey(symbol));
    if (raw === null) return [];
    const parsed: unknown = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.every(isStoredDrawing) ? parsed : [];
  } catch {
    return [];
  }
}

function storeDrawings(symbol: string, drawings: any[]): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(drawingStorageKey(symbol), JSON.stringify(drawings));
  } catch {
    // Browser preferences are best-effort and never chart-data authority.
  }
}

interface Props {
  symbol?: string;
  widgetId?: string;
}

export const ChartWidget: React.FC<Props> = ({ symbol = 'EURUSD', widgetId }) => {
  const { products, openOrderTicket, submitOrder, theme } = useTradingStore();
  const { orderConfirmationRequired, toggleExpandWidget, setWidgetSymbol } = useWorkspaceStore();

  const [activeSymbol, setActiveSymbol] = useState(symbol);
  const [searchQuery, setSearchQuery] = useState(symbol);
  const [activeMarketRow, setActiveMarketRow] = useState<MarketRow | null>(null);

  const targetProduct: Product = useMemo(
    () =>
      products.find((p) => p.symbol === activeSymbol) || {
        symbol: activeSymbol,
        name: activeSymbol,
        adr10: 0,
        atr14: 0,
        decimals: 2,
        assetClass: 'Futures',
        contractMonth: '',
        lastPrice: 0,
        change: 0,
        changePercent: 0,
        open: 0,
        priorSettle: 0,
        high: 0,
        low: 0,
        volume: 0,
        bid: 0,
        ask: 0,
      },
    [products, activeSymbol]
  );

  const symbolDigits = useMemo(() => {
    if (typeof activeMarketRow?.digits === 'number' && activeMarketRow.digits >= 0) {
      return activeMarketRow.digits;
    }
    if (typeof targetProduct?.decimals === 'number' && targetProduct.decimals >= 0 && targetProduct.decimals !== 2) {
      return targetProduct.decimals;
    }
    const upper = activeSymbol.toUpperCase();
    if (upper.includes('JPY')) return 3;
    if (
      upper.includes('USD') ||
      upper.includes('EUR') ||
      upper.includes('GBP') ||
      upper.includes('AUD') ||
      upper.includes('CAD') ||
      upper.includes('CHF')
    ) {
      return 5;
    }
    return 2;
  }, [activeMarketRow, targetProduct, activeSymbol]);

  const [universe, setUniverse] = useState<string[]>([]);
  const [universeStatus, setUniverseStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [suggestOpen, setSuggestOpen] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const suggestionIdPrefix = useRef(`chart-symbol-suggestion-${Math.random().toString(36).slice(2, 8)}`);

  useEffect(() => {
    setActiveSymbol(symbol);
    setSearchQuery(symbol);
  }, [symbol]);

  // Report the charted symbol back to the workspace so the widget heading and
  // its persisted symbol follow the chart instead of naming whatever it was
  // created with.
  useEffect(() => {
    if (!widgetId) return;
    setWidgetSymbol(widgetId, activeSymbol);
  }, [widgetId, activeSymbol, setWidgetSymbol]);

  useEffect(() => {
    let cancelled = false;
    void loadSymbolUniverse()
      .then((symbols) => {
        if (cancelled) return;
        setUniverse(symbols);
        setUniverseStatus('ready');
      })
      .catch(() => {
        if (cancelled) return;
        setUniverseStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const closeSuggestions = () => {
    setSuggestOpen(false);
    setHighlight(-1);
  };

  const selectSymbol = (candidate: string) => {
    const resolved = resolveSourceSymbol(universe, candidate) ?? candidate.trim().toUpperCase();
    if (resolved) {
      setActiveSymbol(resolved);
      setSearchQuery(resolved);
    }
    closeSuggestions();
  };

  const suggestions = suggestOpen ? filterSymbols(universe, searchQuery) : [];

  const handleSymbolKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setSuggestOpen(true);
      setHighlight((prev) => (suggestions.length === 0 ? -1 : (prev + 1) % suggestions.length));
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setHighlight((prev) =>
        suggestions.length === 0 ? -1 : prev <= 0 ? suggestions.length - 1 : prev - 1
      );
      return;
    }
    if (event.key === 'Escape') {
      closeSuggestions();
      return;
    }
    if (event.key === 'Tab' && suggestions.length > 0) {
      event.preventDefault();
      const choice = highlight >= 0 && suggestions[highlight] ? suggestions[highlight] : suggestions[0];
      selectSymbol(choice);
      return;
    }
    if (event.key === 'Enter') {
      event.preventDefault();
      const choice = highlight >= 0 && suggestions[highlight] ? suggestions[highlight] : searchQuery;
      selectSymbol(choice);
    }
  };

  // Range By Controls ("Bars" or "Date")
  // Bounded by the backend's API_MAX_BAR_COUNT. The upper end exists for
  // backtest-scale reads (ten years of M5 is roughly 750k bars), not because
  // a million candles are legible at once.
  const BAR_COUNT_OPTIONS = [
    100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000,
  ];
  const [rangeBy, setRangeBy] = useState<'Bars' | 'Date'>('Bars');
  const [barCount, setBarCount] = useState<number>(100);
  const [dateFrom, setDateFrom] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split('T')[0];
  });
  const [dateTo, setDateTo] = useState<string>(() => new Date().toISOString().split('T')[0]);

  // State Management for TradingView Toolbar Controls & Dropdowns
  const [timeframe, setTimeframe] = useState<BarTimeframe>('H1');
  const [chartType, setChartType] = useState('Candles');
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null); // 'timeframe' | 'chartStyle' | 'indicators' | 'layoutGrid' | null
  const [activeTool, setActiveTool] = useState('crosshair');
  const [isAveragePriceOn, setIsAveragePriceOn] = useState(true);
  const [selectedIndicators, setSelectedIndicators] = useState<string[]>([]);
  const [indicatorSeries, setIndicatorSeries] = useState<Partial<Record<'ema' | 'rsi', IndicatorSeries>>>({});
  const [indicatorErrors, setIndicatorErrors] = useState<Partial<Record<'ema' | 'rsi', string>>>({});
  const [loadingIndicators, setLoadingIndicators] = useState<Set<'ema' | 'rsi'>>(new Set());
  const [indicatorSearchQuery, setIndicatorSearchQuery] = useState('');
  const [starredItems, setStarredItems] = useState(['H1', 'Candles']);
  const [indicatorCatalogue, setIndicatorCatalogue] = useState<IndicatorSpec[]>([]);
  const [catalogueStatus, setCatalogueStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [showVolumeLegend, setShowVolumeLegend] = useState(true);
  const [panOffset, setPanOffset] = useState(0);
  const [chartPlotWidth, setChartPlotWidth] = useState(632);
  const [isPanning, setIsPanning] = useState(false);
  const isPanningRef = useRef(false);
  const panStartRef = useRef(0);

  // Sync Controls (Multi-Chart Layout Dropdown)
  const [syncSymbol, setSyncSymbol] = useState(false);
  const [syncInterval, setSyncInterval] = useState(false);
  const [syncCrosshair, setSyncCrosshair] = useState(true);
  const [syncTime, setSyncTime] = useState(false);
  const [syncDateRange, setSyncDateRange] = useState(false);

  // Drawing Tools & Submenus State matching Screenshots
  const [activeSubmenu, setActiveSubmenu] = useState<string | null>(null); // 'cursor' | 'lines' | 'fib' | 'patterns' | 'prediction' | 'brush' | 'text' | 'emojis' | 'trash' | null
  const [submenuPosition, setSubmenuPosition] = useState({ top: 0, left: 0 });
  const [cursorMode, setCursorMode] = useState('cross'); // 'cross' | 'dot' | 'arrow' | 'demonstration' | 'eraser'
  const [isStayInDrawingMode, setIsStayInDrawingMode] = useState(false);
  const [isSyncDrawings, setIsSyncDrawings] = useState(true);
  const [selectedEmoji, setSelectedEmoji] = useState('😊');
  const [iconPickerTab, setIconPickerTab] = useState('emojis');

  const [isMagnetOn, setIsMagnetOn] = useState(false);
  const [magnetStrength, setMagnetStrength] = useState('weak');
  const [isLocked, setIsLocked] = useState(false);
  const [isDrawingsHidden, setIsDrawingsHidden] = useState(false);
  const [isIndicatorsHidden, setIsIndicatorsHidden] = useState(false);
  const [arePositionsHidden, setArePositionsHidden] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [drawings, setDrawings] = useState<any[]>(() => loadStoredDrawings(symbol));
  const drawingsSymbolRef = useRef(symbol);
  const skipDrawingPersistRef = useRef(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const [currentLine, setCurrentLine] = useState<any | null>(null);

  useEffect(() => {
    if (drawingsSymbolRef.current === activeSymbol) return;
    drawingsSymbolRef.current = activeSymbol;
    skipDrawingPersistRef.current = true;
    setSelectedDrawingId(null);
    setDrawings(loadStoredDrawings(activeSymbol));
  }, [activeSymbol]);

  useEffect(() => {
    if (drawingsSymbolRef.current !== activeSymbol) return;
    if (skipDrawingPersistRef.current) {
      skipDrawingPersistRef.current = false;
      return;
    }
    storeDrawings(activeSymbol, drawings);
  }, [activeSymbol, drawings]);

  // Quantity Stepper for Buy/Sell Overlay
  const [orderQty, setOrderQty] = useState('1');

  // Mouse Crosshair Position State
  const [crosshairPos, setCrosshairPos] = useState<{ x: number; y: number; price: number | null; time: string | null }>({ x: -1, y: -1, price: null, time: null });

  // Floating Tool Property Editor Toolbar State (matching User's Screenshot)
  const [selectedDrawingId, setSelectedDrawingId] = useState<string | number | null>(null);
  const [toolEditorPos, setToolEditorPos] = useState({ x: 300, y: 50 });
  const [showColorPicker, setShowColorPicker] = useState(false);
  const [showWidthPicker, setShowWidthPicker] = useState(false);
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [isDraggingEditor, setIsDraggingEditor] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const selectedDrawing = drawings.find((d) => String(d.id) === String(selectedDrawingId)) || (drawings.length > 0 ? drawings[drawings.length - 1] : null);

  const updateSelectedDrawing = (updates: any) => {
    if (!selectedDrawing) return;
    const targetId = selectedDrawing.id;
    setDrawings(drawings.map((d) => (d.id === targetId ? { ...d, ...updates } : d)));
  };

  const deleteSelectedDrawing = () => {
    if (!selectedDrawing) return;
    const targetId = selectedDrawing.id;
    setDrawings(drawings.filter((d) => d.id !== targetId));
    setSelectedDrawingId(null);
  };

  const cloneSelectedDrawing = () => {
    if (!selectedDrawing) return;
    const cloned = {
      ...selectedDrawing,
      id: `draw_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
      startX: selectedDrawing.startX + 20,
      startY: selectedDrawing.startY + 20,
      endX: selectedDrawing.endX + 20,
      endY: selectedDrawing.endY + 20
    };
    setDrawings([...drawings, cloned]);
    setSelectedDrawingId(cloned.id);
    setShowMoreMenu(false);
  };

  const bringToFront = () => {
    if (!selectedDrawing) return;
    const targetId = selectedDrawing.id;
    setDrawings([...drawings.filter((d) => d.id !== targetId), selectedDrawing]);
    setShowMoreMenu(false);
  };

  const sendToBack = () => {
    if (!selectedDrawing) return;
    const targetId = selectedDrawing.id;
    setDrawings([selectedDrawing, ...drawings.filter((d) => d.id !== targetId)]);
    setShowMoreMenu(false);
  };

  const handleEditorGripMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsDraggingEditor(true);
    setDragOffset({
      x: e.clientX - toolEditorPos.x,
      y: e.clientY - toolEditorPos.y
    });
  };

  useEffect(() => {
    const handleGlobalMouseMove = (e: MouseEvent) => {
      if (isDraggingEditor) {
        setToolEditorPos({
          x: e.clientX - dragOffset.x,
          y: e.clientY - dragOffset.y
        });
      }
    };
    const handleGlobalMouseUp = () => {
      if (isDraggingEditor) setIsDraggingEditor(false);
    };
    window.addEventListener('mousemove', handleGlobalMouseMove);
    window.addEventListener('mouseup', handleGlobalMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleGlobalMouseMove);
      window.removeEventListener('mouseup', handleGlobalMouseUp);
    };
  }, [isDraggingEditor, dragOffset]);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const toggleDropdown = (name: string) => {
    setActiveDropdown(activeDropdown === name ? null : name);
  };

  const toggleDrawingSubmenu = (name: string, event: React.MouseEvent<HTMLElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setSubmenuPosition({
      top: Math.max(4, Math.min(rect.top, window.innerHeight - 430)),
      left: rect.right
    });
    setActiveSubmenu(activeSubmenu === name ? null : name);
  };

  const toggleStar = (item: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (starredItems.includes(item)) {
      setStarredItems(starredItems.filter((i) => i !== item));
    } else {
      setStarredItems([...starredItems, item]);
    }
  };

  // Symbol precision and quote evidence from the connected runtime broker.
  // Kept separate from the bar read so a quote failure never blanks the chart.
  useEffect(() => {
    let cancelled = false;
    void apiClients.data
      .quotes([activeSymbol])
      .then((response) => {
        if (cancelled) return;
        const matched = unwrapData(response)?.rows?.find((r) => r.symbol === activeSymbol);
        setActiveMarketRow(matched ? (matched as unknown as MarketRow) : null);
      })
      .catch(() => {
        if (!cancelled) setActiveMarketRow(null);
      });
    return () => {
      cancelled = true;
    };
  }, [activeSymbol]);

  // Historical bars from the connected runtime broker (MT5) via the Data domain.
  const [candles, setCandles] = useState<BarData[]>([]);
  const [isLoadingBars, setIsLoadingBars] = useState(true);
  const [barsError, setBarsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setIsLoadingBars(true);
    setBarsError(null);

    async function fetchBars() {
      try {
        const response = await apiClients.data.bars({
          symbol: activeSymbol,
          timeframe,
          ...(rangeBy === 'Bars'
            ? { limit: barCount }
            : {
                start: `${dateFrom}T00:00:00Z`,
                end: `${dateTo}T23:59:59Z`,
              }),
        });
        if (cancelled) return;

        const rows = toChartBars(unwrapData(response), timeframe);
        setCandles(rows);
        // An empty series is reported, never papered over: the broker having no
        // history for this symbol and timeframe is real information.
        setBarsError(
          rows.length === 0 ? `No ${timeframe} bars available for ${activeSymbol}` : null
        );
        anchorToLatestRef.current = true;
        setPanOffset(0);
      } catch (error) {
        if (cancelled) return;
        setCandles([]);
        setBarsError(error instanceof Error ? error.message : 'Bars unavailable');
      } finally {
        if (!cancelled) setIsLoadingBars(false);
      }
    }

    void fetchBars();

    return () => {
      cancelled = true;
    };
  }, [activeSymbol, timeframe, rangeBy, barCount, dateFrom, dateTo]);

  useEffect(() => {
    const requested: ['ema' | 'rsi', number][] = [];
    if (selectedIndicators.includes('ema')) requested.push(['ema', 20]);
    if (selectedIndicators.includes('rsi')) requested.push(['rsi', 14]);
    const requestedIds = new Set(requested.map(([indicatorId]) => indicatorId));
    setIndicatorSeries((current) =>
      Object.fromEntries(Object.entries(current).filter(([key]) => requestedIds.has(key as 'ema' | 'rsi')))
    );
    setIndicatorErrors((current) =>
      Object.fromEntries(Object.entries(current).filter(([key]) => requestedIds.has(key as 'ema' | 'rsi')))
    );
    if (requested.length === 0) {
      setLoadingIndicators(new Set());
      return;
    }

    let cancelled = false;
    setLoadingIndicators(new Set(requestedIds));
    for (const [indicatorId, period] of requested) {
      void apiClients.indicators
        .series({
          indicatorId,
          symbol: activeSymbol,
          timeframe,
          period,
          source: 'close',
          limit: rangeBy === 'Bars' ? barCount : Math.max(candles.length, period + 1),
          ...(rangeBy === 'Date'
            ? {
                start: `${dateFrom}T00:00:00Z`,
                end: `${dateTo}T23:59:59Z`,
              }
            : {}),
        })
        .then((response) => {
          if (cancelled) return;
          const series = unwrapData(response);
          setIndicatorSeries((current) => ({ ...current, [indicatorId]: series }));
          setIndicatorErrors((current) => ({ ...current, [indicatorId]: undefined }));
        })
        .catch((error) => {
          if (cancelled) return;
          setIndicatorSeries((current) => ({ ...current, [indicatorId]: undefined }));
          setIndicatorErrors((current) => ({
            ...current,
            [indicatorId]: error instanceof Error ? error.message : 'Indicator unavailable',
          }));
        })
        .finally(() => {
          if (cancelled) return;
          setLoadingIndicators((current) => {
            const next = new Set(current);
            next.delete(indicatorId);
            return next;
          });
        });
    }
    return () => {
      cancelled = true;
    };
  }, [activeSymbol, timeframe, rangeBy, barCount, dateFrom, dateTo, candles.length, selectedIndicators]);

  useEffect(() => {
    if (activeDropdown !== 'indicators') return;
    let cancelled = false;
    setCatalogueStatus('loading');
    void apiClients.indicators
      .catalogue()
      .then((response) => {
        if (cancelled) return;
        setIndicatorCatalogue(unwrapData(response));
        setCatalogueStatus('ready');
      })
      .catch(() => {
        if (cancelled) return;
        setIndicatorCatalogue([]);
        setCatalogueStatus('error');
      });
    return () => {
      cancelled = true;
    };
  }, [activeDropdown]);

  const emaByTime = useMemo(
    () => new Map(indicatorSeries.ema?.points.map((point) => [point.time, point.value]) ?? []),
    [indicatorSeries.ema]
  );
  const rsiByTime = useMemo(
    () => new Map(indicatorSeries.rsi?.points.map((point) => [point.time, point.value]) ?? []),
    [indicatorSeries.rsi]
  );
  const missingBarCount = useMemo(
    () => candles.reduce((count, candle) => count + (candle.missingBarsBefore ?? 0), 0),
    [candles]
  );

  const rsiSegments = useMemo(() => {
    const segments: { x: number; y: number }[][] = [];
    let segment: { x: number; y: number }[] = [];
    const candleWidth = Math.max(
      6,
      (chartPlotWidth / Math.min(Math.max(candles.length, 1), 60)) * zoomLevel
    );
    const range = visibleBarRange(candles.length, chartPlotWidth, candleWidth, panOffset);
    for (let candleIndex = range.start; candleIndex < range.end; candleIndex++) {
      const candle = candles[candleIndex];
      const value = rsiByTime.get(candle.timestamp);
      if (value === null || value === undefined) {
        if (segment.length) segments.push(segment);
        segment = [];
        continue;
      }
      if (candle.missingBarsBefore && segment.length) {
        segments.push(segment);
        segment = [];
      }
      segment.push({
        x: candleIndex * candleWidth + candleWidth / 2 + panOffset,
        y: 100 - value,
      });
    }
    if (segment.length) segments.push(segment);
    return segments;
  }, [candles, chartPlotWidth, panOffset, rsiByTime, zoomLevel]);

  // Extend the forming bar with the live quote. A zero price means the product
  // is not quoted yet, and must not overwrite a real close.
  useEffect(() => {
    const lastPrice = targetProduct.lastPrice;
    if (!(lastPrice > 0)) return;
    setCandles((prev) => {
      if (!prev.length) return prev;
      const last = { ...prev[prev.length - 1] };
      last.close = lastPrice;
      last.high = Math.max(last.high, lastPrice);
      last.low = Math.min(last.low, lastPrice);
      return [...prev.slice(0, -1), last];
    });
  }, [targetProduct.lastPrice]);

  // Chart Panning / Moving State
  // A freshly loaded series opens on its most recent bars. Starting at offset 0
  // shows the oldest instead, which is unnoticeable at 100 bars and useless at
  // backtest scale — a ten-year window would open ten years in the past.
  const anchorToLatestRef = useRef(true);
  // Main Canvas Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const container = canvas.parentElement;
    if (!container) return;
    const width = canvas.width = container.clientWidth || 700;
    const rsiPanelHeight = selectedIndicators.includes('rsi') ? 120 : 0;
    const height = canvas.height = Math.max(120, (container.clientHeight || 400) - rsiPanelHeight);

    ctx.clearRect(0, 0, width, height);
    if (!candles.length) return;

    const paddingRight = 68;
    const paddingBottom = 28;
    const chartWidth = width - paddingRight;
    const chartHeight = height - paddingBottom;
    if (chartWidth !== chartPlotWidth) setChartPlotWidth(chartWidth);

    const visibleBarsTarget = 60;
    const candleWidth = Math.max(6, (chartWidth / Math.min(candles.length, visibleBarsTarget)) * zoomLevel);

    // Calculate viewport visible candle range based on panOffset and candleWidth
    const visibleRange = visibleBarRange(candles.length, chartWidth, candleWidth, panOffset);
    const visibleStartIndex = visibleRange.start;
    const visibleEndIndex = visibleRange.end;
    const hasVisibleRange = visibleEndIndex > visibleStartIndex;
    const scaleFrom = hasVisibleRange ? visibleStartIndex : 0;
    const scaleTo = hasVisibleRange ? visibleEndIndex : candles.length;

    // Only bars inside the clipped viewport can appear, so the draw loops walk
    // this window rather than the whole series. At backtest scale the
    // difference is ~60 canvas operations instead of a million per frame.
    const drawStart = scaleFrom;
    const drawEnd = scaleTo;
    const visibleEntries = candles
      .slice(drawStart, drawEnd)
      .map((candle, localIndex) => ({ candle, index: drawStart + localIndex }));
    const visibleCandles = visibleEntries.map(({ candle }) => candle);

    // Geometry is only known here, so the anchor is resolved on the first
    // paint of a new series and then handed back to normal panning.
    if (anchorToLatestRef.current) {
      anchorToLatestRef.current = false;
      const latest = Math.min(0, chartWidth - candles.length * candleWidth);
      if (latest !== panOffset) {
        setPanOffset(latest);
        return;
      }
    }

    const { min: rawMinPrice, max: rawMaxPrice } = barExtent(candles, scaleFrom, scaleTo);
    const pricePadding = (rawMaxPrice - rawMinPrice) * 0.08 || 0.001;
    const priceMin = rawMinPrice - pricePadding;
    const priceMax = rawMaxPrice + pricePadding;
    const priceRange = priceMax - priceMin || 1;

    const isLight = theme === 'light';
    const gridColor = isLight ? '#E5E7EB' : '#20334b';
    const textColor = isLight ? '#4B5563' : '#dbdbdb';
    const axisBg = isLight ? '#F9FAFB' : '#112b4a';
    const upColor = '#00e473';
    const downColor = isLight ? '#E53935' : '#ff003d';

    // 1. Grid Lines
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 3]);

    const gridStepY = chartHeight / 8;
    for (let y = gridStepY; y < chartHeight; y += gridStepY) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(chartWidth, y);
      ctx.stroke();
    }

    const timeStepX = Math.max(1, Math.floor(Math.max(1, visibleEndIndex - visibleStartIndex) / 8));

    // Move the time-based chart content while keeping the price axis and
    // crosshair anchored to the canvas viewport.
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, chartWidth, height);
    ctx.clip();
    ctx.translate(panOffset, 0);

    const firstGridIndex = Math.ceil(drawStart / timeStepX) * timeStepX;
    for (let i = firstGridIndex; i < drawEnd; i += timeStepX) {
      const x = i * candleWidth;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, chartHeight);
      ctx.stroke();
    }
    ctx.setLineDash([]);

    // Broker gaps remain visible and break every continuous series path.
    visibleEntries.forEach(({ candle, index }) => {
      if (!candle.missingBarsBefore) return;
      const gapWidth = Math.max(6, Math.min(candleWidth, 24));
      const x = index * candleWidth - gapWidth / 2;
      ctx.fillStyle = 'rgba(255, 193, 7, 0.16)';
      ctx.fillRect(x, 0, gapWidth, chartHeight);
      ctx.strokeStyle = '#ffc107';
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(index * candleWidth, 0);
      ctx.lineTo(index * candleWidth, chartHeight);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // 2. Render Candlesticks / Styles (Supports all 18 Chart Types)
    if (chartType === 'Line' || chartType === 'Line with markers' || chartType === 'Step line') {
      ctx.strokeStyle = upColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      let drawingLine = false;
      visibleEntries.forEach(({ candle: c, index: idx }) => {
        const x = idx * candleWidth + candleWidth / 2;
        const yClose = chartHeight - ((c.close - priceMin) / priceRange) * chartHeight;
        if (!drawingLine || c.missingBarsBefore) {
          ctx.moveTo(x, yClose);
        } else if (chartType === 'Step line') {
          const prevYClose = chartHeight - ((candles[idx - 1].close - priceMin) / priceRange) * chartHeight;
          ctx.lineTo(x, prevYClose);
          ctx.lineTo(x, yClose);
        } else {
          ctx.lineTo(x, yClose);
        }
        drawingLine = true;
      });
      ctx.stroke();

      if (chartType === 'Line with markers') {
        visibleEntries.forEach(({ candle: c, index: idx }) => {
          const x = idx * candleWidth + candleWidth / 2;
          const yClose = chartHeight - ((c.close - priceMin) / priceRange) * chartHeight;
          ctx.beginPath();
          ctx.arc(x, yClose, 3, 0, 2 * Math.PI);
          ctx.fillStyle = upColor;
          ctx.fill();
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 1;
          ctx.stroke();
        });
      }
    } else if (chartType === 'Area' || chartType === 'HLC area') {
      if (chartType === 'HLC area') {
        ['high', 'low', 'close'].forEach((field) => {
          ctx.beginPath();
          ctx.strokeStyle = field === 'close' ? upColor : 'rgba(0, 200, 83, 0.35)';
          ctx.lineWidth = field === 'close' ? 2 : 1;
          let drawingBand = false;
          visibleEntries.forEach(({ candle, index }) => {
            const value = candle[field as 'high' | 'low' | 'close'];
            const x = index * candleWidth + candleWidth / 2;
            const y = chartHeight - ((value - priceMin) / priceRange) * chartHeight;
            if (!drawingBand || candle.missingBarsBefore) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
            drawingBand = true;
          });
          ctx.stroke();
        });
      } else {
        ctx.beginPath();
        ctx.strokeStyle = upColor;
        ctx.lineWidth = 2;
        let drawingArea = false;
        visibleEntries.forEach(({ candle, index }) => {
          const x = index * candleWidth + candleWidth / 2;
          const yClose = chartHeight - ((candle.close - priceMin) / priceRange) * chartHeight;
          if (!drawingArea || candle.missingBarsBefore) ctx.moveTo(x, yClose);
          else ctx.lineTo(x, yClose);
          drawingArea = true;
        });
        ctx.stroke();
      }
    } else if (chartType === 'Baseline') {
      const baselineVal = candles[0].open;
      const yBase = chartHeight - ((baselineVal - priceMin) / priceRange) * chartHeight;

      ctx.strokeStyle = textColor;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, yBase);
      ctx.lineTo(chartWidth, yBase);
      ctx.stroke();
      ctx.setLineDash([]);

      visibleEntries.forEach(({ candle: c, index: idx }) => {
        const x = idx * candleWidth + candleWidth / 2;
        const yClose = chartHeight - ((c.close - priceMin) / priceRange) * chartHeight;
        const isAbove = c.close >= baselineVal;

        ctx.fillStyle = isAbove ? 'rgba(0, 200, 83, 0.25)' : 'rgba(229, 57, 53, 0.25)';
        const topY = Math.min(yClose, yBase);
        const botY = Math.max(yClose, yBase);
        ctx.fillRect(x - candleWidth * 0.4, topY, candleWidth * 0.8, Math.max(1, botY - topY));

        ctx.strokeStyle = isAbove ? upColor : downColor;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(x - candleWidth * 0.4, yClose);
        ctx.lineTo(x + candleWidth * 0.4, yClose);
        ctx.stroke();
      });
    } else if (chartType === 'Columns') {
      visibleEntries.forEach(({ candle: c, index: idx }) => {
        const x = idx * candleWidth + candleWidth / 2;
        const isGreen = c.close >= c.open;
        const yClose = chartHeight - ((c.close - priceMin) / priceRange) * chartHeight;
        const colW = candleWidth * 0.7;

        ctx.fillStyle = isGreen ? upColor : downColor;
        ctx.fillRect(x - colW / 2, yClose, colW, chartHeight - yClose);
      });
    } else if (chartType === 'High-low') {
      visibleEntries.forEach(({ candle: c, index: idx }) => {
        const x = idx * candleWidth + candleWidth / 2;
        const isGreen = c.close >= c.open;
        const yHigh = chartHeight - ((c.high - priceMin) / priceRange) * chartHeight;
        const yLow = chartHeight - ((c.low - priceMin) / priceRange) * chartHeight;
        const barW = candleWidth * 0.5;

        ctx.fillStyle = isGreen ? upColor : downColor;
        ctx.fillRect(x - barW / 2, yHigh, barW, Math.max(2, yLow - yHigh));
      });
    } else if (chartType === 'Heikin Ashi') {
      const haData: { haOpen: number; haHigh: number; haLow: number; haClose: number; index: number }[] = [];
      visibleEntries.forEach(({ candle: c, index }, localIndex) => {
        const haClose = (c.open + c.high + c.low + c.close) / 4;
        const haOpen = localIndex === 0 ? (c.open + c.close) / 2 : (haData[localIndex - 1].haOpen + haData[localIndex - 1].haClose) / 2;
        const haHigh = Math.max(c.high, haOpen, haClose);
        const haLow = Math.min(c.low, haOpen, haClose);
        haData.push({ haOpen, haHigh, haLow, haClose, index });
      });

      haData.forEach((ha) => {
        const x = ha.index * candleWidth + candleWidth / 2;
        const isGreen = ha.haClose >= ha.haOpen;

        const yOpen = chartHeight - ((ha.haOpen - priceMin) / priceRange) * chartHeight;
        const yClose = chartHeight - ((ha.haClose - priceMin) / priceRange) * chartHeight;
        const yHigh = chartHeight - ((ha.haHigh - priceMin) / priceRange) * chartHeight;
        const yLow = chartHeight - ((ha.haLow - priceMin) / priceRange) * chartHeight;

        ctx.strokeStyle = isGreen ? upColor : downColor;
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(x, yHigh);
        ctx.lineTo(x, yLow);
        ctx.stroke();

        ctx.fillStyle = isGreen ? upColor : downColor;
        const bodyTop = Math.min(yOpen, yClose);
        const bodyHeight = Math.max(2, Math.abs(yOpen - yClose));
        ctx.fillRect(x - candleWidth * 0.35, bodyTop, candleWidth * 0.7, bodyHeight);
      });
    } else if (chartType === 'Renko') {
      const brickSize = Math.max(0.5, (priceMax - priceMin) / 20);
      const bricks: { open: number; close: number; isUp: boolean }[] = [];
      let currentPrice = visibleCandles[0].close;

      visibleCandles.forEach((c) => {
        let diff = c.close - currentPrice;
        while (Math.abs(diff) >= brickSize) {
          const isUp = diff > 0;
          const openP = currentPrice;
          const closeP = isUp ? currentPrice + brickSize : currentPrice - brickSize;
          bricks.push({ open: openP, close: closeP, isUp });
          currentPrice = closeP;
          diff = c.close - currentPrice;
        }
      });

      const displayBricks = bricks.length > 0 ? bricks : [{ open: visibleCandles[0].open, close: visibleCandles[0].close, isUp: visibleCandles[0].close >= visibleCandles[0].open }];
      const brickW = chartWidth / displayBricks.length;

      displayBricks.forEach((b, idx) => {
        const x = -panOffset + idx * brickW + brickW / 2;
        const yOpen = chartHeight - ((b.open - priceMin) / priceRange) * chartHeight;
        const yClose = chartHeight - ((b.close - priceMin) / priceRange) * chartHeight;
        const top = Math.min(yOpen, yClose);
        const height = Math.max(3, Math.abs(yOpen - yClose));

        ctx.fillStyle = b.isUp ? upColor : downColor;
        ctx.fillRect(x - brickW * 0.4, top, brickW * 0.8, height);
        ctx.strokeStyle = b.isUp ? upColor : downColor;
        ctx.strokeRect(x - brickW * 0.4, top, brickW * 0.8, height);
      });
    } else if (chartType === 'Line break') {
      const linesData: { open: number; close: number; isUp: boolean }[] = [];
      visibleCandles.forEach((c, idx) => {
        if (idx === 0) {
          linesData.push({ open: c.open, close: c.close, isUp: c.close >= c.open });
        } else {
          const lastLines = linesData.slice(-3);
          const highest = Math.max(...lastLines.map((l) => Math.max(l.open, l.close)));
          const lowest = Math.min(...lastLines.map((l) => Math.min(l.open, l.close)));

          if (c.close > highest) {
            linesData.push({ open: highest, close: c.close, isUp: true });
          } else if (c.close < lowest) {
            linesData.push({ open: lowest, close: c.close, isUp: false });
          }
        }
      });

      const blockW = chartWidth / (linesData.length || 1);
      linesData.forEach((l, idx) => {
        const x = -panOffset + idx * blockW + blockW / 2;
        const yOpen = chartHeight - ((l.open - priceMin) / priceRange) * chartHeight;
        const yClose = chartHeight - ((l.close - priceMin) / priceRange) * chartHeight;
        const top = Math.min(yOpen, yClose);
        const height = Math.max(3, Math.abs(yOpen - yClose));

        ctx.fillStyle = l.isUp ? upColor : downColor;
        ctx.fillRect(x - blockW * 0.4, top, blockW * 0.8, height);
      });
    } else if (chartType === 'Kagi') {
      const revAmount = Math.max(0.5, (priceMax - priceMin) / 15);
      let direction = 1;
      let isYang = true;
      let peak = visibleCandles[0].close;
      let trough = visibleCandles[0].close;
      const firstVisibleIndex = visibleEntries[0].index;
      const kagiPoints = [{ x: firstVisibleIndex * candleWidth + candleWidth / 2, price: visibleCandles[0].close, isYang: true }];

      visibleEntries.forEach(({ candle: c, index: idx }) => {
        const x = idx * candleWidth + candleWidth / 2;
        if (direction === 1) {
          if (c.close > peak) {
            peak = c.close;
            if (!isYang && peak > (kagiPoints[kagiPoints.length - 2]?.price || peak)) {
              isYang = true;
            }
          } else if (peak - c.close >= revAmount) {
            kagiPoints.push({ x, price: peak, isYang });
            direction = -1;
            trough = c.close;
            if (isYang && trough < (kagiPoints[kagiPoints.length - 2]?.price || trough)) {
              isYang = false;
            }
          }
        } else {
          if (c.close < trough) {
            trough = c.close;
            if (isYang && trough < (kagiPoints[kagiPoints.length - 2]?.price || trough)) {
              isYang = false;
            }
          } else if (c.close - trough >= revAmount) {
            kagiPoints.push({ x, price: trough, isYang });
            direction = 1;
            peak = c.close;
            if (!isYang && peak > (kagiPoints[kagiPoints.length - 2]?.price || peak)) {
              isYang = true;
            }
          }
        }
      });
      const lastVisible = visibleEntries[visibleEntries.length - 1];
      kagiPoints.push({ x: lastVisible.index * candleWidth + candleWidth / 2, price: lastVisible.candle.close, isYang });

      for (let i = 1; i < kagiPoints.length; i++) {
        const prev = kagiPoints[i - 1];
        const curr = kagiPoints[i];
        const yPrev = chartHeight - ((prev.price - priceMin) / priceRange) * chartHeight;
        const yCurr = chartHeight - ((curr.price - priceMin) / priceRange) * chartHeight;

        ctx.strokeStyle = curr.isYang ? upColor : downColor;
        ctx.lineWidth = curr.isYang ? 3 : 1.5;

        ctx.beginPath();
        ctx.moveTo(prev.x, yPrev);
        ctx.lineTo(curr.x, yPrev);
        ctx.lineTo(curr.x, yCurr);
        ctx.stroke();
      }
    } else if (chartType === 'Point & figure') {
      const boxSize = Math.max(0.4, (priceMax - priceMin) / 15);
      const cols: { isX: boolean; boxes: number[] }[] = [];
      let curCol: { isX: boolean; boxes: number[] } = { isX: true, boxes: [] };
      let lastPrice = visibleCandles[0].close;

      visibleCandles.forEach((c) => {
        const diff = c.close - lastPrice;
        if (Math.abs(diff) >= boxSize) {
          const boxesCount = Math.floor(Math.abs(diff) / boxSize);
          if (diff > 0) {
            if (!curCol.isX && curCol.boxes.length > 0) {
              cols.push(curCol);
              curCol = { isX: true, boxes: [] };
            }
            for (let b = 0; b < boxesCount; b++) {
              curCol.boxes.push(lastPrice + (b + 1) * boxSize);
            }
          } else {
            if (curCol.isX && curCol.boxes.length > 0) {
              cols.push(curCol);
              curCol = { isX: false, boxes: [] };
            }
            for (let b = 0; b < boxesCount; b++) {
              curCol.boxes.push(lastPrice - (b + 1) * boxSize);
            }
          }
          lastPrice = c.close;
        }
      });
      if (curCol.boxes.length > 0) cols.push(curCol);

      const colW = chartWidth / (cols.length || 1);
      cols.forEach((col, cIdx) => {
        const x = -panOffset + cIdx * colW + colW / 2;
        col.boxes.forEach((pVal) => {
          const y = chartHeight - ((pVal - priceMin) / priceRange) * chartHeight;
          if (col.isX) {
            ctx.strokeStyle = upColor;
            ctx.lineWidth = 1.8;
            ctx.beginPath();
            ctx.moveTo(x - 4, y - 4);
            ctx.lineTo(x + 4, y + 4);
            ctx.moveTo(x + 4, y - 4);
            ctx.lineTo(x - 4, y + 4);
            ctx.stroke();
          } else {
            ctx.strokeStyle = downColor;
            ctx.lineWidth = 1.8;
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.stroke();
          }
        });
      });
    } else {
      // Handles: 'Bars', 'Candles', 'Hollow candles', 'Volume candles', 'HLC bars'
      const maxVol = maxVolume(candles, drawStart, drawEnd);

      for (let idx = drawStart; idx < drawEnd; idx++) {
        const c = candles[idx];
        const x = idx * candleWidth + candleWidth / 2;
        const isGreen = c.close >= c.open;

        const yOpen = chartHeight - ((c.open - priceMin) / priceRange) * chartHeight;
        const yClose = chartHeight - ((c.close - priceMin) / priceRange) * chartHeight;
        const yHigh = chartHeight - ((c.high - priceMin) / priceRange) * chartHeight;
        const yLow = chartHeight - ((c.low - priceMin) / priceRange) * chartHeight;

        if (chartType === 'Bars' || chartType === 'HLC bars') {
          ctx.strokeStyle = isGreen ? upColor : downColor;
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(x, yHigh);
          ctx.lineTo(x, yLow);
          if (chartType === 'Bars') {
            ctx.moveTo(x - candleWidth * 0.3, yOpen);
            ctx.lineTo(x, yOpen);
          }
          ctx.moveTo(x, yClose);
          ctx.lineTo(x + candleWidth * 0.3, yClose);
          ctx.stroke();
        } else {
          // Candles / Hollow candles / Volume candles
          let bodyW = candleWidth * 0.7;
          if (chartType === 'Volume candles') {
            bodyW = candleWidth * (0.15 + 0.65 * (c.volume / maxVol));
          }

          ctx.strokeStyle = isGreen ? upColor : downColor;
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          ctx.moveTo(x, yHigh);
          ctx.lineTo(x, yLow);
          ctx.stroke();

          const bodyTop = Math.min(yOpen, yClose);
          const bodyHeight = Math.max(2, Math.abs(yOpen - yClose));

          if (chartType === 'Hollow candles' && isGreen) {
            ctx.strokeStyle = upColor;
            ctx.strokeRect(x - bodyW / 2, bodyTop, bodyW, bodyHeight);
          } else {
            ctx.fillStyle = isGreen ? upColor : downColor;
            ctx.fillRect(x - bodyW / 2, bodyTop, bodyW, bodyHeight);
          }
        }
      }
    }

    // Volume & Time Axis Labels
    for (let idx = drawStart; idx < drawEnd; idx++) {
      const c = candles[idx];
      const x = idx * candleWidth + candleWidth / 2;
      const isGreen = c.close >= c.open;

      if (!isIndicatorsHidden && selectedIndicators.includes('volume')) {
        const volHeight = (c.volume / 2000) * (chartHeight * 0.22);
        ctx.fillStyle = isGreen ? 'rgba(0, 200, 83, 0.35)' : 'rgba(229, 57, 53, 0.35)';
        ctx.fillRect(x - candleWidth * 0.35, chartHeight - volHeight, candleWidth * 0.7, volHeight);
      }

      if (idx % timeStepX === 0) {
        ctx.fillStyle = textColor;
        ctx.font = '10px "Trebuchet MS", Roboto, Arial, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(c.time, x, height - 10);
      }
    }

    // 3. Indicators-owned EMA line; null warm-up points break the path.
    if (!isIndicatorsHidden && selectedIndicators.includes('ema') && indicatorSeries.ema) {
      ctx.beginPath();
      ctx.strokeStyle = '#FF9800';
      ctx.lineWidth = 1.5;
      let drawingSegment = false;
      for (let idx = drawStart; idx < drawEnd; idx++) {
        const x = idx * candleWidth + candleWidth / 2;
        const emaVal = emaByTime.get(candles[idx].timestamp);
        if (candles[idx].missingBarsBefore || emaVal === null || emaVal === undefined) {
          drawingSegment = false;
          if (emaVal === null || emaVal === undefined) continue;
        }
        const y = chartHeight - ((emaVal - priceMin) / priceRange) * chartHeight;
        if (!drawingSegment) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        drawingSegment = true;
      }
      ctx.stroke();
    }

    ctx.restore();

    // 4. Horizontal Price Line & Right Axis
    const lastCandle = candles[candles.length - 1];
    const currentY = chartHeight - ((lastCandle.close - priceMin) / priceRange) * chartHeight;
    const isUp = lastCandle.close >= lastCandle.open;

    ctx.strokeStyle = isUp ? upColor : downColor;
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.moveTo(0, currentY);
    ctx.lineTo(chartWidth, currentY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = axisBg;
    ctx.fillRect(chartWidth, 0, paddingRight, height);

    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(chartWidth, 0);
    ctx.lineTo(chartWidth, height);
    ctx.moveTo(0, chartHeight);
    ctx.lineTo(width, chartHeight);
    ctx.stroke();

    ctx.fillStyle = textColor;
    ctx.font = '10px "Trebuchet MS", Roboto, Arial, sans-serif';
    ctx.textAlign = 'left';
    for (let i = 0; i <= 8; i++) {
      const pVal = priceMin + (priceRange * i) / 8;
      const y = chartHeight - (i / 8) * chartHeight;
      ctx.fillText(pVal.toFixed(symbolDigits), chartWidth + 8, y + 4);
    }

    // Current Price Badge
    ctx.fillStyle = isUp ? '#00e473' : '#ff003d';
    ctx.fillRect(chartWidth, currentY - 10, paddingRight, 20);
    ctx.fillStyle = isUp ? '#081d37' : '#ffffff';
    ctx.font = 'bold 10px "Segoe UI", Roboto, Arial, sans-serif';
    ctx.fillText(`${activeSymbol} ${lastCandle?.close ? lastCandle.close.toFixed(symbolDigits) : (0).toFixed(symbolDigits)}`, chartWidth + 4, currentY + 3);

    // Drawings
    if (!isDrawingsHidden) {
      ctx.save();
      ctx.beginPath();
      ctx.rect(0, 0, chartWidth, height);
      ctx.clip();
      ctx.translate(panOffset, 0);

      drawings.forEach((shape) => {
        renderDrawingShape(ctx, shape, chartWidth, chartHeight, priceMin, priceRange, priceMax, symbolDigits);
      });

      if (currentLine) {
        renderDrawingShape(ctx, currentLine, chartWidth, chartHeight, priceMin, priceRange, priceMax, symbolDigits);
      }

      ctx.restore();
    }

    // Cursor Modes (Cross, Dot, Arrow, Demonstration)
    if (crosshairPos.x >= 0 && crosshairPos.x <= chartWidth && crosshairPos.y >= 0 && crosshairPos.y <= chartHeight) {
      if (cursorMode === 'dot') {
        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(crosshairPos.x, crosshairPos.y, 4, 0, 2 * Math.PI);
        ctx.fill();
      } else if (cursorMode === 'demonstration') {
        ctx.fillStyle = 'rgba(255, 73, 117, 0.4)';
        ctx.beginPath();
        ctx.arc(crosshairPos.x, crosshairPos.y, 10, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillStyle = '#ff4975';
        ctx.beginPath();
        ctx.arc(crosshairPos.x, crosshairPos.y, 4, 0, 2 * Math.PI);
        ctx.fill();
      } else {
        // Crosshair
        ctx.strokeStyle = '#787b8688';
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);

        ctx.beginPath();
        ctx.moveTo(crosshairPos.x, 0);
        ctx.lineTo(crosshairPos.x, chartHeight);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(0, crosshairPos.y);
        ctx.lineTo(chartWidth, crosshairPos.y);
        ctx.stroke();
        ctx.setLineDash([]);
      }

      const hoverPrice = priceMax - (crosshairPos.y / chartHeight) * priceRange;
      ctx.fillStyle = '#1e355e';
      ctx.fillRect(chartWidth, crosshairPos.y - 9, paddingRight, 18);
      ctx.fillStyle = '#ffffff';
      ctx.font = '10px "Trebuchet MS", Roboto, Arial, sans-serif';
      ctx.fillText(hoverPrice.toFixed(symbolDigits), chartWidth + 8, crosshairPos.y + 4);

      const hoverCandleIdx = Math.floor((crosshairPos.x - panOffset) / candleWidth);
      if (candles[hoverCandleIdx]) {
        const hoverTime = candles[hoverCandleIdx].time;
        ctx.fillStyle = '#1e355e';
        ctx.fillRect(crosshairPos.x - 25, chartHeight, 50, 18);
        ctx.fillStyle = '#ffffff';
        ctx.textAlign = 'center';
        ctx.fillText(hoverTime, crosshairPos.x, chartHeight + 13);
      }
    }
  }, [candles, chartType, selectedIndicators, indicatorSeries.ema, emaByTime, targetProduct.lastPrice, drawings, currentLine, crosshairPos, isDrawingsHidden, isIndicatorsHidden, theme, cursorMode, panOffset, zoomLevel, symbolDigits, activeSymbol, chartPlotWidth]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    let x = e.clientX - rect.left;
    let y = e.clientY - rect.top;
    const chartX = x - panOffset;

    if (isPanningRef.current) {
      setPanOffset(e.clientX - panStartRef.current);
      return;
    }

    if (isMagnetOn && candles.length) {
      const candleWidth = Math.max(6, ((canvas.width - 68) / Math.min(candles.length, 60)) * zoomLevel);
      const candleIdx = Math.max(0, Math.min(candles.length - 1, Math.floor(chartX / candleWidth)));
      const c = candles[candleIdx];
      if (c) {
        const { min: priceLo, max: priceHi } = barExtent(candles, 0, candles.length);
        const priceMin = priceLo - 1.5;
        const priceMax = priceHi + 1.5;
        const priceRange = priceMax - priceMin || 1;
        const chartHeight = canvas.height - 30;
        const snapPrice = c.close;
        const snapY = chartHeight - ((snapPrice - priceMin) / priceRange) * chartHeight;
        if (magnetStrength === 'strong' || Math.abs(snapY - y) <= 14) y = snapY;
      }
    }

    setCrosshairPos((prev) => ({ ...prev, x, y }));
    if (isDrawing && currentLine) {
      setCurrentLine({
        ...currentLine,
        endX: chartX,
        endY: y,
        ...(FREEHAND_TOOLS.has(currentLine.tool)
          ? { points: [...(currentLine.points || []), { x: chartX, y }] }
          : {})
      });
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    let x = e.clientX - rect.left;
    let y = e.clientY - rect.top;
    const chartX = x - panOffset;

    if (cursorMode === 'eraser' || activeTool === 'eraser') {
      if (isLocked) return;
      const hitIndex = [...drawings].reverse().findIndex((shape) => {
        const margin = 18;
        const shapePoints = shape.points?.length ? shape.points : [
          { x: shape.startX, y: shape.startY }, { x: shape.endX, y: shape.endY }
        ];
        const xs = shapePoints.map((point: any) => point.x);
        const ys = shapePoints.map((point: any) => point.y);
        return chartX >= Math.min(...xs) - margin && chartX <= Math.max(...xs) + margin
          && y >= Math.min(...ys) - margin && y <= Math.max(...ys) + margin;
      });
      if (hitIndex >= 0) {
        const actualIndex = drawings.length - 1 - hitIndex;
        setDrawings(drawings.filter((_, index) => index !== actualIndex));
        setSelectedDrawingId(null);
      }
      return;
    }

    // Default Crosshair / Hand Tool -> Pan chart or select existing drawing shape!
    if (['crosshair', 'select', 'cross', 'dot', 'arrow', 'demonstration'].includes(activeTool) || activeTool === 'select') {
      // Check if clicking near an existing drawing shape
      const clickedShape = isLocked ? null : [...drawings].reverse().find((shape) => {
        const margin = 30;
        const minX = Math.min(shape.startX, shape.endX) - margin;
        const maxX = Math.max(shape.startX, shape.endX) + margin;
        const minY = Math.min(shape.startY, shape.endY) - margin;
        const maxY = Math.max(shape.startY, shape.endY) + margin;
        return chartX >= minX && chartX <= maxX && y >= minY && y <= maxY;
      });

      if (clickedShape) {
        setSelectedDrawingId(clickedShape.id);
        setToolEditorPos({
          x: Math.max(80, Math.min(clickedShape.endX + panOffset, 550)),
          y: Math.max(40, clickedShape.startY - 40)
        });
      } else {
        // Start chart panning / moving view
        isPanningRef.current = true;
        panStartRef.current = e.clientX - panOffset;
        setIsPanning(true);
      }
      return;
    }

    if (activeTool === 'zoom') {
      const nextZoom = e.shiftKey
        ? Math.max(0.75, zoomLevel / 1.25)
        : Math.min(3, zoomLevel * 1.25);
      const factor = nextZoom / zoomLevel;
      setPanOffset(x - (x - panOffset) * factor);
      setZoomLevel(nextZoom);
      return;
    }

    // A specific drawing tool is active (e.g. trendline, fib, rectangle, etc.) -> Draw new shape!
    if (isLocked) return;
    if (isMagnetOn && candles.length) {
      const candleWidth = Math.max(6, ((canvas.width - 68) / Math.min(candles.length, 60)) * zoomLevel);
      const candleIdx = Math.max(0, Math.min(candles.length - 1, Math.floor(chartX / candleWidth)));
      const c = candles[candleIdx];
      if (c) {
        const { min: priceLo, max: priceHi } = barExtent(candles, 0, candles.length);
        const priceMin = priceLo - 1.5;
        const priceMax = priceHi + 1.5;
        const priceRange = priceMax - priceMin || 1;
        const chartHeight = canvas.height - 30;
        const snapY = chartHeight - ((c.close - priceMin) / priceRange) * chartHeight;
        if (magnetStrength === 'strong' || Math.abs(snapY - y) <= 14) y = snapY;
      }
    }

    const newId = `draw_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`;
    setIsDrawing(true);
    setCurrentLine({
      id: newId,
      tool: activeTool,
      startX: chartX,
      startY: y,
      endX: chartX,
      endY: y,
      emoji: selectedEmoji,
      points: FREEHAND_TOOLS.has(activeTool) ? [{ x: chartX, y }] : undefined,
      color: '#3cc8ff',
      lineWidth: 2
    });
  };

  const handleMouseUp = () => {
    if (isPanningRef.current) {
      isPanningRef.current = false;
      setIsPanning(false);
      return;
    }

    if (isDrawing && currentLine) {
      const newDrawing = { ...currentLine };
      setDrawings((prev) => [...prev, newDrawing]);
      setCurrentLine(null);
      setIsDrawing(false);

      setSelectedDrawingId(newDrawing.id);
      setToolEditorPos({
        x: Math.max(80, Math.min(newDrawing.endX + panOffset, 550)),
        y: Math.max(40, newDrawing.startY - 40)
      });

      // Automatically reset active tool to Default Crosshair / Hand Tool!
      if (!isStayInDrawingMode) {
        setActiveTool('crosshair');
        setCursorMode('cross');
      }
    }
  };

  useEffect(() => {
    const stopPanning = () => {
      if (!isPanningRef.current) return;
      isPanningRef.current = false;
      setIsPanning(false);
    };

    window.addEventListener('mouseup', stopPanning);
    return () => window.removeEventListener('mouseup', stopPanning);
  }, []);

  const handleQuickTrade = (side: OrderSide) => {
    if (!orderConfirmationRequired) {
      submitOrder({ symbol: targetProduct.symbol, side, qty: Number(orderQty) || 1, orderType: 'Market' });
    } else {
      openOrderTicket({ symbol: targetProduct.symbol, side, type: 'Market' });
    }
  };

  const currentOHLC = candles[candles.length - 1] || {};

  const filteredIndicators = indicatorCatalogue.filter((indicator) =>
    `${indicator.indicator_id} ${indicator.name}`.toLowerCase().includes(indicatorSearchQuery.toLowerCase())
  );

  return (
    <div
      style={{ display: 'flex', flexDirection: 'column', height: '100%', background: 'var(--tv-bg)', color: 'var(--text-white)', position: 'relative' }}
      onClick={() => activeDropdown && setActiveDropdown(null)}
    >
      {/* 1. TOP TOOLBAR matching Reference Screenshot */}
      <div className="tv-toolbar">
        <div className="tv-toolbar-group" style={{ gap: '3px' }}>
          {/* (+) Plus Circle Icon */}
          <button className="tv-btn-clean" onClick={() => toggleDropdown('indicators')} title="Add Symbol / Comparison">
            <PlusCircle size={16} color="#ffffff" />
          </button>

          <div className="tv-toolbar-divider" />

          {/* 1. Symbol Search Pill Box [ 🔍 ESU6 ] with Symbol Universe Autocomplete */}
          <div className="tv-search-pill-box" style={{ position: 'relative' }}>
            <Search size={12} color="#ffffff" />
            <input
              type="text"
              value={searchQuery}
              role="combobox"
              aria-label="Symbol search"
              aria-expanded={suggestions.length > 0}
              aria-controls={`${suggestionIdPrefix.current}-listbox`}
              aria-autocomplete="list"
              aria-activedescendant={
                highlight >= 0 ? `${suggestionIdPrefix.current}-${highlight}` : undefined
              }
              autoComplete="off"
              title={
                universeStatus === 'ready'
                  ? `${universe.length} instruments available from connected runtime broker`
                  : universeStatus === 'error'
                    ? 'Instrument universe unavailable'
                    : 'Loading instrument universe…'
              }
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setSuggestOpen(true);
                setHighlight(-1);
              }}
              onFocus={() => setSuggestOpen(true)}
              onBlur={() => window.setTimeout(closeSuggestions, 150)}
              onKeyDown={handleSymbolKeyDown}
              // Content sizing fallback for browsers without `field-sizing`.
              // Ignored where that is supported, which measures glyphs exactly.
              size={Math.max(7, searchQuery.length + 1)}
              className="tv-search-input-field"
            />
            {suggestions.length > 0 && (
              <ul
                id={`${suggestionIdPrefix.current}-listbox`}
                role="listbox"
                aria-label="Symbol suggestions"
                style={{
                  position: 'absolute',
                  top: 'calc(100% + 4px)',
                  left: 0,
                  zIndex: 100,
                  margin: 0,
                  padding: '4px',
                  listStyle: 'none',
                  minWidth: '160px',
                  maxHeight: '220px',
                  overflowY: 'auto',
                  background: 'var(--cme-navy-surface, #132238)',
                  border: '1px solid var(--cme-navy-border, #1e3a5f)',
                  borderRadius: '4px',
                  boxShadow: '0 6px 18px rgba(0, 0, 0, 0.45)',
                }}
              >
                {suggestions.map((item, index) => (
                  <li
                    key={item}
                    id={`${suggestionIdPrefix.current}-${index}`}
                    role="option"
                    aria-selected={index === highlight}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      selectSymbol(item);
                    }}
                    onMouseEnter={() => setHighlight(index)}
                    style={{
                      padding: '5px 10px',
                      fontSize: '11px',
                      fontWeight: 600,
                      cursor: 'pointer',
                      borderRadius: '3px',
                      color: index === highlight ? '#ffffff' : 'var(--text-primary, #e2e8f0)',
                      background: index === highlight ? 'var(--cme-navy-active, #1e3a5f)' : 'transparent',
                    }}
                  >
                    {item}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="tv-toolbar-divider" />

          {/* 2. Timeframe Dropdown */}
          <div style={{ position: 'relative' }}>
            <button
              className="tv-btn-clean"
              onClick={(e) => { e.stopPropagation(); toggleDropdown('timeframe'); }}
            >
              <span>{timeframe}</span>
            </button>

            {/* Timeframe Dropdown Menu */}
            {activeDropdown === 'timeframe' && (
              <div className="tv-dropdown" style={{ width: '180px' }} onClick={(e) => e.stopPropagation()}>
                {TIMEFRAME_MENU.map((group) => (
                  <React.Fragment key={group.heading}>
                    <div className="tv-dropdown-section-header">{group.heading} <ChevronUp size={12} /></div>
                    {group.items.map(({ label, key }) => (
                      <div
                        key={key}
                        className={`tv-dropdown-item ${timeframe === key ? 'active' : ''}`}
                        onClick={() => { setTimeframe(key); setActiveDropdown(null); }}
                      >
                        <span>{label}</span>
                        <Star
                          size={13}
                          className={`tv-star-icon ${starredItems.includes(key) ? 'starred' : ''}`}
                          onClick={(e) => toggleStar(key, e)}
                        />
                      </div>
                    ))}
                  </React.Fragment>
                ))}
              </div>
            )}
          </div>

          <div className="tv-toolbar-divider" />

          {/* 3. Range By Section (Bars vs Date) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted, #718294)' }}>
              Range By
            </span>
            <select
              value={rangeBy}
              onChange={(e) => setRangeBy(e.target.value as 'Bars' | 'Date')}
              aria-label="Range By"
              style={{
                background: 'var(--cme-navy-dark, #0b1426)',
                color: 'var(--text-primary, #e2e8f0)',
                border: '1px solid var(--cme-navy-border, #1e3a5f)',
                borderRadius: '4px',
                padding: '2px 6px',
                fontSize: '11px',
                fontWeight: 600,
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="Bars">Bars</option>
              <option value="Date">Date</option>
            </select>

            {/* Child Section based on Range By selection */}
            {rangeBy === 'Bars' ? (
              <select
                value={barCount}
                onChange={(e) => setBarCount(Number(e.target.value))}
                aria-label="Bar Count"
                style={{
                  background: 'var(--cme-navy-dark, #0b1426)',
                  color: 'var(--text-primary, #e2e8f0)',
                  border: '1px solid var(--cme-navy-border, #1e3a5f)',
                  borderRadius: '4px',
                  padding: '2px 6px',
                  fontSize: '11px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                {BAR_COUNT_OPTIONS.map((count) => (
                  <option key={count} value={count}>
                    {count.toLocaleString()}
                  </option>
                ))}
              </select>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  aria-label="Date From"
                  style={{
                    background: 'var(--cme-navy-dark, #0b1426)',
                    color: 'var(--text-primary, #e2e8f0)',
                    border: '1px solid var(--cme-navy-border, #1e3a5f)',
                    borderRadius: '4px',
                    padding: '2px 6px',
                    fontSize: '11px',
                    fontWeight: 600,
                    outline: 'none',
                    colorScheme: 'dark',
                  }}
                />
                <span style={{ fontSize: '11px', color: 'var(--text-muted, #718294)' }}>to</span>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  aria-label="Date To"
                  style={{
                    background: 'var(--cme-navy-dark, #0b1426)',
                    color: 'var(--text-primary, #e2e8f0)',
                    border: '1px solid var(--cme-navy-border, #1e3a5f)',
                    borderRadius: '4px',
                    padding: '2px 6px',
                    fontSize: '11px',
                    fontWeight: 600,
                    outline: 'none',
                    colorScheme: 'dark',
                  }}
                />
              </div>
            )}
          </div>

          <div className="tv-toolbar-divider" />

          {/* 4. Chart Style Dropdown Icon */}
          <div style={{ position: 'relative' }}>
            <button
              className="tv-btn-clean"
              onClick={(e) => { e.stopPropagation(); toggleDropdown('chartStyle'); }}
              title={`Chart Style: ${chartType}`}
            >
              {renderChartIcon(chartType)}
            </button>

            {/* Chart Style Dropdown Menu */}
            {activeDropdown === 'chartStyle' && (
              <div className="tv-dropdown" style={{ width: '200px', maxHeight: '380px', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>
                {['Bars', 'Candles', 'Hollow candles', 'Volume candles', 'HLC bars', 'Line', 'Line with markers', 'Step line', 'Area', 'HLC area', 'Baseline', 'Columns', 'High-low', 'Heikin Ashi', 'Renko', 'Line break', 'Kagi', 'Point & figure'].map((style) => {
                  const isSelected = chartType === style;
                  return (
                    <div
                      key={style}
                      className={`tv-dropdown-item ${isSelected ? 'active' : ''}`}
                      onClick={() => { setChartType(style); setActiveDropdown(null); }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {renderChartIcon(style)}
                        <span>{style}</span>
                      </div>
                      <Star
                        size={13}
                        className={`tv-star-icon ${starredItems.includes(style) ? 'starred' : ''}`}
                        onClick={(e) => toggleStar(style, e)}
                      />
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="tv-toolbar-divider" />

          {/* 5. fx Indicators Button */}
          <button
            className="tv-btn-clean"
            onClick={(e) => { e.stopPropagation(); toggleDropdown('indicators'); }}
          >
            <span className="tv-fx-icon">f<sub>x</sub></span>
            <span>Indicators</span>
          </button>

          <div className="tv-toolbar-divider" />

          {/* Average Price Toggle Button */}
          <div className="tv-avg-price-container" onClick={() => setIsAveragePriceOn(!isAveragePriceOn)}>
            <span>Average Price</span>
            <div className={`tv-toggle-pill ${isAveragePriceOn ? 'active' : ''}`}>
              <div className="tv-toggle-circle" />
            </div>
          </div>

          <div className="tv-toolbar-divider" />

          {/* Undo / Redo */}
          <button className="tv-btn-clean" onClick={() => setDrawings(drawings.slice(0, -1))} title="Undo">
            <RotateCcw size={14} color="#ffffff" />
          </button>
          <button className="tv-btn-clean" title="Redo">
            <RotateCw size={14} color="#ffffff" />
          </button>
        </div>

        {/* Right Controls Bar & Multi-Chart Layout Picker */}
        <div className="tv-toolbar-group" style={{ gap: '4px' }}>
          {/* Multi-Chart Grid Layout Dropdown */}
          <div style={{ position: 'relative' }}>
            <button
              className="tv-btn-clean"
              onClick={(e) => { e.stopPropagation(); toggleDropdown('layoutGrid'); }}
              title="Multi-Chart Layout Grid"
            >
              <Grid size={15} color="#ffffff" />
            </button>

            {/* Layout Grid Dropdown Popup */}
            {activeDropdown === 'layoutGrid' && (
              <div className="tv-dropdown" style={{ width: '260px', right: 0, padding: '10px' }} onClick={(e) => e.stopPropagation()}>
                <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted-grey)', marginBottom: '8px' }}>LAYOUT GRID PRESETS</div>

                <div className="tv-layout-grid-picker">
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((num) => (
                    <div
                      key={num}
                      className={`tv-layout-option ${num === 1 ? 'active' : ''}`}
                      onClick={() => setActiveDropdown(null)}
                    >
                      <span style={{ fontSize: '11px', fontWeight: 600 }}>{num}</span>
                    </div>
                  ))}
                </div>

                <div className="tv-dropdown-section-header" style={{ padding: '8px 0 4px 0', borderTop: '1px solid var(--border-color)', marginTop: '8px' }}>
                  SYNC IN LAYOUT
                </div>

                {[
                  { label: 'Symbol', val: syncSymbol, setVal: setSyncSymbol },
                  { label: 'Interval', val: syncInterval, setVal: setSyncInterval },
                  { label: 'Crosshair', val: syncCrosshair, setVal: setSyncCrosshair },
                  { label: 'Time', val: syncTime, setVal: setSyncTime },
                  { label: 'Date range', val: syncDateRange, setVal: setSyncDateRange }
                ].map((item) => (
                  <div key={item.label} className="tv-dropdown-item" onClick={() => item.setVal(!item.val)}>
                    <span>{item.label}</span>
                    <div style={{ width: '24px', height: '12px', background: item.val ? '#0066CC' : 'var(--border-color)', borderRadius: '10px', position: 'relative' }}>
                      <div style={{ width: '8px', height: '8px', background: '#fff', borderRadius: '50%', position: 'absolute', top: '2px', left: item.val ? '14px' : '2px', transition: 'left 0.15s ease' }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Stacked Save Button */}
          <button className="tv-save-stacked-btn" title="Save Chart Layout">
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', lineHeight: 1.1 }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#ffffff' }}>Save</span>
              <span style={{ fontSize: '9px', color: '#8e95a4' }}>Save</span>
            </div>
            <ChevronDown size={11} color="#ffffff" />
          </button>

          <div className="tv-toolbar-divider" />

          {isLoadingBars && (
            <span style={{ fontSize: '10px', color: '#64748b', fontWeight: 600, padding: '0 4px' }}>
              Loading {timeframe} bars…
            </span>
          )}

          {!isLoadingBars && barsError && (
            <span
              title={barsError}
              style={{ fontSize: '10px', color: 'var(--cme-sell-red, #ff003d)', fontWeight: 600, padding: '0 4px' }}
            >
              {barsError}
            </span>
          )}

          <button className="tv-btn-clean" title="Take Snapshot">
            <Camera size={15} color="#ffffff" />
          </button>

          <button className="tv-btn-clean" title="Chart Properties">
            <Settings size={15} color="#ffffff" />
          </button>

          <button className="tv-btn-clean" onClick={() => toggleExpandWidget(widgetId ?? null)} title="Fullscreen / Expand Window">
            <Maximize2 size={15} color="#ffffff" />
          </button>
        </div>
      </div>

      {/* 2. MAIN CANVAS AREA & LEFT SIDEBAR */}
      <div style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
        {/* Left Drawing Sidebar Column matching Screenshots 1, 2, 3, 4 */}
        <div className="tv-sidebar" style={{ '--submenu-top': `${submenuPosition.top}px`, '--submenu-left': `${submenuPosition.left}px` } as React.CSSProperties} onClick={(e) => e.stopPropagation()}>
          {/* Top Badge: (+) Plus Circle */}
          <div className="tv-sidebar-btn" onClick={() => toggleDropdown('indicators')} title="Add Symbol / Indicator">
            <PlusCircle size={17} color="#ffffff" />
          </div>

          <div className="tv-sidebar-divider" />

          {/* 1. Cursor Tools Group (Screenshot 2) */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${['cross', 'dot', 'arrow', 'demonstration', 'eraser'].includes(cursorMode) ? 'active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('cursor', e)}
              title="Cursor Tools"
            >
              {cursorMode === 'dot' ? <CircleDot size={15} /> :
               cursorMode === 'arrow' ? <MousePointer size={15} /> :
               cursorMode === 'demonstration' ? <CircleDot size={15} color="#ff4975" /> :
               cursorMode === 'eraser' ? <Eraser size={15} /> :
               <Crosshair size={15} />}
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>

            {activeSubmenu === 'cursor' && (
              <div className="tv-sidebar-submenu" style={{ width: '200px' }}>
                {[
                  { id: 'cross', label: 'Cross', icon: <Crosshair size={14} /> },
                  { id: 'dot', label: 'Dot', icon: <CircleDot size={14} /> },
                  { id: 'arrow', label: 'Arrow', icon: <MousePointer size={14} /> },
                  { id: 'demonstration', label: 'Demonstration', icon: <CircleDot size={14} color="#ff4975" /> },
                  { id: 'eraser', label: 'Eraser', icon: <Eraser size={14} /> },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${cursorMode === item.id ? 'active' : ''}`}
                    onClick={() => { setCursorMode(item.id); setActiveTool(item.id === 'eraser' ? 'eraser' : 'select'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {item.icon}
                      <span>{item.label}</span>
                    </div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 2. Lines Tools Group (Screenshot 3) */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${['trendline', 'ray', 'infoline', 'extendedline', 'trendangle', 'horizontalline', 'horizontalray', 'verticalline', 'crossline', 'parallelchannel', 'regressiontrend', 'flattopbottom', 'disjointchannel', 'pitchfork', 'schiffpitchfork', 'modifiedschiff', 'insidepitchfork'].includes(activeTool) ? 'active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('lines', e)}
              title="Lines & Channels"
            >
              <Slash size={15} />
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>

            {activeSubmenu === 'lines' && (
              <div className="tv-sidebar-submenu" style={{ width: '240px' }}>
                <div className="tv-submenu-header">LINES</div>
                {[
                  { id: 'trendline', label: 'Trend Line', hotkey: 'Alt + T' },
                  { id: 'ray', label: 'Ray' },
                  { id: 'infoline', label: 'Info Line' },
                  { id: 'extendedline', label: 'Extended Line' },
                  { id: 'trendangle', label: 'Trend Angle' },
                  { id: 'horizontalline', label: 'Horizontal Line', hotkey: 'Alt + H' },
                  { id: 'horizontalray', label: 'Horizontal Ray', hotkey: 'Alt + J' },
                  { id: 'verticalline', label: 'Vertical Line', hotkey: 'Alt + V' },
                  { id: 'crossline', label: 'Cross Line', hotkey: 'Alt + C' },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`}
                    onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Slash size={13} />
                      <span>{item.label}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {item.hotkey && <span className="tv-hotkey-text">{item.hotkey}</span>}
                      <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                    </div>
                  </div>
                ))}

                <div className="tv-submenu-header">CHANNELS</div>
                {[
                  { id: 'parallelchannel', label: 'Parallel Channel' },
                  { id: 'regressiontrend', label: 'Regression Trend' },
                  { id: 'flattopbottom', label: 'Flat Top/Bottom' },
                  { id: 'disjointchannel', label: 'Disjoint Channel' },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`}
                    onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Layers size={13} />
                      <span>{item.label}</span>
                    </div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}

                <div className="tv-submenu-header">PITCHFORKS</div>
                {[
                  { id: 'pitchfork', label: 'Pitchfork' },
                  { id: 'schiffpitchfork', label: 'Schiff Pitchfork' },
                  { id: 'modifiedschiff', label: 'Modified Schiff Pitchfork' },
                  { id: 'insidepitchfork', label: 'Inside Pitchfork' },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`}
                    onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Share2 size={13} />
                      <span>{item.label}</span>
                    </div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 3. Fibonacci & Gann Group (Screenshot 4) */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${['fib', 'fibextension', 'fibchannel', 'fibtimezone', 'fibfan', 'trendbasedfibtime', 'fibcircles', 'fibspiral', 'fibarcs', 'fibwedge', 'pitchfan', 'gannbox', 'gannsquarefixed', 'gannsquare', 'gannfan'].includes(activeTool) ? 'active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('fib', e)}
              title="Fibonacci & Gann Tools"
            >
              <SlidersHorizontal size={15} />
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>

            {activeSubmenu === 'fib' && (
              <div className="tv-sidebar-submenu" style={{ width: '240px' }}>
                <div className="tv-submenu-header">FIBONACCI</div>
                {[
                  { id: 'fib', label: 'Fib Retracement', hotkey: 'Alt + F' },
                  { id: 'fibextension', label: 'Trend-Based Fib Extension' },
                  { id: 'fibchannel', label: 'Fib Channel' },
                  { id: 'fibtimezone', label: 'Fib Time Zone' },
                  { id: 'fibfan', label: 'Fib Speed Resistance Fan' },
                  { id: 'trendbasedfibtime', label: 'Trend-Based Fib Time' },
                  { id: 'fibcircles', label: 'Fib Circles' },
                  { id: 'fibspiral', label: 'Fib Spiral' },
                  { id: 'fibarcs', label: 'Fib Speed Resistance Arcs' },
                  { id: 'fibwedge', label: 'Fib Wedge' },
                  { id: 'pitchfan', label: 'Pitchfan' },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`}
                    onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Minus size={13} />
                      <span>{item.label}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {item.hotkey && <span className="tv-hotkey-text">{item.hotkey}</span>}
                      <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                    </div>
                  </div>
                ))}

                <div className="tv-submenu-header">GANN</div>
                {[
                  { id: 'gannbox', label: 'Gann Box' },
                  { id: 'gannsquarefixed', label: 'Gann Square Fixed' },
                  { id: 'gannsquare', label: 'Gann Square' },
                  { id: 'gannfan', label: 'Gann Fan' },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`}
                    onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Grid size={13} />
                      <span>{item.label}</span>
                    </div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 4. Geometric Patterns */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${PATTERN_TOOLS.has(activeTool) || ['cycliclines', 'timecycles', 'sineline'].includes(activeTool) ? 'active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('patterns', e)}
              title="Geometric Patterns"
            >
              <Share2 size={15} />
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>

            {activeSubmenu === 'patterns' && (
              <div className="tv-sidebar-submenu" style={{ width: '220px' }}>
                <div className="tv-submenu-header">PATTERNS</div>
                {[
                  { id: 'xabcd', label: 'XABCD Pattern' },
                  { id: 'cypher', label: 'Cypher Pattern' },
                  { id: 'headandshoulders', label: 'Head and Shoulders' },
                  { id: 'abcd', label: 'ABCD Pattern' },
                  { id: 'trianglepattern', label: 'Triangle Pattern' },
                  { id: 'threedrives', label: 'Three Drives Pattern' },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`}
                    onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Share2 size={13} />
                      <span>{item.label}</span>
                    </div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
                <div className="tv-submenu-header">ELLIOTT WAVES</div>
                {[
                  { id: 'elliott12345', label: 'Elliott Impulse Wave (12345)' },
                  { id: 'elliottabc', label: 'Elliott Correction Wave (ABC)' },
                  { id: 'elliottabcde', label: 'Elliott Triangle Wave (ABCDE)' },
                  { id: 'elliottwxy', label: 'Elliott Double Combo Wave (WXY)' },
                  { id: 'elliottwxyxz', label: 'Elliott Triple Combo Wave (WXYXZ)' },
                ].map((item) => (
                  <div key={item.id} className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`} onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Share2 size={13} /><span>{item.label}</span></div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
                <div className="tv-submenu-header">CYCLES</div>
                {[
                  { id: 'cycliclines', label: 'Cyclic Lines' },
                  { id: 'timecycles', label: 'Time Cycles' },
                  { id: 'sineline', label: 'Sine Line' },
                ].map((item) => (
                  <div key={item.id} className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`} onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Activity size={13} /><span>{item.label}</span></div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 5. Prediction & Measurement */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${['longposition', 'shortposition', 'forecast', 'barspattern', 'ghostfeed', 'projection', 'anchoredvwap', 'fixedrangevolumeprofile', 'pricerange', 'daterange', 'dateandpricerange'].includes(activeTool) ? 'active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('prediction', e)}
              title="Prediction & Projection"
            >
              <TrendingUp size={15} />
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>

            {activeSubmenu === 'prediction' && (
              <div className="tv-sidebar-submenu" style={{ width: '210px' }}>
                <div className="tv-submenu-header">PROJECTION</div>
                {[
                  { id: 'longposition', label: 'Long Position', icon: <TrendingUp size={13} color="#00e473" /> },
                  { id: 'shortposition', label: 'Short Position', icon: <TrendingDown size={13} color="#ff003d" /> },
                  { id: 'forecast', label: 'Forecast', icon: <TrendingUp size={13} /> },
                  { id: 'barspattern', label: 'Bars Pattern', icon: <BarChart2 size={13} /> },
                  { id: 'ghostfeed', label: 'Ghost Feed', icon: <Activity size={13} /> },
                  { id: 'projection', label: 'Projection', icon: <TrendingUp size={13} /> },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`}
                    onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {item.icon}
                      <span>{item.label}</span>
                    </div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
                <div className="tv-submenu-header">VOLUME-BASED</div>
                {[
                  { id: 'anchoredvwap', label: 'Anchored VWAP' },
                  { id: 'fixedrangevolumeprofile', label: 'Fixed Range Volume Profile' },
                ].map((item) => (
                  <div key={item.id} className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`} onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><BarChart2 size={13} /><span>{item.label}</span></div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
                <div className="tv-submenu-header">MEASURER</div>
                {[
                  { id: 'pricerange', label: 'Price Range' },
                  { id: 'daterange', label: 'Date Range' },
                  { id: 'dateandpricerange', label: 'Date and Price Range' },
                ].map((item) => (
                  <div key={item.id} className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`} onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Ruler size={13} /><span>{item.label}</span></div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 6. Brush & Shapes */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${FREEHAND_TOOLS.has(activeTool) || ARROW_TOOLS.has(activeTool) || ['rectangle', 'rotatedrectangle', 'circle', 'ellipse', 'triangle', 'arc'].includes(activeTool) ? 'active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('brush', e)}
              title="Drawings & Shapes"
            >
              <Paintbrush size={15} />
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>

            {activeSubmenu === 'brush' && (
              <div className="tv-sidebar-submenu" style={{ width: '220px' }}>
                <div className="tv-submenu-header">BRUSHES</div>
                {[
                  { id: 'brush', label: 'Brush' },
                  { id: 'highlighter', label: 'Highlighter' },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`}
                    onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Paintbrush size={13} />
                      <span>{item.label}</span>
                    </div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
                <div className="tv-submenu-header">ARROWS</div>
                {[
                  { id: 'arrowmarker', label: 'Arrow Marker' },
                  { id: 'arrowline', label: 'Arrow' },
                  { id: 'arrowup', label: 'Arrow Mark Up' },
                  { id: 'arrowdown', label: 'Arrow Mark Down' },
                  { id: 'arrowleft', label: 'Arrow Mark Left' },
                  { id: 'arrowright', label: 'Arrow Mark Right' },
                ].map((item) => (
                  <div key={item.id} className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`} onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><TrendingUp size={13} /><span>{item.label}</span></div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
                <div className="tv-submenu-header">SHAPES</div>
                {[
                  { id: 'rectangle', label: 'Rectangle', hotkey: 'Alt + Shift + R' },
                  { id: 'rotatedrectangle', label: 'Rotated Rectangle' },
                  { id: 'path', label: 'Path' },
                  { id: 'circle', label: 'Circle' },
                  { id: 'ellipse', label: 'Ellipse' },
                  { id: 'polyline', label: 'Polyline' },
                  { id: 'triangle', label: 'Triangle' },
                  { id: 'arc', label: 'Arc' },
                  { id: 'curve', label: 'Curve' },
                  { id: 'doublecurve', label: 'Double Curve' },
                ].map((item) => (
                  <div key={item.id} className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`} onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><CircleDot size={13} /><span>{item.label}</span></div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>{item.hotkey && <span className="tv-hotkey-text">{item.hotkey}</span>}<Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} /></div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 7. Text & Annotations */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${TEXT_TOOLS.has(activeTool) || ['pin', 'table'].includes(activeTool) ? 'active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('text', e)}
              title="Text & Annotations"
            >
              <Type size={15} />
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>

            {activeSubmenu === 'text' && (
              <div className="tv-sidebar-submenu" style={{ width: '190px' }}>
                <div className="tv-submenu-header">TEXT & NOTES</div>
                {[
                  { id: 'text', label: 'Text' },
                  { id: 'anchoredtext', label: 'Anchored Text' },
                  { id: 'note', label: 'Note' },
                  { id: 'pricenote', label: 'Price Note' },
                  { id: 'pin', label: 'Pin' },
                  { id: 'table', label: 'Table' },
                  { id: 'callout', label: 'Callout' },
                  { id: 'comment', label: 'Comment' },
                  { id: 'pricelabel', label: 'Price Label' },
                  { id: 'signpost', label: 'Signpost' },
                  { id: 'flagmark', label: 'Flag Mark' },
                ].map((item) => (
                  <div
                    key={item.id}
                    className={`tv-submenu-item ${activeTool === item.id ? 'active' : ''}`}
                    onClick={() => { setActiveTool(item.id); setCursorMode('cross'); setActiveSubmenu(null); }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Type size={13} />
                      <span>{item.label}</span>
                    </div>
                    <Star size={12} className={`tv-star-icon ${starredItems.includes(item.label) ? 'starred' : ''}`} onClick={(e) => toggleStar(item.label, e)} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 8. Emojis */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${['emoji', 'icon'].includes(activeTool) ? 'active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('emojis', e)}
              title="Icons & Emojis"
            >
              <Smile size={15} />
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>

            {activeSubmenu === 'emojis' && (
              <div className="tv-sidebar-submenu" style={{ width: '220px', padding: '10px' }}>
                <div className="tv-submenu-header" style={{ marginBottom: '6px' }}>ICONS & EMOJIS</div>
                <div className="tv-icon-picker-tabs">
                  {['emojis', 'stickers', 'icons'].map((tab) => (
                    <button key={tab} className={iconPickerTab === tab ? 'active' : ''} onClick={() => setIconPickerTab(tab)}>
                      {tab[0].toUpperCase() + tab.slice(1)}
                    </button>
                  ))}
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', fontSize: '18px', textAlign: 'center', cursor: 'pointer' }}>
                  {(iconPickerTab === 'emojis'
                    ? ['😊', '👍', '🚀', '🔥', '⭐', '❤️', '⚠️', '✅']
                    : iconPickerTab === 'stickers'
                      ? ['🎯', '💡', '📌', '🚩', '💰', '📈', '📉', '⏰']
                      : ['●', '▲', '▼', '◆', '★', '!', '✓', '×']
                  ).map((emoji) => (
                    <div
                      key={emoji}
                      className="tv-icon-option"
                      style={{ padding: '4px', borderRadius: '4px', background: 'rgba(255,255,255,0.06)' }}
                      onClick={() => { setSelectedEmoji(emoji); setActiveTool(iconPickerTab === 'icons' ? 'icon' : 'emoji'); setActiveSubmenu(null); }}
                    >
                      {emoji}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="tv-sidebar-divider" />

          {/* 9. Ruler / Measure */}
          <div
            className={`tv-sidebar-btn ${activeTool === 'measure' ? 'active' : ''}`}
            onClick={() => setActiveTool(activeTool === 'measure' ? 'select' : 'measure')}
            title="Measure (Ruler)"
          >
            <Ruler size={15} />
          </div>

          {/* 10. Zoom In */}
          <div
            className={`tv-sidebar-btn ${activeTool === 'zoom' ? 'active' : ''}`}
            onClick={() => setActiveTool(activeTool === 'zoom' ? 'select' : 'zoom')}
            title="Zoom In"
          >
            <ZoomIn size={15} />
          </div>

          <div className="tv-sidebar-divider" />

          {/* 11. Magnet Mode (Snaps to Candle High/Low/Close) */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${isMagnetOn ? 'magnet-active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('magnets', e)}
              title="Magnet Mode"
            >
              <Magnet size={15} color={isMagnetOn ? '#00e473' : '#718294'} />
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>
            {activeSubmenu === 'magnets' && (
              <div className="tv-sidebar-submenu" style={{ width: '175px' }}>
                {['weak', 'strong'].map((strength) => (
                  <div key={strength} className={`tv-submenu-item ${isMagnetOn && magnetStrength === strength ? 'active' : ''}`} onClick={() => { setMagnetStrength(strength); setIsMagnetOn(true); setActiveSubmenu(null); }}>
                    <span>{strength === 'weak' ? 'Weak Magnet' : 'Strong Magnet'}</span>
                    {isMagnetOn && magnetStrength === strength && <Check size={13} />}
                  </div>
                ))}
                <div className="tv-submenu-item" onClick={() => { setIsMagnetOn(false); setActiveSubmenu(null); }}><span>Magnet Off</span></div>
              </div>
            )}
          </div>

          {/* 12. Stay in Drawing Mode */}
          <div
            className={`tv-sidebar-btn ${isStayInDrawingMode ? 'active' : ''}`}
            onClick={() => setIsStayInDrawingMode(!isStayInDrawingMode)}
            title="Stay in Drawing Mode"
          >
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Paintbrush size={13} />
              <Lock size={8} style={{ position: 'absolute', bottom: -2, right: -4, color: '#3cc8ff' }} />
            </div>
          </div>

          {/* 13. Lock All Drawing Tools */}
          <div
            className={`tv-sidebar-btn ${isLocked ? 'active' : ''}`}
            onClick={() => setIsLocked(!isLocked)}
            title="Lock All Drawing Tools"
          >
            {isLocked ? <Lock size={15} color="#ff4975" /> : <Unlock size={15} />}
          </div>

          {/* 14. Hide drawings, indicators, and trading overlays */}
          <div style={{ position: 'relative' }}>
            <div
              className={`tv-sidebar-btn ${isDrawingsHidden || isIndicatorsHidden || arePositionsHidden ? 'active' : ''}`}
              onClick={(e) => toggleDrawingSubmenu('hide', e)}
              title="Hide Options"
            >
              {isDrawingsHidden && isIndicatorsHidden && arePositionsHidden ? <EyeOff size={15} color="#ff4975" /> : <Eye size={15} />}
              <ChevronRight size={10} className="tv-sub-arrow" />
            </div>
            {activeSubmenu === 'hide' && (
              <div className="tv-sidebar-submenu" style={{ width: '205px' }}>
                <div className={`tv-submenu-item ${isDrawingsHidden ? 'active' : ''}`} onClick={() => setIsDrawingsHidden(!isDrawingsHidden)}><span>Hide drawings</span>{isDrawingsHidden && <Check size={13} />}</div>
                <div className={`tv-submenu-item ${isIndicatorsHidden ? 'active' : ''}`} onClick={() => setIsIndicatorsHidden(!isIndicatorsHidden)}><span>Hide indicators</span>{isIndicatorsHidden && <Check size={13} />}</div>
                <div className={`tv-submenu-item ${arePositionsHidden ? 'active' : ''}`} onClick={() => setArePositionsHidden(!arePositionsHidden)}><span>Hide positions & orders</span>{arePositionsHidden && <Check size={13} />}</div>
                <div className="tv-submenu-item" onClick={() => {
                  const shouldHideAll = !(isDrawingsHidden && isIndicatorsHidden && arePositionsHidden);
                  setIsDrawingsHidden(shouldHideAll); setIsIndicatorsHidden(shouldHideAll); setArePositionsHidden(shouldHideAll); setActiveSubmenu(null);
                }}><span>Hide all</span></div>
              </div>
            )}
          </div>

          {/* 15. Sync Drawings across multi-chart */}
          <div
            className={`tv-sidebar-btn ${isSyncDrawings ? 'active' : ''}`}
            onClick={() => setIsSyncDrawings(!isSyncDrawings)}
            title="Sync Drawings across charts"
          >
            <Link size={15} color={isSyncDrawings ? '#3cc8ff' : '#718294'} />
          </div>

          <div className="tv-sidebar-divider" />

          {/* 16. Remove Drawings / Indicators Trash */}
          <div style={{ position: 'relative' }}>
            <div
              className="tv-sidebar-btn"
              onClick={(e) => toggleDrawingSubmenu('trash', e)}
              title="Remove Drawings / Indicators"
            >
              <Trash2 size={15} />
            </div>

            {activeSubmenu === 'trash' && (
              <div className="tv-sidebar-submenu" style={{ width: '210px' }}>
                <div
                  className="tv-submenu-item"
                  onClick={() => { setDrawings([]); setActiveSubmenu(null); }}
                >
                  <span>Remove {drawings.length} Drawings</span>
                </div>
                <div
                  className="tv-submenu-item"
                  onClick={() => { setSelectedIndicators([]); setActiveSubmenu(null); }}
                >
                  <span>Remove {selectedIndicators.length} Indicators</span>
                </div>
                <div
                  className="tv-submenu-item"
                  style={{ color: '#ff4975', fontWeight: 600 }}
                  onClick={() => { setDrawings([]); setSelectedIndicators([]); setActiveSubmenu(null); }}
                >
                  <span>Remove Drawings & Indicators</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Top-Left Overlay Legend */}
        <div className="tv-overlay-legend">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', fontWeight: 600 }}>
            <span style={{ color: 'var(--text-white)', fontWeight: 700 }}>{activeSymbol} • {timeframe.replace('m', '')} • HaruQuantAI</span>
            <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#00C853' }} />

            <span style={{ fontFamily: 'var(--font-sans)', fontSize: '11px', color: '#00C853', fontWeight: 600 }}>
              O <span style={{ color: '#00C853' }}>{currentOHLC.open !== undefined ? currentOHLC.open.toFixed(symbolDigits) : (0).toFixed(symbolDigits)}</span> H <span style={{ color: '#00C853' }}>{currentOHLC.high !== undefined ? currentOHLC.high.toFixed(symbolDigits) : (0).toFixed(symbolDigits)}</span> L <span style={{ color: '#00C853' }}>{currentOHLC.low !== undefined ? currentOHLC.low.toFixed(symbolDigits) : (0).toFixed(symbolDigits)}</span> C <span style={{ color: '#00C853' }}>{currentOHLC.close !== undefined ? currentOHLC.close.toFixed(symbolDigits) : (0).toFixed(symbolDigits)}</span>
            </span>
          </div>

          {!arePositionsHidden && <div className="tv-buy-sell-boxes">
            <div className="tv-order-box buy" onClick={() => handleQuickTrade('BUY')}>
              <span style={{ fontSize: '13px', fontWeight: 400, lineHeight: '16px' }}>{targetProduct.ask ? targetProduct.ask.toFixed(symbolDigits) : (currentOHLC.close || 0).toFixed(symbolDigits)}</span>
              <span style={{ fontSize: '11px', fontWeight: 400, lineHeight: '12px' }}>BUY</span>
            </div>

            <div className="tv-qty-box">
              <input
                type="text"
                value={orderQty}
                onChange={(e) => setOrderQty(e.target.value)}
                style={{ width: '28px', background: 'transparent', border: 'none', color: 'var(--text-white)', textAlign: 'center', outline: 'none', fontSize: '11px', fontWeight: 600 }}
              />
            </div>

            <div className="tv-order-box sell" onClick={() => handleQuickTrade('SELL')}>
              <span style={{ fontSize: '13px', fontWeight: 400, lineHeight: '16px' }}>{targetProduct.bid ? targetProduct.bid.toFixed(symbolDigits) : (currentOHLC.close || 0).toFixed(symbolDigits)}</span>
              <span style={{ fontSize: '11px', fontWeight: 400, lineHeight: '12px' }}>SELL</span>
            </div>
          </div>}

          {!isIndicatorsHidden && selectedIndicators.includes('volume') && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--cme-sell-red)', fontWeight: 600 }}>
              <span>Volume {currentOHLC.volume || 16}</span>
              <button
                onClick={() => setShowVolumeLegend(!showVolumeLegend)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-muted-grey)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
              >
                {showVolumeLegend ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>
            </div>
          )}
        </div>

        {/* Canvas & Floating Tool Property Editor Toolbar */}
        <div style={{ flex: 1, position: 'relative' }}>
          {/* FLOATING TOOL PROPERTY EDITOR matching User's Screenshot */}
          {selectedDrawing && (
            <div
              className="tv-floating-tool-editor"
              style={{
                left: `${Math.max(60, Math.min(toolEditorPos.x, 500))}px`,
                top: `${Math.max(20, Math.min(toolEditorPos.y, 350))}px`
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Drag Grip Handle (::) */}
              <div className="tv-editor-btn grip" onMouseDown={handleEditorGripMouseDown} title="Drag Toolbar">
                <GripVertical size={14} color="#718294" />
              </div>

              <div className="tv-editor-divider" />

              {/* Templates / Presets (4 small squares) */}
              <div className="tv-editor-btn" title="Template Presets">
                <Grid size={14} color="#ffffff" />
              </div>

              {/* Color Picker (Pencil/Brush with color spectrum) */}
              <div style={{ position: 'relative' }}>
                <div
                  className="tv-editor-btn"
                  onClick={() => setShowColorPicker(!showColorPicker)}
                  title="Line / Fill Color"
                >
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
                    <Paintbrush size={13} color={selectedDrawing.color || '#3cc8ff'} />
                    <div style={{ width: '12px', height: '3px', borderRadius: '2px', background: selectedDrawing.color || '#3cc8ff' }} />
                  </div>
                </div>

                {showColorPicker && (
                  <div className="tv-color-picker-popover">
                    {['#3cc8ff', '#00e473', '#ff003d', '#ff9800', '#ffffff', '#9c27b0', '#718294', '#006eb6'].map((c) => (
                      <div
                        key={c}
                        style={{ width: '18px', height: '18px', borderRadius: '50%', background: c, cursor: 'pointer', border: selectedDrawing.color === c ? '2px solid #ffffff' : 'none' }}
                        onClick={() => { updateSelectedDrawing({ color: c }); setShowColorPicker(false); }}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Line Width / Thickness e.g. — 2px */}
              <div style={{ position: 'relative' }}>
                <div
                  className="tv-editor-btn text-btn"
                  onClick={() => setShowWidthPicker(!showWidthPicker)}
                  title="Line Thickness"
                >
                  <span style={{ fontSize: '11px', fontWeight: 700, color: '#ffffff' }}>— {selectedDrawing.lineWidth || 2}px</span>
                </div>

                {showWidthPicker && (
                  <div className="tv-color-picker-popover" style={{ width: '110px', flexDirection: 'column', gap: '4px' }}>
                    {[1, 2, 3, 4].map((w) => (
                      <div
                        key={w}
                        className={`tv-submenu-item ${selectedDrawing.lineWidth === w ? 'active' : ''}`}
                        onClick={() => { updateSelectedDrawing({ lineWidth: w }); setShowWidthPicker(false); }}
                      >
                        <span>— {w}px</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="tv-editor-divider" />

              {/* Settings / Gear */}
              <div
                className="tv-editor-btn"
                onClick={() => setShowSettingsModal(true)}
                title="Settings / Properties"
              >
                <Settings size={14} color="#ffffff" />
              </div>

              {/* Lock Toggle */}
              <div
                className={`tv-editor-btn ${selectedDrawing.isLocked ? 'active' : ''}`}
                onClick={() => updateSelectedDrawing({ isLocked: !selectedDrawing.isLocked })}
                title="Lock / Unlock Drawing"
              >
                {selectedDrawing.isLocked ? <Lock size={14} color="#ff4975" /> : <Unlock size={14} color="#ffffff" />}
              </div>

              {/* Delete / Trash */}
              <div
                className="tv-editor-btn danger"
                onClick={deleteSelectedDrawing}
                title="Delete Drawing"
              >
                <Trash2 size={14} color="#ffffff" />
              </div>

              <div className="tv-editor-divider" />

              {/* More Actions Menu (•••) */}
              <div style={{ position: 'relative' }}>
                <div
                  className="tv-editor-btn"
                  onClick={() => setShowMoreMenu(!showMoreMenu)}
                  title="More Actions"
                >
                  <MoreHorizontal size={14} color="#ffffff" />
                </div>

                {showMoreMenu && (
                  <div className="tv-sidebar-submenu" style={{ width: '150px', right: 0, top: '30px', left: 'auto' }}>
                    <div className="tv-submenu-item" onClick={cloneSelectedDrawing}>
                      <span>Clone / Duplicate</span>
                    </div>
                    <div className="tv-submenu-item" onClick={bringToFront}>
                      <span>Bring to Front</span>
                    </div>
                    <div className="tv-submenu-item" onClick={sendToBack}>
                      <span>Send to Back</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TOOL SETTINGS MODAL */}
          {showSettingsModal && selectedDrawing && (
            <div
              className="tv-modal-overlay"
              onClick={() => setShowSettingsModal(false)}
              style={{
                position: 'fixed',
                inset: 0,
                background: 'rgba(0,0,0,0.65)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: 10000
              }}
            >
              <div
                className="tv-modal-content"
                onClick={(e) => e.stopPropagation()}
                style={{
                  width: '320px',
                  background: '#0d1b2e',
                  border: '1px solid #1c324f',
                  borderRadius: '8px',
                  padding: '16px',
                  boxShadow: '0 12px 32px rgba(0,0,0,0.8)',
                  color: '#ffffff'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', borderBottom: '1px solid #1c324f', paddingBottom: '10px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 700, letterSpacing: '0.2px' }}>Tool Properties Settings</span>
                  <button
                    onClick={() => setShowSettingsModal(false)}
                    style={{ background: 'transparent', border: 'none', color: '#718294', cursor: 'pointer', display: 'flex', alignItems: 'center' }}
                  >
                    <X size={16} />
                  </button>
                </div>

                {/* Note / Text Input */}
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ fontSize: '11px', color: '#718294', display: 'block', marginBottom: '5px', fontWeight: 600 }}>Text / Annotation Label</label>
                  <input
                    type="text"
                    value={selectedDrawing.text || ''}
                    onChange={(e) => updateSelectedDrawing({ text: e.target.value })}
                    placeholder="Enter custom text or note..."
                    style={{
                      width: '100%',
                      background: '#112b4a',
                      border: '1px solid #1c324f',
                      borderRadius: '4px',
                      padding: '7px 10px',
                      color: '#ffffff',
                      fontSize: '12px',
                      outline: 'none'
                    }}
                  />
                </div>

                {/* Line Style (Solid vs Dashed) */}
                <div style={{ marginBottom: '14px' }}>
                  <label style={{ fontSize: '11px', color: '#718294', display: 'block', marginBottom: '5px', fontWeight: 600 }}>Line Style</label>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {['solid', 'dashed'].map((style) => (
                      <button
                        key={style}
                        className={`tv-editor-btn ${selectedDrawing.lineStyle === style ? 'active' : ''}`}
                        onClick={() => updateSelectedDrawing({ lineStyle: style })}
                        style={{ flex: 1, padding: '6px', textTransform: 'capitalize', fontSize: '11px', fontWeight: 600 }}
                      >
                        {style}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Line Thickness Stepper */}
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ fontSize: '11px', color: '#718294', display: 'block', marginBottom: '5px', fontWeight: 600 }}>Line Thickness</label>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    {[1, 2, 3, 4, 5].map((w) => (
                      <button
                        key={w}
                        className={`tv-editor-btn ${selectedDrawing.lineWidth === w ? 'active' : ''}`}
                        onClick={() => updateSelectedDrawing({ lineWidth: w })}
                        style={{ flex: 1, padding: '6px', fontSize: '11px', fontWeight: 700 }}
                      >
                        {w}px
                      </button>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', borderTop: '1px solid #1c324f', paddingTop: '12px' }}>
                  <button
                    onClick={() => setShowSettingsModal(false)}
                    style={{ background: '#005b9e', border: 'none', borderRadius: '4px', padding: '7px 16px', color: '#fff', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
                  >
                    Done
                  </button>
                </div>
              </div>
            </div>
          )}

          {missingBarCount > 0 && (
            <div
              role="status"
              data-testid="chart-gap-status"
              style={{ position: 'absolute', top: 4, right: 76, zIndex: 2, fontSize: '10px', color: '#ffc107', fontWeight: 600 }}
            >
              {missingBarCount} missing {missingBarCount === 1 ? 'bar' : 'bars'} shown as gaps
            </div>
          )}
          <canvas
            ref={canvasRef}
            data-testid="chart-canvas"
            data-pan-offset={panOffset}
            data-zoom-level={zoomLevel}
            data-chart-type={chartType}
            onMouseMove={handleMouseMove}
            onMouseDown={handleMouseDown}
            onMouseUp={handleMouseUp}
            style={{
              width: '100%',
              height: selectedIndicators.includes('rsi') ? 'calc(100% - 120px)' : '100%',
              display: 'block',
              cursor: isPanning ? 'grabbing' : ['crosshair', 'select'].includes(activeTool) ? 'grab' : 'default'
            }}
          />
          {!isIndicatorsHidden && selectedIndicators.includes('rsi') && (
            <section
              aria-label="RSI indicator panel"
              data-testid="rsi-panel"
              style={{ height: '120px', borderTop: '1px solid var(--border-color)', position: 'relative', background: 'var(--cme-navy-dark, #0b1426)' }}
            >
              <div style={{ position: 'absolute', top: 4, left: 8, zIndex: 1, fontSize: '11px', color: '#b39ddb', fontWeight: 600 }}>
                RSI · period 14 · close
                {loadingIndicators.has('rsi') && ' · Loading'}
                {indicatorSeries.rsi?.availability === 'insufficient_history' && ' · Unavailable: insufficient history (warmup)'}
                {indicatorErrors.rsi && ` · Unavailable: ${indicatorErrors.rsi}`}
              </div>
              <svg role="img" aria-label="RSI series" viewBox={`0 0 ${chartPlotWidth} 100`} preserveAspectRatio="none" style={{ width: 'calc(100% - 68px)', height: '100%', overflow: 'hidden' }}>
                <line x1="0" y1="30" x2={chartPlotWidth} y2="30" stroke="#5c6b7a" strokeDasharray="2 2" vectorEffect="non-scaling-stroke" />
                <line x1="0" y1="70" x2={chartPlotWidth} y2="70" stroke="#5c6b7a" strokeDasharray="2 2" vectorEffect="non-scaling-stroke" />
                {rsiSegments.map((segment, index) => (
                  <polyline
                    key={index}
                    data-testid="rsi-segment"
                    points={segment.map((point) => `${point.x},${point.y}`).join(' ')}
                    fill="none"
                    stroke="#b39ddb"
                    strokeWidth="1.5"
                    vectorEffect="non-scaling-stroke"
                  />
                ))}
              </svg>
              <span style={{ position: 'absolute', right: 4, top: '27%', fontSize: 9, color: '#718294' }}>70</span>
              <span style={{ position: 'absolute', right: 4, top: '67%', fontSize: 9, color: '#718294' }}>30</span>
            </section>
          )}
          {!isIndicatorsHidden && selectedIndicators.includes('ema') && (
            <div style={{ position: 'absolute', top: 4, left: 8, zIndex: 1, fontSize: '11px', color: '#ff9800', fontWeight: 600 }}>
              EMA · period 20 · close
              {loadingIndicators.has('ema') && ' · Loading'}
              {indicatorSeries.ema?.availability === 'insufficient_history' &&
                ' · Unavailable: insufficient history (warmup)'}
              {indicatorErrors.ema && ` · Unavailable: ${indicatorErrors.ema}`}
            </div>
          )}
        </div>
      </div>

      {/* 3. BOTTOM SCALE BAR */}
      <div className="tv-bottom-bar">
        <button className="tv-pill-btn" style={{ border: 'none', background: 'transparent', padding: 0 }} title="Go to Date">
          <Calendar size={14} />
        </button>

        <div style={{ display: 'flex', gap: '4px' }}>
          {['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', 'ALL'].map((r) => (
            <button key={r} className="tv-pill-btn" style={{ padding: '2px 6px', fontSize: '10px' }}>{r}</button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-canvas)' }}>
          <span className="tv-pill-btn" style={{ padding: '2px 6px' }}>%</span>
          <span className="tv-pill-btn" style={{ padding: '2px 6px' }}>log</span>
          <span className="tv-pill-btn" style={{ padding: '2px 6px' }}>auto</span>
          <span style={{ fontSize: '14px', color: '#ffffff' }}>UTC-5</span>
        </div>
      </div>

      {/* 4. INDICATORS FULL MODAL (Image 3) */}
      {activeDropdown === 'indicators' && (
        <div className="modal-overlay" onClick={() => setActiveDropdown(null)}>
          <div className="tv-indicators-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <span>Indicators</span>
              <button className="widget-btn" onClick={() => setActiveDropdown(null)}>✕</button>
            </div>

            <div style={{ padding: '10px', borderBottom: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', background: 'var(--bg-main)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '6px 10px', gap: '8px' }}>
                <Search size={14} color="var(--text-muted-grey)" />
                <input
                  type="text"
                  placeholder="Search indicator script name..."
                  value={indicatorSearchQuery}
                  onChange={(e) => setIndicatorSearchQuery(e.target.value)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--text-white)', fontSize: '12px', width: '100%', outline: 'none' }}
                />
              </div>
            </div>

            <div style={{ padding: '8px 12px', fontSize: '10px', fontWeight: 700, color: 'var(--text-muted-grey)', background: 'var(--bg-header)', borderBottom: '1px solid var(--border-color)' }}>
              SCRIPT NAME
            </div>

            <div style={{ flex: 1, overflowY: 'auto' }}>
              {catalogueStatus === 'loading' && (
                <div role="status" style={{ padding: '14px', color: 'var(--text-muted-grey)' }}>
                  Loading registered indicatorsâ€¦
                </div>
              )}
              {catalogueStatus === 'error' && (
                <div role="alert" style={{ padding: '14px', color: 'var(--cme-sell-red)' }}>
                  Indicator catalogue unavailable
                </div>
              )}
              {catalogueStatus === 'ready' && filteredIndicators.length === 0 && (
                <div style={{ padding: '14px', color: 'var(--text-muted-grey)' }}>
                  No registered indicators found
                </div>
              )}
              {catalogueStatus === 'ready' && filteredIndicators.map((indicator) => {
                const indicatorId = indicator.indicator_id;
                const isChartEnabled = indicatorId === 'ema' || indicatorId === 'rsi';
                const isSelected = selectedIndicators.includes(indicatorId);
                return (
                  <button
                    type="button"
                    key={indicatorId}
                    className={`tv-dropdown-item ${isSelected ? 'active' : ''}`}
                    disabled={!isChartEnabled}
                    onClick={() => {
                      if (isSelected) setSelectedIndicators(selectedIndicators.filter((id) => id !== indicatorId));
                      else setSelectedIndicators([...selectedIndicators, indicatorId]);
                    }}
                    style={{ padding: '8px 14px', width: '100%', border: 0, opacity: isChartEnabled ? 1 : 0.6 }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ textAlign: 'left' }}>
                        <span style={{ display: 'block' }}>{indicator.name}</span>
                        <span style={{ display: 'block', fontSize: '9px', color: 'var(--text-muted-grey)' }}>
                          {indicatorId} · v{indicator.indicator_version}
                        </span>
                      </span>
                    </div>
                    {!isChartEnabled && <span style={{ fontSize: '9px' }}>Not chart-enabled yet</span>}
                    {isSelected && <Check size={14} color="var(--cme-blue-bright)" />}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
