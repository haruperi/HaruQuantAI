import { describe, expect, it } from 'vitest';
import { activeMemberships, formatStockLines, normalizeGroupName, parseStockGroupsJson, parseStockLines, serializeStockGroupsJson, serializeStockMembersJson, summarizeGroup, type StockGroupDefinition } from '../../../../../../app/workspace/DataManager/Catalogs/StockGroups/stockGroups';

const group: StockGroupDefinition = { id:'g1',name:'[Index]',description:'History-aware index',system:false,members:[{ticker:'AAPL'},{ticker:'MSFT',from:'2020-12-01'},{ticker:'OLD',from:'2007-04-15',to:'2015-05-30'}] };

describe('stock groups', () => {
  it('normalizes and validates HaruQuantAI group names', () => {
    expect(normalizeGroupName('  Index  ')).toBe('[Index]');
    expect(normalizeGroupName('Index', true)).toBe('[[Index]]');
    expect(() => normalizeGroupName('')).toThrow("Group's name must be set");
    expect(() => normalizeGroupName('X'.repeat(60))).toThrow('50 characters');
  });

  it('parses both compiled date formats and preserves history periods', () => {
    const rows = parseStockLines('AAPL\nMSFT;01.12.2020\nOLD;2007.04.15;30.05.2015\nBAD;not-a-date');
    expect(rows).toEqual([{ticker:'AAPL'},{ticker:'MSFT',from:'2020-12-01'},{ticker:'OLD',from:'2007-04-15',to:'2015-05-30'},{ticker:'BAD'}]);
    expect(formatStockLines(rows)).toContain('OLD;15.04.2007;30.05.2015');
    expect(formatStockLines(rows, true)).toContain('AAPL;');
    expect(activeMemberships(group, '2026-01-01').map(row => row.ticker)).toEqual(['AAPL','MSFT']);
  });

  it('requires data for every member before reporting readiness', () => {
    const summary = summarizeGroup(group, [{symbol:'AAPL',from:'2010-01-01',to:'2026-01-01',bars:4000}]);
    expect(summary).toMatchObject({active:2,total:3,numberOfSymbols:1,downloaded:1,ready:false,from:'2010-01-01',to:'2026-01-01'});
    expect(summarizeGroup({...group,members:[]},[]).ready).toBe(false);
  });

  it('round trips the versioned Groups JSON shape with ISO dates', () => {
    const json = serializeStockGroupsJson([group]);
    const payload=JSON.parse(json);expect(payload).toMatchObject({version:1,kind:'stock-groups'});expect(payload.groups[0]).toMatchObject({name:'[Index]'});expect(payload.groups[0].members[0]).toEqual({ticker:'AAPL'});
    expect(parseStockGroupsJson(json)[0]).toMatchObject({name:'[Index]',members:group.members});
    expect(JSON.parse(serializeStockMembersJson(group.members))).toMatchObject({version:1,kind:'stock-group-members',stocks:group.members});
  });
});
