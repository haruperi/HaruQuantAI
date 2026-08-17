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
 * One renderable split of the header clock.
 *
 * The profile-section clock renders the time as separate digit groups
 * (`05 : 24 : 52`) followed by a suffix (`pm UTC-6 08/10/2026`); these
 * segments carry exactly that decomposition so both the digital display and
 * its accessible label derive from one computation.
 */
export interface ClockSegments {
  hour: string;
  minute: string;
  second: string;
  meridiem: string;
  label: string;
  date: string;
}

/** Decompose a wall-clock `Date` (read via its UTC getters) into segments. */
function segmentsOf(shifted: Date, label: string): ClockSegments {
  const rawHour = shifted.getUTCHours();
  const hour12 = rawHour % 12 === 0 ? 12 : rawHour % 12;
  return {
    hour: pad2(hour12),
    minute: pad2(shifted.getUTCMinutes()),
    second: pad2(shifted.getUTCSeconds()),
    meridiem: rawHour < 12 ? "am" : "pm",
    label,
    date: `${pad2(shifted.getUTCMonth() + 1)}/${pad2(shifted.getUTCDate())}/${shifted.getUTCFullYear()}`,
  };
}

/**
 * Compute the clock segments for a UTC instant shifted to a given offset.
 *
 * Args:
 *   utcMs: UTC epoch milliseconds to display.
 *   offsetMinutes: Signed offset in minutes applied to `utcMs`.
 *   label: Zone label rendered in the suffix.
 *
 * Returns:
 *   Digit-group segments plus the suffix parts for the digital clock.
 */
export function clockSegmentsAtOffset(
  utcMs: number,
  offsetMinutes: number,
  label: string,
): ClockSegments {
  return segmentsOf(new Date(utcMs + offsetMinutes * 60_000), label);
}

/**
 * Compute the clock segments for the device-local wall time.
 *
 * Args:
 *   label: Zone label rendered in the suffix.
 *
 * Returns:
 *   Digit-group segments plus the suffix parts for the digital clock.
 */
export function localClockSegments(label: string): ClockSegments {
  // Read local wall time through the UTC getters by shifting the epoch by
  // the device offset, mirroring the fixed-offset path.
  return segmentsOf(
    new Date(Date.now() + localOffsetMinutes() * 60_000),
    label,
  );
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
  const s = clockSegmentsAtOffset(utcMs, offsetMinutes, label);
  return `${s.hour}:${s.minute}:${s.second} ${s.meridiem} ${s.label} ${s.date}`;
}
