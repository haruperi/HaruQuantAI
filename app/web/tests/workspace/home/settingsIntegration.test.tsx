import { renderToString } from 'react-dom/server';
import { describe, expect, it, vi } from 'vitest';
import { DataTab } from '../../../workspaces/home/SettingsData/module';
import { MoneyManagementTab } from '../../../workspaces/home/SettingsMoneyManagement/module';
import { TradingOptionsTab } from '../../../workspaces/home/SettingsOptions/module';
import { NotesTab } from '../../../workspaces/home/SettingsNotes/module';
import { ProjectController, SavedProjectProvider } from '../../../workspaces/home/projectController';
import type { homeClient } from '../../../workspaces/home/homeClient';

async function savedProject() {
  const settings = { execution: { mode: 'RETEST', seed: 42,
    dataset: { symbol: 'ACTUAL', source: 'catalog-source', timeframe: 'M1' },
    model: { initial_capital: 275, commission_per_order: 2.5 },
    money_management: { method: 'FixedSize', size: 0.5, decimals: 8 }, strategy_result_ids: ['stored'] } };
  const client = {
    getProject: vi.fn().mockResolvedValue({ manifest: { project_id: 'saved', name: 'Saved', schema_version: 1 }, revision: 7,
      databanks: {}, metadata: { notes: '<script>plain 日本語</script>' },
      tasks: { real: { task_id: 'real', task_type: 'retest', enabled: true, settings, databank_target: 'bank', dependencies: [], name: 'Saved task' } } }),
    saveSettings: vi.fn().mockResolvedValue({ status: 'saved', task_id: 'real', revision: 8 }),
  } as unknown as ReturnType<typeof homeClient>;
  const controller = new ProjectController('retester', client);
  await controller.selectProject('saved');
  return { controller, client, binding: { controller, state: controller.getSnapshot() } };
}

describe('native shared settings forms', () => {
  it('renders saved market, capital, sizing and costs rather than fixture values', async () => {
    const { controller, binding } = await savedProject();
    const html = renderToString(<SavedProjectProvider binding={binding}><DataTab /><MoneyManagementTab /><TradingOptionsTab /><NotesTab /></SavedProjectProvider>);
    expect(html).toContain('value="ACTUAL"');
    expect(html).toContain('value="catalog-source"');
    expect(html).toContain('value="275"');
    expect(html).toContain('value="0.5"');
    expect(html).toContain('value="2.5"');
    expect(html).toContain('&lt;script&gt;plain 日本語&lt;/script&gt;');
    expect(html).not.toContain('AUDUSD_dukascopy');
    expect(html).not.toContain('Real ticks');
    controller.dispose();
  });
  it('blocks invalid edits and saves corrected native configuration with its revision', async () => {
    const { controller, client } = await savedProject();
    controller.patchExecution({ model: { initial_capital: -1 } });
    controller.validate('money', 'Initial capital must be positive.');
    await controller.save();
    expect(client.saveSettings).not.toHaveBeenCalled();
    controller.patchExecution({ model: { initial_capital: 300 } });
    controller.validate('money', '');
    await controller.save();
    expect(client.saveSettings).toHaveBeenCalledWith('saved', 'real', expect.objectContaining({ execution: expect.objectContaining({ model: { initial_capital: 300 } }) }), 7);
    expect(controller.getSnapshot().project?.revision).toBe(8);
    controller.dispose();
  });
});
