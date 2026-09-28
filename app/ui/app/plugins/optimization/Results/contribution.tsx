import type { UIContribution } from '../../../host/contributions';
export const contribution: UIContribution = { id:'plugin.results.optimization_surface', kind:'plugin', version:'1.0.0', owner:'workspace.results', slot:'optimization.presentation', contractVersion:'1.0.0', loadPorts: () => import('./OptimizationSurface') };
