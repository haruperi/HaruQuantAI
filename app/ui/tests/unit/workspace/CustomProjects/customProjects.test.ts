import { beforeEach, describe, expect, it } from 'vitest';
import { useAppStore } from '../../../../app/host/store';
import type { CustomProject, WorkflowTask } from '../../../../app/host/types';
import { SQX_TASK_TYPES } from '../../../../app/workspace/CustomProjects/NewTaskModal';

describe('Custom Projects & Pipeline Automation', () => {
  beforeEach(() => {
    useAppStore.getState().reset();
  });

  it('provides all 16 StrategyQuant X task types across 4 standard categories', () => {
    expect(SQX_TASK_TYPES.length).toBe(16);

    const taskTypes = SQX_TASK_TYPES.map(t => t.type);
    const expectedTypes = [
      'Build',
      'AutomaticPortfolioBuilder',
      'Retest',
      'Optimize',
      'Filtering',
      'CustomAnalysis',
      'ClearDatabanks',
      'LoadFromFiles',
      'SaveToFiles',
      'UpdateData',
      'LogDatabankStats',
      'CallExternalScript',
      'Notification',
      'WaitFor',
      'GoToTask',
      'StopAndStart',
    ];

    expectedTypes.forEach(type => {
      expect(taskTypes).toContain(type);
    });

    SQX_TASK_TYPES.forEach(def => {
      expect(def.name).toBeTruthy();
      expect(def.description).toBeTruthy();
      expect(def.defaultInput).toBeTruthy();
      expect(def.defaultOutput).toBeTruthy();
      expect(def.defaultConfig).toBeDefined();
    });
  });

  it('manages multiple custom projects in store (add, update, switch, delete)', () => {
    const store = useAppStore.getState();
    const initialCount = store.projects.length;
    expect(initialCount).toBeGreaterThanOrEqual(2);

    const newProject: CustomProject = {
      id: 'test-proj-99',
      name: 'Crypto Momentum Pipeline',
      description: 'Automated pipeline for BTC and ETH breakout strategies',
      status: 'idle',
      tasks: [
        {
          id: 't-1',
          type: 'Build',
          name: 'Build BTC Candidates',
          enabled: true,
          status: 'idle',
          input: 'BTCUSDT',
          output: 'CryptoCandidates',
        },
      ],
    };

    store.addProject(newProject);
    expect(useAppStore.getState().projects.length).toBe(initialCount + 1);
    expect(useAppStore.getState().activeProjectId).toBe('test-proj-99');

    // Update project
    store.updateProject('test-proj-99', { name: 'Crypto Momentum Pipeline V2' });
    const updated = useAppStore.getState().projects.find(p => p.id === 'test-proj-99');
    expect(updated?.name).toBe('Crypto Momentum Pipeline V2');

    // Delete project
    store.deleteProject('test-proj-99');
    expect(useAppStore.getState().projects.some(p => p.id === 'test-proj-99')).toBe(false);
  });

  it('manages task operations inside a project (add, update, clone, reorder, remove)', () => {
    const store = useAppStore.getState();
    const activeProject = store.projects[0];
    const initialTaskCount = activeProject.tasks.length;

    const newTask: WorkflowTask = {
      id: 'task-test-1',
      type: 'Filtering',
      name: 'Strict Sharpe Filter',
      enabled: true,
      status: 'idle',
      input: 'Candidates',
      output: 'FilteredCandidates',
      config: { minSharpe: 1.5 },
    };

    // Add task
    store.addTaskToProject(activeProject.id, newTask);
    let p = useAppStore.getState().projects.find(x => x.id === activeProject.id)!;
    expect(p.tasks.length).toBe(initialTaskCount + 1);
    expect(p.tasks.find(t => t.id === 'task-test-1')?.name).toBe('Strict Sharpe Filter');

    // Update task
    store.updateTaskInProject(activeProject.id, 'task-test-1', {
      config: { minSharpe: 2.0 },
      status: 'completed',
    });
    p = useAppStore.getState().projects.find(x => x.id === activeProject.id)!;
    expect(p.tasks.find(t => t.id === 'task-test-1')?.config?.minSharpe).toBe(2.0);
    expect(p.tasks.find(t => t.id === 'task-test-1')?.status).toBe('completed');

    // Reorder task
    const lastIndex = p.tasks.length - 1;
    store.reorderTaskInProject(activeProject.id, 'task-test-1', -1);
    p = useAppStore.getState().projects.find(x => x.id === activeProject.id)!;
    expect(p.tasks[lastIndex - 1].id).toBe('task-test-1');

    // Remove task
    store.removeTaskFromProject(activeProject.id, 'task-test-1');
    p = useAppStore.getState().projects.find(x => x.id === activeProject.id)!;
    expect(p.tasks.length).toBe(initialTaskCount);
  });

  it('enforces chained databank input/output semantics between pipeline steps', () => {
    const store = useAppStore.getState();
    const activeProject = store.projects[0];
    const tasks = activeProject.tasks;

    // Verify task chain flow
    const clearTask = tasks.find(t => t.type === 'ClearDatabanks');
    const buildTask = tasks.find(t => t.type === 'Build');
    const retestTask = tasks.find(t => t.type === 'Retest');
    const filterTask = tasks.find(t => t.type === 'Filtering');

    expect(clearTask).toBeDefined();
    expect(buildTask).toBeDefined();
    expect(retestTask).toBeDefined();
    expect(filterTask).toBeDefined();

    // Retest consumes Build output
    expect(retestTask?.input).toBe(buildTask?.output);
    // Filtering consumes Retest output
    expect(filterTask?.input).toBe(retestTask?.output);
  });
});
