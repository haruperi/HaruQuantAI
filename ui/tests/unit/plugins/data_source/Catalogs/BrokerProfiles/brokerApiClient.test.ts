import {beforeEach,describe,expect,it,vi} from 'vitest';
import {createDomainClient} from '../../../../../../app/host/transport';
import {deleteBrokers,fetchBrokers,fetchBrokerStocks,saveBroker,saveBrokerStocks,importBrokerRecords,setBrokerApiClient,toBrokerProfile,type RemoteBrokerRecord} from '../../../../../../app/plugins/data_source/Catalogs/BrokerProfiles/brokerApiClient';
import {useDataManagerStore} from '../../../../../../app/plugins/data_source/Common/dataManagerStore';

const row:RemoteBrokerRecord={id:'1',name:'Demo',description:'Saved',timezone:'UTC',postfix:'_d',stockpicker_use:true,mt_use:true,is_system:false,stocks:[],customized_stocks:0,total_instruments:0,total_sessions:0,spread_model:{model:'inherit'},commission_model:{model:'inherit'}};
const response=(data:unknown)=>new Response(JSON.stringify({status:'success',data}));
function setup(){const fetchFn=vi.fn();setBrokerApiClient(createDomainClient('/data',{fetchFn,baseUrl:'/api/v1'}));return fetchFn;}
beforeEach(()=>useDataManagerStore.setState({brokers:[],brokerLoading:false,brokerError:''}));

describe('confirmed broker transport and state',()=>{
  it('accepts zero counts and inherited costs and validates identities',async()=>{
    const fetchFn=setup().mockResolvedValue(response([row]));
    expect(await fetchBrokers()).toEqual([expect.objectContaining({id:'1',stocks:[],spreadModel:{model:'inherit'}})]);
    expect(fetchFn.mock.calls[0][0]).toContain('/data/brokers');
    expect(()=>toBrokerProfile({...row,customized_stocks:2})).toThrow();
    expect(()=>toBrokerProfile({...row,id:'01'})).toThrow();
    expect(()=>toBrokerProfile({...row,is_system:1 as unknown as boolean})).toThrow();
  });
  it('rejects malformed and duplicate catalogs',async()=>{
    const fetchFn=setup();
    for(const data of [{},[row,row],[row,{...row,id:'2'}]]){
      fetchFn.mockResolvedValueOnce(response(data));await expect(fetchBrokers()).rejects.toThrow();
    }
  });
  it('posts configured costs and trusts only confirmed stock membership',async()=>{
    const fetchFn=setup().mockResolvedValue(response({...row,spread_model:{model:'fixed',value:0}}));
    const profile={...toBrokerProfile(row),id:'',stocks:['LOCAL'],spreadModel:{model:'fixed' as const,value:0}};
    const saved=await saveBroker(profile);
    expect(saved.stocks).toEqual([]);
    const body=JSON.parse(String(fetchFn.mock.calls[0][1].body));
    expect(body).toMatchObject({spread_model:{model:'fixed',value:0},commission_model:{model:'inherit'},timezone:'UTC'});
    expect(body).not.toHaveProperty('is_system');expect(body).not.toHaveProperty('stocks');expect(body).not.toHaveProperty('id');
    fetchFn.mockResolvedValueOnce(response({...row,id:'2'}));await expect(saveBroker(toBrokerProfile(row))).rejects.toThrow('confirm');
  });
  it('preserves confirmed empty stocks and rejects unconfirmed replacement',async()=>{
    const fetchFn=setup().mockResolvedValueOnce(response({broker_id:'1',stocks:[]}));
    expect(await fetchBrokerStocks('1')).toEqual([]);
    fetchFn.mockResolvedValueOnce(response({broker_id:'1',stocks:['AAPL'],count:1}));
    expect(await saveBrokerStocks('1',[' AAPL ','aapl'])).toEqual(['AAPL']);
    fetchFn.mockResolvedValueOnce(response({broker_id:'2',stocks:[],count:0}));await expect(saveBrokerStocks('1',[])).rejects.toThrow();
    await expect(fetchBrokerStocks('1garbage')).rejects.toThrow();
  });
  it('clears stale brokers on an authoritative empty response and surfaces errors',async()=>{
    const fetchFn=setup().mockResolvedValueOnce(response([]));
    useDataManagerStore.setState({brokers:[toBrokerProfile(row)]});
    await useDataManagerStore.getState().syncBrokers();expect(useDataManagerStore.getState().brokers).toEqual([]);
    fetchFn.mockRejectedValueOnce(new Error('offline'));await useDataManagerStore.getState().syncBrokers();
    expect(useDataManagerStore.getState().brokerError).not.toBe('');expect(useDataManagerStore.getState().brokerLoading).toBe(false);
  });
  it('retains server results when saving and never creates local profiles on failure',async()=>{
    const fetchFn=setup().mockResolvedValueOnce(response(row));
    await useDataManagerStore.getState().saveBroker({...toBrokerProfile(row),id:''});
    expect(useDataManagerStore.getState().brokers).toEqual([toBrokerProfile(row)]);
    fetchFn.mockRejectedValueOnce(new Error('failed'));
    await expect(useDataManagerStore.getState().saveBroker({...toBrokerProfile(row),id:'',name:'Other'})).rejects.toThrow();
    expect(useDataManagerStore.getState().brokers).toHaveLength(1);
  });
  it('reports partial imports and refuses misleading response counts',async()=>{
    const fetchFn=setup();const options={selected_names:['ONE','TWO'],postfix:'_d',conflict_policy:'error' as const,use_profile_costs:false};
    const result={broker_id:'1',imported_count:1,created_count:1,updated_count:0,records:[{id:'1',symbol:'ONE_d',broker_id:1}],failed:[{name:'TWO_d',reason:'Invalid record'}],unattempted:[]};
    fetchFn.mockResolvedValueOnce(response(result));
    expect(await importBrokerRecords('instrument','1',[{symbol:'ONE'},{symbol:'TWO'}],options)).toEqual(result);
    expect(JSON.parse(String(fetchFn.mock.calls[0][1].body))).toMatchObject({version:1,kind:'instruments',options});
    fetchFn.mockResolvedValueOnce(response({...result,imported_count:2}));
    await expect(importBrokerRecords('instrument','1',[],options)).rejects.toThrow('invalid import result');
  });
});

