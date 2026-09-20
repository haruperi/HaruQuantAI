import { describe, expect, it, vi } from 'vitest';
import { darwinexCatalogue, darwinexDefinitions, darwinexDownloadRanges, discoverDarwinex, parseDarwinex } from './darwinex';
import { today } from './dukascopyDownload';
describe('Darwinex source rules', () => {
  it('parses all donor symbols and rejects invalid dates and duplicate rows', () => {
    expect(darwinexCatalogue).toHaveLength(328); expect(darwinexCatalogue[0]).toMatchObject({ symbol: 'AUDCAD', dateFrom: '2017-10-01' });
    expect(() => parseDarwinex('A;31.02.2020;1;1;1;1;1;1')).toThrow();
    expect(() => parseDarwinex('A;01.01.2020;1;1;1;1;1;1\nA;01.01.2020;1;1;1;1;1;1')).toThrow();
  });
  it('discovers only direct log.gz data and supports catalogue-symbol folder fallback', () => {
    expect(discoverDarwinex(['Root/EURUSD/a.log.gz','Root/EURUSD/b.log.gz','Root/GBPUSD/a.txt','Root/OTHER/deep/a.log.gz']).symbols).toEqual(['EURUSD']);
    expect(discoverDarwinex(['AUDUSD/a.log.gz']).symbols).toEqual(['AUDUSD']);
    expect(discoverDarwinex(['Unknown/a.log.gz']).symbols).toEqual([]);
    expect(discoverDarwinex(['Root/EURUSD/a.LOG.GZ']).symbols).toEqual([]);
    expect(() => discoverDarwinex(['Root/../a.log.gz'])).toThrow('Invalid');
  });
  it('validates names and mappings and skips only explicit skipped symbols', () => {
    const broker = { id:'b', name:'Broker', postfix:'_B', timezone:'Europe/Prague', mtUse:true, instruments:['AUDUSD.b'] };
    expect(() => darwinexDefinitions(['AUDUSD'],'',[],broker,{})).toThrow('instrument');
    expect(darwinexDefinitions(['AUDUSD','AUDCAD'],'_B',[],broker,{ AUDUSD:'AUDUSD.b', AUDCAD:'-1000' })[0]).toMatchObject({ symbol:'AUDUSD_B', instrument:'AUDUSD.b', timezone:'Europe/Prague', bars:0 });
    expect(() => darwinexDefinitions(['AUDUSD'],'',['AUDUSD'])).toThrow('exists');
  });
  it('uses per-target last dates, rejects clones and validates dates', () => {
    const targets = darwinexDefinitions(['AUDUSD','EURUSD'],'_D',[]); targets[0].to='2025-01-01'; targets[1].to='2025-02-01';
    const request = { targets, dateFrom:'2025-01-01', dateTo:'2025-03-01', dateType:'sinceLast' as const, overwrite:false };
    expect(darwinexDownloadRanges(request)['darwinex:EURUSD_D'].from).toBe('2025-02-01');
    expect(() => darwinexDownloadRanges({ ...request,dateFrom:'bad' })).toThrow('valid date');
    expect(() => darwinexDownloadRanges({ ...request,targets:[{...targets[0],sourceDataId:'clone'}] })).toThrow('cloned');
  });
});
async function isolated() {
  vi.resetModules(); const memory = new Map<string,string>(); const storage={getItem:(key:string)=>memory.get(key)??null,setItem:(key:string,value:string)=>{memory.set(key,value);}}; vi.stubGlobal('localStorage',storage);
  const store=(await import('./darwinexStore')).useDarwinex; return { store,memory,storage };
}
it('commits partial additions, reloads paused, completes and deduplicates downloads', async () => {
  const { store }=await isolated(); const definitions=darwinexDefinitions(['AUDUSD','EURUSD'],'_D',[]);
  store.getState().start('add',definitions,false); for(let i=0;i<10;i++) store.getState().advance(); expect(store.getState().definitions).toHaveLength(1);
  vi.resetModules(); const restored=(await import('./darwinexStore')).useDarwinex; expect(restored.getState().job?.state).toBe('paused'); restored.getState().action('resume'); for(let i=0;i<10;i++) restored.getState().advance();
  const request={targets:definitions,dateFrom:'2025-01-01',dateTo:'2025-01-03',dateType:'custom' as const,overwrite:false};
  expect(() => restored.getState().download(request,false,false)).toThrow('full license');
  for(let run=0;run<2;run++){restored.getState().download(request,true,false);for(let i=0;i<20;i++)restored.getState().advance();}
  expect(restored.getState().ranges[definitions[0].id]).toEqual([{from:'2025-01-01',to:'2025-01-03'}]);
  restored.getState().download({...request,overwrite:true,dateFrom:'2025-01-02',dateTo:'2025-01-02'},true,false);for(let i=0;i<20;i++)restored.getState().advance();expect(restored.getState().ranges[definitions[0].id]).toEqual([{from:'2025-01-01',to:'2025-01-03'}]);
});
it('preserves completed work on stop and storage on failure/corruption', async () => {
  const {store,memory,storage}=await isolated(); store.getState().start('import',darwinexDefinitions(['AUDUSD','EURUSD'],'_I',[]),false,'Folder','_I');for(let i=0;i<10;i++)store.getState().advance();store.getState().action('stop');store.getState().advance();expect(store.getState().definitions).toHaveLength(1);
  expect(() => store.getState().start('add',darwinexDefinitions(['AUDCAD'],'',[]),true)).toThrow('active');
  store.getState().start('add',darwinexDefinitions(['AUDCAD'],'',[]),false);const prior=memory.get('sqx-darwinex-v1'); storage.setItem=()=>{throw new Error('quota');};store.getState().advance();expect(store.getState().job?.state).toBe('failed');expect(memory.get('sqx-darwinex-v1')).toBe(prior);
  memory.set('sqx-darwinex-v1','bad');vi.resetModules();const corrupt=(await import('./darwinexStore')).useDarwinex;expect(corrupt.getState().storageError).toContain('preserved');expect(memory.get('sqx-darwinex-v1')).toBe('bad');
  expect(today()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
});
