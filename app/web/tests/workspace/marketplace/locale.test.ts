import { describe, expect, it } from 'vitest';
import { MarketplaceLocale } from '../../../workspaces/marketplace/locale';

describe('marketplace language normalization', () => {
  const testCases: [string | null, string][] = [
    [null, 'en'],
    ['', 'en'],
    ['  ', 'en'],
    ['cz', 'cs'],
    ['CZ', 'cs'],
    [' cz ', 'cs'],
    [' EN ', 'EN'],
    ['fr', 'fr'],
  ];

  it.each(testCases)(
    'normalizes flag %j to %j',
    (input, expected) => {
      expect(MarketplaceLocale.from_flag(input)).toBe(expected);
    },
  );
});
