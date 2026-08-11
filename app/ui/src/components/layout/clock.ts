/**
 * Pure helpers for the header clock.
 *
 * The clock renders the operator-configured `TIMEZONE` system setting, which
 * is stored as a fixed UTC-offset label (e.g. `"UTC-6"`, `"UTC"`, `"UTC+14"`).
 * Fixed offsets carry no DST information, so the offset is applied directly to
 * a UTC instant and the resulting wall time is compared against the device's
 * own offset to flag a mismatch (rendered red in the UI).
 */

/** Clamp for valid UTC offsets in minutes (-12h .. +14h, inclusive). */
const MIN_OFFSET_MINUTES = -12 * 60;
const MAX_OFFSET_MINUTES = 14 * 60;

/**
 * Parse a stored `TIMEZONE` label into signed offset minutes.
 *
 * Args:
 *   value: Canonical stored value, e.g. `"UTC"`, `"UTC-6"`, `"UTC+14"`.
 *
 * Returns:
 *   Signed offset in minutes (`UTC-6` -> -360), or `null` when the value is
 *   blank, malformed, or outside the real-world offset range.
 */
export function parseUtcOffset(value: string | undefined | null): number | null {
  if (value === undefined || value === null) return null;
  const trimmed = value.trim();
  if (!trimmed) return null;
  const match = /^(UTC|GMT|UT)([+-]\d{1,2})?$/.exec(trimmed.toUpperCase());
  if (!match) return null;
  const hours = match[2] === undefined ? 0 : Number(match[2]);
  if (!Number.isInteger(hours) || hours < -14 || hours > 14) return null;
  const minutes = hours * 60;
  if (minutes < MIN_OFFSET_MINUTES || minutes > MAX_OFFSET_MINUTES) return null;
  return minutes;
}

/**
 * Report the device-local UTC offset in minutes (sign-corrected).
 *
 * `Date.getTimezoneOffset()` returns minutes *behind* UTC (positive west of
 * Greenwich); this normalizes to the conventional sign (`UTC-6` -> -360).
 *
 * Returns:
 *   Signed local offset in minutes.
 */
export function localOffsetMinutes(): number {
  return -new Date().getTimezoneOffset();
}

/** Zero-pad a number to two digits. */
function pad2(value: number): string {
  return value < 10 ? `0${value}` : String(value);
}

/**
 * Format a wall-clock string for a UTC instant shifted to a given offset.
 *
 * The output mirrors the existing header format (lowercase 12-hour time with
 * seconds, a zone label, then `MM/DD/YYYY`). The `label` is rendered verbatim
 * (typically the stored offset string such as `"UTC-6"`).
 *
 * Args:
 *   utcMs: UTC epoch milliseconds to display.
 *   offsetMinutes: Signed offset in minutes applied to `utcMs`.
 *   label: Zone label appended after the time.
 *
 * Returns:
 *   Formatted clock string, e.g. `"07:16:31 pm UTC-6 08/10/2026"`.
 */
export function formatClockAtOffset(
  utcMs: number,
  offsetMinutes: number,
  label: string,
): string {
  const shifted = new Date(utcMs + offsetMinutes * 60_000);
  const rawHour = shifted.getUTCHours();
  const hour12 = rawHour % 12 === 0 ? 12 : rawHour % 12;
  const minute = shifted.getUTCMinutes();
  const second = shifted.getUTCSeconds();
  const meridiem = rawHour < 12 ? "am" : "pm";
  const month = pad2(shifted.getUTCMonth() + 1);
  const day = pad2(shifted.getUTCDate());
  const year = shifted.getUTCFullYear();
  return `${pad2(hour12)}:${pad2(minute)}:${pad2(second)} ${meridiem} ${label} ${month}/${day}/${year}`;
}
