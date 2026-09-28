import type { UIContribution } from '../../../host/contributions';
export const contribution: UIContribution = {
  id: 'plugin.data_manager.indicators',
  kind: 'plugin',
  version: '1.0.0',
  owner: 'workspace.data_manager',
  slot: 'data_source.presentation',
  contractVersion: '1.0.0',
  loadPorts: () => import('./presentation'),
};
