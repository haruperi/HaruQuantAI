import { useProjectBinding } from '../home/projectController';
export function SettingsSummary({ onOpenFullSettings }: { onOpenFullSettings: () => void }) {
  const binding = useProjectBinding();
  const task = binding?.state.project?.tasks[binding.state.taskId];
  const execution = task?.settings.execution as Record<string, unknown> | undefined;
  const dataset = execution?.dataset as Record<string, unknown> | undefined;
  return <div className="sqd-settings-col"><div className="sqd-card sqd-simple-settings"><div className="sqd-summary-title">Settings summary</div>
    <dl>{['symbol', 'timeframe', 'source', 'revision'].map(key => <div key={key}><dt>{key}</dt><dd>{String(dataset?.[key] ?? 'Not configured')}</dd></div>)}
    <dt>Mode</dt><dd>{String(execution?.mode ?? 'Not configured')}</dd><dt>Destination</dt><dd>{task?.databank_target ?? 'Not configured'}</dd></dl>
    <button className="sqd-link-button" onClick={onOpenFullSettings}>Open full settings</button>
  </div></div>;
}
