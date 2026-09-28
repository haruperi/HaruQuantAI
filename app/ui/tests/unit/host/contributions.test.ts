import { describe, expect, it } from 'vitest';
import { validateContributions, type UIContribution } from '../../../app/host/contributions';

const owner: UIContribution = { id: 'test.owner', kind: 'workspace', version: '1.0.0', slots: ['test.slot'] };
const child: UIContribution = { id: 'test.child', kind: 'plugin', version: '1.0.0', owner: owner.id, slot: 'test.slot', contractVersion: '1.0.0' };

describe('owner attachment validation', () => {
  it('accepts an empty host, empty owner, and compatible child without executing loaders', () => {
    const load = async () => { throw new Error('must remain lazy'); };
    expect(validateContributions([])).toEqual([]);
    expect(validateContributions([owner])).toEqual([owner]);
    expect(validateContributions([owner, { ...child, load }])).toHaveLength(2);
  });
  it('rejects orphan and wrong-slot children while preserving unrelated owners', () => {
    expect(validateContributions([child])).toEqual([]);
    expect(validateContributions([owner, { ...child, slot: 'test.wrong' }])).toEqual([owner]);
    expect(validateContributions([owner, { ...child, owner: 'test.absent' }])).toEqual([owner]);
  });
  it('rejects ambiguous owner identities and their children', () => {
    expect(validateContributions([owner, { ...owner }, child])).toEqual([]);
  });
  it('rejects conflicting route owners and their attachments', () => {
    const navigation = { id: 'test', path: '/same', label: 'Test', icon: () => null, order: 1 };
    expect(validateContributions([{ ...owner, navigation }, { ...owner, id: 'test.other', navigation }, child])).toEqual([]);
  });
});
