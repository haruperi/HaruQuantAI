import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { ProgressDashboard } from '../../../workspaces/builder/ProgressDashboard';
import { engineStatus, type EngineRunHandle } from '../../../workspaces/home/EnginePanel/EngineCtrl';
const run: EngineRunHandle = { status: 'running', step: 4, log: ['Evaluated 2/5'], clearOnStart: false,
  setClearOnStart: () => {}, act: () => {}, clearLog: () => {}, canStart: false, jobId: 'actual-job',
  receipt: { candidates_evaluated: 2, candidates_accepted: 1, candidates_rejected: 1 } };
describe('Builder backend presentation', () => {
  it('renders actual evaluation receipt and progress without generated fixture telemetry', () => {
    const html = renderToString(<ProgressDashboard run={run} onOpenFullSettings={() => {}} onOpenResults={() => {}} />);
    expect(html).toContain('Evaluated 2/5'); expect(html).toContain('aria-valuenow="40"');
    expect(html).toContain('No stored backtest results'); expect(html).toContain('Telemetry is unavailable');
    expect(html).not.toContain('sqd-infinite');
  });
  it('maps every Core terminal and admission state explicitly', () => {
    expect(['QUEUED','RUNNING','PAUSED','COMPLETED','FAILED','CANCELLED','INTERRUPTED'].map(engineStatus)).toEqual(['queued','running','paused','complete','error','cancelled','interrupted']);
    expect(() => engineStatus('invented')).toThrow('Unknown engine state');
  });
});
