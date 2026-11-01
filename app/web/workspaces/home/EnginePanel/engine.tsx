import type { EvidenceResult } from '../resultProjection';
import { CircleStop, CirclePause, CirclePlay } from 'lucide-react';
import type { ReactNode } from 'react';
import { useEnginePanel, type EngineRunHandle } from './EngineCtrl';
import { ProjectConfigHelpPopup } from './projectConfigHelpPopup';
import { EngineChartPanel } from './directives/engineChartPanel/engineChartPanel';
import { ResultsChart } from '../../../common/project/results/ResultsCharts';
import { downloadText } from '../../../common/project/results/resultsModel';

export function ProjectProgress({
  title,
  run,
  stats,
  summary,
  result,
  onOpenResults,
  onSettings,
  startError,
}: {
  title: string;
  run: EngineRunHandle;
  stats: [string, string][];
  summary: ReactNode;
  result: EvidenceResult | null;
  onOpenResults: () => void;
  onSettings: () => void;
  startError?: string;
}) {
  const { detail, setDetail, sample, setSample, running } = useEnginePanel(run);
  const isStartDisabled = running || run.canStart === false || !!startError;
  const startTitle =
    run.canStart === false
      ? 'Engine cannot run without an active project'
      : run.status === 'paused'
        ? 'Resume'
        : 'Start';

  return (
    <div className="sqd-dashboard">
      <div className="sqd-flex pw-progress">
        <section className="pw-engine">
          <div className="sqd-card pw-controls">
            <button className="sqd-btn" disabled={run.pending || !['queued', 'running', 'paused'].includes(run.status)} onClick={() => run.act('stop')}>
              <CircleStop size={13} className="sqd-ico-stop" />
              Stop
            </button>
            <button className="sqd-btn" disabled={run.pending || !running} onClick={() => run.act('pause')}>
              <CirclePause size={13} className="sqd-ico-pause" />
              Pause
            </button>
            <button
              className="sqd-btn sqd-btn-start"
              disabled={isStartDisabled}
              title={startTitle}
              onClick={() => run.act('start')}
            >
              <CirclePlay size={13} />
              {run.status === 'paused' ? 'Resume' : 'Start'}
            </button>
            <button className="sqd-btn" onClick={() => setDetail('Project configuration')}>
              Config
            </button>
          </div>
          {startError && <p role="alert">{startError}</p>}
          <div
            className="sqd-progress"
            role="progressbar"
            aria-label={`${title} progress`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={run.step * 10}
          >
            <div className="sqd-progress-bar" style={{ width: `${run.step * 10}%` }} />
          </div>
          <div className="sqd-task-desc">
            Task: {title} · <span role="status">{run.status}</span>
            {run.jobId ? ` · Job ${run.jobId}` : ''}
          </div>
          <div className="sqd-log-card">
            <div className="sqd-log-scroll">
              {run.log.map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
            <div className="sqd-log-buttons">
              <button className="sqd-btn" onClick={run.clearLog}>
                Clear log
              </button>
              <label>
                <input
                  type="checkbox"
                  checked={run.clearOnStart}
                  onChange={e => run.setClearOnStart(e.target.checked)}
                />{' '}
                Clear on start
              </label>
              <button
                className="sqd-btn"
                onClick={() => downloadText(`${title.toLowerCase()}.log`, run.log.join('\n'))}
              >
                Save log
              </button>
            </div>
          </div>
          <div className="sqd-card sqd-stats-card">
            <table className="sqd-stats-table">
              <tbody>
                {stats.map(([label, value]) => (
                  <tr key={label}>
                    <td>{label}:</td>
                    <td>{value}</td>
                    <td>
                      <button
                        className="sqd-link-button"
                        aria-label={`${label} details`}
                        onClick={() => setDetail(label)}
                      >
                        Detailed
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <EngineChartPanel step={run.step} />
        </section>
        <section className="pw-summary">
          <h3>Settings summary</h3>
          <div inert={running || run.status === 'paused'}>{summary}</div>
          <button className="sqd-btn" onClick={() => onSettings()}>
            Full settings
          </button>
        </section>
        <section className="sqd-results-wrap pw-results">
          <div className="sqd-result-card">
            <button className="sqd-result-title" onClick={onOpenResults} disabled={!result}>
              {result ? `Selected strategy: ${result.name}` : 'No results so far'}
            </button>
            {result && (
              <div className="sqd-result-body">
                <div className="sqd-btn-group">
                  {['Full', 'IS', 'OOS'].map(s => (
                    <button key={s} disabled={s !== 'Full' && !result.sampleEquity} className={(result.sampleEquity ? sample : 'Full') === s ? 'active' : ''} onClick={() => setSample(s)}>
                      {s}
                    </button>
                  ))}
                </div>
                <ResultsChart
                  values={
                    !result.sampleEquity || sample === 'Full' ? result.equity : sample === 'IS' ? result.sampleEquity.in : result.sampleEquity.out
                  }
                  title={`Equity / ${result.sampleEquity ? sample : 'Full'}`}
                />
                <button className="sqd-btn" onClick={onOpenResults}>
                  Open Results
                </button>
              </div>
            )}
          </div>
        </section>
        {detail && (
          <ProjectConfigHelpPopup
            detail={detail}
            title={title}
            stats={stats}
            onClose={() => setDetail(null)}
            onSettings={onSettings}
          />
        )}
      </div>
    </div>
  );
}
