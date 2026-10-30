export type IndicatorRowClass =
  | 'checked'
  | 'unchecked'
  | 'passed'
  | 'failed'
  | 'other';

function isFilled(value: string | null): value is string {
  return value !== null && value !== '' && value !== 'not set' && value !== 'undefined';
}

function between(label: string, opening: string, closing: string): string | null {
  const start = label.indexOf(opening);
  const end = label.indexOf(closing);
  return start >= 0 && end > start ? label.slice(start + 1, end) : null;
}

/** Pure display helpers for indicator test labels and result rows. */
export class IndicatorTestPresentation {
  static format_parameters(
    indicator_name: string,
    parameters: string | null,
    shift: number,
  ): string {
    return `${indicator_name.split('.')[0]}(${isFilled(parameters) ? parameters : ''})[${shift}]`;
  }

  static row_class(checked: boolean, result: string | null): IndicatorRowClass {
    if (!isFilled(result)) return checked ? 'checked' : 'unchecked';
    if (result.startsWith('Passed')) return 'passed';
    if (result.startsWith('Failed')) return 'failed';
    return 'other';
  }

  static raw_parameters(label: string): string | null {
    return between(label, '(', ')');
  }

  static shift_text(label: string): string | null {
    return between(label, '[', ']');
  }
}
