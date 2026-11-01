import { useState } from 'react';
import { useAppStore } from '../../shell/store';
import { useEngineRun, type EngineRunStatus, type EngineRunHandle } from '../home/EnginePanel/EngineCtrl';
import { useProjectBinding } from '../home/projectController';
import { EnginePanel } from './EnginePanel';
import { SettingsSummary } from './SettingsSummary';
import { ResultsColumn } from './ResultsColumn';
import { idleProgressStats, type SampleType } from './fixtures';

/** Preserve the three-column layout while rendering observed backend execution. */
export function ProgressDashboard({ run: providedRun, onOpenFullSettings, onOpenResults }: {
  run?: EngineRunHandle; strategyNames?: string[]; runStatus?: EngineRunStatus; onRunStatusChange?: (status: EngineRunStatus) => void; onOpenFullSettings: () => void; onOpenResults: (rank?: number) => void;
}) {
  const fallbackRun = useEngineRun(providedRun ? null : undefined);
  const run = providedRun ?? fallbackRun;
  const binding = useProjectBinding(), notify = useAppStore(s => s.notify);
  const [sampleType, setSampleType] = useState<SampleType>('full');
  const evaluated = Number(run.receipt?.candidates_evaluated ?? 0), accepted = Number(run.receipt?.candidates_accepted ?? 0);
  const stats = { ...idleProgressStats, strategiesGenerated: evaluated,
    accepted: String(accepted), rejected: String(run.receipt?.candidates_rejected ?? 0),
    inDatabank: binding?.state.results.length ?? 0, timePerStrategy: 'Unavailable',
    timePerAcceptedStrategy: 'Unavailable', strategiesPerHour: 'Unavailable', acceptedPerHour: 'Unavailable', runningTime: 'Unavailable' };
  return <div className="sqd-dashboard"><div className="sqd-flex">
    <EnginePanel runStatus={run.status} stats={stats} lastEvent={run.log.at(-1) ?? ''} log={run.log}
      canStart={run.canStart} pending={run.pending} progress={run.step * 10}
      clearOnStart={run.clearOnStart} onStart={() => void run.act('start')} onPause={() => void run.act('pause')}
      onStop={() => void run.act('stop')} onClearLog={run.clearLog} onToggleClearOnStart={run.setClearOnStart} onNotify={notify} />
    <SettingsSummary onOpenFullSettings={onOpenFullSettings} />
    <ResultsColumn sampleType={sampleType} onSampleSelect={setSampleType} onOpenResults={onOpenResults} />
  </div>{run.error && <p role="alert">{run.error}</p>}</div>;
}
