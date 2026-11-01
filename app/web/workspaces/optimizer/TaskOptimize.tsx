import React from 'react';

export interface TaskOptimizeProps {
  status: 'IDLE' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'STOPPED' | 'FAILED';
  progressPct: number;
  evaluationsCompleted: number;
  evaluationsTotal: number;
  bestFitness?: number;
  onStart?: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onStop?: () => void;
}

export function TaskOptimize({
  status,
  progressPct,
  evaluationsCompleted,
  evaluationsTotal,
  bestFitness,
  onStart,
  onPause,
  onResume,
  onStop,
}: TaskOptimizeProps) {
  return (
    <div className="task-optimize-panel" data-testid="task-optimize-panel">
      <div className="task-optimize-status">
        <h3>Optimization Engine: {status}</h3>
        <p>
          Evaluations: {evaluationsCompleted} / {evaluationsTotal} ({progressPct.toFixed(1)}%)
        </p>
        {bestFitness !== undefined && (
          <p>
            Best Fitness: <strong>{bestFitness.toFixed(4)}</strong>
          </p>
        )}
      </div>

      <div className="task-optimize-controls">
        {status === 'IDLE' && onStart && (
          <button className="sqd-btn primary" onClick={onStart} aria-label="Start Optimization">
            Start Optimization
          </button>
        )}
        {status === 'RUNNING' && onPause && (
          <button className="sqd-btn" onClick={onPause} aria-label="Pause Optimization">
            Pause
          </button>
        )}
        {status === 'PAUSED' && onResume && (
          <button className="sqd-btn primary" onClick={onResume} aria-label="Resume Optimization">
            Resume
          </button>
        )}
        {(status === 'RUNNING' || status === 'PAUSED') && onStop && (
          <button className="sqd-btn danger" onClick={onStop} aria-label="Stop Optimization">
            Stop
          </button>
        )}
      </div>
    </div>
  );
}
