import React from 'react';
import { GeneticOptionsTab } from './settings/GeneticOptionsTab';

export interface SettingsGeneticOptionsProps {
  className?: string;
}

export const SettingsGeneticOptions: React.FC<SettingsGeneticOptionsProps> = ({
  className = '',
}) => {
  return (
    <div data-testid="settings-genetic-options-container" className={className}>
      <GeneticOptionsTab />
    </div>
  );
};

export default SettingsGeneticOptions;
