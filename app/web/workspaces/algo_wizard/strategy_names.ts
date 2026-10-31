const DISALLOWED_CODE_UNIT_PATTERN = /[^A-Za-z0-9 _.-]/g;
const REGEX_META_CHARS_PATTERN = /[.*+?^${}()|[\]\\]/g;

export class StrategyNames {
  static sanitize(name: string, replace_with: string = ''): string {
    return name.replace(DISALLOWED_CODE_UNIT_PATTERN, replace_with);
  }

  static unique(base_name: string, existing_names: readonly string[]): string {
    if (!existing_names.includes(base_name)) {
      return base_name;
    }

    const escapedBase = base_name.replace(REGEX_META_CHARS_PATTERN, '\\$&');
    const numberedVariantPattern = new RegExp(`^${escapedBase} \\((\\d+)\\)$`);

    let maximum = 1;
    for (const candidate of existing_names) {
      const match = numberedVariantPattern.exec(candidate);
      if (match !== null) {
        const parsed = Number.parseInt(match[1], 10);
        if (parsed > maximum) {
          maximum = parsed;
        }
      }
    }

    return `${base_name} (${maximum + 1})`;
  }
}
