import React from 'react';
import { useEngineRun, type EngineRunHandle } from '../home/EnginePanel/EngineCtrl';
import { ProgressDashboard } from './ProgressDashboard';
import { type EngineRunStatus } from './fixtures';

export interface TaskBuildProps {
  className?: string;
  run?: EngineRunHandle;
  strategyNames?: string[];
  runStatus?: EngineRunStatus;
  onRunStatusChange?: (status: EngineRunStatus) => void;
  onOpenFullSettings?: () => void;
  onOpenResults?: (rank?: number) => void;
}

export const TaskBuild: React.FC<TaskBuildProps> = ({
  className = '',
  run: providedRun,
  onOpenFullSettings = () => {},
  onOpenResults = () => {},
}) => {
  const fallback = useEngineRun(providedRun ? null : undefined);
  const run = providedRun ?? fallback;

  return (
    <div data-testid="task-build-container" className={className}>
      <ProgressDashboard
        run={run}
        onOpenFullSettings={onOpenFullSettings}
        onOpenResults={onOpenResults}
      />
    </div>
  );
};

export default TaskBuild;
