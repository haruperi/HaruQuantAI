import {describe,it,expect} from 'vitest';
import {retestRouting,retestDataDefaults} from '../../../../app/workspace/Retester/retesterFixtures';
import {dataTabDefaults} from '../../../../app/plugins/project/ProjectWorkbench/settings/sharedSettingsFixtures';
describe('FEAT-UI-RETESTER_WORKSPACE preview',()=>{
 it('distinguishes copy and overwrite wording without mutating data',()=>{
  expect(retestRouting('Results','Retest')).toBe('copy');
  expect(retestRouting('Results','Results')).toBe('overwrite');
 });
 it('initializes its own empty OOS ranges without changing Builder defaults',()=>{
  expect(retestDataDefaults.oosRanges).toEqual([]);
  expect(retestDataDefaults.oosRanges).not.toBe(dataTabDefaults.oosRanges);
 });
});
