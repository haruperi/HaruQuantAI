import { describe, expect, it } from 'vitest';
import { makeRenameValue } from '../../../../app/plugins/databank/DatabankRename/ui/DatabankRenamePopupCtrl';
describe('existing mock rename payload contract', () => {
  it('trims a single name and retains the original for whitespace input', () => {
    expect(makeRenameValue(1, 'Original', '  Updated  ', 'unused', 'unused')).toEqual({ name: 'Updated' });
    expect(makeRenameValue(1, 'Original', '   ', 'unused', 'unused')).toEqual({ name: 'Original' });
  });
  it('keeps multi-selection affixes independent of the single-name field', () => {
    expect(makeRenameValue(2, 'Original', 'ignored', '  pre- ', ' -post  ')).toEqual({ prefix: 'pre-', postfix: '-post' });
    expect(makeRenameValue(3, 'Original', 'ignored', '  ', '  ')).toEqual({ prefix: '', postfix: '' });
  });
});
