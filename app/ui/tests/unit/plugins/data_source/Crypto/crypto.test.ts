import { describe, expect, it, vi } from 'vitest';
import { cryptoDefinitions, cryptoDownloadRanges, cryptoExchange, cryptoExchanges, cryptoTargets } from '../../../../../app/plugins/data_source/Crypto/crypto';

describe('Crypto provider rules', () => {
  it('defines all six source exchanges with their exact provider timeframes', () => {
    expect(cryptoExchanges.map(item => item.id)).toEqual(['Binance','BinanceCoinM','BinanceUsdtM','Bitfinex','Poloniex','Coinbase']);
    expect(cryptoExchange('Binance').timeframes).toEqual(['M1','M3','M5','M15','M30','H1','H2','H4','H6','H8','H12','D1']);
    expect(cryptoExchange('Bitfinex').timeframes).toEqual(['M1','M5','M15','M30','H1','H3','H6','H12','D1']);
    expect(cryptoExchange('Poloniex').timeframes).toEqual(['M5','M15','M30','H2','H4','D1']);
    expect(cryptoExchange('Coinbase').timeframes).toEqual(['M1','M5','M15','H1','H6','D1']);
    expect(() => cryptoExchange('Unknown')).toThrow('Unknown');
  });
  it('keeps native symbol syntax and validates selection, timeframes and global names', () => {
    expect(cryptoDefinitions('Coinbase',['BTC-USD'],'M1','_CB',[])[0]).toMatchObject({ id:'crypto:Coinbase:BTC-USD_CB', symbol:'BTC-USD_CB', underlying:'BTC-USD', exchange:'Coinbase', source:'Crypto', bars:0 });
    expect(() => cryptoDefinitions('Binance',[],'M1','',[])).toThrow('No symbols');
    expect(() => cryptoDefinitions('Poloniex',['BTC_USDT'],'M1','',[])).toThrow('supported timeframe');
    expect(() => cryptoDefinitions('Binance',['BTCUSDT'],'M1','',['BTCUSDT'])).toThrow('exists');
  });
  it('isolates Crypto targets, rejects clones and applies per-target since-last ranges', () => {
    const targets = cryptoDefinitions('Binance',['BTCUSDT','ETHUSDT'],'M1','_C',[]); targets[0].to='2025-01-01'; targets[1].to='2025-02-01';
    const request={targets,dateFrom:'2025-01-01',dateTo:'2025-03-01',dateType:'sinceLast' as const,overwrite:false};
    expect(cryptoDownloadRanges(request)[targets[1].id].from).toBe('2025-02-01');
    expect(() => cryptoTargets([{...targets[0],sourceDataId:'clone'}])).toThrow('cloned');
    expect(() => cryptoDownloadRanges({...request,dateFrom:'bad'})).toThrow('valid date');
  });
});

async function isolated() {
  vi.resetModules(); const memory=new Map<string,string>(); const storage={getItem:(key:string)=>memory.get(key)??null,setItem:(key:string,value:string)=>{memory.set(key,value);}}; vi.stubGlobal('localStorage',storage);
  const store=(await import('../../../../../app/plugins/data_source/Crypto/cryptoStore')).useCrypto; return {store,memory,storage};
}
it('persists add/download jobs, reloads paused, stops partial work and merges coverage', async () => {
  const {store}=await isolated(); const definitions=cryptoDefinitions('Binance',['BTCUSDT','ETHUSDT'],'M1','_C',[]);
  store.getState().startAdd(definitions,false); for(let i=0;i<10;i++)store.getState().advance(); expect(store.getState().definitions).toHaveLength(1);
  vi.resetModules(); const restored=(await import('../../../../../app/plugins/data_source/Crypto/cryptoStore')).useCrypto; expect(restored.getState().job?.state).toBe('paused'); restored.getState().action('stop'); expect(restored.getState().definitions).toHaveLength(1);
  const target=restored.getState().definitions[0], request={targets:[target],dateFrom:'2025-01-01',dateTo:'2025-01-03',dateType:'custom' as const,overwrite:false};
  restored.getState().startDownload(request,false); for(let i=0;i<20;i++)restored.getState().advance(); expect(restored.getState().ranges[target.id]).toEqual([{from:'2025-01-01',to:'2025-01-03'}]);
  restored.getState().startDownload(request,false); for(let i=0;i<20;i++)restored.getState().advance(); expect(restored.getState().ranges[target.id]).toHaveLength(1);
});
it('fails closed for active work, quota errors and corrupt saved state', async () => {
  const {store,memory,storage}=await isolated(); const definition=cryptoDefinitions('Coinbase',['BTC-USD'],'M1','_C',[]);
  expect(()=>store.getState().startAdd(definition,true)).toThrow('active'); store.getState().startAdd(definition,false); const prior=memory.get('sqx-crypto-data-v1'); storage.setItem=()=>{throw new Error('quota');}; store.getState().advance(); expect(store.getState().job?.state).toBe('failed'); expect(memory.get('sqx-crypto-data-v1')).toBe(prior);
  memory.set('sqx-crypto-data-v1','bad'); vi.resetModules(); const corrupt=(await import('../../../../../app/plugins/data_source/Crypto/cryptoStore')).useCrypto; expect(corrupt.getState().storageError).toContain('preserved'); expect(memory.get('sqx-crypto-data-v1')).toBe('bad');
});
