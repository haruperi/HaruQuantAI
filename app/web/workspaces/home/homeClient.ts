import { createDomainClient, type TransportConfig } from '../../shell/transport';

export interface RecentProject {
  id: string;
  name: string;
  workspace: string;
  last_activity: string;
}

export interface HomeIndex {
  recent_projects: RecentProject[];
}

export interface AboutInfo {
  application: string;
  version: string;
  build_timestamp: string;
  runtime: string;
  metadata_source: string;
  license: { state: string; reason: string };
}

export interface ReleaseInfo {
  state: 'available' | 'unavailable' | 'unsupported' | 'error';
  reason: string;
  current_version: string;
  latest_version: string | null;
  update_available: boolean | null;
  changelog: string | null;
  release_url: string | null;
  published_at: string | null;
  checked_at: string;
}

export interface DiagnosticsInfo {
  status: string;
  database: { exists: boolean; path: string; error: string | null };
  hardware: { ram_total_bytes: number; ram_available_bytes: number; ram_used_pct: number };
  directories: Record<string, string>;
}

export interface SavedTask {
  task_id: string; task_type: string; name: string; enabled: boolean; databank_target: string;
  settings: Record<string, unknown>; dependencies: string[];
}

export interface StoredResult {
  result_id: string; strategy_id: string; strategy_name: string; databank_id: string;
  metrics: Record<string, number | string>; trades: Record<string, unknown>[];
  equity_curve: { timestamp: number; equity: number; balance: number; drawdown: number }[];
  parameters: Record<string, unknown>; strategy_payload: Record<string, unknown>;
  mae_mfe: Record<string, unknown>[];
}

export interface ProjectDocumentData {
  revision: number;
  manifest: {
    schema_version: number;
    project_id: string;
    name: string;
    created_at?: string;
    updated_at?: string;
  };
  pipeline?: string[];
  databanks?: Record<string, string>;
  tasks: Record<string, SavedTask>;
  metadata?: Record<string, unknown> & { revision?: number; notes?: string };
}

export interface SaveSettingsResult {
  status: string;
  task_id: string;
  revision: number;
}

export interface SaveNotesResult {
  status: string;
  notes: string;
  revision: number;
}

export interface ApplyTemplateResult {
  status: string;
  task_id: string;
  strategy_type: string;
  revision: number;
}

export interface ResolveResourcesResult {
  status: string;
  resolved_count: number;
  revision: number;
}

export interface EngineActionResult {
  action: string;
  status: string;
  project_id: string;
  task_id: string | null;
  job_id: string | null;
}

export interface EngineStatusResult {
  project_id: string;
  status: string;
  job_id: string | null;
  progress: number;
  message: string;
  result?: Record<string, unknown> | null;
}

export interface DashboardStrategySummary {
  id: string;
  strategy_id: string;
  name: string;
  [metric: string]: string | number;
}

