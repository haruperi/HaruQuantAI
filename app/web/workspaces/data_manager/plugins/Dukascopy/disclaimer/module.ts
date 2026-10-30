import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { DisclaimerPopup } from './disclaimerPopup';
export { DisclaimerCdnDisclaimerPopup } from './cdnDisclaimerPopup';
export const disclaimerCommand = {
  id: 'dukascopy-information',
  label: 'Dukascopy Data Disclaimer',
  icon: 'information',
  dialog: 'dukascopy-information',
} as const satisfies DataSourceCommand;
