import {describe,it,expect} from 'vitest';
import {retestRouting,retestDataDefaults,dataTabDefaults} from '../../../../app/workspace/Retester/retesterFixtures';
describe('FEAT-UI-RETESTER_WORKSPACE preview',()=>{
 it('distinguishes copy and overwrite wording without mutating data',()=>{
  expect(retestRouting('Results','Retest')).toBe('copy');
  expect(retestRouting('Results','Results')).toBe('overwrite');
 });
 it('initializes its own empty OOS ranges as local preview data',()=>{
  expect(retestDataDefaults.oosRanges).toEqual([]);
  expect(retestDataDefaults.oosRanges).not.toBe(dataTabDefaults.oosRanges);
 });
});
