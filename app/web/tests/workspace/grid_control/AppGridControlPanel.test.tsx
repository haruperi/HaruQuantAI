import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { GridControlWorkspace } from '../../../workspaces/grid_control/GridControlWorkspace';
import { ClusterPanel } from '../../../workspaces/grid_control/ClusterPanel';
import { AddNodeModal } from '../../../workspaces/grid_control/AddNodeModal';
import type { ComputeNode } from '../../../shell/types';

describe('AppGridControlPanel components', () => {
  it('renders GridControlWorkspace with header, panels, and cluster overview', () => {
    const html = renderToString(<GridControlWorkspace />);
    expect(html).toContain('Grid engine overview');
    expect(html).toContain('Auto-refresh every');
    expect(html).toContain('seconds');
    expect(html).toContain('data-testid="cluster-panel"');
    expect(html).toContain('data-testid="grid-panel-running"');
    expect(html).toContain('data-testid="grid-panel-waiting"');
    expect(html).toContain('data-testid="grid-panel-finished"');
    expect(html).toContain('Jobs in progress');
    expect(html).toContain('Waiting jobs');
    expect(html).toContain('Last 100 finished jobs');
  });

  it('renders ClusterPanel with node metrics and worker table', () => {
    const testNodes: ComputeNode[] = [
      {
        id: 'node-1',
        name: 'Worker Alpha',
        host: '192.168.1.10',
        ip: '192.168.1.10',
        port: 9092,
        cores: 8,
        memoryGb: 16,
        gpu: true,
        status: 'Online',
        cpuUsagePct: 15,
        latencyMs: 3,
      },
      {
        id: 'node-2',
        name: 'Worker Beta',
        host: '192.168.1.11',
        ip: '192.168.1.11',
        port: 9092,
        cores: 16,
        memoryGb: 32,
        gpu: false,
        status: 'Idle',
        cpuUsagePct: 0,
        latencyMs: 5,
      },
    ];

    const html = renderToString(
      <ClusterPanel
        nodes={testNodes}
        onAddNode={() => undefined}
        onRemoveNode={() => undefined}
      />,
    );

    expect(html).toContain('24');
    expect(html).toContain('Cores');
    expect(html).toContain('48');
    expect(html).toContain('GB');
    expect(html).toContain('Worker Alpha');
    expect(html).toContain('Worker Beta');
    expect(html).toContain('192.168.1.10');
    expect(html).toContain('192.168.1.11');
  });

  it('renders ClusterPanel empty state when no nodes registered', () => {
    const html = renderToString(
      <ClusterPanel
        nodes={[]}
        onAddNode={() => undefined}
        onRemoveNode={() => undefined}
      />,
    );

    expect(html).toContain('0');
    expect(html).toContain('Cores');
    expect(html).toContain('GB');
    expect(html).toContain('No remote compute nodes registered. Compute runs on local machine.');
  });

  it('renders AddNodeModal form fields and buttons', () => {
    const html = renderToString(
      <AddNodeModal
        onClose={() => undefined}
        onAddNode={() => undefined}
      />,
    );

    expect(html).toContain('Register Distributed Compute Node');
    expect(html).toContain('Node Display Name');
    expect(html).toContain('Hostname / FQDN');
    expect(html).toContain('IP Address');
    expect(html).toContain('Worker Daemon Port');
    expect(html).toContain('CPU Cores');
    expect(html).toContain('RAM (GB)');
    expect(html).toContain('GPU Acceleration');
    expect(html).toContain('Validate Target');
    expect(html).toContain('Register Node');
  });
});