export interface DashboardResultsData {
  project_id: string;
  databank_id: string;
  sample_type: string;
  metric: string;
  total_candidates: number;
  strategies: DashboardStrategySummary[];
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
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new Error('Invalid numeric value.');
  return value;
}
function boolean(value: unknown): boolean {
  if (typeof value !== 'boolean') throw new Error('Invalid boolean status.');
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
    async getProject(projectId: string): Promise<ProjectDocumentData> {
      const raw = object(await client.get<unknown>(`/project/${encodeURIComponent(projectId)}`));
      const manifest = object(raw.manifest);
      const tasks = Object.fromEntries(Object.entries(object(raw.tasks)).map(([id, entry]) => {
        const task = object(entry);
        if (!Array.isArray(task.dependencies) || !task.dependencies.every(v => typeof v === 'string')) throw new Error('Invalid task dependencies.');
        const parsed: SavedTask = { task_id: text(task.task_id), task_type: text(task.task_type), name: text(task.name),
          enabled: boolean(task.enabled), databank_target: text(task.databank_target),
          dependencies: task.dependencies, settings: object(task.settings) };
        if (parsed.task_id !== id) throw new Error('Mismatched task identity.');
        return [id, parsed];
      }));
      if (text(manifest.project_id) !== projectId) throw new Error('Mismatched project identity.');
      return { manifest: { project_id: text(manifest.project_id), name: text(manifest.name), schema_version: number(manifest.schema_version) },
        revision: number(raw.revision), tasks, metadata: object(raw.metadata),
        pipeline: Array.isArray(raw.pipeline) ? raw.pipeline.map(text) : [],
        databanks: Object.fromEntries(Object.entries(object(raw.databanks)).map(([key, value]) => [key, text(value)])) };
    },
    async saveSettings(projectId: string, taskId: string, settings: Record<string, unknown>, expectedRevision: number): Promise<SaveSettingsResult> {
      const value = object(await client.post<unknown>(`/project/${encodeURIComponent(projectId)}/settings`, {
        task_id: taskId,
        settings,
        expected_revision: expectedRevision,
      }));
      return {
        status: text(value.status),
        task_id: text(value.task_id),
        revision: number(value.revision),
      };
    },
    async saveNotes(projectId: string, notes: string, expectedRevision: number): Promise<SaveNotesResult> {
      const value = object(await client.post<unknown>(`/project/${encodeURIComponent(projectId)}/notes`, {
        notes,
        expected_revision: expectedRevision,
      }));
      return {
        status: text(value.status),
        notes: text(value.notes),
        revision: number(value.revision),
      };
    },
    async applyTemplate(projectId: string, taskId: string, strategyType: string, expectedRevision: number): Promise<ApplyTemplateResult> {
      const value = object(await client.post<unknown>(`/project/${encodeURIComponent(projectId)}/template`, {
        task_id: taskId,
        strategy_type: strategyType,
        expected_revision: expectedRevision,
      }));
      return {
        status: text(value.status),
        task_id: text(value.task_id),
        strategy_type: text(value.strategy_type ?? value.template),
        revision: number(value.revision),
      };
    },
    async resolveResources(projectId: string, resolutions: Record<string, string>, expectedRevision: number): Promise<ResolveResourcesResult> {
      const value = object(await client.post<unknown>(`/project/${encodeURIComponent(projectId)}/resources/resolve`, {
        resolutions,
        expected_revision: expectedRevision,
      }));
      return {
        status: text(value.status),
        resolved_count: number(value.resolved_count),
        revision: number(value.revision),
      };
    },
    async saveAnalysis(projectId: string, names: string[], expectedRevision: number): Promise<{ revision: number; names: string[] }> {
      const value = object(await client.post<unknown>(`/project/${encodeURIComponent(projectId)}/analysis`, { names, expected_revision: expectedRevision }));
      if (value.status !== 'saved' || !Array.isArray(value.analysis_tabs) || JSON.stringify(value.analysis_tabs) !== JSON.stringify(names)) throw new Error('Analysis save was not acknowledged.');
      return { revision: number(value.revision), names: value.analysis_tabs.map(text) };
    },
    async engineAction(projectId: string, action: 'start' | 'pause' | 'resume' | 'stop', taskId?: string, expectedRevision?: number, jobId?: string | null): Promise<EngineActionResult> {
      const value = object(await client.post<unknown>(`/engine/${encodeURIComponent(projectId)}/${encodeURIComponent(action)}`, {
        task_id: taskId ?? null, expected_revision: expectedRevision ?? null, job_id: jobId ?? null,
      }));
      return {
        action: text(value.action ?? action),
        status: text(value.status),
        project_id: text(value.project_id),
        task_id: nullableText(value.task_id),
        job_id: nullableText(value.job_id),
      };
    },
    async getEngineStatus(projectId: string, jobId?: string | null): Promise<EngineStatusResult> {
      const value = object(await client.get<unknown>(`/engine/${encodeURIComponent(projectId)}/status${jobId ? `?job_id=${encodeURIComponent(jobId)}` : ''}`));
      return {
        project_id: text(value.project_id),
        status: text(value.status),
        job_id: nullableText(value.job_id),
        result: value.result == null ? null : object(value.result),
        progress: number(value.progress),
        message: text(value.message),
      };
    },
    async getResult(projectId: string, resultId: string): Promise<StoredResult> {
      const value = object(await client.get<unknown>(`/project/${encodeURIComponent(projectId)}/result/${encodeURIComponent(resultId)}`));
      const array = (raw: unknown) => { if (!Array.isArray(raw)) throw new Error('Invalid result records.'); return raw.map(object); };
      const metrics = Object.fromEntries(Object.entries(object(value.metrics)).map(([key, entry]) => [key, typeof entry === 'string' ? entry : number(entry)]));
      const result: StoredResult = { result_id: text(value.result_id), strategy_id: text(value.strategy_id),
        strategy_name: text(value.strategy_name), databank_id: text(value.databank_id), metrics,
        trades: array(value.trades), mae_mfe: array(value.mae_mfe),
        parameters: object(value.parameters), strategy_payload: object(value.strategy_payload),
        equity_curve: array(value.equity_curve).map(point => ({ timestamp: number(point.timestamp), equity: number(point.equity), balance: number(point.balance), drawdown: number(point.drawdown) })) };
      if (result.result_id !== resultId) throw new Error('Mismatched result identity.');
      return result;
    },
    async getDashboardResults(options: {
      projectId: string;
      databankId?: string;
      sampleType?: string;
      metric?: string;
      limit?: number;
    }): Promise<DashboardResultsData> {
      const params = new URLSearchParams();
      params.set('project_id', options.projectId);
      if (options.databankId) params.set('databank_id', options.databankId);
      if (options.sampleType) params.set('sample_type', options.sampleType);
      if (options.metric) params.set('metric', options.metric);
      if (options.limit !== undefined) params.set('limit', String(options.limit));

      const value = object(await client.get<unknown>(`/dashboard/results?${params.toString()}`));
      if (!Array.isArray(value.strategies)) throw new Error('Invalid dashboard strategies.');
      return {
        project_id: text(value.project_id),
        databank_id: text(value.databank_id),
        sample_type: text(value.sample_type),
        metric: text(value.metric),
        total_candidates: number(value.total_candidates),
        strategies: value.strategies.map(s => {
          const item = object(s);
          return { id: text(item.id), strategy_id: text(item.strategy_id), name: text(item.name), [text(value.metric)]: number(item[text(value.metric)]) };
        }),
      };
    },
  };
}
