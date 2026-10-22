import {beforeEach,describe,expect,it,vi} from 'vitest';
import {createDomainClient} from '../../../../../../app/host/transport';
import {deleteStockGroups,fetchStockGroups,saveStockGroup,saveStockGroupMembers,setStockGroupApiClient,toStockGroupDefinition,type RemoteBasketRecord} from '../../../../../../app/plugins/data_source/Catalogs/StockGroups/stockGroupApiClient';
import {useStockGroups} from '../../../../../../app/plugins/data_source/Catalogs/StockGroups/stockGroupsStore';
const record:RemoteBasketRecord={id:'1',name:'[Tech]',description:'Technology',system:false,items:[{symbol:'OLD',date_from:'1950-01-01',date_to:'2000-01-01'}]};
const response=(data:unknown)=>new Response(JSON.stringify({status:'success',data}));
function setup(){const fetchFn=vi.fn();setStockGroupApiClient(createDomainClient('/data',{fetchFn,baseUrl:'/api/v1'}));return fetchFn;}
beforeEach(()=>useStockGroups.setState({groups:[],loading:false,storageError:''}));
describe('confirmed baskets',()=>{
  it('validates catalog identities and historical periods',async()=>{
    const fetchFn=setup().mockResolvedValueOnce(response([record]));
    expect((await fetchStockGroups())[0].members[0]).toEqual({ticker:'OLD',from:'1950-01-01',to:'2000-01-01'});
    for(const value of [{},[record,record],[{...record,system:1}],[{...record,items:[{symbol:'BAD',date_from:'2025-02-30',date_to:null}]}]]){
      fetchFn.mockResolvedValueOnce(response(value));await expect(fetchStockGroups()).rejects.toThrow();
    }
  });
  it('confirms identities and sends metadata or canonical member strings',async()=>{
    const fetchFn=setup().mockResolvedValueOnce(response(record));
    await saveStockGroup({...toStockGroupDefinition(record),id:''});
    expect(JSON.parse(String(fetchFn.mock.calls[0][1].body))).toEqual({name:'[Tech]',description:'Technology'});
    fetchFn.mockResolvedValueOnce(response({...record,items:[]}));
    expect((await saveStockGroupMembers('1',[])).members).toEqual([]);
    expect(JSON.parse(String(fetchFn.mock.calls[1][1].body))).toEqual({symbols:[]});
    fetchFn.mockResolvedValueOnce(response({...record,id:'2'}));
    await expect(saveStockGroupMembers('1',[])).rejects.toThrow('different');
    fetchFn.mockResolvedValueOnce(response({...record,id:'2'}));
    await expect(saveStockGroup(toStockGroupDefinition(record))).rejects.toThrow('confirm');
  });
  it('retains confirmed state on failure and accepts authoritative empty catalogs',async()=>{
    const fetchFn=setup().mockRejectedValueOnce(new Error('offline'));
    await expect(useStockGroups.getState().saveGroup('Tech','Technology')).rejects.toThrow('offline');
    expect(useStockGroups.getState().groups).toEqual([]);
    fetchFn.mockResolvedValueOnce(response(record));await useStockGroups.getState().saveGroup('Tech','Technology');
    fetchFn.mockRejectedValueOnce(new Error('failed'));
    await expect(useStockGroups.getState().replaceMembers('1',[])).rejects.toThrow('failed');
    expect(useStockGroups.getState().groups[0].members).toHaveLength(1);
    fetchFn.mockResolvedValueOnce(response([]));await useStockGroups.getState().syncRemote();
    expect(useStockGroups.getState().groups).toEqual([]);
  });
  it('ignores stale reads and surfaces load failures',async()=>{
    let resolve!:(value:Response)=>void;
    const fetchFn=setup().mockImplementationOnce(()=>new Promise<Response>(done=>{resolve=done;}));
    const read=useStockGroups.getState().syncRemote();
    fetchFn.mockResolvedValueOnce(response(record));await useStockGroups.getState().saveGroup('Tech','Technology');
    resolve(response([]));await read;expect(useStockGroups.getState().groups).toHaveLength(1);
    fetchFn.mockRejectedValueOnce(new Error('offline'));await useStockGroups.getState().syncRemote();
    expect(useStockGroups.getState().storageError).toBe('offline');expect(useStockGroups.getState().loading).toBe(false);
  });
  it('protects system groups and reports partial file load progress',async()=>{
    const fetchFn=setup();
    useStockGroups.setState({groups:[toStockGroupDefinition({...record,system:true,name:'[[Tech]]'})]});
    await expect(useStockGroups.getState().replaceMembers('1',[])).rejects.toThrow('editable');
    await expect(useStockGroups.getState().saveGroup('Tech','',useStockGroups.getState().groups[0])).rejects.toThrow('System');
    useStockGroups.setState({groups:[]});
    fetchFn.mockResolvedValueOnce(response(record)).mockRejectedValueOnce(new Error('membership failed'));
    await expect(useStockGroups.getState().applyImported([toStockGroupDefinition(record)],{})).rejects.toThrow('0 groups fully loaded');
    expect(useStockGroups.getState().groups).toHaveLength(1);
  });
});


