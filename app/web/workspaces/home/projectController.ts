import { createContext, createElement, useContext, useEffect, useMemo, useSyncExternalStore, type ReactNode } from 'react';
import { useHostConnection } from '../../shell/HostConnection';
import { useAppStore } from '../../shell/store';
import { homeClient, type ProjectDocumentData, type RecentProject, type StoredResult } from './homeClient';

export interface ProjectState {
  projects: RecentProject[]; project: ProjectDocumentData | null; taskId: string;
  draft: Record<string, unknown>; dirty: boolean; busy: boolean; error: string | null;
  results: StoredResult[]; selectedResultId: string | null;
  validationErrors: Record<string, string>;
}
const initial = (): ProjectState => ({ projects: [], project: null, taskId: '', draft: {}, dirty: false, busy: false, error: null, results: [], selectedResultId: null, validationErrors: {} });
const types: Record<string, string[]> = { builder: ['build', 'builder'], retester: ['retest', 'retester'], optimizer: ['optimize', 'optimizer'] };

/** One project authority per mounted workspace; generation guards reject stale replies. */
export class ProjectController {
  private state = initial();
  private listeners = new Set<() => void>();
  private abort = new AbortController();
  private generation = 0;
  private saving = false;
  constructor(readonly workspace: string, private suppliedClient?: ReturnType<typeof homeClient>) {}
  getSnapshot = () => this.state;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => this.listeners.delete(listener); };
  private update(patch: Partial<ProjectState>) { this.state = { ...this.state, ...patch }; this.listeners.forEach(listener => listener()); }
  private client() { return this.suppliedClient ?? homeClient({ signal: this.abort.signal }); }
  dispose() { this.generation++; this.abort.abort(); }
  disconnect() { this.dispose(); this.validate('connection', 'Connect to the host before saving or running.'); }
  async connect(preferredId?: string) {
    this.validate('connection', '');
    if (!this.state.project) { await this.initialize(preferredId); return; }
    this.abort = new AbortController(); this.generation++;
    this.update({ busy: false, error: null });
    await this.refreshResults();
  }
  async initialize(preferredId?: string) {
    this.abort = new AbortController();
    const generation = ++this.generation;
    this.update({ busy: true, error: null });
    try {
      const index = await this.client().index();
      if (generation !== this.generation) return;
      this.update({ projects: index.recent_projects, busy: false });
      const preferred = index.recent_projects.find(p => p.id === preferredId);
      const project = preferred ?? index.recent_projects.find(p => p.workspace === this.workspace);
      if (project) await this.selectProject(project.id);
    } catch (error) { if (generation === this.generation) this.update({ busy: false, error: String(error) }); }
  }
  async selectProject(id: string) {
    this.abort.abort(); this.abort = new AbortController();
    const generation = ++this.generation;
    this.update({ project: null, taskId: '', draft: {}, dirty: false, results: [], selectedResultId: null, validationErrors: {}, busy: true, error: null });
    if (!id) { this.update({ busy: false }); return; }
    try {
      const project = await this.client().getProject(id);
      if (generation !== this.generation) return;
      const task = Object.values(project.tasks).find(task => task.enabled && types[this.workspace]?.includes(task.task_type.toLowerCase()));
      this.update({ project, taskId: task?.task_id ?? '', draft: structuredClone(task?.settings ?? {}), busy: false,
        error: task ? null : 'This project has no supported saved task for this workspace.' });
      useAppStore.getState().setActiveProject(project.manifest.project_id);
      await this.refreshResults();
    } catch (error) { if (generation === this.generation) this.update({ busy: false, error: String(error) }); }
  }
  selectTask(id: string) {
    const task = this.state.project?.tasks[id];
    if (!task || !types[this.workspace]?.includes(task.task_type.toLowerCase())) return;
    this.update({ taskId: id, draft: structuredClone(task.settings), dirty: false, validationErrors: {}, error: null });
  }
  patch(patch: Record<string, unknown>) { this.update({ draft: { ...this.state.draft, ...patch }, dirty: true, error: null }); }
  execution(): Record<string, unknown> { return (this.state.draft.execution ?? {}) as Record<string, unknown>; }
  patchExecution(part: Record<string, unknown>) {
    const execution = this.execution();
    const base = Object.keys(execution).length ? execution : { mode: { builder: 'RANDOM', retester: 'RETEST', optimizer: 'GRID' }[this.workspace], seed: 42, dataset: { symbol: '', source: '', timeframe: 'M1' } };
    this.patch({ execution: { ...base, ...part } });
  }
  validate(section: string, error: string) {
    const errors = { ...this.state.validationErrors };
    if (error) errors[section] = error; else delete errors[section];
    this.update({ validationErrors: errors });
  }
  async save() {
    const { project, taskId, draft } = this.state;
    if (!project || !taskId || this.saving || Object.keys(this.state.validationErrors).length) return;
    this.saving = true;
    const generation = this.generation, sent = structuredClone(draft);
    this.update({ busy: true, error: null });
    try {
      const saved = await this.client().saveSettings(project.manifest.project_id, taskId, sent, project.revision);
      if (generation !== this.generation) return;
      const current = this.state.project!;
      this.update({ project: { ...current, revision: saved.revision,
        tasks: { ...current.tasks, [taskId]: { ...current.tasks[taskId], settings: sent } } },
        dirty: JSON.stringify(this.state.draft) !== JSON.stringify(sent), busy: false });
    } catch (error) { if (generation === this.generation) this.update({ busy: false, error: String(error) }); }
    finally { this.saving = false; }
  }
  noteRevision(revision: number, notes: string) {
    if (this.state.project) this.update({ project: { ...this.state.project, revision, metadata: { ...this.state.project.metadata, notes } } });
  }
  async saveAnalysis(names: string[]): Promise<boolean> {
    const project = this.state.project, generation = this.generation;
    if (!project || this.saving) return false;
    this.saving = true; this.update({ busy: true, error: null });
    try {
      const saved = await this.client().saveAnalysis(project.manifest.project_id, names, project.revision);
      if (generation !== this.generation) return false;
      this.update({ project: { ...this.state.project!, revision: saved.revision, metadata: { ...this.state.project?.metadata, analysis_tabs: saved.names } }, busy: false });
      return true;
    } catch (error) { if (generation === this.generation) this.update({ busy: false, error: String(error) }); return false; }
    finally { this.saving = false; }
  }
  selectResult(id: string) { this.update({ selectedResultId: id }); }
  async refreshResults() {
    const project = this.state.project;
    if (!project) return;
    const generation = this.generation;
    try {
      const results: StoredResult[] = [];
      for (const bank of new Set(Object.values(project.databanks ?? {}))) {
        const ranked = await this.client().getDashboardResults({ projectId: project.manifest.project_id, databankId: bank, limit: 100 });
        for (const item of ranked.strategies) results.push(await this.client().getResult(project.manifest.project_id, item.id));
      }
      if (generation === this.generation) this.update({ results, selectedResultId: results.some(r => r.result_id === this.state.selectedResultId) ? this.state.selectedResultId : results[0]?.result_id ?? null });
    } catch (error) { if (generation === this.generation) this.update({ error: String(error) }); }
  }
}

