import { beforeEach, describe, expect, it, vi } from 'vitest';
import { analyzeQuality, applyReviewMutation, availableReviewTimeframes, createCloneDefinitions, generateReviewRows, reviewKey, selectCloneTargets, selectReviewTarget, validateReviewChange, type CloneSettings, type ToolTarget } from '../../../../../workspaces/data_manager/plugins/Tools/dataTools';

const target: ToolTarget = { id:'d1', symbol:'EURUSD', symbolDefinition:'EURUSD', source:'Dukascopy', timeframe:'M1 → H1', timezone:'UTC', from:'2025-01-01', to:'2025-12-31', bars:5000, category:'Forex' };
const settings: CloneSettings = { postfix:'_{timeframe}_{cloneTime}', timezoneType:'shift', shiftHours:5, timezone:'UTC', removeWeekends:false };

describe('Data Tools contracts', () => {
  it('enforces clone and review selection rules', () => {
    expect(selectCloneTargets([target], ['d1'])).toEqual([target]);
    expect(() => selectCloneTargets([target], [])).toThrow('select some symbol');
    expect(() => selectCloneTargets([{ ...target, sourceDataId:'d0' }], ['d1'])).toThrow('cannot clone it again');
    expect(selectReviewTarget([target], ['d1'])).toEqual(target);
    expect(() => selectReviewTarget([{ ...target, bars:0 }], ['d1'])).toThrow("doesn't contain any data");
  });

  it('creates unique derived definitions with lineage and persisted settings', () => {
    const clones = createCloneDefinitions([target, { ...target, id:'d2' }], settings, ['EURUSD_M1_+5']);
    expect(clones.map(item => item.symbol)).toEqual(['EURUSD_M1_+5_2', 'EURUSD_M1_+5_3']);
    expect(clones[0]).toMatchObject({ source:'Cloned data', sourceDataId:'d1', timezone:'UTC +5h' });
    expect(() => createCloneDefinitions([target], { ...settings, shiftHours:24 }, [])).toThrow('-23 to 23');
  });

  it('derives compatible timeframes and stable review rows', () => {
    expect(availableReviewTimeframes('M15 → D1')).toEqual(['M15','M30','H1','H4','D1','W1','MN1']);
    expect(availableReviewTimeframes('TICK → D1')[0]).toBe('TICK');
    const first = generateReviewRows(target, 'M1', 'No Session', 400); const second = generateReviewRows(target, 'M1', 'No Session', 400);
    expect(first).toEqual(second); expect(first).toHaveLength(400); expect(first[138].date > first[137].date).toBe(true);
  });

  it('applies edits/deletions and detects quality issues', () => {
    const rows = generateReviewRows(target, 'M1', 'No Session', 400); const changed = { [rows[0].id]: { close:rows[0].close + 1 } };
    const visible = applyReviewMutation(rows, { changed, deleted:[rows[1].id] });
    expect(visible).toHaveLength(399); expect(visible[0].close).toBe(rows[0].close + 1);
    const quality = analyzeQuality(visible, 'M1'); expect(quality.counts.gap).toBeGreaterThan(0); expect(quality.counts.spike).toBeGreaterThan(0); expect(quality.counts.ohlc).toBeGreaterThan(0);
    expect(() => validateReviewChange({ ...rows[0], high:Number.NaN }, false)).toThrow('valid numbers');
    expect(reviewKey('d1','M1','No Session')).toBe('d1|M1|No Session');
  });
});

async function isolated() {
  vi.resetModules(); const memory = new Map<string,string>();
  vi.stubGlobal('localStorage', { getItem:(key:string) => memory.get(key) ?? null, setItem:(key:string,value:string) => { memory.set(key,value); } });
  return { store:(await import('../../../../../workspaces/data_manager/plugins/Tools/dataToolsStore')).useDataTools, memory };
}
beforeEach(() => vi.unstubAllGlobals());

it('submits a real clone job without inventing browser definitions',async()=>{
  const {store}=await isolated();
  const module=await import('../../../../../workspaces/data_manager/plugins/Tools/dataToolsStore');
  const post=vi.fn().mockResolvedValue({job_id:'clone-real',status:'QUEUED',progress:0,message:'Queued'});
  module.setDataClient({post,get:vi.fn(),put:vi.fn(),delete:vi.fn()});
  await store.getState().startClone([target],settings,[],false);
  expect(post).toHaveBeenCalledWith('/datasets/clone-timezone',expect.objectContaining({dataset_id:'d1',shift_hours:5}));
  expect(store.getState().definitions).toEqual([]);expect(store.getState().job).toBeNull();
});

it('propagates rejected jobs and refuses conflicting submissions',async()=>{
  const {store,memory}=await isolated();
  const module=await import('../../../../../workspaces/data_manager/plugins/Tools/dataToolsStore');
  module.setDataClient({post:vi.fn().mockRejectedValue(new Error('Clone rejected')),get:vi.fn(),put:vi.fn(),delete:vi.fn()});
  await expect(store.getState().startClone([target],settings,[],false)).rejects.toThrow('Clone rejected');
  await expect(store.getState().startClone([target],settings,[],true)).rejects.toThrow('active');
  memory.set('haru-data-tools-v1','bad');vi.resetModules();
  const corrupt=(await import('../../../../../workspaces/data_manager/plugins/Tools/dataToolsStore')).useDataTools;
  expect(corrupt.getState().storageError).toContain('preserved');expect(memory.get('haru-data-tools-v1')).toBe('bad');
});
