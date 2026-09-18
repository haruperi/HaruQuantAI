import { useMemo, useRef, useState } from 'react';
import { createColumnHelper, flexRender, getCoreRowModel, getSortedRowModel, useReactTable, type SortingState } from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { Strategy } from '../app/types';

const column = createColumnHelper<Strategy>();
export function StrategyTable({ data, selectedId, selectedRows, onSelect, onRows }: { data: Strategy[]; selectedId: string; selectedRows: string[]; onSelect: (id: string) => void; onRows: (ids: string[]) => void }) {
  const [sorting, setSorting] = useState<SortingState>([{ id: 'netProfit', desc: true }]); const parentRef = useRef<HTMLDivElement>(null);
  const columns = useMemo(() => [
    column.display({ id: 'select', size: 34, header: () => <input aria-label="Select all" type="checkbox" checked={data.length > 0 && data.every(x => selectedRows.includes(x.id))} onChange={e => onRows(e.target.checked ? data.map(x => x.id) : [])}/>, cell: c => <input aria-label={`Select ${c.row.original.name}`} type="checkbox" checked={selectedRows.includes(c.row.original.id)} onChange={e => onRows(e.target.checked ? [...selectedRows, c.row.original.id] : selectedRows.filter(id => id !== c.row.original.id))}/> }),
    column.accessor('name', { header: 'Strategy name', size: 190 }), column.accessor('symbol', { header: 'Symbol', size: 86 }), column.accessor('timeframe', { header: 'TF', size: 54 }),
    column.accessor(s => s.metrics.netProfit, { id: 'netProfit', header: 'Net profit', size: 100, cell: c => `$${c.getValue().toLocaleString()}` }),
    column.accessor(s => s.metrics.profitFactor, { id: 'pf', header: 'Profit factor', size: 92 }), column.accessor(s => s.metrics.maxDrawdown, { id: 'dd', header: 'Drawdown', size: 92, cell: c => `$${c.getValue().toLocaleString()}` }),
    column.accessor(s => s.metrics.trades, { id: 'trades', header: 'Trades', size: 70 }), column.accessor(s => s.metrics.sharpe, { id: 'sharpe', header: 'Sharpe', size: 70 }), column.accessor(s => s.metrics.stability, { id: 'stability', header: 'Stability', size: 74, cell: c => `${c.getValue()}%` }),
  ], [data, selectedRows, onRows]);
  const table = useReactTable({ data, columns, state: { sorting }, onSortingChange: setSorting, getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel() });
  const rows = table.getRowModel().rows; const virtual = useVirtualizer({ count: rows.length, getScrollElement: () => parentRef.current, estimateSize: () => 29, overscan: 10 });
  return <div className="data-grid"><div className="grid-header">{table.getHeaderGroups().map(group => group.headers.map(header => <button key={header.id} style={{ width: header.getSize() }} onClick={header.column.getToggleSortingHandler()}>{flexRender(header.column.columnDef.header, header.getContext())}<span>{header.column.getIsSorted() === 'asc' ? ' ▲' : header.column.getIsSorted() === 'desc' ? ' ▼' : ''}</span></button>))}</div><div ref={parentRef} className="grid-scroll"><div style={{ height: virtual.getTotalSize(), position: 'relative' }}>{virtual.getVirtualItems().map(v => { const row = rows[v.index]; return <div key={row.id} className={`grid-row ${row.original.id === selectedId ? 'active' : ''}`} style={{ transform: `translateY(${v.start}px)` }} onClick={() => onSelect(row.original.id)} onDoubleClick={() => onSelect(row.original.id)}>{row.getVisibleCells().map(cell => <div key={cell.id} style={{ width: cell.column.getSize() }}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</div>)}</div>; })}</div></div></div>;
}
