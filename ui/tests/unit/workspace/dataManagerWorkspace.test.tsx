import { renderToString } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { DataManagerChart } from '../../../app/workspace/DataManager/DataManagerChart';
import { DataManagerDock } from '../../../app/workspace/DataManager/DataManagerDock';
import { fetchWorkspace, openWorkspaceTab, workspaceTabIds, type WorkspaceLayout, type WorkspaceSnapshot } from '../../../app/workspace/DataManager/dataManagerWorkspaceClient';

const layout: WorkspaceLayout = {
  tabs: workspaceTabIds.map((id, index) => ({ id, title: id, core: index < 5 })),
  active_tab: 'data', layout: { core_group: 'catalogs', chart_position: 'right' },
};
const snapshot: WorkspaceSnapshot = {
  active_tab: 'chart', selection: { id: 'recorded:D1', symbol: 'EURUSD', timeframe: 'D1', broker_name: 'Research', timezone: 'UTC' },
  preview: { state: 'ready', reason: '', limit: 500, rows: [{ time: 1767225600, open: 1, high: 3, low: 0.5, close: 2, volume: 30 }] },
};
const response = (data: unknown) => new Response(JSON.stringify({ status: 'success', data }));

describe('Data Manager shell contracts', () => {
  it('loads the five core panel descriptors through the host transport', async () => {
    const fetchFn = vi.fn().mockResolvedValue(response(layout));
    expect(await fetchWorkspace({ baseUrl: '/api/v1', fetchFn })).toEqual(layout);
    expect(fetchFn.mock.calls[0][0]).toBe('/api/v1/data/workspace');
  });

  it('opens the exact dataset ID without sending symbols or storage paths', async () => {
    const fetchFn = vi.fn().mockResolvedValue(response(snapshot));
    const result = await openWorkspaceTab('chart', 'recorded:D1', { baseUrl: '/api/v1', fetchFn });
    expect(result.selection?.timeframe).toBe('D1');
    expect(fetchFn.mock.calls[0][0]).toBe('/api/v1/data/workspace/tabs/chart');
    expect(JSON.parse(fetchFn.mock.calls[0][1].body)).toEqual({ context: { dataset_id: 'recorded:D1' } });
  });

  it('rejects incomplete or duplicate panel catalogs', async () => {
    await expect(fetchWorkspace({ fetchFn: vi.fn().mockResolvedValue(response({ ...layout, tabs: layout.tabs.slice(1) })) })).rejects.toThrow('Invalid Data Manager workspace response');
    await expect(fetchWorkspace({ fetchFn: vi.fn().mockResolvedValue(response({ ...layout, tabs: layout.tabs.map(() => layout.tabs[0]) })) })).rejects.toThrow('Invalid Data Manager workspace response');
  });

  it('explains when the running host needs to load the new workspace', async () => {
    const fetchFn = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'error', error: { code: 'NOT_FOUND', message: 'Not Found' } }), { status: 404 }));
    await expect(fetchWorkspace({ fetchFn })).rejects.toThrow('Restart the host to load the updated Data Manager workspace.');
  });

  it.each([
    { ...snapshot, selection: { ...snapshot.selection, id: 'other' } },
    { ...snapshot, preview: { ...snapshot.preview, rows: [{ time: 1, open: 5, high: 1, low: 2, close: 3, volume: 1 }] } },
    { ...snapshot, preview: { ...snapshot.preview, rows: [...snapshot.preview.rows, ...snapshot.preview.rows] } },
    { ...snapshot, preview: { ...snapshot.preview, state: 'unavailable' } },
  ])('refuses mismatched identities or invalid recorded arrays', async value => {
    await expect(openWorkspaceTab('chart', 'recorded:D1', { fetchFn: vi.fn().mockResolvedValue(response(value)) })).rejects.toThrow('Invalid Data Manager workspace response');
  });

  it('cancels requests without publishing a superseded result', async () => {
    const controller = new AbortController();
    const fetchFn = vi.fn().mockImplementation(async () => { controller.abort(); return response(snapshot); });
    await expect(openWorkspaceTab('chart', 'recorded:D1', { signal: controller.signal, fetchFn })).rejects.toMatchObject({ name: 'AbortError' });
  });

  it('renders recorded values and explicit unavailable/loading/error states', () => {
    const props = { snapshot, loading: false, error: '', onRetry: () => {} };
    const html = renderToString(<DataManagerChart {...props} />);
    expect(html).toContain('EURUSD · D1');
    expect(html).toContain('Recorded bars');
    expect(html).toContain('2026-01-01T00:00:00.000Z');
    expect(html).toContain('Recorded candlestick chart');
    expect(renderToString(<DataManagerChart {...props} loading />)).toContain('Loading recorded history');
    expect(renderToString(<DataManagerChart {...props} error="History unavailable" />)).toContain('History unavailable');
    expect(renderToString(<DataManagerChart {...props} snapshot={null} />)).toContain('Select a saved dataset');
  });

  it('renders the dock container without duplicate lower tab headers', () => {
    const html = renderToString(
      <DataManagerDock
        layout={layout}
        activeId="data"
        activation={0}
        chartRequest={0}
        arrangeRequest={{ seq: 1, action: 'right', targetId: 'instruments' }}
        onActivate={() => {}}
        renderPanel={() => null}
      />,
    );
    expect(html).toContain('Data Manager dockable workspace');
    expect(html).not.toContain('dm-dock-tab');
  });
});
