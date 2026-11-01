import React, { useState } from 'react';
import { ProgressDashboard } from './ProgressDashboard';
import { type EngineRunStatus } from './fixtures';

export interface TaskBuildProps {
  className?: string;
  strategyNames?: string[];
  runStatus?: EngineRunStatus;
  onRunStatusChange?: (status: EngineRunStatus) => void;
  onOpenFullSettings?: () => void;
  onOpenResults?: (rank?: number) => void;
}

export const TaskBuild: React.FC<TaskBuildProps> = ({
  className = '',
  strategyNames = [],
  runStatus: controlledRunStatus,
  onRunStatusChange: controlledOnChange,
  onOpenFullSettings = () => {},
  onOpenResults = () => {},
}) => {
  const [internalStatus, setInternalStatus] = useState<EngineRunStatus>('idle');
  const runStatus = controlledRunStatus ?? internalStatus;
  const handleStatusChange = controlledOnChange ?? setInternalStatus;

  return (
    <div data-testid="task-build-container" className={className}>
      <ProgressDashboard
        strategyNames={strategyNames}
        runStatus={runStatus}
        onRunStatusChange={handleStatusChange}
        onOpenFullSettings={onOpenFullSettings}
        onOpenResults={onOpenResults}
      />
    </div>
  );
};

export default TaskBuild;
