'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useTradingStore } from '../../store/useTradingStore';
import type { Widget } from '../../types/widget';
import { MarketsWidget } from '../widgets/MarketsWidget';
import { WatchlistWidget } from '../widgets/WatchlistWidget';
import { ChartWidget } from '../widgets/ChartWidget';
import { PriceLadderWidget } from '../widgets/PriceLadderWidget';
import { OptionsGridWidget } from '../widgets/OptionsGridWidget';
import { PositionsWidget } from '../widgets/PositionsWidget';
import { TradeLogWidget } from '../widgets/TradeLogWidget';
import { TradePlanWidget } from '../widgets/TradePlanWidget';
import { EducationWidget } from '../widgets/EducationWidget';
import { ChallengesWidget } from '../widgets/ChallengesWidget';
import { DashboardView } from '../workflow/dashboard';
import { DataWorkspace } from '../workflow/data';
import { StrategyWorkspace } from '../workflow/strategies';
import { ResearchWorkspace } from '../workflow/research';
import { OptimizationView } from '../workflow/optimization';
import { PortfolioView } from '../workflow/portfolio';
import { AgenticView } from '../workflow/agentic';
import { SimulationView } from '../workflow/simulation';
import { RiskView } from '../workflow/risk';
import { TradingView } from '../workflow/trading';
import { IndicatorWorkspace } from '../workflow/indicators';
import { X, Maximize2, Minimize2, GripHorizontal, Layers, ArrowRightLeft } from 'lucide-react';

import {
  GRID_COLUMNS,
  GRID_ROW_HEIGHT,
  GRID_GAP,
  rectOf,
  isAreaFree,
  cellFromPoint,
  usedRowCount
} from '../../utils/gridLayout';