describe('existing server clock labels',()=>{
  it('accepts persisted system profiles with EETUS and rejects unknown labels',async()=>{
    setup().mockResolvedValue(response([{...row,name:'[[Existing]]',is_system:true,timezone:'EETUS'}]));
    expect(await fetchBrokers()).toEqual([expect.objectContaining({system:true,timezone:'EETUS'})]);
    expect(()=>toBrokerProfile({...row,timezone:'Unknown/BrokerClock'})).toThrow();
  });
});


describe('confirmed broker deletion',()=>{
  it('validates exact deleted identities and request IDs',async()=>{
    const fetchFn=setup().mockResolvedValueOnce(response({deleted_ids:['1'],deleted_count:1}));
    expect(await deleteBrokers(['1','1'])).toEqual(['1']);
    expect(JSON.parse(String(fetchFn.mock.calls[0][1].body))).toEqual({ids:['1']});
    for(const result of [{deleted_ids:['2'],deleted_count:1},{deleted_ids:['1','1'],deleted_count:2},{deleted_ids:['1'],deleted_count:0},{}]){
      fetchFn.mockResolvedValueOnce(response(result));await expect(deleteBrokers(['1'])).rejects.toThrow('confirm');
    }
    await expect(deleteBrokers([])).rejects.toThrow();await expect(deleteBrokers(['0'])).rejects.toThrow();
  });
  it('retains rows until confirmed and preserves them on failure',async()=>{
    const fetchFn=setup();useDataManagerStore.setState({brokers:[toBrokerProfile(row)]});
    fetchFn.mockRejectedValueOnce(new Error('in use'));
    await expect(useDataManagerStore.getState().removeBrokers(['1'])).rejects.toThrow('in use');
    expect(useDataManagerStore.getState().brokers).toHaveLength(1);
    fetchFn.mockResolvedValueOnce(response({deleted_ids:['1'],deleted_count:1}));
    await useDataManagerStore.getState().removeBrokers(['1']);expect(useDataManagerStore.getState().brokers).toEqual([]);
    useDataManagerStore.setState({brokers:[toBrokerProfile({...row,is_system:true})]});
    await expect(useDataManagerStore.getState().removeBrokers(['1'])).rejects.toThrow('custom');
  });
  it('prevents an earlier catalog read from restoring deleted rows',async()=>{
    let resolveRead!:(value:Response)=>void;
    const fetchFn=setup().mockImplementationOnce(()=>new Promise<Response>(resolve=>{resolveRead=resolve;}));
    useDataManagerStore.setState({brokers:[toBrokerProfile(row)]});
    const read=useDataManagerStore.getState().syncBrokers();
    fetchFn.mockResolvedValueOnce(response({deleted_ids:['1'],deleted_count:1}));
    await useDataManagerStore.getState().removeBrokers(['1']);
    resolveRead(response([row]));await read;
    expect(useDataManagerStore.getState().brokers).toEqual([]);
    expect(useDataManagerStore.getState().brokerLoading).toBe(false);
  });
});
