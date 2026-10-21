import { renderToString } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import {
  HelpTooltip,
  resolveActiveTutorial,
  type HelpGuidePayload,
} from '../../../app/components/HelpTooltip';
import {
  DEFAULT_DM_TUTORIALS,
  fetchDataManagerHelp,
  helpTopicForTab,
} from '../../../app/workspace/DataManager/DataManager';

describe('HelpTooltip & DataManagerHelp', () => {
  it('renders closed trigger by default and expands contextual help dialog when open', () => {
    const closedHtml = renderToString(
      <HelpTooltip
        title="Data Manager Overview"
        summary="Download, import, and export market data."
        topic="overview"
        availableTopics={['overview', 'export', 'import']}
        tutorials={DEFAULT_DM_TUTORIALS}
      />,
    );
    expect(closedHtml).toContain('data-testid="help-tooltip-trigger"');
    expect(closedHtml).toContain('aria-expanded="false"');
    expect(closedHtml).not.toContain('data-testid="help-tooltip-panel"');

    const openHtml = renderToString(
      <HelpTooltip
        title="Data Manager Overview"
        summary="Download, import, and export market data."
        topic="overview"
        availableTopics={['overview', 'export', 'import']}
        tutorials={DEFAULT_DM_TUTORIALS}
        defaultOpen
      />,
    );
    expect(openHtml).toContain('aria-expanded="true"');
    expect(openHtml).toContain('data-testid="help-tooltip-panel"');
    expect(openHtml).toContain('Data Manager Overview');
    expect(openHtml).toContain('data-testid="dm-help-openlink-btn"');
    expect(openHtml).toContain('data-testid="dm-help-openlink-btn-2"');
    expect(openHtml).toContain('data-testid="dm-help-openlink-btn-3"');
    expect(openHtml).toContain('data-testid="help-tutorial-steps-tick-precision-testing"');
  });

  it('resolves selected tutorials and renders steps for export and import guides', () => {
    expect(resolveActiveTutorial(DEFAULT_DM_TUTORIALS, 'platform-data-export')?.id).toBe(
      'platform-data-export',
    );
    expect(resolveActiveTutorial(DEFAULT_DM_TUTORIALS, 'unknown')?.id).toBe(
      'tick-precision-testing',
    );
    expect(resolveActiveTutorial([], null)).toBeNull();

    const exportTutorialHtml = renderToString(
      <HelpTooltip
        topic="export"
        tutorials={DEFAULT_DM_TUTORIALS}
        defaultActiveTutorialId="platform-data-export"
        defaultOpen
      />,
    );
    expect(exportTutorialHtml).toContain('data-testid="help-tutorial-steps-platform-data-export"');
    expect(exportTutorialHtml).toContain(
      'Open the Export ribbon tab and select the target format.',
    );
  });

  it('renders loaded guide payload, topic selector, and error alert states', () => {
    const guide: HelpGuidePayload = {
      topic: 'export',
      title: 'Multi-Format Data Export',
      summary: 'Export selected datasets to target files.',
      available_topics: ['overview', 'export'],
      tutorials: DEFAULT_DM_TUTORIALS,
    };

    const html = renderToString(
      <HelpTooltip
        topic="export"
        guide={guide}
        initialError="Help service warning"
        defaultOpen
      />,
    );
    expect(html).toContain('Multi-Format Data Export');
    expect(html).toContain('Export selected datasets to target files.');
    expect(html).toContain('data-testid="help-topic-select"');
    expect(html).toContain('data-testid="help-tooltip-error"');
    expect(html).toContain('Help service warning');
  });

  it('fetches contextual help from /data/help and maps all Data Manager tabs to topics', async () => {
    expect(helpTopicForTab['Home']).toBe('overview');
    expect(helpTopicForTab['Data sources']).toBe('data');
    expect(helpTopicForTab['Export']).toBe('export');
    expect(helpTopicForTab['Instruments']).toBe('instruments');
    expect(helpTopicForTab['Sessions']).toBe('sessions');
    expect(helpTopicForTab['External indicators']).toBe('custom-data');
    expect(helpTopicForTab['Stock groups']).toBe('stock-groups');
    expect(helpTopicForTab['Broker profiles']).toBe('brokers');
    expect(helpTopicForTab['Log']).toBe('log');
    expect(helpTopicForTab['Chart']).toBe('chart');

    const payload: HelpGuidePayload = {
      topic: 'export',
      title: 'Multi-Format Data Export',
      summary: 'Export selected datasets to target files.',
      available_topics: ['overview', 'export'],
      tutorials: DEFAULT_DM_TUTORIALS,
    };
    const fetchFn = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: 'success', data: payload }), { status: 200 }),
    );

    const result = await fetchDataManagerHelp('export', { baseUrl: '/api/v1', fetchFn });
    expect(result).toEqual(payload);
    expect(fetchFn.mock.calls[0][0]).toBe('/api/v1/data/help?topic=export');
  });
});
