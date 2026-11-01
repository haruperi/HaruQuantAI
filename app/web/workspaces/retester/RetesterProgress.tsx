import { ProjectProgress, type ResultDocument, type EngineRunHandle } from '../../common/project';
import { useProjectBinding } from '../home/projectController';
import type { RetestDraft } from './retesterFixtures';
export function RetesterProgress({ run, draft, result, onResults, onSettings }: {
  run: EngineRunHandle; draft: RetestDraft; onChange: (value: RetestDraft) => void; banks: string[];
  result: ResultDocument | null; onResults: () => void; onSettings: (section?: string) => void; selectionCount: number;
}) {
  const binding = useProjectBinding();
  const execution = binding?.state.draft.execution as { dataset?: { symbol?: string; timeframe?: string }; strategy_result_ids?: string[] } | undefined;
  const summary = <><h4>Backtest options</h4><p>{execution?.dataset?.symbol ?? 'No dataset'} / {execution?.dataset?.timeframe ?? 'No timeframe'}</p>
    <p>Selected strategies: {execution?.strategy_result_ids?.length ?? 0}</p><p>Destination: {draft.destination || 'Not configured'}</p>
    <p>Earlier results are preserved.</p><button className="sqd-link-button" onClick={() => onSettings('data')}>Configure retest</button></>;
  return <ProjectProgress title="Retester" run={run} summary={summary} result={result} onOpenResults={onResults} onSettings={onSettings}
    stats={Object.entries(run.receipt ?? {}).filter(([key]) => key.startsWith('candidates_')).map(([key, value]) => [key, String(value)])} />;
}
