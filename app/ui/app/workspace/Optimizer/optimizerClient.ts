import { createDomainClient, type BatchExecutionResult } from '../../host/transport';

// Route base mirrors the pre-reset gateway path; provisional until the backend
// host architecture ratifies the mounting scheme.
const client = createDomainClient('/executions');

const demoGraphDocument = () => ({
  schema_version: 1,
  spec: {
    nodes: [{ id: 'rsi_node', plugin_ref: 'indicator.rsi@1.0.0', operation_id: 'compute', parameters: { period: 14 } }],
    edges: [],
    designated_roots: [{ node_id: 'rsi_node', port_key: 'rsi' }],
  },
});

export function runOptimizationTrials(): Promise<BatchExecutionResult> {
  return client.post('/batch', {
    graph_document: demoGraphDocument(),
    inputs: { values: [44.0, 44.5, 45.0, 44.8, 45.2, 46.0] },
    trials: [
      { trial_id: 'trial_14', parameter_overrides: { rsi_node: { period: 14 } } },
      { trial_id: 'trial_21', parameter_overrides: { rsi_node: { period: 21 } } },
    ],
  });
}
