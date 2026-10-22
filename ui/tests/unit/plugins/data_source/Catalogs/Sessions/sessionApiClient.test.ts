import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createDomainClient } from '../../../../../../app/host/transport';
import { cloneRemoteSession, fetchRemoteSessions, fromSessionDefinition, saveSessionElement, setSessionApiClient, toSessionDefinition, type RemoteSessionDefinition } from '../../../../../../app/plugins/data_source/Catalogs/Sessions/sessionApiClient';
import { useSessions } from '../../../../../../app/plugins/data_source/Catalogs/Sessions/sessionStore';

const row: RemoteSessionDefinition = {
  id: '1', name: 'Configured', broker_id: 0, description: 'Recorded profile', timezone: 'America/New_York', is_default: true,
  windows: [{ day_from: 'Sun', day_to: 'Mon', start_time: '23:50:15', end_time: '00:10:45', eod: true, session_type: 'Extended', day_of_week: 6 }],
  holidays: [{ date_str: '2028-02-29', description: 'Configured closure' }],
};
const response = (data: unknown) => new Response(JSON.stringify({ status: 'success', data }));
function setup() {
  const fetchFn = vi.fn();
  setSessionApiClient(createDomainClient('/data', { fetchFn, baseUrl: '/api/v1' }));
  return fetchFn;
}
beforeEach(() => useSessions.getState().reset());

describe('authoritative session contracts', () => {
  it('round trips timezone, seconds, holiday descriptions, broker zero and window metadata', () => {
    expect(fromSessionDefinition(toSessionDefinition(row))).toEqual(row);
  });
  it('carries legacy read notes without sending them back on save', () => {
    const normalized = toSessionDefinition({ ...row, normalization_warnings: ['EOD was not stored; default False is used.'] });
    expect(normalized.normalizationWarnings).toEqual(['EOD was not stored; default False is used.']);
    expect(fromSessionDefinition(normalized)).toEqual(row);
  });
  it.each([null, 'warning', [1], ['']])('rejects invalid read notes %j', warnings => {
    expect(() => toSessionDefinition({ ...row, normalization_warnings: warnings } as RemoteSessionDefinition)).toThrow('normalization warnings');
  });
  it('waits for confirmation and never adds a local clone after rejection', async () => {
    let resolve!: (value: Response) => void;
    const fetchFn = setup().mockReturnValueOnce(new Promise<Response>(done => { resolve = done; })).mockRejectedValueOnce(new Error('conflict'));
    const pending = useSessions.getState().save(toSessionDefinition(row));
    expect(useSessions.getState().sessions).toEqual([]);
    resolve(response(row)); await pending;
    await expect(useSessions.getState().clone(toSessionDefinition(row), 'Copy', 30)).rejects.toThrow('conflict');
    expect(useSessions.getState().sessions.map(item => item.name)).toEqual(['Configured']);
    expect(JSON.parse(fetchFn.mock.calls[1][1].body)).toEqual({ session_id: '1', new_name: 'Copy', timezone_offset: 30 });
  });
  it('clears empty results and exposes a failed refresh with no cache fallback', async () => {
    setup().mockResolvedValueOnce(response([row])).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(response([]));
    await useSessions.getState().refreshFromServer();
    await useSessions.getState().refreshFromServer();
    expect(useSessions.getState().error).toContain('offline');
    expect(useSessions.getState().sessions).toHaveLength(1);
    await useSessions.getState().refreshFromServer();
    expect(useSessions.getState().sessions).toEqual([]);
  });
  it('reports individual deletion failures without removing unconfirmed rows', async () => {
    const other = { ...row, id: '2', name: 'Other' };
    setup().mockResolvedValueOnce(response([row, other])).mockResolvedValueOnce(response({ id: '1', deleted: true })).mockRejectedValueOnce(new Error('unavailable'));
    await useSessions.getState().refreshFromServer();
    expect(await useSessions.getState().remove(['1','2'])).toEqual({ deleted: ['1'], failed: ['2'] });
    expect(useSessions.getState().sessions.map(item => item.id)).toEqual(['2']);
  });
  it('ignores reads from an old host session and reads older than a confirmed write', async () => {
    let resolve!: (value: Response) => void;
    setup().mockReturnValueOnce(new Promise<Response>(done => { resolve = done; })).mockResolvedValueOnce(response({ ...row, description: 'Confirmed' }));
    const pending = useSessions.getState().refreshFromServer();
    await useSessions.getState().save({ ...toSessionDefinition(row), description: 'Confirmed' });
    resolve(response([row])); await pending;
    expect(useSessions.getState().sessions[0].description).toBe('Confirmed');
    let oldResolve!: (value: Response) => void;
    setup().mockReturnValueOnce(new Promise<Response>(done => { oldResolve = done; }));
    const old = useSessions.getState().refreshFromServer();
    useSessions.getState().reset(); oldResolve(response([row])); await old;
    expect(useSessions.getState().sessions).toEqual([]);
  });
  it('checks IDs on element responses and validates clone shifts before sending', async () => {
    const fetchFn = setup().mockResolvedValue(response({ ...row, id: '2' }));
    await expect(saveSessionElement('1', 'remove', 0)).rejects.toThrow('different session identity');
    expect(JSON.parse(fetchFn.mock.calls[0][1].body)).toEqual({ action: 'remove', index: 0 });
    await expect(cloneRemoteSession('1','Copy',NaN)).rejects.toThrow('integer minutes');
    expect(fetchFn).toHaveBeenCalledTimes(1);
  });
  it.each([null, {}, [row, row], [{ ...row, id: 1 }], [{ ...row, holidays: [{ date_str: '2027-02-29', description: '' }] }], [{ ...row, windows: [{ ...row.windows[0], day_from: 'Invalid' }] }]])('rejects malformed calendars %j', async data => {
    setup().mockResolvedValue(response(data));
    await expect(fetchRemoteSessions()).rejects.toThrow();
  });
});
