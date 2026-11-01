import React from 'react';
import { RankingTab } from './settings/RankingTab';

export interface SettingsRankingsProps {
  className?: string;
}

export const SettingsRankings: React.FC<SettingsRankingsProps> = ({
  className = '',
}) => {
  return (
    <div data-testid="settings-rankings-container" className={className}>
      <RankingTab />
    </div>
  );
};

export default SettingsRankings;
