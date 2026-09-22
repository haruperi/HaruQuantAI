import React from 'react';
import { describe, expect, it, vi } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ParameterForm } from '../../../src/components/plugin/ParameterForm';
import { GraphEditor } from '../../../src/components/plugin/GraphEditor';
import { ExecutionResult } from '../../../src/components/plugin/ExecutionResult';
import { CatalogStore } from '../../../src/api/catalogStore';
import type { HaruApiClient } from '../../../src/api/client';
import type {
  CatalogView,
  GraphDocument,
  ParameterSpec,
  SingleExecutionResult,
} from '../../../src/api/contracts.generated';

describe('Generic Plugin Presentation Components', () => {
  describe('ParameterForm', () => {
    it('renders scalar, boolean, and enum parameter controls', () => {
      const specs: ParameterSpec[] = [
        {
          key: 'period',
          kind: 'scalar',
          label: 'Period',
          description: 'RSI period',
          required: true,
          default: 14,
          constraint: { type: 'numeric', min_value: 2, max_value: 100, allow_negative: false },
        },
        {
          key: 'active',
          kind: 'boolean',
          label: 'Is Active',
          description: 'Enable calculation',
          required: true,
          default: true,
        },
        {
          key: 'mode',
          kind: 'categorical',
          label: 'Mode',
          description: 'Calculation mode',
          required: true,
          default: 'standard',
          constraint: {
            type: 'enum',
            choices: [
              { value: 'standard', label: 'Standard', description: 'Wilder smoothing' },
              { value: 'simple', label: 'Simple', description: 'SMA smoothing' },
            ],
          },
        },
      ];

      const values = { period: 14, active: true, mode: 'standard' };
      const handleChange = vi.fn();

      const html = renderToStaticMarkup(
        <ParameterForm
          parameters={specs}
          values={values}
          onChange={handleChange}
        />
      );

      expect(html).toContain('Period');
      expect(html).toContain('Is Active');
      expect(html).toContain('Mode');
      expect(html).toContain('value="14"');
      expect(html).toContain('Standard');
      expect(html).toContain('Simple');
    });
  });

  describe('GraphEditor', () => {
    it('renders nodes and indicates unavailable plugin losslessly', () => {
      const doc: GraphDocument = {
        schema_version: 1,
        spec: {
          nodes: [
            {
              id: 'unknown_1',
              plugin_ref: 'unknown.probe@1.0.0',
              operation_id: 'compute',
              parameters: { foo: 'bar', secret: 42 },
              title: 'Unknown Probe',
            },
          ],
          edges: [],
          designated_roots: [],
        },
      };

      const catalog: CatalogView = {
        entries: [],
        catalog_fingerprint: 'abc',
      };

      const handleChange = vi.fn();

      const html = renderToStaticMarkup(
        <GraphEditor
          document={doc}
          catalog={catalog}
          onChange={handleChange}
        />
      );

      expect(html).toContain('Unknown Probe');
      expect(html).toContain('Unavailable Plugin');
      expect(html).toContain('unknown.probe@1.0.0');
    });
  });

  describe('ExecutionResult', () => {
    it('renders success banner, provenance fingerprints, and outputs table', () => {
      const result: SingleExecutionResult = {
        success: true,
        elapsed_seconds: 0.005,
        issues: [],
        reproducibility: {
          graph_id: 'rsi_1',
          graph_fingerprint: 'fp_graph_test',
          catalog_fingerprint: 'fp_catalog_test',
          dependency_fingerprint: 'fp_dep_test',
          plugin_versions: [['rsi_1', 'indicator.rsi@1.0.0']],
          source_digests: [['rsi_1', 'digest123']],
          normalized_parameters: { period: 14 },
          input_hash: 'in_hash',
          output_hash: 'out_hash',
          numerical_policy: { tolerance: 1e-9, nan_policy: 'reject', missing_policy: 'propagate' },
          engine_version: '1.0.0',
          elapsed_seconds: 0.005,
          status: 'completed',
        },
        outputs: {
          'rsi_1.rsi': [50.0, 55.2, 62.1],
        },
      };

      const html = renderToStaticMarkup(<ExecutionResult result={result} />);

      expect(html).toContain('Execution Succeeded');
      expect(html).toContain('5.0 ms');
      expect(html).toContain('rsi_1.rsi');
      expect(html).toContain('3 samples');
      expect(html).toContain('55.2');
    });
  });

  describe('CatalogStore', () => {
    it('manages catalog fetching and draft recovery', async () => {
      const mockClient = {
        getCatalog: vi.fn().mockResolvedValue({
          entries: [
            {
              ref: 'indicator.rsi@1.0.0',
              family: 'indicators',
              description: 'Relative Strength Index',
              kind: 'indicator',
              operations: [
                {
                  operation_id: 'compute',
                  description: 'Compute RSI',
                  inputs: [],
                  outputs: [],
                  parameters: [],
                },
              ],
              capabilities_required: [],
              capabilities_provided: [],
              author: 'Haru Team',
              license: 'Apache-2.0',
            },
          ],
          catalog_fingerprint: 'fingerprint_test',
        }),
      } as unknown as HaruApiClient;

      const store = new CatalogStore(mockClient);
      expect(store.getState().loading).toBe(false);

      const cat = await store.fetchCatalog();
      expect(cat.catalog_fingerprint).toBe('fingerprint_test');
      expect(store.isPluginAvailable('indicator.rsi@1.0.0')).toBe(true);
      expect(store.isPluginAvailable('unknown.probe@1.0.0')).toBe(false);
      expect(store.getOperation('indicator.rsi@1.0.0', 'compute')?.operation_id).toBe('compute');

      const draftDoc: GraphDocument = {
        schema_version: 1,
        spec: { nodes: [], edges: [], designated_roots: [] },
      };
      store.saveDraft('draft_1', draftDoc);
      expect(store.getDraft('draft_1')).toEqual(draftDoc);
      expect(store.listDrafts()).toEqual(['draft_1']);

      store.deleteDraft('draft_1');
      expect(store.getDraft('draft_1')).toBeUndefined();
    });
  });
});
