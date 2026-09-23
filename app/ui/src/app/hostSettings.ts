/** Host-owned shell preferences and authenticated settings event stream. */

import { applicationLanguages } from './globalSettings';
import { ApiClientError, createDomainClient, getAuthToken, hostBaseUrl, type TransportConfig } from './transport';
import type { AppSettings } from './types';

export type ShellPreferences = Pick<AppSettings, 'theme' | 'language' | 'zoom'>;

export function shellPreferences(settings: AppSettings): ShellPreferences {
  return { theme: settings.theme, language: settings.language, zoom: settings.zoom };
}

export function parseHostPreferences(value: unknown): ShellPreferences | null {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    throw new Error('Host settings must be an object');
  }
  const ui = (value as Record<string, unknown>).ui;
  if (ui === undefined) return null;
  if (typeof ui !== 'object' || ui === null || Array.isArray(ui)) {
    throw new Error('Host UI preferences must be an object');
  }
  const fields = ui as Record<string, unknown>;
  if (fields.theme !== 'dark' && fields.theme !== 'light') {
    throw new Error('Host theme is invalid');
  }
  if (typeof fields.language !== 'string' || !applicationLanguages.some(item => item === fields.language)) {
    throw new Error('Host language is invalid');
  }
  if (typeof fields.zoom !== 'number' || !Number.isFinite(fields.zoom) ||
      fields.zoom < 0.7 || fields.zoom > 1.8) {
    throw new Error('Host zoom is invalid');
  }
  return { theme: fields.theme, language: fields.language, zoom: fields.zoom };
}

export async function readHostPreferences(config: TransportConfig = {}): Promise<ShellPreferences | null> {
  const settings = await createDomainClient('', config).get<unknown>('/settings');
  return parseHostPreferences(settings);
}

export async function writeHostPreferences(
  preferences: ShellPreferences,
  config: TransportConfig = {},
): Promise<ShellPreferences> {
  const settings = await createDomainClient('', config).put<unknown>('/settings', { ui: preferences });
  const saved = parseHostPreferences(settings);
  if (saved === null) throw new Error('Host did not return saved UI preferences');
  return saved;
}

export interface SettingsStreamOptions {
  signal: AbortSignal;
  onChanged: () => Promise<void>;
  onConnection: (connected: boolean) => void;
  fetchFn?: typeof fetch;
  baseUrl?: string;
}

function delay(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) { resolve(); return; }
    const timer = setTimeout(resolve, ms);
    signal.addEventListener('abort', () => { clearTimeout(timer); reject(signal.reason); }, { once: true });
  });
}

export async function watchSettingsChanges(options: SettingsStreamOptions): Promise<void> {
  const { signal, onChanged, onConnection } = options;
  const fetchFn = options.fetchFn ?? fetch;
  const baseUrl = options.baseUrl ?? hostBaseUrl();
  let backoffMs = 1000;
  while (!signal.aborted) {
    try {
      const token = getAuthToken();
      if (!token) throw new ApiClientError('UNAUTHORIZED', 'Host session required', [], 401);
      const response = await fetchFn(`${baseUrl}/events?channels=settings.changed`, {
        headers: { Authorization: `Bearer ${token}`, Accept: 'text/event-stream' },
        signal,
      });
      if (response.status === 401) throw new ApiClientError('UNAUTHORIZED', 'Host session expired', [], 401);
      if (!response.ok || !response.body) throw new Error(`Settings stream failed (${response.status})`);
      onConnection(true);
      await onChanged(); // Re-read after every connection; the stream has no replay.
      backoffMs = 1000;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      try {
        while (!signal.aborted) {
          const chunk = await reader.read();
          if (chunk.done) break;
          buffer += decoder.decode(chunk.value, { stream: true }).replace(/\r\n/g, '\n');
          let frameEnd = buffer.indexOf('\n\n');
          while (frameEnd >= 0) {
            const frame = buffer.slice(0, frameEnd);
            buffer = buffer.slice(frameEnd + 2);
            for (const line of frame.split('\n')) {
              if (!line.startsWith('data:')) continue;
              const payload: unknown = JSON.parse(line.slice(5).trim());
              if (typeof payload === 'object' && payload !== null &&
                  (payload as { channel?: unknown }).channel === 'settings.changed') {
                await onChanged();
              }
            }
            frameEnd = buffer.indexOf('\n\n');
          }
        }
      } finally {
        await reader.cancel().catch(() => undefined);
      }
    } catch (error) {
      if (signal.aborted) return;
      if (error instanceof ApiClientError && error.status === 401) throw error;
    }
    if (signal.aborted) return;
    onConnection(false);
    await delay(backoffMs, signal);
    backoffMs = Math.min(backoffMs * 2, 10000);
  }
}
