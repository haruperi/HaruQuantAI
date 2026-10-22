import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { SessionsModal } from '../../../../../../app/plugins/data_source/Catalogs/Sessions/SessionsModal';

const brokers = [{ id: '-1', name: 'Default', postfix: '' }];
describe('session profile form', () => {
  it('makes draft persistence, timezone, holidays and lunch gaps explicit', () => {
    const html = renderToString(<SessionsModal mode="add" brokers={brokers} onClose={() => {}} onSaved={() => {}}/>);
    for (const label of ['Session name','Timezone','Description','Full-day holidays','Add holiday','Add interval','Intervals stay in this draft until Save.','Lunch pauses are gaps']) expect(html).toContain(label);
    expect(html).not.toContain('data-workspace-panel');
  });
  it.each(['edit', 'clone'] as const)('shows legacy defaults before an explicit %s save', mode => {
    const source = { id: '1', name: 'Legacy', broker: '-1', brokerName: 'Default', timezone: 'UTC', description: '', isDefault: false, holidays: [], elements: [], normalizationWarnings: ['EOD was not stored; default False is used.'] };
    const html = renderToString(<SessionsModal mode={mode} source={source} brokers={brokers} onClose={() => {}} onSaved={() => {}}/>);
    expect(html).toContain('Stored session compatibility');
    expect(html).toContain('EOD was not stored');
    expect(html).toContain('Reading leaves the stored profile unchanged.');
  });
  it('labels clone shifts as minutes and retains calendar identity', () => {
    const source = { id: '1', name: 'Recorded', broker: '-1', brokerName: 'Default', timezone: 'Europe/London', description: '', isDefault: false, holidays: [], elements: [] };
    const html = renderToString(<SessionsModal mode="clone" source={source} brokers={brokers} onClose={() => {}} onSaved={() => {}}/>);
    expect(html).toContain('Shift schedule (minutes)');
    expect(html).toContain('does not convert timezones or shift holidays');
  });
});
