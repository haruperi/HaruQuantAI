import React, { useMemo, useRef, useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { Strategy } from '../../../app/types';
import {
  DATABANK_METRIC_COLUMNS,
  type ColumnDefinition,
  type DatabankView,
} from './databankColumns';

interface StrategyTableProps {
  data: Strategy[];
  selectedId: string;
  selectedRows: string[];
  onSelect: (id: string) => void;
  onRows: (ids: string[]) => void;
  activeView: DatabankView;
}

/**
 * Inline mini equity chart sparkline rendered via SVG.
 */
function MiniEquitySparkline({ equity }: { equity?: number[] }) {
  if (!equity || equity.length < 2) {
    return <span style={{ color: '#8b949e', fontSize: 11 }}>—</span>;
  }

  const min = Math.min(...equity);
  const max = Math.max(...equity);
  const range = max - min || 1;
  const w = 90;
  const h = 20;

  const points = equity
    .map((v, i) => {
      const x = (i / (equity.length - 1)) * (w - 4) + 2;
      const y = h - 2 - ((v - min) / range) * (h - 4);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(' ');

  const isProfitable = equity[equity.length - 1] >= equity[0];
  const strokeColor = isProfitable ? '#3fb950' : '#f85149';

  return (
    <svg width={w} height={h} style={{ display: 'block', margin: '0 auto' }}>
      <polyline
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={points}
      />
    </svg>
  );
}

const columnHelper = createColumnHelper<Strategy>();

export function StrategyTable({
  data,
  selectedId,
  selectedRows,
  onSelect,
  onRows,
  activeView,
}: StrategyTableProps) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'netProfit', desc: true }]);
  const parentRef = useRef<HTMLDivElement>(null);

  const metricMap = useMemo(() => {
    const map = new Map<string, ColumnDefinition>();
    for (const m of DATABANK_METRIC_COLUMNS) {
      map.set(m.id, m);
    }
    return map;
  }, []);

  const columns = useMemo(() => {
    // 1. Selection Checkbox Column
    const cols: ColumnDef<Strategy, any>[] = [
      columnHelper.display({
        id: 'select',
        size: 34,
        header: () => (
          <input
            aria-label="Select all"
            type="checkbox"
            checked={data.length > 0 && data.every(x => selectedRows.includes(x.id))}
            onChange={e => onRows(e.target.checked ? data.map(x => x.id) : [])}
          />
        ),
        cell: c => (
          <input
            aria-label={`Select ${c.row.original.name}`}
            type="checkbox"
            checked={selectedRows.includes(c.row.original.id)}
            onChange={e =>
              onRows(
                e.target.checked
                  ? [...selectedRows, c.row.original.id]
                  : selectedRows.filter(id => id !== c.row.original.id)
              )
            }
          />
        ),
      }),
    ];

    // 2. Dynamic Metric Columns from Active View
    for (const viewCol of activeView.columns) {
      const metric = metricMap.get(viewCol.columnId);
      if (!metric) continue;

      cols.push(
        columnHelper.accessor(
          strategy => {
            try {
              return metric.calculate(strategy);
            } catch {
              return 'N/A';
            }
          },
          {
            id: metric.id,
            header: metric.name,
            size: viewCol.width || metric.defaultWidth,
            cell: cellProps => {
              const val = cellProps.getValue();
              const align = metric.align;

              if (metric.format === 'sparkline') {
                return (
                  <div style={{ textAlign: 'center' }}>
                    <MiniEquitySparkline equity={cellProps.row.original.equity?.map(e => e.value)} />
                  </div>
                );
              }

              let formatted = String(val);
              let color = 'inherit';

              if (typeof val === 'number') {
                if (metric.format === 'currency') {
                  formatted = `$${val.toLocaleString(undefined, {
                    minimumFractionDigits: metric.decimals ?? 0,
                    maximumFractionDigits: metric.decimals ?? 2,
                  })}`;
                  if (metric.id === 'netProfit' || metric.id === 'avgTrade') {
                    color = val > 0 ? '#3fb950' : val < 0 ? '#f85149' : 'inherit';
                  }
                } else if (metric.format === 'percent') {
                  formatted = `${val.toFixed(metric.decimals ?? 1)}%`;
                } else if (metric.format === 'integer') {
                  formatted = val.toLocaleString();
                } else {
                  formatted = val.toFixed(metric.decimals ?? 2);
                }
              }

              return (
                <div
                  style={{
                    textAlign: align,
                    color,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    fontWeight: metric.id === 'name' ? 600 : 'normal',
                  }}
                  title={String(val)}
                >
                  {formatted}
                </div>
              );
            },
          }
        )
      );
    }

    return cols;
  }, [data, selectedRows, onRows, activeView, metricMap]);

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const rows = table.getRowModel().rows;
  const virtual = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 30,
    overscan: 10,
  });

  return (
    <div className="data-grid" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="grid-header" style={{ display: 'flex', flexShrink: 0 }}>
        {table.getHeaderGroups().map(group =>
          group.headers.map(header => (
            <button
              key={header.id}
              style={{
                width: header.getSize(),
                textAlign: 'left',
                padding: '4px 8px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
              onClick={header.column.getToggleSortingHandler()}
            >
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {flexRender(header.column.columnDef.header, header.getContext())}
              </span>
              <span>
                {header.column.getIsSorted() === 'asc'
                  ? ' ▲'
                  : header.column.getIsSorted() === 'desc'
                  ? ' ▼'
                  : ''}
              </span>
            </button>
          ))
        )}
      </div>

      <div ref={parentRef} className="grid-scroll" style={{ flex: 1, overflow: 'auto' }}>
        <div style={{ height: virtual.getTotalSize(), position: 'relative' }}>
          {virtual.getVirtualItems().map(v => {
            const row = rows[v.index];
            if (!row) return null;
            return (
              <div
                key={row.id}
                className={`grid-row ${row.original.id === selectedId ? 'active' : ''}`}
                style={{
                  transform: `translateY(${v.start}px)`,
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  height: 30,
                }}
                onClick={() => onSelect(row.original.id)}
                onDoubleClick={() => onSelect(row.original.id)}
              >
                {row.getVisibleCells().map(cell => (
                  <div
                    key={cell.id}
                    style={{
                      width: cell.column.getSize(),
                      padding: '2px 8px',
                      boxSizing: 'border-box',
                    }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
