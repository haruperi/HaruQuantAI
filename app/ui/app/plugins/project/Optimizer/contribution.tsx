import type { UIContribution } from '../../../host/contributions';
export const contribution: UIContribution = { id:'plugin.optimizer.project_workbench', kind:'plugin', version:'1.0.0', owner:'workspace.optimizer', slot:'project.workbench', contractVersion:'1.0.0', loadPorts: () => import('./index') };
