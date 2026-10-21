import { createDomainClient, type TransportConfig } from '../../host/transport';

export interface RecentProject { id: string; name: string; workspace: string; last_activity: string }
export interface HomeIndex { recent_projects: RecentProject[] }
export interface AboutInfo {
  application: string; version: string; build_timestamp: string; runtime: string;
  metadata_source: string; license: { state: string; reason: string };
}
export interface ReleaseInfo {
  state: 'available' | 'unavailable' | 'unsupported' | 'error'; reason: string;
  current_version: string; latest_version: string | null; update_available: boolean | null;
  changelog: string | null; release_url: string | null; published_at: string | null; checked_at: string;
}
export interface DiagnosticsInfo {
  status: string; database: { exists: boolean; path: string; error: string | null };
  hardware: { ram_total_bytes: number; ram_available_bytes: number; ram_used_pct: number };
  directories: Record<string, string>;
}

function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid Home response.');
  return value as Record<string, unknown>;
}
function text(value: unknown): string {
  if (typeof value !== 'string') throw new Error('Invalid Home text field.');
  return value;
}
function nullableText(value: unknown): string | null { return value === null ? null : text(value); }
function number(value: unknown): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('Invalid diagnostic value.');
  return value;
}
function boolean(value: unknown): boolean {
  if (typeof value !== 'boolean') throw new Error('Invalid diagnostic status.');
  return value;
}

export function homeClient(config: TransportConfig = {}) {
  const client = createDomainClient('/home', config);
  return {
    async index(): Promise<HomeIndex> {
      const value = object(await client.get<unknown>(''));
      if (!Array.isArray(value.recent_projects)) throw new Error('Invalid project summaries.');
      return { recent_projects: value.recent_projects.map(item => {
        const project = object(item);
        return { id: text(project.id), name: text(project.name), workspace: text(project.workspace), last_activity: text(project.last_activity) };
      }) };
    },
    async about(): Promise<AboutInfo> {
      const value = object(await client.get<unknown>('/about')), license = object(value.license);
      return { application: text(value.application), version: text(value.version), build_timestamp: text(value.build_timestamp),
        runtime: text(value.runtime), metadata_source: text(value.metadata_source), license: { state: text(license.state), reason: text(license.reason) } };
    },
    async updates(): Promise<ReleaseInfo> {
      const value = object(await client.get<unknown>('/updates'));
      if (!['available', 'unavailable', 'unsupported', 'error'].includes(text(value.state))) throw new Error('Invalid release state.');
      return { state: value.state as ReleaseInfo['state'], update_available: value.update_available === null ? null : boolean(value.update_available),
        reason: text(value.reason), current_version: text(value.current_version), latest_version: nullableText(value.latest_version),
        changelog: nullableText(value.changelog), release_url: nullableText(value.release_url), published_at: nullableText(value.published_at), checked_at: text(value.checked_at) };
    },
    async diagnostics(): Promise<DiagnosticsInfo> {
      const value = object(await client.get<unknown>('/diagnostics')), database = object(value.database), hardware = object(value.hardware);
      const directories = Object.fromEntries(Object.entries(object(value.directories)).map(([key, entry]) => [key, text(entry)]));
      return { status: text(value.status), directories,
        database: { exists: boolean(database.exists), path: text(database.path), error: nullableText(database.error) },
        hardware: { ram_total_bytes: number(hardware.ram_total_bytes), ram_available_bytes: number(hardware.ram_available_bytes), ram_used_pct: number(hardware.ram_used_pct) } };
    },
  };
}