export interface ProjectBinding { controller: ProjectController; state: ProjectState }
const ProjectContext = createContext<ProjectBinding | null>(null);
export const useProjectBinding = () => useContext(ProjectContext);
export function useSavedProject(workspace: string): ProjectBinding {
  const { status } = useHostConnection();
  const controller = useMemo(() => new ProjectController(workspace), [workspace]);
  const state = useSyncExternalStore(controller.subscribe, controller.getSnapshot, controller.getSnapshot);
  useEffect(() => { if (status === 'online') void controller.connect(useAppStore.getState().activeProjectId); else controller.disconnect(); return () => controller.dispose(); }, [controller, status]);
  return { controller, state };
}
export function SavedProjectProvider({ binding, children }: { binding: ProjectBinding; children: ReactNode }) {
  return createElement(ProjectContext.Provider, { value: binding }, children);
}
export function SavedProjectControls({ binding }: { binding: ProjectBinding }) {
  const { state, controller } = binding;
  return createElement('div', { className: 'pw-actions', 'aria-label': 'Saved project controls' },
    createElement('label', null, 'Project ', createElement('select', { 'aria-label': 'Saved project', value: state.project?.manifest.project_id ?? '', disabled: state.busy || state.dirty,
      onChange: (event: { target: { value: string } }) => void controller.selectProject(event.target.value) },
      createElement('option', { value: '' }, 'Select saved project'), ...state.projects.map(p => createElement('option', { key: p.id, value: p.id }, p.name)))),
    createElement('label', null, 'Task ', createElement('select', { 'aria-label': 'Saved task', value: state.taskId, disabled: state.busy || state.dirty,
      onChange: (event: { target: { value: string } }) => controller.selectTask(event.target.value) },
      createElement('option', { value: '' }, 'Select saved task'), ...Object.values(state.project?.tasks ?? {}).filter(t => types[controller.workspace]?.includes(t.task_type.toLowerCase())).map(t => createElement('option', { key: t.task_id, value: t.task_id }, t.name || t.task_id)))),
    createElement('button', { className: 'sqd-btn', disabled: !state.dirty || state.busy || Object.keys(state.validationErrors).length > 0, onClick: () => void controller.save() }, state.busy ? 'Savingâ€¦' : 'Save settings'),
    state.dirty ? createElement('span', { role: 'status' }, 'Unsaved settings') : null,
    state.error ? createElement('span', { role: 'alert' }, state.error) : null,
    ...Object.entries(state.validationErrors).map(([key, error]) => createElement('span', { key, role: 'alert' }, error)));
}