describe('confirmed basket deletion',()=>{
  it('validates IDs and exact host confirmation',async()=>{
    const fetchFn=setup().mockResolvedValueOnce(response({deleted_ids:['1'],deleted_count:1}));
    expect(await deleteStockGroups(['1','1'])).toEqual(['1']);
    expect(JSON.parse(String(fetchFn.mock.calls[0][1].body))).toEqual({ids:['1']});
    for(const result of [{},{deleted_ids:['2'],deleted_count:1},{deleted_ids:['1','1'],deleted_count:2},{deleted_ids:['1'],deleted_count:0}]){
      fetchFn.mockResolvedValueOnce(response(result));await expect(deleteStockGroups(['1'])).rejects.toThrow('confirm');
    }
    await expect(deleteStockGroups([])).rejects.toThrow();await expect(deleteStockGroups(['0'])).rejects.toThrow();
    await expect(deleteStockGroups(Array(1001).fill('1'))).rejects.toThrow();
  });
  it('retains rows on failed or invalid confirmations and removes only confirmed selections',async()=>{
    const fetchFn=setup();const saved=toStockGroupDefinition(record);
    useStockGroups.setState({groups:[saved,{...saved,id:'2',name:'[Other]'}]});
    fetchFn.mockRejectedValueOnce(new Error('offline'));
    await expect(useStockGroups.getState().remove(['1'])).rejects.toThrow('offline');expect(useStockGroups.getState().groups).toHaveLength(2);
    fetchFn.mockResolvedValueOnce(response({deleted_ids:['2'],deleted_count:1}));
    await expect(useStockGroups.getState().remove(['1'])).rejects.toThrow('confirm');expect(useStockGroups.getState().groups).toHaveLength(2);
    fetchFn.mockResolvedValueOnce(response({deleted_ids:['1'],deleted_count:1}));
    await useStockGroups.getState().remove(['1']);expect(useStockGroups.getState().groups.map(row=>row.id)).toEqual(['2']);
    useStockGroups.setState({groups:[{...saved,system:true}]});
    await expect(useStockGroups.getState().remove(['1'])).rejects.toThrow('custom');
    await expect(useStockGroups.getState().remove(['999'])).rejects.toThrow('custom');
  });
  it('does not restore deleted rows from an older catalog read',async()=>{
    let resolve!:(value:Response)=>void;const fetchFn=setup().mockImplementationOnce(()=>new Promise<Response>(done=>{resolve=done;}));
    useStockGroups.setState({groups:[toStockGroupDefinition(record)]});const read=useStockGroups.getState().syncRemote();
    fetchFn.mockResolvedValueOnce(response({deleted_ids:['1'],deleted_count:1}));await useStockGroups.getState().remove(['1']);
    resolve(response([record]));await read;expect(useStockGroups.getState().groups).toEqual([]);expect(useStockGroups.getState().loading).toBe(false);
  });
});
