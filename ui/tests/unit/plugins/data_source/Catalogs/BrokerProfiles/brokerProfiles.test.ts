import {describe,expect,it} from 'vitest';import {validateBrokerCosts,normalizeBrokerName,parseBrokerStocks,parseBrokersJson,serializeBrokersJson,serializeBrokerStocksJson,validateBroker,type BrokerProfile} from '../../../../../../app/plugins/data_source/Catalogs/BrokerProfiles/brokerProfiles';
const profile:BrokerProfile={id:'b1',name:'Broker',desc:'Test',postfix:'_b',timezone:'UTC',mtUse:true,stockPickerUse:true,system:false,stocks:['AAPL','TSLA'],instruments:[]};
describe('broker profiles',()=>{
  it('normalizes and validates broker names',()=>{expect(normalizeBrokerName(' Demo ')).toBe('Demo');expect(normalizeBrokerName('Demo')).toBe('Demo');expect(()=>normalizeBrokerName('')).toThrow("Broker's name must be set");expect(()=>validateBroker({...profile,name:'Broker'},[{...profile,id:'other',name:'Broker'}])).toThrow('Name must be unique');});
  it('parses line-separated stocks and exports typed JSON',()=>{expect(parseBrokerStocks('AAPL\nTSLA;ignored\n\n AMD ')).toEqual(['AAPL','TSLA','AMD']);expect(JSON.parse(serializeBrokerStocksJson(profile.stocks))).toEqual({version:1,kind:'broker-stocks',stocks:['AAPL','TSLA']});});
  it('round trips the versioned Brokers JSON shape',()=>{const json=serializeBrokersJson([profile]);expect(JSON.parse(json)).toMatchObject({version:1,kind:'brokers',brokers:[{name:'Broker',postfix:'_b',stocks:['AAPL','TSLA']}]});const [loaded]=parseBrokersJson(json);expect(loaded).toMatchObject({name:'Broker',desc:'Test',stocks:['AAPL','TSLA'],mtUse:true,stockPickerUse:true});});
  it('rejects invalid envelopes and handles JSON imports',()=>{expect(()=>parseBrokersJson('{"version":1,"kind":"wrong","brokers":[]}')).toThrow('No Brokers found');const json=JSON.stringify({version:1,kind:'brokers',brokers:[{name:'Legacy',desc:'',postfix:'',timezone:'',mtUse:false,stockPickerUse:false,stocks:[]}]});expect(parseBrokersJson(json)[0].name).toBe('Legacy');});
});

describe('broker cost defaults',()=>{
  it('round trips fixed zero spread and configured commissions',()=>{
    const costs={spreadModel:{model:'fixed' as const,value:0},commissionModel:{model:'Per trade' as const,value:3.5,unit:'share',min:0,minUnit:'money',max:0,maxUnit:'money'}};
    expect(parseBrokersJson(serializeBrokersJson([{...profile,...costs}]))[0]).toMatchObject(costs);
  });
  it('distinguishes inherit from explicit zero and rejects invalid costs',()=>{
    expect(()=>validateBrokerCosts({model:'inherit'},{model:'inherit'})).not.toThrow();
    for(const value of [-1,NaN,Infinity])expect(()=>validateBrokerCosts({model:'fixed',value},{model:'inherit'})).toThrow();
    expect(()=>validateBrokerCosts({model:'inherit'},{model:'Unknown',value:0})).toThrow();
  });
});

describe('configured broker clock labels',()=>{
  it('retains EETUS metadata without interpreting it as an IANA conversion',()=>{
    const saved=validateBroker({...profile,timezone:'EETUS'},[]);
    expect(saved.timezone).toBe('EETUS');
    expect(parseBrokersJson(serializeBrokersJson([saved]))[0].timezone).toBe('EETUS');
    expect(()=>validateBroker({...profile,timezone:'Unknown/BrokerClock'},[])).toThrow('timezone');
  });
});
