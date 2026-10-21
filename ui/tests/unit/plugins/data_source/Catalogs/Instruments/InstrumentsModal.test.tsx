import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { InstrumentsModal } from '../../../../../../app/plugins/data_source/Catalogs/Instruments/InstrumentsModal';

describe('instrument form contract', () => {
  it('exposes independent contract, pip, precision and margin fields without guessing sizes', () => {
    const html = renderToString(<InstrumentsModal mode="add" selected={[]} brokers={[{ id: '-1', name: 'Default', postfix: '', timezone: 'UTC' }]} onClose={() => {}} onSaved={() => {}}/>);
    for (const label of ['Contract size','Pip size','Margin rate (fraction)','Price decimals','Minimum volume','Maximum volume','Volume step','Tick value in money']) expect(html).toContain(label);
    expect(html).toContain('Add instrument');
    expect(html).not.toContain('data-workspace-panel');
  });
});
