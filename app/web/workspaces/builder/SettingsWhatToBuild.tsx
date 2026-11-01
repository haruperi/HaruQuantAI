import React from 'react';
import { WhatToBuildTab } from './settings/WhatToBuildTab';
import { whatToBuildDefaults, type WhatToBuildState } from './settings/settingsFixtures';

export interface SettingsWhatToBuildProps {
  state?: WhatToBuildState;
  onChange?: (state: WhatToBuildState) => void;
}

export const SettingsWhatToBuild: React.FC<SettingsWhatToBuildProps> = ({
  state = whatToBuildDefaults,
  onChange = () => {},
}) => {
  return (
    <div data-testid="settings-what-to-build-container">
      <WhatToBuildTab state={state} onChange={onChange} />
    </div>
  );
};

export default SettingsWhatToBuild;
