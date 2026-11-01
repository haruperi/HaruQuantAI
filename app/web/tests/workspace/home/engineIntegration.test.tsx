import { HostConnectionProvider } from '../../../shell/HostConnection';
import { renderToString } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { ProjectProgress } from '../../../workspaces/home/EnginePanel/engine';
import { executeEngineAction, type EngineRunHandle } from '../../../workspaces/home/EnginePanel/EngineCtrl';
import { OptimizerWorkspace } from '../../../workspaces/optimizer/OptimizerWorkspace';
import { RetesterWorkspace } from '../../../workspaces/retester/RetesterWorkspace';
import type { homeClient } from '../../../workspaces/home/homeClient';

describe('EnginePanel rendering and execution integration', () => {
  it('renders ProjectProgress with real job id and without preview label', () => {
    const mockRun: EngineRunHandle = {
      status: 'running',
      step: 5,
      log: ['Step 5 running'],
      clearOnStart: false,
      setClearOnStart: () => {},
      act: () => {},
      clearLog: () => {},
      jobId: 'job-abc-123',
      canStart: false,
    };

    const html = renderToString(
      <ProjectProgress
        title="Optimizer Task"
        run={mockRun}
        stats={[['Metric', 'Value']]}
        summary={<div>Test summary</div>}
        result={null}
        onOpenResults={() => {}}
        onSettings={() => {}}
      />
    );

    expect(html).toContain('Job job-abc-123');
    expect(html).not.toContain('Local UI preview');
    expect(html).toContain('Optimizer Task');
    expect(html).toContain('Pause');
    expect(html).toContain('Stop');
  });

  it('disables Start button and warns when no project is loaded', () => {
    const mockRun: EngineRunHandle = {
      status: 'idle',
      step: 0,
      log: [],
      clearOnStart: false,
      setClearOnStart: () => {},
      act: () => {},
      clearLog: () => {},
      canStart: false,
      projectId: null,
    };

    const html = renderToString(
      <ProjectProgress
        title="Optimizer Task"
        run={mockRun}
        stats={[['Metric', 'Value']]}
        summary={<div>Test summary</div>}
        result={null}
        onOpenResults={() => {}}
        onSettings={() => {}}
      />
    );

    expect(html).toContain('disabled');
    expect(html).toContain('Engine cannot run without an active project');
  });

  it('rejects engine start action when no project is loaded', async () => {
    const result = await executeEngineAction(undefined, 'start', 'idle');
    expect(result.status).toBe('error');
    expect(result.error).toBe('No active project loaded');
    expect(result.message).toContain('No active project loaded');
  });

  it('dispatches engine actions via homeClient when project is loaded', async () => {
    const mockEngineAction = vi.fn().mockResolvedValue({
      action: 'start',
      status: 'running',
      project_id: 'proj-1',
      task_id: 'task-opt',
      job_id: 'job-999',
    });

    const client = {
      engineAction: mockEngineAction,
    } as unknown as ReturnType<typeof homeClient>;

    const result = await executeEngineAction('proj-1', 'start', 'idle', 'task-opt', client);

    expect(mockEngineAction).toHaveBeenCalledWith('proj-1', 'start', 'task-opt', undefined, undefined);
    expect(result.status).toBe('running');
    expect(result.jobId).toBe('job-999');
    expect(result.error).toBeNull();
  });

  it('handles pause and resume action semantics correctly', async () => {
    const mockEngineAction = vi.fn().mockImplementation((_pid, action) => {
      return Promise.resolve({
        action,
        status: action === 'resume' ? 'running' : 'paused',
        project_id: 'proj-1',
        task_id: 'task-opt',
        job_id: 'job-999',
      });
    });

    const client = {
      engineAction: mockEngineAction,
    } as unknown as ReturnType<typeof homeClient>;

    const pauseRes = await executeEngineAction('proj-1', 'pause', 'running', 'task-opt', client);
    expect(mockEngineAction).toHaveBeenCalledWith('proj-1', 'pause', 'task-opt', undefined, undefined);
    expect(pauseRes.status).toBe('paused');

    const resumeRes = await executeEngineAction('proj-1', 'start', 'paused', 'task-opt', client);
    expect(mockEngineAction).toHaveBeenCalledWith('proj-1', 'resume', 'task-opt', undefined, undefined);
    expect(resumeRes.status).toBe('running');
  });

  it('renders OptimizerWorkspace and RetesterWorkspace wired to engine run', () => {
    const optHtml = renderToString(<HostConnectionProvider><OptimizerWorkspace /></HostConnectionProvider>);
    expect(optHtml).toContain('Optimizer');
    expect(optHtml).not.toContain('Local UI preview');

    const retestHtml = renderToString(<HostConnectionProvider><RetesterWorkspace /></HostConnectionProvider>);
    expect(retestHtml).toContain('Retester');
    expect(retestHtml).not.toContain('Local UI preview');
  });
});
