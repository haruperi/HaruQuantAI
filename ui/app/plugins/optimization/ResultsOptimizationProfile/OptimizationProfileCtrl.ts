import { useMemo, useRef, useState } from 'react';
import type { Dispatch, MouseEvent, RefObject, SetStateAction } from 'react';
import type { SurfacePoint } from '../../../host/types';
import { generateOptimizationGrid } from './optimizationSurfaceLogic';
import type { OptimizationGridResult } from './optimizationSurfaceLogic';

/** Existing local surface state; all values remain synthetic presentation data. */
export interface OptimizationProfileController extends OptimizationGridResult {
  paramX: string;
  setParamX: Dispatch<SetStateAction<string>>;
  paramY: string;
  setParamY: Dispatch<SetStateAction<string>>;
  metricZ: string;
  setMetricZ: Dispatch<SetStateAction<string>>;
  displayMode: '3d' | 'contour' | 'scatter';
  setDisplayMode: Dispatch<SetStateAction<'3d' | 'contour' | 'scatter'>>;
  rotX: number;
  setRotX: Dispatch<SetStateAction<number>>;
  rotY: number;
  setRotY: Dispatch<SetStateAction<number>>;
  zoom: number;
  setZoom: Dispatch<SetStateAction<number>>;
  canvasRef: RefObject<HTMLCanvasElement | null>;
  availableParams: string[];
  availableMetrics: string[];
  gridSize: number;
  handleMouseDown: (event: MouseEvent<HTMLCanvasElement>) => void;
  handleMouseMove: (event: MouseEvent<HTMLCanvasElement>) => void;
  handleMouseUp: () => void;
}

/** Retain the original state initialization, grid memo and mouse-only orbit. */
export function useOptimizationProfileController(
  initialXParam: string,
  initialYParam: string,
  initialZMetric: string,
): OptimizationProfileController {
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


  // Mouse drag handlers for 3D rotation
  const handleMouseDown = (e: MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: MouseEvent<HTMLCanvasElement>) => {
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

  return {
    paramX, setParamX, paramY, setParamY, metricZ, setMetricZ,
    displayMode, setDisplayMode, rotX, setRotX, rotY, setRotY, zoom, setZoom,
    canvasRef, availableParams, availableMetrics, gridSize,
    points, grid, clusters, stats, handleMouseDown, handleMouseMove, handleMouseUp,
  };
}
