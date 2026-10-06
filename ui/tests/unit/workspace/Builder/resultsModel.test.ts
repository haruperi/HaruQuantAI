import { describe, expect, it } from 'vitest';
import { csvTrades, demoResult, resultSnapshot, visibleTrades } from '../../../../src/workspace/Builder/results/resultsModel';
describe('Results presentation documents',()=>{
 const result=demoResult('str-1','First result');
 it('intersects market, direction and sample without mutating the source',()=>{
  const before=JSON.stringify(result);
  expect(visibleTrades(result,'long','out','EURUSD / H1').map(t=>t.id)).toEqual([17,19,21,23]);
  expect(visibleTrades(result,'long','out','GBPUSD / H1')).toEqual([]);
  expect(JSON.stringify(result)).toBe(before);
 });
 it('includes expired rows only when requested',()=>{
  expect(visibleTrades(result,'both','full','Main backtest')).toHaveLength(23);
  expect(visibleTrades(result,'both','full','Main backtest',true)).toHaveLength(24);
 });
 it('keeps precomputed summary and equity consistent with each filtered fixture',()=>{
  for(const direction of ['both','long','short'])for(const sample of ['full','in','out'])for(const market of result.markets){
   const rows=visibleTrades(result,direction,sample,market);
   const snapshot=resultSnapshot(direction,sample,market);
   expect(snapshot.equity.at(-1)).toBe(10000+rows.reduce((sum,t)=>sum+t.profit,0));
   expect(snapshot.metrics.find(([key])=>key==='# of trades')?.[1]).toBe(String(rows.length));
  }
 });
 it('quotes CSV delimiters, quotes and decimal-comma output',()=>{
  const row={...result.trades[0],market:'Demo, "Market"'};
  expect(csvTrades([row])).toContain('"Demo, ""Market"""');
  expect(csvTrades([row],true)).toContain(';"120,00"');
 });
 it('separates unavailable-chart and stockpicker fixture capabilities',()=>{
  expect(demoResult('str-3','No chart').chartData).toBe(false);
  expect(demoResult('str-2','Stocks').stockpicker).toBe(true);
  expect(result.stockpicker).toBe(false);
 });
});
