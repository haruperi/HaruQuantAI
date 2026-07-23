import { create } from 'zustand';
import { initialProducts } from '../mock/productsData';
import {
  GRID_COLUMNS,
  MIN_COL_SPAN,
  MAX_COL_SPAN,
  MIN_ROW_SPAN,
  MAX_ROW_SPAN,
  rectOf,
  isAreaFree,
  findFreeCell
} from '../utils/gridLayout';

export const useTradingStore = create((set, get) => ({
  // Account Financial State
  practiceBalance: 100000.00,
  challengeBalance: 100218.75,
  netPL: 0.00,
  margin: 0.00,
  available: 100000.00,
  ranking: '2nd',
  mode: 'practice', // 'practice' | 'challenge'
  theme: 'dark',   // 'dark' | 'light'
  oneClickTrading: false,

  // Workspace Management
  workspaces: [
    {
      id: 1,
      name: 'HaruQuantAI Workspace',
      expandedWidgetId: null,
      widgets: [
        { id: 'markets-1', type: 'markets', title: 'Markets', col: 1, row: 1, colSpan: 6, rowSpan: 2 },
        { id: 'chart-1', type: 'chart', title: 'ESU5 Chart', symbol: 'ESU5', col: 7, row: 1, colSpan: 6, rowSpan: 2 },
        { id: 'ladder-1', type: 'priceLadder', title: 'ESU5 DOM', symbol: 'ESU5', col: 1, row: 3, colSpan: 4, rowSpan: 2 },
        { id: 'positions-1', type: 'positions', title: 'Positions & Orders', col: 5, row: 3, colSpan: 8, rowSpan: 2 }
      ]
    },
    {
      id: 2,
      name: 'New Workspace-1',
      expandedWidgetId: null,
      widgets: [
        { id: 'watchlist-1', type: 'watchlist', title: 'Watchlist', col: 1, row: 1, colSpan: 6, rowSpan: 2 },
        { id: 'options-1', type: 'optionsGrid', title: 'ESU5 Options', symbol: 'ESU5', col: 7, row: 1, colSpan: 6, rowSpan: 2 }
      ]
    }
  ],
  activeWorkspaceId: 1,
  defaultWorkspaceId: 1,

  // Market Quotes Data
  products: initialProducts,
  selectedSymbol: 'ESU5',

  // Trading State: Orders, Positions, Trade Log
  orders: [
    {
      id: 'ORD-101',
      side: 'SELL',
      symbol: 'MGCQ5',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 1,
      type: 'LMT',
      fillPx: '-',
      limitPx: 3315.8,
      stopPx: '-',
      status: 'Working',
      timestamp: '11:14:20'
    },
    {
      id: 'ORD-102',
      side: 'SELL',
      symbol: 'MGCQ5',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 1,
      type: 'STP',
      fillPx: '-',
      limitPx: '-',
      stopPx: 3305.8,
      status: 'Working',
      timestamp: '11:14:35'
    },
    {
      id: 'ORD-103',
      side: 'BUY',
      symbol: 'MGCQ5',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 0,
      type: 'MKT',
      fillPx: 3308.3,
      limitPx: '-',
      stopPx: '-',
      status: 'Filled',
      timestamp: '11:15:02'
    },
    {
      id: 'ORD-104',
      side: 'SELL',
      symbol: 'CLQ5',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 0,
      type: 'MKT',
      fillPx: 65.07,
      limitPx: '-',
      stopPx: '-',
      status: 'Filled',
      timestamp: '11:16:10'
    },
    {
      id: 'ORD-105',
      side: 'BUY',
      symbol: 'ESU5',
      month: 'Sep 25',
      strike: '-',
      cp: '-',
      qty: 1,
      leaves: 0,
      type: 'STP',
      fillPx: 6244.0,
      limitPx: '-',
      stopPx: 6244.0,
      status: 'Filled',
      timestamp: '11:18:45'
    }
  ],

  positions: [
    {
      symbol: 'CLQ5',
      contract: 'WTI Crude Oil',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      position: 'Short 1',
      buys: 0,
      sells: 1,
      averagePx: 65.07,
      unrealizedPL: -10.00,
      realizedPL: 0.00
    },
    {
      symbol: 'ESU5',
      contract: 'E-mini S&P 500',
      month: 'Sep 25',
      strike: '-',
      cp: '-',
      position: 'Long 1',
      buys: 1,
      sells: 0,
      averagePx: 6244.00,
      unrealizedPL: -187.50,
      realizedPL: 0.00
    },
    {
      symbol: 'MGCQ5',
      contract: 'Micro Gold',
      month: 'Aug 25',
      strike: '-',
      cp: '-',
      position: 'Long 1',
      buys: 1,
      sells: 0,
      averagePx: 3308.30,
      unrealizedPL: 0.00,
      realizedPL: 0.00
    }
  ],

  tradeLog: [
    {
      id: 1,
      symbol: 'MNQU5',
      transactionDate: '6/27/2025 | 2:36:10 PM',
      openClose: 'Open',
      side: 'BUY',
      cp: '-',
      strike: '-',
      qty: 1,
      type: 'MKT',
      px: 0.0,
      tif: 'DAY',
      fillPx: 22681.25,
      stop: '-',
      stopPx: '$0.0',
      notes: 'Breakout entry on morning high'
    },
    {
      id: 2,
      symbol: 'MNQU5',
      transactionDate: '6/27/2025 | 2:40:53 PM',
      openClose: 'Close',
      side: 'SELL',
      cp: '-',
      strike: '-',
      qty: 1,
      type: 'MKT',
      px: 0.0,
      tif: 'DAY',
      fillPx: 22695.0,
      stop: '-',
      stopPx: '$0.0',
      notes: 'Profit target hit +13.75 pts'
    }
  ],

  // Active Order Ticket State
  isOrderTicketOpen: false,
  orderTicketProps: {
    symbol: 'ESU5',
    side: 'BUY',
    type: 'Market',
    defaultTab: 'futures'
  },

  // State Actions
  setMode: (mode) => set({ mode }),
  toggleTheme: () => set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
  toggleOneClickTrading: () => set((state) => ({ oneClickTrading: !state.oneClickTrading })),
  resetBalance: () => set((state) => ({
    practiceBalance: 100000.00,
    netPL: 0.00,
    margin: 0.00,
    available: 100000.00
  })),

  // Workspace Actions
  setActiveWorkspace: (id) => set({ activeWorkspaceId: id }),

  setDefaultWorkspace: (id) => set({ defaultWorkspaceId: id }),

  renameWorkspace: (id, name) => set((state) => ({
    workspaces: state.workspaces.map((ws) => ws.id == id ? { ...ws, name: name.trim() || ws.name } : ws)
  })),

  duplicateWorkspace: (id) => set((state) => {
    const source = state.workspaces.find((ws) => ws.id == id);
    if (!source || state.workspaces.length >= 10) return state;
    const newId = Math.max(...state.workspaces.map((ws) => Number(ws.id) || 0)) + 1;
    const copy = {
      ...source,
      id: newId,
      name: `${source.name} Copy`,
      expandedWidgetId: null,
      widgets: source.widgets.map((widget) => ({ ...widget, id: `${widget.type}-${newId}-${Date.now()}-${Math.random().toString(36).slice(2, 6)}` }))
    };
    return { workspaces: [...state.workspaces, copy], activeWorkspaceId: newId };
  }),

  deleteWorkspace: (id) => set((state) => {
    if (state.workspaces.length <= 1) return state;
    const remaining = state.workspaces.filter((ws) => ws.id != id);
    const nextActive = state.activeWorkspaceId == id ? remaining[0].id : state.activeWorkspaceId;
    const nextDefault = state.defaultWorkspaceId == id ? remaining[0].id : state.defaultWorkspaceId;
    return { workspaces: remaining, activeWorkspaceId: nextActive, defaultWorkspaceId: nextDefault };
  }),

  expandWidget: (widgetId) => set((state) => {
    const activeWs = state.workspaces.find((ws) => ws.id == state.activeWorkspaceId) || state.workspaces[0];
    const targetId = widgetId || (activeWs?.widgets[0]?.id);
    return {
      workspaces: state.workspaces.map((ws) =>
        ws.id == state.activeWorkspaceId ? { ...ws, expandedWidgetId: targetId } : ws
      )
    };
  }),

  contractWidget: () => set((state) => ({
    workspaces: state.workspaces.map((ws) =>
      ws.id == state.activeWorkspaceId ? { ...ws, expandedWidgetId: null } : ws
    )
  })),

  toggleExpandWidget: (widgetId) => set((state) => {
    const activeWs = state.workspaces.find((ws) => ws.id == state.activeWorkspaceId) || state.workspaces[0];
    const isCurrentlyExpanded = Boolean(activeWs?.expandedWidgetId);
    const targetId = widgetId || (activeWs?.widgets[0]?.id);
    return {
      workspaces: state.workspaces.map((ws) =>
        ws.id == state.activeWorkspaceId ? { ...ws, expandedWidgetId: isCurrentlyExpanded ? null : targetId } : ws
      )
    };
  }),

  switchExpandedWidget: (widgetId) => set((state) => ({
    workspaces: state.workspaces.map((ws) =>
      ws.id == state.activeWorkspaceId ? { ...ws, expandedWidgetId: widgetId } : ws
    )
  })),

  addWorkspace: () => set((state) => {
    if (state.workspaces.length >= 10) return state; // max 10 workspaces

    // Find highest index among existing "New Workspace-X" names
    let maxNum = 0;
    state.workspaces.forEach((ws) => {
      const match = ws.name.match(/^New Workspace-(\d+)$/i);
      if (match) {
        const num = parseInt(match[1], 10);
        if (num > maxNum) maxNum = num;
      }
    });
    const nextNum = maxNum + 1;
    const newId = Date.now();
    const newWs = {
      id: newId,
      name: `New Workspace-${nextNum}`,
      widgets: [
        { id: `markets-${newId}`, type: 'markets', title: 'Markets', colSpan: 6, rowSpan: 2 },
        { id: `chart-${newId}`, type: 'chart', title: 'ESU5 Chart', symbol: 'ESU5', colSpan: 6, rowSpan: 2 }
      ],
      expandedWidgetId: null
    };
    return {
      workspaces: [...state.workspaces, newWs],
      activeWorkspaceId: newId
    };
  }),

  /**
   * Drop a widget onto another widget: the two exchange rectangles. Each widget
   * adopts the other's position AND size, so a narrow DOM dropped on a wide
   * Positions slot grows to fill it. Nothing else in the grid moves.
   */
  reorderWidgets: (sourceWidgetId, targetWidgetId) => set((state) => {
    const activeWs = state.workspaces.find((ws) => ws.id == state.activeWorkspaceId);
    if (!activeWs || !targetWidgetId || targetWidgetId === 'END') return state;

    const widgets = [...activeWs.widgets];
    const sourceIdx = widgets.findIndex((w) => String(w.id) === String(sourceWidgetId));
    const targetIdx = widgets.findIndex((w) => String(w.id) === String(targetWidgetId));
    if (sourceIdx === -1 || targetIdx === -1 || sourceIdx === targetIdx) return state;

    const sourceRect = rectOf(widgets[sourceIdx]);
    const targetRect = rectOf(widgets[targetIdx]);

    widgets[sourceIdx] = { ...widgets[sourceIdx], ...targetRect };
    widgets[targetIdx] = { ...widgets[targetIdx], ...sourceRect };

    return {
      workspaces: state.workspaces.map((ws) =>
        ws.id === state.activeWorkspaceId ? { ...ws, widgets } : ws
      )
    };
  }),

  /**
   * Drop a widget onto empty canvas: it is pinned at those exact coordinates
   * and stays there, leaving a hole behind. This is the whole point of explicit
   * placement - an order-only grid always re-packs the widget back against its
   * neighbours, so blank space can never actually be occupied.
   *
   * Returns unchanged state when the target area is taken, so a bad drop is a
   * no-op rather than an overlap.
   */
  moveWidgetToCell: (widgetId, col, row) => set((state) => {
    const activeWs = state.workspaces.find((ws) => ws.id == state.activeWorkspaceId);
    if (!activeWs) return state;

    const widget = activeWs.widgets.find((w) => String(w.id) === String(widgetId));
    if (!widget) return state;

    const { colSpan, rowSpan } = rectOf(widget);
    // Keep the widget fully on-grid if dropped near the right edge.
    const nextCol = Math.min(Math.max(col, 1), GRID_COLUMNS - colSpan + 1);
    const nextRow = Math.max(row, 1);

    if (widget.col === nextCol && widget.row === nextRow) return state;
    if (!isAreaFree(activeWs.widgets, { col: nextCol, row: nextRow, colSpan, rowSpan }, widgetId)) {
      return state;
    }

    return {
      workspaces: state.workspaces.map((ws) =>
        ws.id == state.activeWorkspaceId
          ? {
              ...ws,
              widgets: ws.widgets.map((w) =>
                String(w.id) === String(widgetId) ? { ...w, col: nextCol, row: nextRow } : w
              )
            }
          : ws
      )
    };
  }),

  /**
   * Resize a widget by corner drag. Spans are clamped to the 12-column grid;
   * MIN_COL_SPAN keeps a widget wide enough for its header controls to fit.
   */
  resizeWidget: (widgetId, colSpan, rowSpan) => set((state) => {
    const activeWs = state.workspaces.find((ws) => ws.id == state.activeWorkspaceId);
    if (!activeWs) return state;

    const widget = activeWs.widgets.find((w) => String(w.id) === String(widgetId));
    if (!widget) return state;

    const { col, row } = rectOf(widget);
    // Cap the width at the grid edge as well as the absolute maximum.
    const nextColSpan = Math.min(
      Math.max(Math.round(colSpan), MIN_COL_SPAN),
      Math.min(MAX_COL_SPAN, GRID_COLUMNS - col + 1)
    );
    const nextRowSpan = Math.min(Math.max(Math.round(rowSpan), MIN_ROW_SPAN), MAX_ROW_SPAN);

    // No-op when the pointer hasn't crossed a cell boundary yet, so a resize
    // drag doesn't re-render the workspace on every single mousemove.
    if (widget.colSpan === nextColSpan && widget.rowSpan === nextRowSpan) return state;

    // Refuse to grow into a neighbour; shrinking is always allowed.
    const grew = nextColSpan > (widget.colSpan || 6) || nextRowSpan > (widget.rowSpan || 2);
    if (grew && !isAreaFree(activeWs.widgets, { col, row, colSpan: nextColSpan, rowSpan: nextRowSpan }, widgetId)) {
      return state;
    }

    return {
      workspaces: state.workspaces.map((ws) =>
        ws.id == state.activeWorkspaceId
          ? {
              ...ws,
              widgets: ws.widgets.map((w) =>
                String(w.id) === String(widgetId)
                  ? { ...w, colSpan: nextColSpan, rowSpan: nextRowSpan }
                  : w
              )
            }
          : ws
      )
    };
  }),

  addWidgetToWorkspace: (widgetType, customTitle, symbol = 'ESU5') => set((state) => {
    const updatedWs = state.workspaces.map((ws) => {
      if (ws.id === state.activeWorkspaceId) {
        const newWidgetId = `${widgetType}-${Date.now()}`;
        // Drop new widgets into the first gap that fits, so they never land on
        // top of an existing one now that placement is explicit.
        const cell = findFreeCell(ws.widgets, 6, 2);
        return {
          ...ws,
          widgets: [
            ...ws.widgets,
            { id: newWidgetId, type: widgetType, title: customTitle || widgetType, symbol, ...cell, colSpan: 6, rowSpan: 2 }
          ]
        };
      }
      return ws;
    });
    return { workspaces: updatedWs };
  }),

  removeWidget: (widgetId) => set((state) => ({
    workspaces: state.workspaces.map((ws) => {
      if (ws.id === state.activeWorkspaceId) {
        return {
          ...ws,
          widgets: ws.widgets.filter((w) => w.id !== widgetId)
        };
      }
      return ws;
    })
  })),

  // Order Ticket Controls
  openOrderTicket: (props = {}) => set((state) => ({
    isOrderTicketOpen: true,
    orderTicketProps: { ...state.orderTicketProps, ...props }
  })),
  closeOrderTicket: () => set({ isOrderTicketOpen: false }),

  // Order Execution & Simulation Engine
  submitOrder: (orderData) => set((state) => {
    const { symbol, side, qty, orderType, limitPrice, stopPrice, tif, cp, strike } = orderData;
    const targetProduct = state.products.find((p) => p.symbol === symbol) || state.products[0];
    const fillPrice = orderType === 'Market' ? (side === 'BUY' ? targetProduct.ask : targetProduct.bid) : (limitPrice || targetProduct.lastPrice);

    const newOrder = {
      id: `ORD-${Math.floor(1000 + Math.random() * 9000)}`,
      side,
      symbol,
      month: targetProduct.contractMonth,
      strike: strike || '-',
      cp: cp || '-',
      qty: Number(qty),
      leaves: orderType === 'Market' ? 0 : Number(qty),
      type: orderType === 'Market' ? 'MKT' : orderType === 'Limit' ? 'LMT' : 'STP',
      fillPx: orderType === 'Market' ? fillPrice : '-',
      limitPx: limitPrice || '-',
      stopPx: stopPrice || '-',
      status: orderType === 'Market' ? 'Filled' : 'Working',
      timestamp: new Date().toLocaleTimeString('en-US', { hour12: false })
    };

    let updatedPositions = [...state.positions];
    let updatedLog = [...state.tradeLog];
    let netPLChange = 0;

    if (orderType === 'Market') {
      const existingPosIndex = updatedPositions.findIndex((p) => p.symbol === symbol);
      if (existingPosIndex >= 0) {
        const existingPos = updatedPositions[existingPosIndex];
        const isLong = existingPos.position.includes('Long');
        const posQty = parseInt(existingPos.position.replace(/[^0-9]/g, '')) || 1;

        if ((side === 'BUY' && isLong) || (side === 'SELL' && !isLong)) {
          // Increase position size
          const newQty = posQty + Number(qty);
          updatedPositions[existingPosIndex] = {
            ...existingPos,
            position: `${isLong ? 'Long' : 'Short'} ${newQty}`,
            buys: side === 'BUY' ? existingPos.buys + Number(qty) : existingPos.buys,
            sells: side === 'SELL' ? existingPos.sells + Number(qty) : existingPos.sells
          };
        } else {
          // Reduce or close position
          if (posQty <= Number(qty)) {
            updatedPositions.splice(existingPosIndex, 1);
          } else {
            const newQty = posQty - Number(qty);
            updatedPositions[existingPosIndex] = {
              ...existingPos,
              position: `${isLong ? 'Long' : 'Short'} ${newQty}`
            };
          }
        }
      } else {
        // Create new position
        updatedPositions.push({
          symbol,
          contract: targetProduct.name,
          month: targetProduct.contractMonth,
          strike: strike || '-',
          cp: cp || '-',
          position: `${side === 'BUY' ? 'Long' : 'Short'} ${qty}`,
          buys: side === 'BUY' ? Number(qty) : 0,
          sells: side === 'SELL' ? Number(qty) : 0,
          averagePx: fillPrice,
          unrealizedPL: 0.00,
          realizedPL: 0.00
        });
      }

      // Add to Trade Log
      updatedLog.unshift({
        id: Date.now(),
        symbol,
        transactionDate: `${new Date().toLocaleDateString()} | ${new Date().toLocaleTimeString()}`,
        openClose: 'Open',
        side,
        cp: cp || '-',
        strike: strike || '-',
        qty: Number(qty),
        type: newOrder.type,
        px: 0.0,
        tif: tif || 'DAY',
        fillPx: fillPrice,
        stop: '-',
        stopPx: '$0.0',
        notes: 'Simulated Order Execution'
      });
    }

    return {
      orders: [newOrder, ...state.orders],
      positions: updatedPositions,
      tradeLog: updatedLog,
      isOrderTicketOpen: false
    };
  }),

  flattenPositions: () => set((state) => {
    // Flatten all active positions instantly
    const newLogEntries = state.positions.map((pos) => ({
      id: Date.now() + Math.random(),
      symbol: pos.symbol,
      transactionDate: `${new Date().toLocaleDateString()} | ${new Date().toLocaleTimeString()}`,
      openClose: 'Close',
      side: pos.position.includes('Long') ? 'SELL' : 'BUY',
      cp: pos.cp,
      strike: pos.strike,
      qty: parseInt(pos.position.replace(/[^0-9]/g, '')) || 1,
      type: 'MKT',
      px: 0.0,
      tif: 'DAY',
      fillPx: pos.averagePx,
      stop: '-',
      stopPx: '$0.0',
      notes: 'Flatten All Positions Shortcut'
    }));

    return {
      positions: [],
      tradeLog: [...newLogEntries, ...state.tradeLog]
    };
  }),

  cancelAllOrders: () => set((state) => ({
    orders: state.orders.map((o) => o.status === 'Working' ? { ...o, status: 'Cancelled', leaves: 0 } : o)
  })),

  cancelOrder: (orderId) => set((state) => ({
    orders: state.orders.map((o) => o.id === orderId ? { ...o, status: 'Cancelled', leaves: 0 } : o)
  })),

  // Real-Time Ticker Simulator Loop
  updateQuotes: () => set((state) => {
    const updatedProducts = state.products.map((p) => {
      const delta = (Math.random() - 0.49) * (p.lastPrice > 1000 ? 0.75 : 0.05);
      const newLast = parseFloat((p.lastPrice + delta).toFixed(2));
      const newChange = parseFloat((p.change + delta).toFixed(2));
      const newChangePct = parseFloat(((newChange / p.priorSettle) * 100).toFixed(2));
      const newBid = parseFloat((newLast - (p.lastPrice > 1000 ? 0.25 : 0.01)).toFixed(2));
      const newAsk = parseFloat((newLast + (p.lastPrice > 1000 ? 0.25 : 0.01)).toFixed(2));

      return {
        ...p,
        lastPrice: newLast,
        change: newChange,
        changePercent: newChangePct,
        high: Math.max(p.high, newLast),
        low: Math.min(p.low, newLast),
        bid: newBid,
        ask: newAsk,
        volume: p.volume + Math.floor(Math.random() * 3)
      };
    });

    // Update Unrealized P/L for open positions
    const updatedPositions = state.positions.map((pos) => {
      const prod = updatedProducts.find((p) => p.symbol === pos.symbol);
      if (!prod) return pos;
      const isLong = pos.position.includes('Long');
      const qty = parseInt(pos.position.replace(/[^0-9]/g, '')) || 1;
      const diff = isLong ? (prod.lastPrice - pos.averagePx) : (pos.averagePx - prod.lastPrice);
      const multiplier = pos.symbol.startsWith('M') ? 5 : 50; // Contract multiplier
      const uPL = parseFloat((diff * qty * multiplier).toFixed(2));
      return { ...pos, unrealizedPL: uPL };
    });

    const totalNetPL = updatedPositions.reduce((acc, pos) => acc + pos.unrealizedPL, 0);

    return {
      products: updatedProducts,
      positions: updatedPositions,
      netPL: totalNetPL,
      available: state.practiceBalance + totalNetPL
    };
  })
}));
