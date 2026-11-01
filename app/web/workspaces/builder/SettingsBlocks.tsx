import React from 'react';
import { BuildingBlocksTab } from './settings/BuildingBlocksTab';

export interface SettingsBlocksProps {
  className?: string;
}

export const SettingsBlocks: React.FC<SettingsBlocksProps> = ({
  className = '',
}) => {
  return (
    <div data-testid="settings-blocks-container" className={className}>
      <BuildingBlocksTab />
    </div>
  );
};

export default SettingsBlocks;
