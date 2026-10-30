import { describe, expect, it } from 'vitest';

import { IndicatorTestPresentation as Presentation } from '../../../workspaces/code_editor/indicator_test_presentation';

describe('IndicatorTestPresentation', () => {
  it.each([
    ['RSI.Main', '14', 1, 'RSI(14)[1]'],
    ['RSI', null, 0, 'RSI()[0]'],
    ['RSI', 'not set', 2, 'RSI()[2]'],
    ['RSI', ' ', 1, 'RSI( )[1]'],
    ['RSI', '', 1, 'RSI()[1]'],
    ['RSI', 'undefined', 1, 'RSI()[1]'],
    ['RSI.Main.Other', 'false', -1, 'RSI(false)[-1]'],
    [' RSI.Main', ' not set ', 1, ' RSI( not set )[1]'],
  ] as const)('formats %s / %s / %s', (name, parameters, shift, expected) => {
    expect(Presentation.format_parameters(name, parameters, shift)).toBe(expected);
  });

  it.each([
    [false, 'Passed 10/10', 'passed'],
    [true, 'Failed 1/10', 'failed'],
    [true, 'Result Passed', 'other'],
    [false, 'passed', 'other'],
    [false, null, 'unchecked'],
    [true, 'undefined', 'checked'],
    [true, null, 'checked'],
    [false, '', 'unchecked'],
    [true, '', 'checked'],
    [false, 'not set', 'unchecked'],
    [true, 'not set', 'checked'],
    [false, 'undefined', 'unchecked'],
    [true, 'Passed', 'passed'],
    [false, 'Failed', 'failed'],
    [false, 'failed', 'other'],
    [true, ' Passed', 'other'],
    [false, ' ', 'other'],
    [true, 'false', 'other'],
  ] as const)('classifies checked=%s result=%s', (checked, result, expected) => {
    expect(Presentation.row_class(checked, result)).toBe(expected);
  });

  it.each([
    ['RSI(14,close)[1]', '14,close'],
    ['RSI()[1]', ''],
    [')x(', null],
    ['RSI(14', null],
    ['RSI14)', null],
    ['', null],
    ['RSI( first )(second)', ' first '],
    ['(a(b)c)', 'a(b'],
  ])('extracts parameters from %s', (label, expected) => {
    expect(Presentation.raw_parameters(label)).toBe(expected);
  });

  it.each([
    ['RSI(14)[01]', '01'],
    ['RSI(14)', null],
    [']x[', null],
    ['RSI[1', null],
    ['RSI1]', null],
    ['RSI[]', ''],
    ['RSI[ text ][2]', ' text '],
    ['[a[b]c]', 'a[b'],
  ])('extracts shift text from %s', (label, expected) => {
    expect(Presentation.shift_text(label)).toBe(expected);
  });
});
