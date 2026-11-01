import { createDomainClient, type BatchExecutionResult } from '../../shell/transport';

// Route base mirrors the pre-reset gateway path; provisional until the backend
// host architecture ratifies the mounting scheme.
const executionClient = createDomainClient('/executions');
const optimizerClient = createDomainClient('/api/optimizer');

export interface OptimizerWorkspaceStateDto {
  project_id: string;
  status: 'IDLE' | 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'STOPPED' | 'FAILED';
  progress_pct: number;
  evaluations_completed: number;
  evaluations_total: number;
  best_fitness: number;
  active_result_tab: string;
}

export function startOptimization(projectId: string): Promise<OptimizerWorkspaceStateDto> {
  return optimizerClient.post<OptimizerWorkspaceStateDto>('/start', { project_id: projectId });
}

export function getOptimizerState(projectId: string): Promise<OptimizerWorkspaceStateDto> {
  return optimizerClient.get<OptimizerWorkspaceStateDto>(`/state?project_id=${encodeURIComponent(projectId)}`);
}

const demoGraphDocument = () => ({
  schema_version: 1,
  spec: {
    nodes: [{ id: 'rsi_node', plugin_ref: 'indicator.rsi@1.0.0', operation_id: 'compute', parameters: { period: 14 } }],
    edges: [],
    designated_roots: [{ node_id: 'rsi_node', port_key: 'rsi' }],
  },
});

export function runOptimizationTrials(): Promise<BatchExecutionResult> {
  return executionClient.post('/batch', {
    graph_document: demoGraphDocument(),
    inputs: { values: [44.0, 44.5, 45.0, 44.8, 45.2, 46.0] },
    trials: [
      { trial_id: 'trial_14', parameter_overrides: { rsi_node: { period: 14 } } },
      { trial_id: 'trial_21', parameter_overrides: { rsi_node: { period: 21 } } },
    ],
  });
}
