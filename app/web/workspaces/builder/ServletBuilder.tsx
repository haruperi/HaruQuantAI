import React from 'react';

export interface ServletBuilderProps {
  onDispatch?: (action: string, payload?: Record<string, unknown>) => void;
  className?: string;
}

export const ServletBuilder: React.FC<ServletBuilderProps> = ({
  onDispatch = () => {},
  className = '',
}) => {
  return (
    <div data-testid="servlet-builder-container" className={className}>
      <button
        type="button"
        onClick={() => onDispatch('build/start')}
        data-testid="servlet-builder-start-btn"
      >
        Start
      </button>
      <button
        type="button"
        onClick={() => onDispatch('build/stop')}
        data-testid="servlet-builder-stop-btn"
      >
        Stop
      </button>
    </div>
  );
};

export default ServletBuilder;
