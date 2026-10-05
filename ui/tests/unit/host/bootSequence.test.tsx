/**
 * Boot transport contract tests using an in-memory WebSocket double.
 * Verify first-frame credentials, faithful stage updates, malformed-handshake
 * rejection, and socket cleanup. These checks do not connect to a live backend
 * or claim that a reported research provider has been implemented.
 */
import { describe, expect, it, vi } from 'vitest';
import { connectBootStream, setAuthToken } from '../../../app/host/transport';

/** Minimal callback-driven socket double; send/close calls remain observable. */
class Socket {
  readyState = 1;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;
  onclose: (() => void) | null = null;
  send = vi.fn();
  close = vi.fn();
}

describe('boot WebSocket transport', () => {
  it('keeps credentials out of the URL and applies actual stage outcomes', async () => {
    const socket = new Socket();
    const factory = vi.fn(() => socket as unknown as WebSocket);
    setAuthToken('ephemeral');
    const snapshots = vi.fn();
    const controller = new AbortController();
    const stream = connectBootStream(controller.signal, snapshots, vi.fn(), factory);
    socket.onopen?.();
    expect(factory.mock.calls[0]).not.toContain('ephemeral');
    expect(JSON.parse(socket.send.mock.calls[0][0]).token).toBe('ephemeral');
    socket.onmessage?.({ data: JSON.stringify({ type: 'snapshot', boot: { schema_version: 2, state: 'SERVER_READY', sequence: 1, stages: [{ stage: 'services', outcome: 'pending' }] } }) });
    await stream.ready;
    socket.onmessage?.({ data: JSON.stringify({ channel: 'boot.progress', sequence: 2, data: { stage: 'services', outcome: 'failed', reason: 'optional_provider_failed' } }) });
    expect(snapshots.mock.calls.at(-1)?.[0].stages[0].outcome).toBe('failed');
    controller.abort();
    expect(socket.close).toHaveBeenCalled();
    setAuthToken(null);
  });

  it('rejects malformed handshakes and releases the socket', async () => {
    const socket = new Socket();
    const failed = vi.fn();
    const stream = connectBootStream(new AbortController().signal, vi.fn(), failed, () => socket as unknown as WebSocket);
    socket.onmessage?.({ data: 'malformed' });
    await expect(stream.ready).rejects.toThrow('Invalid host progress response');
    expect(failed).toHaveBeenCalled();
    expect(socket.close).toHaveBeenCalled();
  });
});


describe('boot schema compatibility', () => {
  it.each([undefined, 1, 3, '2'])('rejects version %s explicitly and closes the socket', async version => {
    const socket = new Socket();
    const stream = connectBootStream(new AbortController().signal, vi.fn(), vi.fn(), () => socket as unknown as WebSocket);
    socket.onmessage?.({ data: JSON.stringify({ type: 'snapshot', boot: { schema_version: version, state: 'SERVER_READY', sequence: 0, stages: [] } }) });
    await expect(stream.ready).rejects.toThrow('Incompatible host boot schema; version 2 required');
    expect(socket.close).toHaveBeenCalled();
  });
});
