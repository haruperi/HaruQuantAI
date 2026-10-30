import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { ConfigureMcpModal } from '../../../workspaces/ai/ConfigureMcpModal';
import type { McpServerConfig } from '../../../shell/types';

describe('MCPPanel & ConfigureMcpModal (Phase 19.2: I-ServletMCP)', () => {
  it('renders modal with default title, fields, and transport selection', () => {
    const html = renderToString(
      <ConfigureMcpModal onClose={() => {}} onSaveServer={() => {}} />
    );

    expect(html).toContain('Model Context Protocol (MCP) &amp; AI Agent Gateway');
    expect(html).toContain('Gateway / Server Name');
    expect(html).toContain('Local AI Quant Gateway');
    expect(html).toContain('Transport Type');
    expect(html).toContain('Server-Sent Events (SSE / HTTP)');
    expect(html).toContain('Local Subprocess (Standard I/O)');
  });

  it('renders enabled agent tools and capabilities checkboxes', () => {
    const html = renderToString(
      <ConfigureMcpModal onClose={() => {}} onSaveServer={() => {}} />
    );

    expect(html).toContain('Enabled Agent Tools &amp; Capabilities');
    expect(html).toContain('Strategy Generation');
    expect(html).toContain('Backtest Engine');
    expect(html).toContain('Code Synthesis');
    expect(html).toContain('Market Feed');
    expect(html).toContain('Order Execution');
  });

  it('renders modal with existing server configuration', () => {
    const customServer: McpServerConfig = {
      id: 'srv-remote-99',
      name: 'Custom Alpha Node',
      url: 'https://mcp.internal.quant/v1',
      transport: 'sse',
      status: 'Connected',
      capabilities: ['live_data_feed', 'order_routing'],
      activeCalls: 5,
    };

    const html = renderToString(
      <ConfigureMcpModal
        onClose={() => {}}
        onSaveServer={() => {}}
        existingServer={customServer}
      />
    );

    expect(html).toContain('Custom Alpha Node');
    expect(html).toContain('https://mcp.internal.quant/v1');
    expect(html).toContain('Ping Gateway');
    expect(html).toContain('Save Gateway Config');
  });
});