/** Supported execution fields are stored verbatim under native task.settings. */
export function ExecutionSettingsEditor() {
  const binding = useProjectBinding();
  if (!binding?.state.taskId) return createElement('p', null, 'Load a supported saved task to configure execution.');
  const { state, controller } = binding;
  const execution = (state.draft.execution ?? {}) as Record<string, unknown>;
  const dataset = (execution.dataset ?? {}) as Record<string, unknown>;
  const model = (execution.model ?? {}) as Record<string, unknown>;
  const patch = (part: Record<string, unknown>) => controller.patch({ execution: { ...execution, ...part } });
  const field = (label: string, value: unknown, change: (value: string) => void, numeric = false) => createElement('label', { className: 'pw-form-row', key: label }, label,
    createElement('input', { 'aria-label': label, type: numeric ? 'number' : 'text', value: value == null ? '' : String(value),
      onChange: (event: { target: { value: string } }) => change(event.target.value) }));
  const initialize = () => patch({ mode: { builder: 'RANDOM', retester: 'RETEST', optimizer: 'GRID' }[controller.workspace], seed: 42,
    dataset: { symbol: '', source: '', timeframe: 'M1' }, model: { initial_capital: 10000, pip_size: 0.0001, point_value: 1 }, candidates: 1 });
  return createElement('fieldset', { className: 'sqd-tab-content', disabled: state.busy },
    createElement('legend', null, 'Saved execution settings'),
    !state.draft.execution ? createElement('button', { className: 'sqd-btn', onClick: initialize }, 'Configure execution') : null,
    createElement('p', null, `Algorithm: ${String(execution.mode ?? 'Not configured')}. Other algorithms are unavailable.`),
    ...['symbol', 'source', 'timeframe'].map(key => field(`Dataset ${key}`, dataset[key], value => patch({ dataset: { ...dataset, [key]: value, revision: null } }))),
    field('Random seed', execution.seed, value => patch({ seed: Number(value) }), true),
    controller.workspace === 'builder' ? field('Candidates', execution.candidates, value => patch({ candidates: Number(value) }), true) : null,
    ...['initial_capital', 'point_value', 'pip_size', 'commission_per_order', 'slippage_points'].map(key => field(key.replaceAll('_', ' '), model[key], value => patch({ model: { ...model, [key]: Number(value) } }), true)),
    field('Sample split epoch seconds (optional)', execution.split_time, value => patch({ split_time: value ? Number(value) : null }), true),
    controller.workspace !== 'builder' ? createElement('label', null, 'Strategies to evaluate', createElement('select', { multiple: controller.workspace === 'retester', 'aria-label': 'Strategies to evaluate',
      value: (execution.strategy_result_ids as string[] | undefined) ?? [],
      onChange: (event: { target: { selectedOptions: HTMLCollectionOf<HTMLOptionElement> } }) => patch({ strategy_result_ids: Array.from(event.target.selectedOptions).map(option => option.value) }) },
      ...state.results.filter(result => Object.keys(result.strategy_payload).length > 0).map(result => createElement('option', { key: result.result_id, value: result.result_id }, `${result.strategy_name} · ${result.result_id}`)))) : null,
    controller.workspace === 'optimizer' ? createElement('div', null,
      field('Parameter name', (execution.parameter_ranges as { name: string }[] | undefined)?.[0]?.name, value => {
        const range = (execution.parameter_ranges as Record<string, unknown>[] | undefined)?.[0] ?? { start: 1, end: 2, step: 1 };
        patch({ parameter_ranges: [{ ...range, name: value }] });
      }), ...['start', 'end', 'step'].map(key => field(`Parameter ${key}`, (execution.parameter_ranges as Record<string, unknown>[] | undefined)?.[0]?.[key], value => {
        const range = (execution.parameter_ranges as Record<string, unknown>[] | undefined)?.[0] ?? { name: '', start: 1, end: 2, step: 1 };
        patch({ parameter_ranges: [{ ...range, [key]: Number(value) }] });
      }, true))) : null,
    createElement('p', null, `Destination: ${state.project?.tasks[state.taskId]?.databank_target || 'Not configured in saved task'}`));
}
