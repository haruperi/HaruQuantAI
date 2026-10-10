import { describe, expect, it } from 'vitest';
import {
  generateMondayFriday,
  parseSessionsJson,
  serializeSessionsJson,
  serializeSessionsXml,
  validateElement,
  validateSession,
  type SessionDefinition,
} from '../../../../../../app/plugins/data_source/Catalogs/Sessions/sessions';

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
  it('serializes native SQX Sessions.xml template', () => {
    const value: SessionDefinition = {
      name: 'US_Index',
      broker: '-1',
      brokerName: 'Default',
      elements: [monday],
    };
    const xml = serializeSessionsXml([value]);
    expect(xml).toContain('<Sessions>');
    expect(xml).toContain('<Session name="US_Index" broker="-1" timezone="UTC">');
    expect(xml).toContain('<SessionElement startDay="Mon" startTime="09:30" endDay="Tue" endTime="16:00" seoc="Yes" type="Regular" />');
  });

  it('normalizes brokerName in toSessionDefinition to Default for SQ default and broker_id -1', async () => {
    const { toSessionDefinition } = await import(
      '../../../../../../app/plugins/data_source/Catalogs/Sessions/sessionApiClient'
    );
    const remote = {
      name: '24/5 Forex',
      broker_id: -1,
      broker_name: 'SQ default',
      description: '',
      timezone: 'UTC',
      windows: [
        {
          day_from: 'Mon',
          day_to: 'Tue',
          start_time: '00:00:00',
          end_time: '00:00:00',
          eod: true,
        },
      ],
    };
    const def = toSessionDefinition(remote);
    expect(def.name).toBe('24/5 Forex');
    expect(def.broker).toBe('-1');
    expect(def.brokerName).toBe('Default');
    expect(def.elements).toHaveLength(1);
    expect(def.elements[0].timeFrom).toBe('00:00');
  });

  it('hydrates and refreshes sessions from remote server in useSessions', async () => {
    const { useSessions } = await import(
      '../../../../../../app/plugins/data_source/Catalogs/Sessions/sessionStore'
    );
    const { setSessionApiClient } = await import(
      '../../../../../../app/plugins/data_source/Catalogs/Sessions/sessionApiClient'
    );

    const mockSessions = [
      {
        name: 'Forex 24/5',
        broker_id: -1,
        broker_name: 'SQ default',
        description: '',
        timezone: 'UTC',
        windows: [{ day_from: 'Mon', day_to: 'Tue', start_time: '00:00', end_time: '00:00', eod: true }],
      },
      {
        name: 'US Equities',
        broker_id: -1,
        broker_name: 'SQ default',
        description: '',
        timezone: 'America/New_York',
        windows: [{ day_from: 'Mon', day_to: 'Mon', start_time: '09:30', end_time: '16:00', eod: true }],
      },
    ];

    setSessionApiClient({
      get: async () => mockSessions,
      post: async () => ({}),
      put: async () => ({}),
      delete: async () => ({}),
    } as any);

    await useSessions.getState().refreshFromServer();
    const state = useSessions.getState();
    expect(state.storageError).toBe('');
    expect(state.sessions.length).toBeGreaterThanOrEqual(2);
    expect(state.sessions.some(s => s.name === 'US Equities')).toBe(true);
    expect(state.sessions.some(s => s.name === 'Forex 24/5')).toBe(true);
  });
});
