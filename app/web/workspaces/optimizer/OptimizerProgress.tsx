import { ProjectProgress, type ResultDocument, type EngineRunHandle } from '../../common/project';
import { useProjectBinding } from '../home/projectController';
import type { OptimizerDraft } from './optimizerFixtures';
export function OptimizerProgress({ run, draft, result, onResults, onSettings }: {
  run: EngineRunHandle; draft: OptimizerDraft; onChange: (value: OptimizerDraft) => void;
  result: ResultDocument | null; onResults: () => void; onSettings: (section?: string) => void;
}) {
  const binding = useProjectBinding();
  const execution = binding?.state.draft.execution as { dataset?: { symbol?: string; timeframe?: string } } | undefined;
  const summary = <><h4>Backtest options</h4><p>{execution?.dataset?.symbol ?? 'No dataset'} / {execution?.dataset?.timeframe ?? 'No timeframe'}</p>
    <h4>Grid optimization</h4><p>Destination: {draft.targetBank || 'Not configured'}</p>
    <p>Parameters: {draft.parameters.map(parameter => parameter.name).join(', ') || 'None configured'}</p>
    <button className="sqd-link-button" onClick={() => onSettings('optimization')}>Configure optimization</button>
    <p>Sequential and walk-forward modes are unavailable.</p></>;
  return <ProjectProgress title="Optimizer" run={run} summary={summary} result={result} onOpenResults={onResults} onSettings={onSettings}
    stats={Object.entries(run.receipt ?? {}).filter(([key]) => key.startsWith('candidates_')).map(([key, value]) => [key, String(value)])} />;
}
