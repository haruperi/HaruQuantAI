import {describe,it,expect} from 'vitest';
import {masterDefaults,masterError} from '../../../../app/workspace/PortfolioMaster/portfolioMasterModel';
describe('FEAT-UI-PORTFOLIO_MASTER_WORKSPACE editing',()=>{
 it('requires enough selected source strategies and valid size bounds',()=>{const d=structuredClone(masterDefaults);expect(masterError(d,10)).toBeUndefined();expect(masterError(d,1)).toMatch(/enough/);d.max=1;expect(masterError(d,10)).toMatch(/size/);});
 it('validates genetic fields without running search',()=>{const d=structuredClone(masterDefaults);d.search='Genetic search';d.population=0;expect(masterError(d,10)).toMatch(/Genetic/);});
 it('rejects invalid correlation and sample ranges',()=>{const d=structuredClone(masterDefaults);d.correlation.max=2;expect(masterError(d,10)).toMatch(/correlation/);d.correlation.max=0.5;d.inSample=100;expect(masterError(d,10)).toMatch(/Sample/);});
});
