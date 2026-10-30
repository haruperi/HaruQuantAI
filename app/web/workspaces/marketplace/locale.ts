/**
 * Marketplace locale code normalization helper.
 *
 * Normalizes locale flag strings for marketplace iframe queries and bridge requests.
 */
export class MarketplaceLocale {
  /**
   * Normalize an incoming locale flag string.
   *
   * Rules:
   * - null -> 'en'
   * - Trim whitespace
   * - If trimmed is empty -> 'en'
   * - If trimmed case-insensitive equals 'cz' -> 'cs'
   * - Otherwise returns trimmed original case
   *
   * @param flag Raw flag or locale identifier
   * @returns Normalized locale code
   */
  public static from_flag(flag: string | null): string {
    if (flag === null) {
      return 'en';
    }
    const trimmed = flag.trim();
    if (trimmed === '') {
      return 'en';
    }
    if (trimmed.toLowerCase() === 'cz') {
      return 'cs';
    }
    return trimmed;
  }
}
