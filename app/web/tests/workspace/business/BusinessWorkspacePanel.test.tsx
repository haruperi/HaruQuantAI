import React from 'react';
import { renderToString } from 'react-dom/server';
import { beforeEach, describe, expect, it } from 'vitest';
import { useAppStore } from '../../../shell/store';
import { BusinessWorkspace } from '../../../workspaces/business/BusinessWorkspace';

describe('BusinessWorkspacePanel Component', () => {
  beforeEach(() => {
    useAppStore.getState().reset();
  });

  it('renders business workspace header and organization branding', () => {
    const html = renderToString(<BusinessWorkspace />);

    expect(html).toContain('HaruQuantAI for Business');
    expect(html).toContain('Multi-Tenant Edition');
    expect(html).toContain('Distributed high-performance computing cluster');
  });

  it('renders compute cluster metrics and action buttons', () => {
    const html = renderToString(<BusinessWorkspace />);

    expect(html).toContain('Distributed Compute Worker Cluster');
    expect(html).toContain('Ping Cluster');
    expect(html).toContain('Recycle Workers');
    expect(html).toContain('Register Node');
  });

  it('renders connected compute nodes table with node entries', () => {
    const html = renderToString(<BusinessWorkspace />);

    expect(html).toContain('Node Name / Host');
    expect(html).toContain('Endpoint');
    expect(html).toContain('Cores');
    expect(html).toContain('RAM');
    expect(html).toContain('GPU');
    expect(html).toContain('Status');

    // Default compute nodes from store
    expect(html).toContain('Master Node (Local Engine)');
    expect(html).toContain('Cluster-Alpha (Dedicated Server)');
  });

  it('renders Model Context Protocol (MCP) enterprise gateways section', () => {
    const html = renderToString(<BusinessWorkspace />);

    expect(html).toContain('Model Context Protocol (MCP)');
    expect(html).toContain('AI Gateways');
    expect(html).toContain('Add Gateway');
    expect(html).toContain('Antigravity Alpha Agent Gateway');
  });

  it('renders team and role-based access control (RBAC) section', () => {
    const html = renderToString(<BusinessWorkspace />);

    expect(html).toContain('Team Members');
    expect(html).toContain('Invite Member');
    expect(html).toContain('Permissions Matrix');
    expect(html).toContain('Role-based access control (RBAC) governance');
  });
});
