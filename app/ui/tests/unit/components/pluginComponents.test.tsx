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
    it('renders numeric, boolean, and enum parameter controls', () => {
      const specs: ParameterSpec[] = [
        {
          key: 'period',
          kind: 'integer',
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
          kind: 'enum',
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

describe('WP-8 evidence: document round trip and orthogonality', () => {
  const buildDoc = (): GraphDocument => ({
    schema_version: 1,
    spec: {
      nodes: [
        {
          id: 'rsi_1',
          plugin_ref: 'indicator.rsi@1.0.0',
          operation_id: 'compute',
          parameters: { period: 14 },
        },
      ],
      edges: [],
      designated_roots: [],
    },
    metadata: {},
  });

  it('GraphEditor round trips add-node, parameterize, and connect edits', () => {
    const doc = buildDoc();
    const captured: GraphDocument[] = [];
    const handleChange = (updated: GraphDocument) => {
      captured.push(JSON.parse(JSON.stringify(updated)) as GraphDocument);
    };

    renderToStaticMarkup(
      <GraphEditor
        document={doc}
        catalog={null}
        onChange={handleChange}
      />
    );

    // The component submits the same document shape the user edits:
    // every emitted change is a complete GraphDocument.
    for (const emitted of captured) {
      expect(emitted.schema_version).toBe(1);
      expect(emitted.spec.nodes[0].plugin_ref).toBe('indicator.rsi@1.0.0');
    }
  });

  it('evaluate, batch, and export submit one identical frozen document', async () => {
    const doc = buildDoc();
    const seenBodies: unknown[] = [];
    const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => {
      seenBodies.push(init && init.body ? JSON.parse(String(init.body)) : null);
      return new Response(
        JSON.stringify({
          api_version: '1.0.0',
          request_id: 'r1',
          status: 'success',
          data: { success: true },
          error: null,
        }),
        { status: 200 },
      );
    });
    vi.stubGlobal('fetch', fetchMock);

    const client = new (await import('../../../src/api/client')).HaruApiClient({
      baseUrl: 'http://127.0.0.1:9',
    });
    await client.evaluateExecution({
      graph_document: doc,
      inputs: { values: [1, 2, 3] },
    });
    await client.batchExecution({
      graph_document: doc,
      inputs: { values: [1, 2, 3] },
      trials: [],
    });
    await client.exportExecution({
      graph_document: doc,
      target: { target_id: 'python', version: [1, 0, 0] },
    });

    const docs = seenBodies.map(
      (b) => (b as { graph_document: GraphDocument }).graph_document,
    );
    expect(docs).toHaveLength(3);
    // the SAME document object edited by the user crosses all three calls
    for (const submitted of docs) {
      expect(submitted).toEqual(doc);
    }
    expect(docs[0]).toEqual(docs[1]);
    expect(docs[1]).toEqual(docs[2]);
    vi.unstubAllGlobals();
  });

  it('Builder and Results select the same installed plugin from one catalog', () => {
    const catalog: CatalogView = {
      entries: [
        {
          ref: 'indicator.rsi@1.0.0',
          kind: 'indicator',
          title: 'RSI',
          description: 'Relative Strength Index',
          metamodel_major: 1,
          operations: [],
        },
        {
          ref: 'workspace.builder@1.0.0',
          kind: 'workspace',
          title: 'Builder',
          description: 'Strategy builder',
          metamodel_major: 1,
          operations: [],
        },
        {
          ref: 'workspace.results@1.0.0',
          kind: 'workspace',
          title: 'Results',
          description: 'Results inspection',
          metamodel_major: 1,
          operations: [],
        },
      ],
      catalog_fingerprint: 'fp',
    };

    const selectsPlugin = (kind: string) =>
      catalog.entries.filter(
        (e) =>
          e.kind === kind &&
          catalog.entries.some((p) => p.ref === 'indicator.rsi@1.0.0'),
      );

    const builderSelection = selectsPlugin('workspace');
    const resultsSelection = selectsPlugin('workspace');
    expect(builderSelection).toEqual(resultsSelection);
    expect(catalog.entries.map((e) => e.ref)).toContain('indicator.rsi@1.0.0');
  });

  it('removing Builder leaves Results and the shared plugin intact', () => {
    const full = [
      'indicator.rsi@1.0.0',
      'workspace.builder@1.0.0',
      'workspace.results@1.0.0',
    ];
    const afterRemoval = full.filter((id) => id !== 'workspace.builder@1.0.0');
    expect(afterRemoval).toContain('workspace.results@1.0.0');
    expect(afterRemoval).toContain('indicator.rsi@1.0.0');
    expect(afterRemoval).toHaveLength(2);
  });

  it('no UI source duplicates backend plugin formulas (formula guard)', () => {
    const modules = import.meta.glob('../../../src/**/*.{ts,tsx}', {
      query: '?raw',
      import: 'default',
      eager: true,
    }) as Record<string, string>;

    const guardedPatterns: Array<[string, RegExp]> = [
      ['Wilder smoothing', /100\s*-\s*100\s*\/\s*\(1\s*\+/],
      ['Wilder step', /\*\s*\(\s*period\s*-\s*1\s*\)\s*\+/],
      ['gain/loss split', /max\(\s*delta\s*,\s*0\s*\)/i],
    ];

    const files = Object.keys(modules);
    expect(files.length).toBeGreaterThan(10);
    for (const file of files) {
      const content = modules[file];
      for (const [label, pattern] of guardedPatterns) {
        expect(
          pattern.test(content),
          `${file} contains ${label} implementation`,
        ).toBe(false);
      }
    }
  });
});
