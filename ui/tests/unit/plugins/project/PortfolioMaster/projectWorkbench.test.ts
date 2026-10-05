import {describe,it,expect} from 'vitest';
import {nextRunStatus} from '../../../../../app/plugins/project/PortfolioMaster/contracts';
describe('FEAT-UI-PROJECT_WORKBENCH preview lifecycle',()=>{
 it('supports pause/resume, cancellation and restart',()=>{
  expect(nextRunStatus('idle','pause')).toBe('idle');
  expect(nextRunStatus('running','pause')).toBe('paused');
  expect(nextRunStatus('paused','start')).toBe('running');
  expect(nextRunStatus('paused','complete')).toBe('paused');
  expect(nextRunStatus('running','complete')).toBe('complete');
  expect(nextRunStatus('running','stop')).toBe('idle');
  expect(nextRunStatus('complete','start')).toBe('running');
 });
});
