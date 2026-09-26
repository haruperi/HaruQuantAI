import { useEffect, useState } from 'react';
import { nextRunStatus, type RunStatus } from './contracts';

/** A bounded clock for previewing job controls. No engine or metric calculation. */
export function usePreviewRun() {
  const [status, setStatus] = useState<RunStatus>('idle');
  const [step, setStep] = useState(0);
  const [log, setLog] = useState<string[]>([]);
  const [clearOnStart, setClearOnStart] = useState(false);
  useEffect(() => {
    if (status !== 'running') return;
    const timer = window.setInterval(() => setStep(s => Math.min(10, s + 1)), 1000);
    return () => window.clearInterval(timer);
  }, [status]);
  useEffect(() => {
    if (step === 10 && status === 'running') {
      setStatus('complete');
      setLog(v => [...v, 'Local preview completed.']);
    }
  }, [step, status]);
  const act = (action: 'start' | 'pause' | 'stop') => {
    if (action === 'start' && status !== 'paused') setStep(0);
    setStatus(nextRunStatus(status, action));
    setLog(v => [...(action === 'start' && clearOnStart ? [] : v), `${action === 'start' && status === 'paused' ? 'Resume' : action} — local preview`]);
  };
  return {status, step, log, clearOnStart, setClearOnStart, act, clearLog: () => setLog([])};
}
