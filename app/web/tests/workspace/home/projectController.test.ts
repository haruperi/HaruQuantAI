import { describe, expect, it, vi } from 'vitest';
import { ProjectController } from '../../../workspaces/home/projectController';
import type { homeClient, ProjectDocumentData } from '../../../workspaces/home/homeClient';

const document = (id = 'saved'): ProjectDocumentData => ({ manifest: { project_id: id, name: id, schema_version: 1 }, revision: 3,
  tasks: { real: { task_id: 'real', task_type: 'build', name: 'Actual task', enabled: true, databank_target: 'bank', dependencies: [], settings: { existing: 'saved' } } }, databanks: {}, metadata: {} });
function setup(saveSettings = vi.fn().mockResolvedValue({ status: 'saved', task_id: 'real', revision: 4 })) {
  const client = { index: vi.fn().mockResolvedValue({ recent_projects: [{ id: 'saved', name: 'Saved', workspace: 'builder', last_activity: '' }] }),
    getProject: vi.fn().mockResolvedValue(document()), saveSettings } as unknown as ReturnType<typeof homeClient>;
  return { controller: new ProjectController('builder', client), client, saveSettings };
}
describe('saved native project controller', () => {
  it('replaces an unrecognized browser identity with an actual server project/task', async () => {
    const { controller } = setup(); await controller.initialize('seeded-browser-project');
    expect(controller.getSnapshot().project?.manifest.project_id).toBe('saved');
    expect(controller.getSnapshot().taskId).toBe('real');
    controller.dispose();
  });
  it('submits the saved revision and preserves drafts after a conflict', async () => {
    const { controller, saveSettings } = setup(vi.fn().mockRejectedValue(new Error('409 conflict')));
    await controller.initialize(); controller.patch({ existing: 'draft' }); await controller.save();
    expect(saveSettings).toHaveBeenCalledWith('saved', 'real', { existing: 'draft' }, 3);
    expect(controller.getSnapshot()).toMatchObject({ dirty: true, draft: { existing: 'draft' }, error: expect.stringContaining('conflict') });
    expect(controller.getSnapshot().project?.revision).toBe(3); controller.dispose();
  });
  it('does not let a stale project reply replace the selected project', async () => {
    const { controller, client } = setup();
    let release!: (value: ProjectDocumentData) => void;
    vi.mocked(client.getProject).mockImplementation(id => id === 'old' ? new Promise(resolve => { release = resolve; }) : Promise.resolve(document(id)));
    const old = controller.selectProject('old'); await controller.selectProject('new');
    release(document('old')); await old;
    expect(controller.getSnapshot().project?.manifest.project_id).toBe('new'); controller.dispose();
  });
  it('preserves edits made while a save is in flight and prevents duplicate saves', async () => {
    let release!: (value: unknown) => void;
    const save = vi.fn().mockImplementation(() => new Promise(resolve => { release = resolve; }));
    const { controller } = setup(save); await controller.initialize(); controller.patch({ existing: 'first' });
    const pending = controller.save(); controller.patch({ existing: 'second' }); await controller.save();
    expect(save).toHaveBeenCalledTimes(1); release({ revision: 4, status: 'saved' }); await pending;
    expect(controller.getSnapshot()).toMatchObject({ dirty: true, draft: { existing: 'second' } });
    expect(controller.getSnapshot().project?.revision).toBe(4); controller.dispose();
  });
});
