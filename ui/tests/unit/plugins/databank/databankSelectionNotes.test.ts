import { describe, expect, it, vi } from 'vitest';
import { handleSelectItem, requestSetNote, applySetNote } from '../../../../app/plugins/databank/ResultsDatabankActions/tools/module';
import { strategies } from '../../../../app/plugins/databank/fixtures';

describe('preserved selection and latent note adapters', () => {
  it('partitions only supplied bank strategies using existing thresholds', () => {
    const selected = strategies.slice(0, 40);
    const setRows = vi.fn(); const notify = vi.fn();
    expect(handleSelectItem('Select:Passed', selected, setRows, notify)).toBe(true);
    const passed = setRows.mock.calls[0][0] as string[];
    expect(handleSelectItem('Select:Failed', selected, setRows, notify)).toBe(true);
    const failed = setRows.mock.calls[1][0] as string[];
    expect([...passed, ...failed].sort()).toEqual(selected.map(strategy => strategy.id).sort());
    expect(passed.filter(id => failed.includes(id))).toEqual([]);
    expect(handleSelectItem('Edit:Strategy', selected, setRows, notify)).toBe(false);
    expect(setRows).toHaveBeenCalledTimes(2);
  });
  it('preserves empty selection guard and exact note callbacks', () => {
    const open = vi.fn(); const notify = vi.fn(); const rename = vi.fn();
    requestSetNote(0, notify, open);
    expect(open).not.toHaveBeenCalled();
    expect(notify).toHaveBeenCalledWith('You have to select at least one strategy');
    requestSetNote(1, notify, open);
    expect(open).toHaveBeenCalledOnce();
    applySetNote(strategies.slice(0, 2), ' untrimmed note ', rename, notify);
    expect(rename.mock.calls).toEqual(strategies.slice(0, 2).map(strategy => [strategy.id, strategy.name, ' untrimmed note ']));
    expect(notify).toHaveBeenLastCalledWith('Note set on 2 strategies');
  });
});
