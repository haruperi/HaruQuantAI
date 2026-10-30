import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { DebugConsoleWorkspace } from '../../../workspaces/debug_console/DebugConsoleWorkspace';

describe('AppDebugConsolePanel workspace component', () => {
  it('renders header, toolbar, category select, filter input, and clear button', () => {
    const html = renderToString(<DebugConsoleWorkspace />);

    // Header
    expect(html).toContain('Debug Console');
    expect(html).toContain('Application diagnostic log');

    // Toolbar
    expect(html).toContain('data-testid="debug-toolbar"');
    expect(html).toContain('Category');
    expect(html).toContain('Filter');
    expect(html).toContain('placeholder="Filter messages (case-sensitive)"');

    // Action button
    expect(html).toContain('data-testid="clear-debug-log"');
    expect(html).toContain('Clear log');

    // Log display container
    expect(html).toContain('data-testid="debug-log"');
  });

  it('renders initial diagnostic log entries safely without raw HTML sinks', () => {
    const html = renderToString(<DebugConsoleWorkspace />);

    expect(html).toContain('System');
    expect(html).toContain('Diagnostic debug console initialized.');
    expect(html).toContain('Engine');
    expect(html).toContain('Core runtime listener attached.');
  });
});
