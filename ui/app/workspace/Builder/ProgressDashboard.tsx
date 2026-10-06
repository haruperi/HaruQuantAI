import { useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../host/store';
import { EnginePanel } from './EnginePanel';
import { SettingsSummary } from './SettingsSummary';
import { ResultsColumn } from './ResultsColumn';
import { idleProgressStats, runFrameAt, type EngineRunStatus, type SampleType } from './fixtures';
/**
 * SQX-style three-column Progress dashboard (donor evidence
 * retained target UI; current donor equivalence unverified): engine column (556px), Settings summary column
 * (500px), and the flex results column, over the dashboard background.
 * The runner is a deterministic mock: no network, no backend, no engine
 * truth — Start/Pause/Stop only drive local demo state.
 */
export function ProgressDashboard({ strategyNames, runStatus, onRunStatusChange, onOpenFullSettings, onOpenResults, }: {
    strategyNames?: string[];
    runStatus: EngineRunStatus;
    onRunStatusChange: (status: EngineRunStatus) => void;
    onOpenFullSettings: () => void;
    onOpenResults: (rank?: number) => void;
}) {
    const notify = useAppStore(s => s.notify);
    const [tick, setTick] = useState(0);
    const [log, setLog] = useState<string[]>([]);
    const [clearOnStart, setClearOnStart] = useState(false);
    const [sampleType, setSampleType] = useState<SampleType>('full');
    const startedRef = useRef(false);
    useEffect(() => {
        if (runStatus !== 'running')
            return;
        const handle = window.setInterval(() => setTick(t => t + 1), 1000);
        return () => window.clearInterval(handle);
    }, [runStatus]);
    useEffect(() => {
        if (runStatus !== 'running' || !startedRef.current)
            return;
        const line = runFrameAt(tick).logLine;
        if (line === null)
            return;
        setLog(current => (current[current.length - 1] === line ? current : [...current, line]));
    }, [tick, runStatus]);
    const onStart = () => {
        startedRef.current = true;
        setTick(0);
        setLog(clearOnStart ? ['Project started'] : current => [...current, 'Project started']);
        onRunStatusChange('running');
    };
    const running = runStatus === 'running';
    const frame = running || tick > 0 ? runFrameAt(tick) : null;
    return (<div className="sqd-dashboard">
      <div className="sqd-flex">
        <EnginePanel runStatus={runStatus} stats={frame ? frame.stats : idleProgressStats} lastEvent={running && frame ? frame.lastEvent : ''} log={log} clearOnStart={clearOnStart} onStart={onStart} onPause={() => onRunStatusChange('paused')} onStop={() => onRunStatusChange('idle')} onClearLog={() => setLog([])} onToggleClearOnStart={setClearOnStart} onNotify={notify}/>
        <SettingsSummary onOpenFullSettings={onOpenFullSettings}/>
        <ResultsColumn strategyNames={strategyNames} sampleType={sampleType} onSampleSelect={setSampleType} onOpenResults={onOpenResults}/>
      </div>
    </div>);
}
