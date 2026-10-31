import { expect, test } from 'vitest';
import { StrategyNames } from '../../../workspaces/algo_wizard/strategy_names';

test('StrategyNames.sanitize', () => {
  const cases: ReadonlyArray<
    readonly [input: string, replaceWith: string | undefined, expected: string]
  > = [
    ['A/B:C', undefined, 'ABC'],
    ['A/B:C', '_', 'A_B_C'],
    ['éΑA 1_.-', undefined, 'A 1_.-'],
    ['  A  ', undefined, '  A  '],
    ['///', undefined, ''],
    ['A/B', '$&', 'A/B'],
    ['A😀B', '_', 'A__B'],
  ];

  for (const [input, replaceWith, expected] of cases) {
    const actual =
      replaceWith === undefined
        ? StrategyNames.sanitize(input)
        : StrategyNames.sanitize(input, replaceWith);
    expect(actual).toBe(expected);
  }
});

test('StrategyNames.unique', () => {
  const cases: ReadonlyArray<
    readonly [
      baseName: string,
      existingNames: readonly string[],
      expected: string,
    ]
  > = [
    ['A', [], 'A'],
    ['A', ['A (9)'], 'A'],
    ['A', ['A'], 'A (2)'],
    ['A', ['A', 'A (2)', 'A (9)'], 'A (10)'],
    ['A', ['A', 'A (0)', 'A (01)'], 'A (2)'],
    ['A.B', ['A.B', 'AxB (90)', 'A.B (3)'], 'A.B (4)'],
    ['A', ['a'], 'A'],
    ['A', ['A', `A (${'9'.repeat(400)})`], 'A (Infinity)'],
  ];

  for (const [baseName, existingNames, expected] of cases) {
    expect(StrategyNames.unique(baseName, existingNames)).toBe(expected);
  }
});
