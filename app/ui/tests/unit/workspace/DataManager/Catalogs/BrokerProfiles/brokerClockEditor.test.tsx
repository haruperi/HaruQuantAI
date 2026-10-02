import { beforeEach, expect, it, vi } from 'vitest';
import { createElement, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { BrokerClockPolicyDialog, BrokerProfileEditorDialog } from '../../../../../../app/workspace/DataManager/Catalogs/BrokerProfiles/BrokerProfileEditorDialog';
import type { BrokerProfile } from '../../../../../../app/workspace/DataManager/Catalogs/BrokerProfiles/brokerProfiles';

// Controlled hook lifecycle without adding a DOM dependency. Real JSX is rendered;
// captured button handlers exercise the component's async host-port actions.
const harness = vi.hoisted(() => ({
  states: [] as unknown[], cursor: 0, initial: true,
  buttons: new Map<string, ButtonHTMLAttributes<HTMLButtonElement>>(),
  read: vi.fn(), write: vi.fn(), saveBroker: vi.fn(),
}));
vi.mock('react', async original => ({
  ...await original<typeof import('react')>(),
  useState: (initial: unknown) => {
    const index = harness.cursor++;
    if (!(index in harness.states)) harness.states[index] = typeof initial === 'function' ? initial() : initial;
    return [harness.states[index], (value: unknown) => {
      harness.states[index] = typeof value === 'function' ? value(harness.states[index]) : value;
    }];
  },
  useEffect: (effect: () => unknown) => { if (harness.initial) effect(); },
}));
vi.mock('../../../../../../app/workspace/DataManager/Common/catalogClient', () => ({
  brokerClockPort: { read: harness.read, write: harness.write },
}));
vi.mock('../../../../../../app/workspace/DataManager/Common/dataManagerStore', () => ({
  useDataManagerStore: () => ({ saveBroker: harness.saveBroker }),
}));
vi.mock('../../../../../../app/components/ui', async original => ({
  ...await original<typeof import('../../../../../../app/components/ui')>(),
  Modal: ({ title, children, footer }: { title: string; children: ReactNode; footer: ReactNode }) =>
    createElement('section', { 'aria-label': title }, children, footer),
  Button: (props: ButtonHTMLAttributes<HTMLButtonElement>) => {
    harness.buttons.set(String(props.children), props);
    return createElement('button', props);
  },
}));
const broker: BrokerProfile = {
  id: '6', name: 'Pepperstone', desc: 'Seeded', postfix: '_pepperstone',
  timezone: 'EETUS', mtUse: true, stockPickerUse: false, system: true,
  stocks: [], instruments: [],
};
const response = {
  revision: 0, revisions: [], database_broker_id: '6',
  schema: { properties: { verified: { type: 'boolean', default: false, title: 'Verified' }, limitations: { type: 'string', default: 'Test only', title: 'Limitations' } } },
};
function render(node: ReactNode): string {
  harness.cursor = 0; harness.buttons.clear();
  const html = renderToStaticMarkup(node);
  harness.initial = false;
  return html;
}
async function flush(): Promise<void> { await Promise.resolve(); await Promise.resolve(); }
beforeEach(() => {
  vi.clearAllMocks(); harness.states = []; harness.cursor = 0; harness.initial = true;
  harness.read.mockResolvedValue(response);
  harness.write.mockResolvedValue({ ...response, revision: 1, revisions: [{}] });
});
it('reads system broker policy and exposes no catalog metadata editing controls', async () => {
  const node = createElement(BrokerClockPolicyDialog, { source: broker, onClose: vi.fn() });
  render(node); await flush(); const html = render(node);
  expect(harness.read).toHaveBeenCalledWith('6');
  expect(html).toContain('Pepperstone clock policy');
  expect(html).toContain('Stored revisions: 0');
  expect(html).toContain('aria-label="Verified"');
  expect(html).not.toContain('Broker profile name');
  expect(html).not.toContain('Database broker association');
  expect(harness.buttons.has('Save')).toBe(false);
  expect(harness.saveBroker).not.toHaveBeenCalled();
});
it('saves only through the policy port with the read revision and closes without catalog writes', async () => {
  const close = vi.fn(); const node = createElement(BrokerClockPolicyDialog, { source: broker, onClose: close });
  render(node); await flush(); render(node);
  harness.buttons.get('Save new clock policy')!.onClick!({} as never);
  await flush();
  expect(harness.write).toHaveBeenCalledWith('6', 0, {
    verified: false, limitations: 'Test only', revision: 1, schema_version: 1,
  });
  render(node);
  harness.buttons.get('Close')!.onClick!({} as never);
  expect(close).toHaveBeenCalledOnce();
  expect(harness.saveBroker).not.toHaveBeenCalled();
});
it('retains the custom profile metadata editor and its independent save action', async () => {
  const source = { ...broker, id: 'custom', system: false };
  const node = createElement(BrokerProfileEditorDialog, {
    mode: 'edit', source, canSetStockPicker: true, canSetMt: true, canSetTimezone: true,
    onClose: vi.fn(), onSaved: vi.fn(),
  });
  expect(render(node)).toContain('Broker profile name');
  harness.buttons.get('Save')!.onClick!({} as never); await flush();
  expect(harness.saveBroker).toHaveBeenCalledWith(source);
  expect(harness.write).not.toHaveBeenCalled();
});
