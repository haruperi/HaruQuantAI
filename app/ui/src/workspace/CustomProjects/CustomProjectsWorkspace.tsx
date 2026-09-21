import React, { useEffect, useRef, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  CheckCircle2,
  CirclePlus,
  Clock,
  CopyPlus,
  FileCode,
  Layers,
  Play,
  RefreshCw,
  Save,
  Settings2,
  Sliders,
  Square,
  Terminal,
  Trash2,
  Workflow,
} from 'lucide-react';
import { useAppStore } from '../../app/store';
import type { CustomProject, WorkflowTask } from '../../app/types';
import { Button, Checkbox, Field, Modal, Select, TextInput } from '../../components/ui';
import { NewTaskModal, SQX_TASK_TYPES } from './NewTaskModal';

export function CustomProjectsWorkspace() {
  const store = useAppStore();
  const [selectedTaskId, setSelectedTaskId] = useState<string>('');
  const [showNewTaskModal, setShowNewTaskModal] = useState<boolean>(false);
  const [showNewProjectModal, setShowNewProjectModal] = useState<boolean>(false);
  const [newProjectName, setNewProjectName] = useState<string>('');
  const [newProjectDesc, setNewProjectDesc] = useState<string>('');
  const [running, setRunning] = useState<boolean>(false);
  const [executionLogs, setExecutionLogs] = useState<string[]>([
    'Pipeline orchestrator initialized. Ready to execute scheduled tasks.',
  ]);

  const runTimerRef = useRef<number | null>(null);

  // Active project fallback
  const activeProject = store.projects.find(p => p.id === store.activeProjectId) || store.projects[0];
  const tasks = activeProject ? activeProject.tasks : [];
  const selectedTask = tasks.find(t => t.id === selectedTaskId) || tasks[0];

  useEffect(() => {
    if (tasks.length > 0 && (!selectedTaskId || !tasks.some(t => t.id === selectedTaskId))) {
      setSelectedTaskId(tasks[0].id);
    }
  }, [tasks, selectedTaskId]);

  useEffect(() => {
    return () => {
      if (runTimerRef.current) {
        window.clearTimeout(runTimerRef.current);
      }
    };
  }, []);

  const addLog = (msg: string) => {
    const time = new Date().toLocaleTimeString();
    setExecutionLogs(prev => [`[${time}] ${msg}`, ...prev].slice(0, 100));
  };

  // Pipeline Execution Engine
  const runPipeline = () => {
    if (!activeProject || tasks.length === 0) return;
    setRunning(true);
    addLog(`Starting execution for project "${activeProject.name}" (${tasks.length} tasks configured)`);

    // Reset status of all tasks
    const initialTasks = tasks.map(t => ({
      ...t,
      status: 'idle' as const,
      progress: 0,
      durationSeconds: 0,
    }));
    store.setProjectTasks(activeProject.id, initialTasks);

    let currentIndex = 0;

    const executeStep = () => {
      const currentTasks = useAppStore.getState().projects.find(p => p.id === activeProject.id)?.tasks || [];
      if (currentIndex >= currentTasks.length) {
        setRunning(false);
        addLog(`Pipeline execution finished successfully for "${activeProject.name}".`);
        store.notify(`Workflow "${activeProject.name}" finished all tasks successfully.`);
        return;
      }

      const currentTask = currentTasks[currentIndex];
      if (!currentTask.enabled) {
        addLog(`Task #${currentIndex + 1} "${currentTask.name}" is disabled. Skipping to next.`);
        currentIndex++;
        runTimerRef.current = window.setTimeout(executeStep, 200);
        return;
      }

      addLog(`Task #${currentIndex + 1} [${currentTask.type}] "${currentTask.name}" executing (input: ${currentTask.input} -> output: ${currentTask.output})...`);

      // Set running
      store.updateTaskInProject(activeProject.id, currentTask.id, {
        status: 'running',
        progress: 15,
      });

      // Progress animation simulation
      runTimerRef.current = window.setTimeout(() => {
        store.updateTaskInProject(activeProject.id, currentTask.id, {
          progress: 65,
        });

        runTimerRef.current = window.setTimeout(() => {
          // Task completion logic
          store.updateTaskInProject(activeProject.id, currentTask.id, {
            status: 'completed',
            progress: 100,
            durationSeconds: Math.floor(Math.random() * 8) + 3,
          });

          addLog(`Task #${currentIndex + 1} [${currentTask.type}] completed. Routed output data to [${currentTask.output}].`);

          // If it was a build task, ensure output databank has strategies or notify
          if (currentTask.type === 'Build') {
            addLog(`Generated candidate strategies deposited into databank "${currentTask.output}".`);
          }

          currentIndex++;
          executeStep();
        }, 500);
      }, 400);
    };

    executeStep();
  };

  const stopPipeline = () => {
    if (runTimerRef.current) {
      window.clearTimeout(runTimerRef.current);
    }
    setRunning(false);
    addLog('Pipeline execution aborted by user.');
    store.notify('Pipeline execution stopped.');
  };

  const handleCreateProject = () => {
    if (!newProjectName.trim()) return;
    const newProj: CustomProject = {
      id: `proj-${Date.now()}`,
      name: newProjectName.trim(),
      description: newProjectDesc.trim() || 'Custom strategy automation workflow.',
      status: 'idle',
      tasks: [
        {
          id: `task-${Date.now()}-1`,
          type: 'Build',
          name: 'Generate Initial Pool',
          enabled: true,
          status: 'idle',
          input: 'EURUSD H1',
          output: 'Generated',
          config: { symbol: 'EURUSD', timeframe: 'H1', targetCount: 20 },
        },
        {
          id: `task-${Date.now()}-2`,
          type: 'Filtering',
          name: 'Filter Robust Candidates',
          enabled: true,
          status: 'idle',
          input: 'Generated',
          output: 'Accepted',
          config: { minSharpe: 1.2, maxDrawdownPct: 20 },
        },
      ],
    };
    store.addProject(newProj);
    setShowNewProjectModal(false);
    setNewProjectName('');
    setNewProjectDesc('');
    store.notify(`Created project "${newProj.name}"`);
  };

  const handleCloneProject = () => {
    if (!activeProject) return;
    const cloned: CustomProject = {
      id: `proj-${Date.now()}`,
      name: `${activeProject.name} (Copy)`,
      description: activeProject.description,
      status: 'idle',
      tasks: activeProject.tasks.map(t => ({
        ...t,
        id: `task-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
        status: 'idle',
        progress: 0,
      })),
    };
    store.addProject(cloned);
    store.notify(`Cloned project to "${cloned.name}"`);
  };

  const handleDeleteProject = () => {
    if (!activeProject) return;
    if (store.projects.length <= 1) {
      store.notify('Cannot delete the last remaining project.');
      return;
    }
    const name = activeProject.name;
    store.deleteProject(activeProject.id);
    store.notify(`Deleted project "${name}"`);
  };

  const handleAddTask = (newTask: WorkflowTask) => {
    if (!activeProject) return;
    store.addTaskToProject(activeProject.id, newTask);
    setSelectedTaskId(newTask.id);
    addLog(`Added task [${newTask.type}] "${newTask.name}" to project.`);
  };

  const handleCloneTask = () => {
    if (!activeProject || !selectedTask) return;
    const cloned: WorkflowTask = {
      ...selectedTask,
      id: `task-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      name: `${selectedTask.name} (Copy)`,
      status: 'idle',
      progress: 0,
    };
    store.addTaskToProject(activeProject.id, cloned);
    setSelectedTaskId(cloned.id);
    addLog(`Cloned task "${selectedTask.name}".`);
  };

  const handleRemoveTask = () => {
    if (!activeProject || !selectedTask) return;
    store.removeTaskFromProject(activeProject.id, selectedTask.id);
    addLog(`Removed task "${selectedTask.name}".`);
  };

  const handleMoveTask = (offset: number) => {
    if (!activeProject || !selectedTask) return;
    store.reorderTaskInProject(activeProject.id, selectedTask.id, offset);
  };

  // Helper for task config updating
  const updateSelectedTaskConfig = (key: string, value: any) => {
    if (!activeProject || !selectedTask) return;
    const currentConfig = selectedTask.config || {};
    store.updateTaskInProject(activeProject.id, selectedTask.id, {
      config: { ...currentConfig, [key]: value },
    });
  };

  const getTaskIcon = (type: string) => {
    const def = SQX_TASK_TYPES.find(t => t.type === type);
    return def ? def.icon : <Settings2 size={16} />;
  };

  return (
    <div className="workflow h-full flex flex-col bg-[var(--bg)]">
      {/* Workflow Header */}
      <div className="wf-header h-12 flex items-center justify-between px-4 bg-[var(--panel)] border-b border-[var(--line)]">
        <div className="flex items-center gap-3">
          <Workflow size={20} className="text-cyan-400" />
          <div>
            <h1 className="text-sm font-bold text-gray-100 flex items-center gap-2">
              Custom Projects
              <span className="text-xs font-normal text-gray-400">
                · {activeProject?.name || 'Project'} ({tasks.length} tasks)
              </span>
            </h1>
            <span className="text-[10px] text-gray-400">
              StrategyQuant X multi-stage autonomous pipeline runner and databank routing orchestrator
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={() => store.notify('Project configuration saved.')}>
            <Save size={14} />
            Save project
          </Button>
          <Button onClick={handleCloneProject}>
            <CopyPlus size={14} />
            Clone project
          </Button>
          <Button
            className="primary"
            disabled={running || tasks.length === 0}
            onClick={runPipeline}
          >
            <Play size={14} />
            Run project
          </Button>
          <Button disabled={!running} onClick={stopPipeline}>
            <Square size={14} />
            Stop
          </Button>
        </div>
      </div>

      {/* Main Body */}
      <div className="wf-body flex-1 grid grid-cols-[220px_1fr_300px] min-h-0">
        {/* Projects Sidebar */}
        <aside className="project-list bg-[#1a1f26] border-r border-[var(--line)] flex flex-col p-2 min-h-0">
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[var(--line)]">
            <strong className="text-xs text-gray-300">Projects</strong>
            <Button className="text-xs px-2 py-1" onClick={() => setShowNewProjectModal(true)}>
              <CirclePlus size={13} />
              New
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto flex flex-col gap-1 pr-1">
            {store.projects.map(p => {
              const isActive = p.id === activeProject?.id;
              return (
                <button
                  key={p.id}
                  className={`w-full text-left p-2.5 rounded border transition-colors flex flex-col gap-1 ${
                    isActive
                      ? 'bg-[#17455a] border-cyan-500 text-white'
                      : 'bg-[var(--panel2)] border-transparent text-gray-300 hover:bg-[#202732]'
                  }`}
                  onClick={() => store.setActiveProject(p.id)}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold truncate">{p.name}</span>
                    <span className="text-[10px] text-gray-400">{p.tasks.length} tasks</span>
                  </div>
                  <small className="text-[10px] text-gray-400 line-clamp-1">
                    {p.description}
                  </small>
                </button>
              );
            })}
          </div>

          <div className="pt-2 mt-2 border-t border-[var(--line)] flex gap-2">
            <Button
              className="flex-1 text-xs"
              onClick={handleDeleteProject}
              disabled={store.projects.length <= 1}
            >
              <Trash2 size={13} />
              Delete project
            </Button>
          </div>
        </aside>

        {/* Task List & Pipeline Canvas */}
        <main className="task-list flex flex-col p-3 min-h-0 overflow-y-auto bg-[var(--bg)]">
          <div className="subtoolbar flex items-center gap-2 mb-3 pb-2 border-b border-[var(--line)]">
            <Button onClick={() => setShowNewTaskModal(true)}>
              <CirclePlus size={14} className="text-cyan-400" />
              Add task
            </Button>
            <Button disabled={!selectedTask} onClick={handleCloneTask}>
              <CopyPlus size={14} />
              Clone
            </Button>
            <Button disabled={!selectedTask} onClick={handleRemoveTask}>
              <Trash2 size={14} />
              Remove
            </Button>
            <div className="h-4 w-px bg-gray-700 mx-1" />
            <Button disabled={!selectedTask} onClick={() => handleMoveTask(-1)}>
              <ArrowUp size={14} />
            </Button>
            <Button disabled={!selectedTask} onClick={() => handleMoveTask(1)}>
              <ArrowDown size={14} />
            </Button>
            <span className="text-xs text-gray-400 ml-auto">
              Chained databank flow: output of step N feeds input of step N+1
            </span>
          </div>

          {/* Task cards list */}
          <div className="flex-1 overflow-y-auto flex flex-col gap-2">
            {tasks.length === 0 ? (
              <div className="p-8 text-center text-gray-400 border border-dashed border-gray-700 rounded my-auto">
                <Workflow size={32} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm font-semibold">No tasks in this project</p>
                <p className="text-xs text-gray-500 mt-1">
                  Click "Add task" to build an automated multi-stage research pipeline.
                </p>
              </div>
            ) : (
              tasks.map((t, idx) => {
                const isSelected = selectedTaskId === t.id;
                return (
                  <div
                    key={t.id}
                    onClick={() => setSelectedTaskId(t.id)}
                    className={`task-card flex items-center gap-3 p-3 rounded border transition-all cursor-pointer ${
                      isSelected
                        ? 'border-cyan-500 bg-[#1b3642]'
                        : 'border-[var(--line)] bg-[var(--panel)] hover:bg-[var(--panel2)]'
                    } ${t.status === 'completed' ? 'border-l-4 border-l-emerald-500' : ''} ${
                      t.status === 'running' ? 'border-l-4 border-l-cyan-400 animate-pulse' : ''
                    }`}
                  >
                    <div className="w-6 text-center font-mono text-xs text-gray-400">
                      {idx + 1}
                    </div>

                    <div className="p-2 bg-gray-900 rounded border border-gray-700 shrink-0">
                      {getTaskIcon(t.type)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <strong className="text-xs text-gray-200 truncate">{t.name}</strong>
                        <span className="text-[10px] text-gray-400 bg-gray-900 px-1.5 py-0.5 rounded border border-gray-700">
                          {t.type}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-[11px] text-gray-400">
                        <span className="font-mono bg-gray-950 px-1 rounded text-cyan-400">
                          {t.input}
                        </span>
                        <span>→</span>
                        <span className="font-mono bg-gray-950 px-1 rounded text-emerald-400">
                          {t.output}
                        </span>
                        {t.durationSeconds ? (
                          <span className="flex items-center gap-1 text-[10px] text-gray-400 ml-auto">
                            <Clock size={11} />
                            {t.durationSeconds}s
                          </span>
                        ) : null}
                      </div>

                      {t.status === 'running' && (
                        <div className="w-full bg-gray-800 rounded-full h-1.5 mt-2 overflow-hidden">
                          <div
                            className="bg-cyan-500 h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${t.progress || 10}%` }}
                          />
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span
                        className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded border ${
                          t.status === 'completed'
                            ? 'bg-emerald-950/60 border-emerald-500/50 text-emerald-400'
                            : t.status === 'running'
                            ? 'bg-cyan-950/60 border-cyan-500/50 text-cyan-300'
                            : 'bg-gray-800 border-gray-700 text-gray-400'
                        }`}
                      >
                        {t.status}
                      </span>

                      <div onClick={e => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          className="accent-cyan-500 cursor-pointer"
                          checked={t.enabled}
                          onChange={e => {
                            if (activeProject) {
                              store.updateTaskInProject(activeProject.id, t.id, { enabled: e.target.checked });
                            }
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Execution Log Console */}
          <div className="mt-3 pt-2 border-t border-[var(--line)]">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-semibold text-gray-300 flex items-center gap-2">
                <Terminal size={13} className="text-cyan-400" />
                Pipeline Execution Logs
              </span>
              <button
                className="text-[10px] text-gray-400 hover:text-gray-200"
                onClick={() => setExecutionLogs(['Log cleared. Ready.'])}
              >
                Clear log
              </button>
            </div>
            <div className="h-28 bg-[#101419] p-2 rounded border border-[var(--line)] font-mono text-[11px] overflow-y-auto flex flex-col gap-1 text-gray-300">
              {executionLogs.map((log, i) => (
                <div key={i} className="leading-tight">
                  {log}
                </div>
              ))}
            </div>
          </div>
        </main>

        {/* Task Settings Drawer */}
        <aside className="task-props bg-[#1a1f26] border-l border-[var(--line)] p-3 overflow-y-auto flex flex-col gap-3">
          <h3 className="text-xs font-bold text-gray-200 pb-2 border-b border-[var(--line)] flex items-center justify-between">
            <span>Task Configuration</span>
            {selectedTask && (
              <span className="text-[10px] text-cyan-400 font-mono">
                {selectedTask.type}
              </span>
            )}
          </h3>

          {selectedTask ? (
            <div className="flex flex-col gap-3">
              <Checkbox
                label="Task Enabled in Pipeline"
                checked={selectedTask.enabled}
                onChange={enabled => {
                  if (activeProject) {
                    store.updateTaskInProject(activeProject.id, selectedTask.id, { enabled });
                  }
                }}
              />

              <Field label="Task Name">
                <TextInput
                  value={selectedTask.name}
                  onChange={e => {
                    if (activeProject) {
                      store.updateTaskInProject(activeProject.id, selectedTask.id, { name: e.target.value });
                    }
                  }}
                />
              </Field>

              <Field label="Input Databank / Source">
                <TextInput
                  value={selectedTask.input}
                  onChange={e => {
                    if (activeProject) {
                      store.updateTaskInProject(activeProject.id, selectedTask.id, { input: e.target.value });
                    }
                  }}
                />
              </Field>

              <Field label="Output Databank / Destination">
                <TextInput
                  value={selectedTask.output}
                  onChange={e => {
                    if (activeProject) {
                      store.updateTaskInProject(activeProject.id, selectedTask.id, { output: e.target.value });
                    }
                  }}
                />
              </Field>

              {/* Task-specific configurations based on SQX task types */}
              <div className="pt-2 border-t border-[var(--line)] flex flex-col gap-2">
                <span className="text-xs font-semibold text-gray-300">
                  {selectedTask.type} Parameters
                </span>

                {selectedTask.type === 'Build' && (
                  <>
                    <Field label="Symbol">
                      <TextInput
                        value={selectedTask.config?.symbol || 'EURUSD'}
                        onChange={e => updateSelectedTaskConfig('symbol', e.target.value)}
                      />
                    </Field>
                    <Field label="Timeframe">
                      <Select
                        value={selectedTask.config?.timeframe || 'H1'}
                        onChange={val => updateSelectedTaskConfig('timeframe', val)}
                      >
                        <option>M15</option>
                        <option>M30</option>
                        <option>H1</option>
                        <option>H4</option>
                        <option>D1</option>
                      </Select>
                    </Field>
                    <Field label="Target Strategy Count">
                      <TextInput
                        type="number"
                        value={selectedTask.config?.targetCount || 30}
                        onChange={e => updateSelectedTaskConfig('targetCount', Number(e.target.value))}
                      />
                    </Field>
                  </>
                )}

                {selectedTask.type === 'Retest' && (
                  <>
                    <Field label="Testing Precision">
                      <Select
                        value={selectedTask.config?.precision || 'Selected timeframe only'}
                        onChange={val => updateSelectedTaskConfig('precision', val)}
                      >
                        <option>Selected timeframe only</option>
                        <option>1 Minute data</option>
                        <option>M1 real tick data</option>
                      </Select>
                    </Field>
                    <Field label="Spread Multiplier">
                      <TextInput
                        type="number"
                        step="0.1"
                        value={selectedTask.config?.spreadMultiplier || 1.2}
                        onChange={e => updateSelectedTaskConfig('spreadMultiplier', Number(e.target.value))}
                      />
                    </Field>
                    <Field label="Slippage (Pips)">
                      <TextInput
                        type="number"
                        value={selectedTask.config?.slippagePips || 1.0}
                        onChange={e => updateSelectedTaskConfig('slippagePips', Number(e.target.value))}
                      />
                    </Field>
                  </>
                )}

                {selectedTask.type === 'Filtering' && (
                  <>
                    <Field label="Minimum Sharpe Ratio">
                      <TextInput
                        type="number"
                        step="0.05"
                        value={selectedTask.config?.minSharpe || 1.2}
                        onChange={e => updateSelectedTaskConfig('minSharpe', Number(e.target.value))}
                      />
                    </Field>
                    <Field label="Max Drawdown %">
                      <TextInput
                        type="number"
                        value={selectedTask.config?.maxDrawdownPct || 20}
                        onChange={e => updateSelectedTaskConfig('maxDrawdownPct', Number(e.target.value))}
                      />
                    </Field>
                    <Field label="Minimum Trades">
                      <TextInput
                        type="number"
                        value={selectedTask.config?.minTrades || 80}
                        onChange={e => updateSelectedTaskConfig('minTrades', Number(e.target.value))}
                      />
                    </Field>
                  </>
                )}

                {selectedTask.type === 'AutomaticPortfolioBuilder' && (
                  <>
                    <Field label="Max Strategies in Portfolio">
                      <TextInput
                        type="number"
                        value={selectedTask.config?.maxStrategies || 5}
                        onChange={e => updateSelectedTaskConfig('maxStrategies', Number(e.target.value))}
                      />
                    </Field>
                    <Field label="Max Correlation">
                      <TextInput
                        type="number"
                        step="0.05"
                        value={selectedTask.config?.maxCorrelation || 0.45}
                        onChange={e => updateSelectedTaskConfig('maxCorrelation', Number(e.target.value))}
                      />
                    </Field>
                    <Field label="Weighting Model">
                      <Select
                        value={selectedTask.config?.weightingModel || 'Risk Parity'}
                        onChange={val => updateSelectedTaskConfig('weightingModel', val)}
                      >
                        <option>Equal weight</option>
                        <option>Risk Parity</option>
                        <option>Minimum Variance</option>
                        <option>Manual weights</option>
                      </Select>
                    </Field>
                  </>
                )}

                {selectedTask.type === 'CustomAnalysis' && (
                  <>
                    <Field label="Simulations Count">
                      <TextInput
                        type="number"
                        value={selectedTask.config?.simulations || 500}
                        onChange={e => updateSelectedTaskConfig('simulations', Number(e.target.value))}
                      />
                    </Field>
                    <Field label="Confidence Level (%)">
                      <TextInput
                        type="number"
                        value={selectedTask.config?.confidenceLevel || 95}
                        onChange={e => updateSelectedTaskConfig('confidenceLevel', Number(e.target.value))}
                      />
                    </Field>
                  </>
                )}

                {selectedTask.type === 'Notification' && (
                  <>
                    <Field label="Notification Channel">
                      <Select
                        value={selectedTask.config?.channel || 'Webhook'}
                        onChange={val => updateSelectedTaskConfig('channel', val)}
                      >
                        <option>Webhook</option>
                        <option>Telegram</option>
                        <option>Slack</option>
                        <option>Email</option>
                      </Select>
                    </Field>
                    <Field label="Target Webhook URL / Recipient">
                      <TextInput
                        value={selectedTask.config?.targetUrl || 'https://webhook.site/alerts'}
                        onChange={e => updateSelectedTaskConfig('targetUrl', e.target.value)}
                      />
                    </Field>
                  </>
                )}

                {selectedTask.type === 'WaitFor' && (
                  <Field label="Wait Duration (Minutes)">
                    <TextInput
                      type="number"
                      value={selectedTask.config?.waitDurationMinutes || 15}
                      onChange={e => updateSelectedTaskConfig('waitDurationMinutes', Number(e.target.value))}
                    />
                  </Field>
                )}

                {selectedTask.type === 'SaveToFiles' && (
                  <>
                    <Field label="Destination Path">
                      <TextInput
                        value={selectedTask.config?.destinationPath || './exports/live/'}
                        onChange={e => updateSelectedTaskConfig('destinationPath', e.target.value)}
                      />
                    </Field>
                    <Field label="Export Format">
                      <Select
                        value={selectedTask.config?.format || 'MQL5'}
                        onChange={val => updateSelectedTaskConfig('format', val)}
                      >
                        <option>MQL5</option>
                        <option>MQL4</option>
                        <option>EasyLanguage</option>
                        <option>Python</option>
                      </Select>
                    </Field>
                  </>
                )}
              </div>

              <div className="pt-2 border-t border-[var(--line)] flex flex-col gap-2">
                <span className="text-xs font-semibold text-gray-300">Failure Policy</span>
                <Field label="On Task Failure">
                  <Select
                    value={selectedTask.errorPolicy || 'Stop project'}
                    onChange={val => {
                      if (activeProject) {
                        store.updateTaskInProject(activeProject.id, selectedTask.id, {
                          errorPolicy: val as any,
                        });
                      }
                    }}
                  >
                    <option>Stop project</option>
                    <option>Continue to next</option>
                    <option>Go to task</option>
                  </Select>
                </Field>
              </div>
            </div>
          ) : (
            <div className="p-4 text-center text-gray-500 text-xs">
              Select a task to edit its settings.
            </div>
          )}
        </aside>
      </div>

      {/* New Task Modal */}
      {showNewTaskModal && (
        <NewTaskModal
          onClose={() => setShowNewTaskModal(false)}
          onAddTask={handleAddTask}
          existingTasksCount={tasks.length}
        />
      )}

      {/* New Project Modal */}
      {showNewProjectModal && (
        <Modal title="Create New Custom Project" onClose={() => setShowNewProjectModal(false)} width={460}>
          <div className="flex flex-col gap-3">
            <Field label="Project Name">
              <TextInput
                value={newProjectName}
                placeholder="e.g. Intraday Breakout Pipeline"
                onChange={e => setNewProjectName(e.target.value)}
              />
            </Field>

            <Field label="Description">
              <TextInput
                value={newProjectDesc}
                placeholder="e.g. Autonomous generation & Monte Carlo robustness pipeline"
                onChange={e => setNewProjectDesc(e.target.value)}
              />
            </Field>

            <div className="flex justify-end gap-2 pt-2 border-t border-gray-700">
              <Button onClick={() => setShowNewProjectModal(false)}>Cancel</Button>
              <Button className="primary" onClick={handleCreateProject}>
                Create Project
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export { CustomProjectsWorkspace as WorkflowManager };
