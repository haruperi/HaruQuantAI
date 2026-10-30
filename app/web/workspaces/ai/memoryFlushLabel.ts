/**
 * Memory flush interval display label formatting helper.
 *
 * Preserves donor behavior from internal/web/SQAI/workspace-panel.js.
 */
export class MemoryFlushLabel {
  /**
   * Return a human-readable description for the memory flush configuration.
   *
   * @param memoryEnabled Whether AI memory retention is enabled.
   * @param minutes The configured flush interval in minutes.
   * @returns Formatted description label:
   *   - "off" if memory is disabled or minutes is negative
   *   - "after every turn" if memory is enabled and minutes is 0
   *   - "every <minutes> min at most" using native string conversion otherwise
   */
  static describe(memoryEnabled: boolean, minutes: number): string {
    if (!memoryEnabled || minutes < 0) {
      return "off";
    }
    if (minutes === 0) {
      return "after every turn";
    }
    return `every ${minutes} min at most`;
  }
}
