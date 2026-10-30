import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { GridTestWorkspace } from '../../../workspaces/grid_test/GridTestWorkspace';

describe('AppGridTestPanel workspace component', () => {
  it('renders complete donor layout with info panel, testGrid, and action controls', () => {
    const html = renderToString(<GridTestWorkspace />);

    // Info panel
    expect(html).toContain('data-testid="info-panel"');
    expect(html).toContain('data-testid="rows-count"');
    expect(html).toContain('Rows in grid:');
    expect(html).toContain('Selected:');

    // Table container
    expect(html).toContain('id="testGrid"');
    expect(html).toContain('data-testid="test-grid"');
    expect(html).toContain('Select');
    expect(html).toContain('Index');
    expect(html).toContain('Multiplier (x2)');
    expect(html).toContain('Text');

    // Control buttons with exact donor IDs
    expect(html).toContain('id="buttonStartStopTest-64a"');
    expect(html).toContain('Start test');

    expect(html).toContain('id="buttonSelectAll-64b"');
    expect(html).toContain('Select All');

    expect(html).toContain('id="buttonSelectNone-64c"');
    expect(html).toContain('Select None');

    expect(html).toContain('id="buttonClear-64d"');
    expect(html).toContain('Clear');

    expect(html).toContain('id="buttonAdd100Rows-64e"');
    expect(html).toContain('Add 100 rows');
  });

  it('renders initial 100 rows with triple values', () => {
    const html = renderToString(<GridTestWorkspace />);

    // Initial batch checks
    expect(html).toContain('0-text');
    expect(html).toContain('99-text');
  });
});
