import { renderToString } from 'react-dom/server';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { HomeScreen } from '../../../app/workspace/Home/HomeScreen';
import { homeClient } from '../../../app/workspace/Home/homeClient';
import content from '../../../app/workspace/Home/homeContent.json';

const host = vi.hoisted(() => ({ status: 'locked' }));
vi.mock('../../../app/host/HostConnection', () => ({ useHostConnection: () => host }));
afterEach(() => { host.status = 'locked'; vi.restoreAllMocks(); });
const response = (data: unknown) => vi.fn(async () => new Response(JSON.stringify({ status: 'success', data }), { headers: { 'Content-Type': 'application/json' } }));

describe('Home landing and host client', () => {
  it.each(['locked', 'offline', 'connecting'])('keeps original local help readable when %s', status => {
    host.status = status;
    const html = renderToString(<MemoryRouter><HomeScreen /></MemoryRouter>);
    expect(html).toContain(content.title);
    for (const guide of content.tutorials) expect(html).toContain(guide.body);
    expect(html).toContain('Local help');
    expect(html).toContain('Connect to view recent projects.');
    expect(html).not.toContain('EURUSD H1 — Genetic research');
    expect(html).not.toContain('Full feature fixture');
    expect(html).toContain('disabled');
  });
  it('reads actual host summaries through the shared transport', async () => {
    const projects = [{ id: 'p1', name: 'Saved project', workspace: 'projects', last_activity: '2026-10-21T00:00:00Z' }];
    const fetchFn = response({ recent_projects: projects });
    expect(await homeClient({ baseUrl: '/api/v1', fetchFn }).index()).toEqual({ recent_projects: projects });
    expect(fetchFn).toHaveBeenCalledWith('/api/v1/home', expect.objectContaining({ method: 'GET' }));
  });
  it.each([{}, null, { recent_projects: [{}] }, { recent_projects: 'not an array' }])('rejects malformed project responses', async data => {
    await expect(homeClient({ fetchFn: response(data) }).index()).rejects.toThrow();
  });
  it('keeps unavailable release status separate from up-to-date', async () => {
    const data = { state: 'unavailable', reason: 'No release feed configured.', current_version: '1.0.0', latest_version: null, update_available: null, changelog: null, release_url: null, published_at: null, checked_at: '2026-10-21T00:00:00Z' };
    expect((await homeClient({ fetchFn: response(data) }).updates()).update_available).toBeNull();
    await expect(homeClient({ fetchFn: response({ ...data, state: 'invented' }) }).updates()).rejects.toThrow();
  });
  it('rejects invalid metadata and diagnostics rather than inventing values', async () => {
    await expect(homeClient({ fetchFn: response({}) }).about()).rejects.toThrow();
    await expect(homeClient({ fetchFn: response({ status: 'OK', database: {}, hardware: {}, directories: {} }) }).diagnostics()).rejects.toThrow();
  });
  it('propagates expired session and cancellation errors', async () => {
    const fetchFn = vi.fn(async () => new Response(JSON.stringify({ status: 'error', error: { code: 'UNAUTHORIZED', message: 'Session expired.' } }), { status: 401 }));
    await expect(homeClient({ fetchFn }).index()).rejects.toThrow('Session expired.');
    const controller = new AbortController(); controller.abort();
    await expect(homeClient({ signal: controller.signal, fetchFn: response({ recent_projects: [] }) }).index()).rejects.toThrow();
  });
});
