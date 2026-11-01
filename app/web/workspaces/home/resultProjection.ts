import { createElement as h } from 'react';
import type { StoredResult } from './homeClient';
import { ProjectResults } from './ProjectResults/module';
import { ResultsChart } from '../../common/project/results/ResultsCharts';
import type { ResultDocument } from '../../common/project/results/resultsModel';
import { useProjectBinding } from './projectController';

export type EvidenceResult = ResultDocument & { sampleEquity?: { in: number[]; out: number[] } | null };

/** Chart/summary adapter only; detailed trades remain in the stored result contract. */
export function progressResult(result: StoredResult | null): EvidenceResult | null {
  if (!result) return null;
  const execution = result.parameters.execution as { split_time?: number | null } | undefined;
  const boundary = execution?.split_time;
  const sampleEquity = typeof boundary === 'number' ? {
    in: result.equity_curve.filter(point => point.timestamp <= boundary).map(point => point.equity),
    out: result.equity_curve.filter(point => point.timestamp > boundary).map(point => point.equity),
  } : null;
  return { sampleEquity, id: result.result_id, name: result.strategy_name, markets: ['Main backtest'],
    trades: [], equity: result.equity_curve.map(point => point.equity),
    metrics: Object.entries(result.metrics).map(([key, value]) => [key, String(value)]),
    chartData: false, stockpicker: false, portfolio: false };
}
export function StoredResults({ result }: { result: StoredResult | null }) {
  const binding = useProjectBinding();
  const content = (node: ReturnType<typeof h>) => h('div', { className: 'sqr-content' }, node);
  const section = (id: string, title: string, position: number, node: ReturnType<typeof h>) => ({ id: `stored-${id}`, title, position, content: content(node) });
  const sections = result ? [
    section('overview', 'Overview', 1, h('table', { className: 'sqr-data-table', 'aria-label': 'Stored metrics' }, h('tbody', null,
      ...Object.entries(result.metrics).map(([key, value]) => h('tr', { key }, h('th', null, key), h('td', null, String(value))))))),
    section('trades', 'List of trades', 2, h('table', { className: 'sqr-data-table', 'aria-label': 'Stored trades' },
      h('thead', null, h('tr', null, ...['Ticket', 'Symbol', 'Open', 'Close', 'Net PnL'].map(label => h('th', { key: label }, label)))),
      h('tbody', null, ...result.trades.map((trade, i) => h('tr', { key: i }, ...['ticket', 'symbol', 'open_price', 'close_price', 'net_pnl'].map(key => h('td', { key }, String(trade[key])))))))),
    section('equity', 'Equity chart', 3, h(ResultsChart, { title: 'Stored equity', values: result.equity_curve.map(point => point.equity) })),
    section('strategy', 'Strategy config', 4, h('pre', null, JSON.stringify(result.strategy_payload, null, 2))),
    section('provenance', 'Execution settings', 5, h('pre', null, JSON.stringify(result.parameters, null, 2))),
  ] : [];
  return h('div', { style: { display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0 } },
    binding ? h('label', null, 'Stored result ', h('select', { 'aria-label': 'Stored result', value: result?.result_id ?? '', onChange: (event: { target: { value: string } }) => binding.controller.selectResult(event.target.value) },
      ...binding.state.results.map(item => h('option', { key: item.result_id, value: item.result_id }, `${item.strategy_name} · ${item.result_id}`)))) : null,
    h(ProjectResults, { result: null, visibleTabIds: [], extraSections: sections, emptyMessage: result ? `${result.strategy_name} — stored backtest ${result.result_id}` : 'No stored result selected.' }));
}
