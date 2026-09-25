import {describe,it,expect} from 'vitest';
import {optimizerDefaults,optimizerDraftError,parameterCombinations} from '../../../../src/workspace/Optimizer/optimizerFixtures';
describe('FEAT-UI-OPTIMIZER_WORKSPACE editing guards',()=>{
 it('counts enabled fixture ranges and rejects empty/invalid selections',()=>{
  const d=structuredClone(optimizerDefaults);
  expect(parameterCombinations(d.parameters)).toBe(25);
  d.parameters.forEach(p=>p.enabled=false);
  expect(optimizerDraftError(d)).toContain('Select at least');
  expect(parameterCombinations(d.parameters)).toBe(0);
  d.parameters[0].enabled=true;d.parameters[0].step=0;
  expect(optimizerDraftError(d)).toContain('positive step');
 });
 it('requires a file when chosen, and validates walk-forward matrix bounds',()=>{
  const d=structuredClone(optimizerDefaults);d.source='file';
  expect(optimizerDraftError(d)).toContain('Choose a strategy file');
  d.fileName='fixture.sqx';expect(optimizerDraftError(d)).toBeUndefined();
  d.mode='Walk - Forward matrix';d.oosStart=80;d.oosStop=20;
  expect(optimizerDraftError(d)).toContain('Matrix ranges');
 });
});
