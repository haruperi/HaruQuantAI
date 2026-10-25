import { renderToString } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { SymbolsModal } from '../../../../../../app/plugins/data_source/Catalogs/Symbols/SymbolsModal';

describe('symbol form contract', () => {
  it('exposes independent contract, pip, precision and margin fields without guessing sizes', () => {
    const html = renderToString(<SymbolsModal mode="add" selected={[]} brokers={[{ id: '-1', name: 'Default', postfix: '', timezone: 'UTC' }]} onClose={() => {}} onSaved={() => {}}/>);
    for (const label of ['Contract size','Pip size','Margin rate (fraction)','Price decimals','Minimum volume','Maximum volume','Volume step','Tick value in money']) expect(html).toContain(label);
    expect(html).toContain('Add symbol');
    expect(html).not.toContain('data-workspace-panel');
  });
});