export const WorkspaceGrid: React.FC = () => {
  const {
    workspaces,
    activeWorkspaceId,
    removeWidget,
    expandWidget,
    contractWidget,
    switchExpandedWidget,
    reorderWidgets,
    moveWidgetToCell,
    resizeWidget
  } = useTradingStore();

  const [draggedWidgetId, setDraggedWidgetId] = useState<string | number | null>(null);
  const [dropTargetId, setDropTargetId] = useState<string | number | null>(null);
  const [resizingWidgetId, setResizingWidgetId] = useState<string | number | null>(null);
  // Cell under the cursor while dragging over blank canvas, for the drop ghost.
  const [ghostCell, setGhostCell] = useState<{ col: number; row: number } | null>(null);

  // Authoritative copy of the dragged id. `dataTransfer.getData()` is blocked
  // during dragover for security, and React state is stale inside native
  // handlers, so the ref is what the drop handlers actually read.
  const draggedIdRef = useRef<string | null>(null);
  const containerRef = useRef<HTMLElement | null>(null);
  // Guards the flicker: dragenter/dragleave also fire when the cursor crosses
  // into a *child* of the card, so we only clear on a real boundary exit.
  const dragDepthRef = useRef<Map<string | number, number>>(new Map());

  // eslint-disable-next-line eqeqeq -- workspace id is number; caller may pass string
  const currentWorkspace = workspaces.find((w) => w.id == activeWorkspaceId) || workspaces[0];
  const expandedWidgetId = currentWorkspace.expandedWidgetId;
  const isExpanded = Boolean(expandedWidgetId);

  const endDrag = useCallback(() => {
    draggedIdRef.current = null;
    dragDepthRef.current.clear();
    setDraggedWidgetId(null);
    setDropTargetId(null);
    setGhostCell(null);
  }, []);

  // Esc cancels an in-flight drag without moving anything.
  useEffect(() => {
    if (!draggedWidgetId) return undefined;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') endDrag();
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [draggedWidgetId, endDrag]);

  const handleDragStart = (e: React.DragEvent, widgetId: string | number) => {
    e.dataTransfer.setData('text/plain', String(widgetId));
    e.dataTransfer.effectAllowed = 'move';

    // Drag the whole card as the ghost, not just the little title tab, so the
    // cursor carries a recognisable picture of the widget being moved.
    const card = (e.currentTarget as HTMLElement).closest('.widget-card');
    if (card && typeof e.dataTransfer.setDragImage === 'function') {
      const rect = card.getBoundingClientRect();
      e.dataTransfer.setDragImage(card, e.clientX - rect.left, e.clientY - rect.top);
    }

    draggedIdRef.current = String(widgetId);
    setDraggedWidgetId(widgetId);
  };

  const handleDragEnd = endDrag;

  const handleDragEnter = (_e: React.DragEvent, targetWidgetId: string | number) => {
    const depth = (dragDepthRef.current.get(targetWidgetId) || 0) + 1;
    dragDepthRef.current.set(targetWidgetId, depth);
    // Never highlight the card being dragged - dropping on yourself is a no-op.
    if (String(draggedIdRef.current) !== String(targetWidgetId)) {
      setDropTargetId(targetWidgetId);
    }
  };

  const handleDragOver = (e: React.DragEvent, targetWidgetId: string | number) => {
    e.preventDefault();
    // Cards stopPropagation, and they cover the whole viewport when the grid
    // overflows - so edge auto-scroll has to be driven from here too, or it can
    // never fire in exactly the case it exists for.
    autoScroll(e);
    const isSelf = String(draggedIdRef.current) === String(targetWidgetId);
    e.dataTransfer.dropEffect = isSelf ? 'none' : 'move';
    if (!isSelf && dropTargetId !== targetWidgetId) {
      setDropTargetId(targetWidgetId);
    }
  };

  const handleDragLeave = (_e: React.DragEvent, targetWidgetId: string | number) => {
    const depth = (dragDepthRef.current.get(targetWidgetId) || 1) - 1;
    dragDepthRef.current.set(targetWidgetId, depth);
    if (depth <= 0) {
      dragDepthRef.current.delete(targetWidgetId);
      setDropTargetId((current) => (current === targetWidgetId ? null : current));
    }
  };

  const handleDrop = (e: React.DragEvent, targetWidgetId: string | number) => {
    e.preventDefault();
    const sourceId = e.dataTransfer.getData('text/plain') || draggedIdRef.current;
    if (sourceId && targetWidgetId && String(sourceId) !== String(targetWidgetId)) {
      reorderWidgets(String(sourceId), String(targetWidgetId));
    }
    endDrag();
  };

  /**
   * Corner resize. Uses pointer capture rather than HTML5 drag-and-drop: DnD is
   * for moving widgets, and mixing the two on one card makes the browser pick
   * the wrong gesture. Pixel deltas are converted to grid spans live, so the
   * widget snaps cell by cell as you pull the corner.
   */
  const startResize = (e: React.PointerEvent<HTMLDivElement>, widget: Widget) => {
    // Left button only, and never let this bubble into a drag or a header click.
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();

    const container = containerRef.current;
    const card = (e.currentTarget as HTMLElement).closest('.widget-card');
    if (!container || !card) return;

    const rowUnit = GRID_ROW_HEIGHT + GRID_GAP;
    const colUnit = (container.clientWidth - 16 + GRID_GAP) / GRID_COLUMNS;

    const startX = e.clientX;
    const startY = e.clientY;
    const startRect = rectOf(widget);
    const startCol = startRect.colSpan;
    const startRow = startRect.rowSpan;

    e.currentTarget.setPointerCapture?.(e.pointerId);
    setResizingWidgetId(widget.id);

    let frame: number | null = null;
    const onMove = (ev: PointerEvent) => {
      if (frame) return; // coalesce to one update per animation frame
      frame = requestAnimationFrame(() => {
        frame = null;
        resizeWidget(
          widget.id,
          startCol + (ev.clientX - startX) / colUnit,
          startRow + (ev.clientY - startY) / rowUnit
        );
      });
    };

    const onUp = () => {
      if (frame) cancelAnimationFrame(frame);
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
      setResizingWidgetId(null);
    };

    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  };

  // Auto-scroll the workspace when the cursor nears its top/bottom edge, so a
  // widget can be dragged to a slot that is currently off-screen.
  const autoScroll = (e: React.DragEvent | DragEvent) => {
    const el = containerRef.current;
    if (!el || el.scrollHeight <= el.clientHeight) return;
    const rect = el.getBoundingClientRect();
    const ZONE = 64;
    const SPEED = 14;
    if (e.clientY - rect.top < ZONE) el.scrollTop -= SPEED;
    else if (rect.bottom - e.clientY < ZONE) el.scrollTop += SPEED;
  };

  const renderWidgetContent = (widget: Widget): React.JSX.Element => {
    switch (widget.type) {
      case 'markets':
        return <MarketsWidget />;
      case 'watchlist':
        return <WatchlistWidget />;
      case 'chart':
        return <ChartWidget symbol={widget.symbol || 'ESU5'} widgetId={widget.id} />;
      case 'priceLadder':
        return <PriceLadderWidget symbol={widget.symbol || 'ESU5'} />;
      case 'optionsGrid':
        return <OptionsGridWidget symbol={widget.symbol || 'ESU5'} />;
      case 'positions':
        return <PositionsWidget />;
      case 'tradeLog':
        return <TradeLogWidget />;
      case 'tradePlan':
        return <TradePlanWidget />;
      case 'education':
        return <EducationWidget />;
      case 'challenges':
        return <ChallengesWidget />;
      case 'dashboard':
        return <DashboardView />;
      case 'data':
        return <DataWorkspace />;
      case 'strategies':
        return <StrategyWorkspace />;
      case 'research':
        return <ResearchWorkspace />;
      case 'optimization':
        return <OptimizationView />;
      case 'portfolio':
        return <PortfolioView />;
      case 'agentic':
        return <AgenticView />;
      case 'simulation':
        return <SimulationView />;
      case 'risk':
        return <RiskView />;
      case 'trading':
        return <TradingView />;
      case 'indicators':
        return <IndicatorWorkspace />;
      default:
        return <MarketsWidget />;
    }
  };

  // Render Fullscreen Expanded Widget with Sub-Tabs Bar
  if (isExpanded) {
    // eslint-disable-next-line eqeqeq -- widget id may match string or number
    const activeWidget = currentWorkspace.widgets.find((w) => w.id == expandedWidgetId) || currentWorkspace.widgets[0];

    return (
      <main className="workspace-container" style={{ display: 'flex', flexDirection: 'column', gap: 0, padding: '6px' }}>
        {/* Workspace Sub-Tabs Bar for Shared Widgets */}
        <div style={{ display: 'flex', alignItems: 'center', background: 'var(--cme-navy-dark)', border: '1px solid var(--cme-navy-border)', borderRadius: 'var(--radius-sm) var(--radius-sm) 0 0', padding: '4px 8px', gap: '4px', overflowX: 'auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '0 8px', color: 'var(--cme-blue-cyan)', fontWeight: 700, fontSize: '11px', whiteSpace: 'nowrap' }}>
            <Layers size={14} /> SUB-TABS:
          </div>

          {currentWorkspace.widgets.map((w) => {
            // eslint-disable-next-line eqeqeq -- widget id comparison
            const isActive = w.id == expandedWidgetId;
            return (
              <div
                key={w.id}
                onClick={() => switchExpandedWidget(w.id)}
                style={{
                  padding: '4px 12px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '11px',
                  fontWeight: isActive ? 600 : 500,
                  background: isActive ? 'var(--cme-blue-primary)' : 'var(--cme-navy-header)',
                  color: isActive ? '#ffffff' : 'var(--text-muted)',
                  cursor: 'pointer',
                  border: '1px solid var(--cme-navy-border)',
                  whiteSpace: 'nowrap',
                  transition: 'all 0.15s ease'
                }}
              >
                {w.title}
              </div>
            );
          })}
        </div>

        {/* Expanded Full-Screen Widget */}
        <div className="widget-card" style={{ flex: 1, borderRadius: '0 0 var(--radius-sm) var(--radius-sm)' }}>
          <div className="widget-header">
            <div className="widget-title">
              <GripHorizontal size={14} color="var(--text-dim)" />
              <span>{activeWidget.title} (EXPANDED VIEW)</span>
            </div>

            <div className="widget-controls">
              {/* Contract Icon to return to shared screen view */}
              <span className="widget-btn" onClick={(e: React.MouseEvent) => { e.stopPropagation(); contractWidget(); }} title="Contract Window (Share Workspace Screen)">
                <Minimize2 size={14} color="var(--cme-blue-cyan)" />
              </span>
              <span className="widget-btn" onClick={(e: React.MouseEvent) => { e.stopPropagation(); contractWidget(); removeWidget(activeWidget.id); }} title="Close Widget">
                <X size={14} />
              </span>
            </div>
          </div>

          <div className="widget-body">
            {renderWidgetContent(activeWidget)}
          </div>
        </div>
      </main>
    );
  }

  // Normal Grid Mode (All Widgets Share the Workspace Screen)
  const draggedTitle =
    currentWorkspace.widgets.find((w) => String(w.id) === String(draggedWidgetId))?.title || 'widget';

  const draggedWidget = currentWorkspace.widgets.find(
    (w) => String(w.id) === String(draggedWidgetId)
  );
  const draggedRect = draggedWidget ? rectOf(draggedWidget) : null;

  // Clamp the ghost so a widget dropped near the right edge stays on the grid,
  // matching what moveWidgetToCell will actually do.
  const ghostColumn =
    ghostCell && draggedRect
      ? Math.min(ghostCell.col, GRID_COLUMNS - draggedRect.colSpan + 1)
      : 1;

  const ghostFits =
    ghostCell && draggedRect
      ? isAreaFree(
          currentWorkspace.widgets,
          { col: ghostColumn, row: ghostCell.row, colSpan: draggedRect.colSpan, rowSpan: draggedRect.rowSpan },
          String(draggedWidgetId)
        )
      : false;

  // Always keep a spare row of blank canvas below the content, so there is
  // somewhere to drop even when the widgets fill the viewport.
  const gridMinRows = usedRowCount(currentWorkspace.widgets) + (draggedWidgetId ? 3 : 1);

  return (
    <main
      ref={containerRef}
      className={`workspace-container ${draggedWidgetId ? 'is-drag-active' : ''}`}
      style={{ gridTemplateRows: `repeat(${gridMinRows}, ${GRID_ROW_HEIGHT}px)` }}
      // Only reached when the cursor is over blank canvas: the cards
      // stopPropagation on their own drag events.
      onDragOver={(e: React.DragEvent<HTMLElement>) => {
        if (!draggedIdRef.current) return;
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        autoScroll(e);
        setDropTargetId(null);
        // Track the cell under the cursor so the ghost previews the landing spot.
        setGhostCell(cellFromPoint(e.currentTarget, e.clientX, e.clientY));
      }}
      onDragLeave={(e: React.DragEvent<HTMLElement>) => {
        if (e.currentTarget.contains(e.relatedTarget as Node)) return;
        setGhostCell(null);
      }}
      onDrop={(e: React.DragEvent<HTMLElement>) => {
        e.preventDefault();
        const sourceId = e.dataTransfer.getData('text/plain') || draggedIdRef.current;
        if (sourceId) {
          const { col, row } = cellFromPoint(e.currentTarget, e.clientX, e.clientY);
          moveWidgetToCell(sourceId, col, row);
        }
        endDrag();
      }}
    >
      {currentWorkspace.widgets.map((w, idx) => {
        const isBeingDragged = String(draggedWidgetId) === String(w.id);
        const isTarget = String(dropTargetId) === String(w.id);
        const isResizing = String(resizingWidgetId) === String(w.id);
        const rect = rectOf(w);

        return (
          <div
            key={w.id}
            className={`widget-card ${draggedWidgetId && !isBeingDragged ? 'drag-candidate' : ''} ${isTarget ? 'drag-over-dark-gray' : ''} ${isBeingDragged ? 'is-dragging' : ''} ${isResizing ? 'is-resizing' : ''}`}
            style={{
              // Explicit placement: the widget sits exactly where it was put.
              gridColumn: `${rect.col} / span ${rect.colSpan}`,
              gridRow: `${rect.row} / span ${rect.rowSpan}`
            }}
            onDragEnter={(e: React.DragEvent) => {
              e.stopPropagation();
              handleDragEnter(e, w.id);
            }}
            onDragOver={(e: React.DragEvent) => {
              e.stopPropagation();
              handleDragOver(e, w.id);
            }}
            onDragLeave={(e: React.DragEvent) => {
              e.stopPropagation();
              handleDragLeave(e, w.id);
            }}
            onDrop={(e: React.DragEvent) => {
              e.stopPropagation();
              handleDrop(e, w.id);
            }}
          >
            {/* Dark Gray Highlighted Drop Zone Overlay */}
            {isTarget && (
              <div className="dark-gray-drop-overlay">
                <div className="dark-gray-drop-badge">
                  <ArrowRightLeft size={16} color="#00e473" />
                  <span>Release to swap with {draggedTitle}</span>
                </div>
              </div>
            )}

            {/* Widget Card Header Bar */}
            <div className="widget-header">
              {/* UPPER LEFT TITLE DRAG TAB (hover, click & hold to drag) */}
              <div
                className="widget-product-code-tab"
                draggable
                onDragStart={(e: React.DragEvent) => handleDragStart(e, w.id)}
                onDragEnd={handleDragEnd}
                role="button"
                aria-grabbed={isBeingDragged}
                aria-label={`Drag ${w.title} (position ${idx + 1} of ${currentWorkspace.widgets.length}) to a new location`}
                title="Click and hold to drag this widget onto another slot to swap, or onto empty space to send it to the end"
              >
                <GripHorizontal size={13} className="drag-grip-icon" />
                <span className="product-title-text">{w.title}</span>
              </div>

              <div className="widget-controls">
                {/* Expand Icon to fill workspace & create sub-tabs */}
                <span className="widget-btn" onClick={(e: React.MouseEvent) => { e.stopPropagation(); expandWidget(w.id); }} title="Expand Window (Fill Workspace)">
                  <Maximize2 size={14} />
                </span>
                <span className="widget-btn" onClick={(e: React.MouseEvent) => { e.stopPropagation(); removeWidget(w.id); }} title="Close Widget">
                  <X size={14} />
                </span>
              </div>
            </div>

            {/* Widget Content */}
            <div className="widget-body">
              {renderWidgetContent(w)}
            </div>

            {/* Bottom-right corner grip: drag to resize across grid cells */}
            <div
              className="widget-resize-handle"
              onPointerDown={(e: React.PointerEvent<HTMLDivElement>) => startResize(e, w)}
              role="separator"
              aria-label={`Resize ${w.title}. Currently ${w.colSpan || 6} of ${GRID_COLUMNS} columns wide.`}
              title="Drag to resize this widget"
            />

            {isResizing && (
              <div className="widget-resize-readout">
                {w.colSpan || 6} x {w.rowSpan || 2}
              </div>
            )}
          </div>
        );
      })}

      {ghostCell && draggedRect && (
        <div
          className={`drop-ghost ${ghostFits ? '' : 'drop-ghost-blocked'}`}
          style={{
            gridColumn: `${ghostColumn} / span ${draggedRect.colSpan}`,
            gridRow: `${ghostCell.row} / span ${draggedRect.rowSpan}`
          }}
        >
          <div className="widget-drop-slot-label">
            <ArrowRightLeft size={16} />
            <span>
              {ghostFits
                ? `Drop ${draggedTitle} here (${ghostColumn}, ${ghostCell.row})`
                : 'Occupied - pick an empty area'}
            </span>
          </div>
        </div>
      )}
    </main>
  );
};
