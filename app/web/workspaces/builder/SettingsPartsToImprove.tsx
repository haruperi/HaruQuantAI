import React from 'react';
import { PartsToImproveTab } from './settings/PartsToImproveTab';

export interface SettingsPartsToImproveProps {
  className?: string;
}

export const SettingsPartsToImprove: React.FC<SettingsPartsToImproveProps> = ({
  className = '',
}) => {
  return (
    <div data-testid="settings-parts-to-improve-container" className={className}>
      <PartsToImproveTab />
    </div>
  );
};

export default SettingsPartsToImprove;
