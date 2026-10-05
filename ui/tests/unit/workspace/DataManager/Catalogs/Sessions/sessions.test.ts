import { describe, expect, it } from 'vitest';
import { generateMondayFriday, parseSessionsJson, serializeSessionsJson, validateElement, validateSession, type SessionDefinition } from '../../../../../../app/workspace/DataManager/Catalogs/Sessions/sessions';

const monday = { dayFrom:'Mon',timeFrom:'09:30',dayTo:'Tue',timeTo:'16:00',eod:true } as const;
describe('session rules',()=>{
  it('validates HaruQuantAI names, elements, and required rows',()=>{
    const value:SessionDefinition={name:'US_Index',broker:'-1',brokerName:'Default',elements:[monday]};
    validateSession(value,[],['-1']);
    expect(()=>validateSession({...value,name:'bad name'},[],['-1'])).toThrow('special characters');
    expect(()=>validateSession({...value,elements:[]},[],['-1'])).toThrow('No sessions defined');
    expect(()=>validateSession(value,['us_index'],['-1'])).toThrow('already exists');
    expect(()=>validateElement({...monday,dayTo:'Mon',timeTo:'08:00'})).toThrow('End time');
    expect(()=>validateElement({...monday,dayTo:'Mon',timeTo:'09:30'})).not.toThrow();
  });
  it('generates weekdays from Monday and preserves weekends',()=>{
    const saturday={dayFrom:'Sat',timeFrom:'10:00',dayTo:'Sat',timeTo:'12:00',eod:false} as const;
    const rows=generateMondayFriday([monday,saturday]);
    expect(rows.map(row=>`${row.dayFrom}-${row.dayTo}`)).toEqual(['Mon-Tue','Tue-Wed','Wed-Thu','Thu-Fri','Fri-Sat','Sat-Sat']);
    expect(rows[4]).toMatchObject({timeFrom:'09:30',timeTo:'16:00',eod:true});
    expect(()=>generateMondayFriday([])).toThrow('No session defined');
    expect(()=>generateMondayFriday([{...monday,dayFrom:'Wed'}])).toThrow('Monday session');
  });
  it('round trips the versioned Sessions JSON shape',()=>{
    const value={name:'US_Index',broker:'-1',brokerName:'Default',elements:[monday]};const json=serializeSessionsJson([value]);
    expect(JSON.parse(json)).toMatchObject({version:1,kind:'sessions',sessions:[{name:'US_Index'}]});expect(parseSessionsJson(json)).toEqual([value]);
    expect(()=>parseSessionsJson('{"version":1,"kind":"instruments","sessions":[]}')).toThrow('valid Sessions JSON');
  });
});
