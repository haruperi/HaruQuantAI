/**
 * Unit tests for the header clock helpers.
 *
 * All cases are deterministic: `formatClockAtOffset` consumes a fixed UTC
 * instant, so wall-time arithmetic is verified without touching `Date.now()`
 * or the host timezone.
 */

import { describe, expect, it } from "vitest";

import {
  clockSegmentsAtOffset,
  dateTimeLocalValue,
  formatClockAtOffset,
  parseUtcOffset,
  utcMsFromLocalValue,
} from "./clock";

describe("parseUtcOffset", () => {
  it("returns 0 for bare UTC/GMT/UT labels", () => {
    expect(parseUtcOffset("UTC")).toBe(0);
    expect(parseUtcOffset("utc")).toBe(0);
    expect(parseUtcOffset("GMT")).toBe(0);
    expect(parseUtcOffset("UT")).toBe(0);
  });

  it("parses signed offsets into minutes", () => {
    expect(parseUtcOffset("UTC-6")).toBe(-360);
    expect(parseUtcOffset("UTC+14")).toBe(840);
    expect(parseUtcOffset("UTC-12")).toBe(-720);
    expect(parseUtcOffset("UTC+5")).toBe(300);
  });

  it("is case-insensitive and trims whitespace", () => {
    expect(parseUtcOffset("  utc-7 ")).toBe(-420);
  });

  it("returns null for malformed or out-of-range values", () => {
    expect(parseUtcOffset(undefined)).toBeNull();
    expect(parseUtcOffset(null)).toBeNull();
    expect(parseUtcOffset("")).toBeNull();
    expect(parseUtcOffset("America/Chicago")).toBeNull();
    expect(parseUtcOffset("UTC-15")).toBeNull();
    expect(parseUtcOffset("UTC+99")).toBeNull();
    expect(parseUtcOffset("UTC-6.5")).toBeNull();
  });
});

describe("formatClockAtOffset", () => {
  // 2026-08-10T00:00:00Z in UTC.
  const UTC_MIDNIGHT = Date.UTC(2026, 7, 10, 0, 0, 0);
  // 2026-08-10T18:16:31Z in UTC.
  const UTC_EVENING = Date.UTC(2026, 7, 10, 18, 16, 31);

  it("renders midnight at UTC-6 as previous calendar day, 6pm", () => {
    // 2026-08-10T00:00:00Z minus 6 hours = 2026-08-09T18:00:00 local.
    expect(formatClockAtOffset(UTC_MIDNIGHT, -360, "UTC-6")).toBe(
      "06:00:00 pm UTC-6 08/09/2026",
    );
  });

  it("renders UTC midnight at UTC+0 unchanged with 12-hour pm convention", () => {
    expect(formatClockAtOffset(UTC_MIDNIGHT, 0, "UTC")).toBe(
      "12:00:00 am UTC 08/10/2026",
    );
  });

  it("rolls the calendar day forward across a positive offset boundary", () => {
    // UTC evening + 8h = next day 02:16:31 local.
    expect(formatClockAtOffset(UTC_EVENING, 480, "UTC+8")).toBe(
      "02:16:31 am UTC+8 08/11/2026",
    );
  });

  it("rolls the calendar day backward across a negative offset boundary", () => {
    // UTC evening - 7h = same day 11:16:31 local.
    expect(formatClockAtOffset(UTC_EVENING, -420, "UTC-7")).toBe(
      "11:16:31 am UTC-7 08/10/2026",
    );
  });

  it("renders noon as 12:xx pm", () => {
    const utcNoon = Date.UTC(2026, 7, 10, 12, 0, 0);
    expect(formatClockAtOffset(utcNoon, 0, "UTC")).toBe(
      "12:00:00 pm UTC 08/10/2026",
    );
  });

  it("zero-pads single-digit minutes, seconds, month, and day", () => {
    const instant = Date.UTC(2026, 0, 3, 5, 7, 9); // Jan 3, 05:07:09 UTC
    expect(formatClockAtOffset(instant, 0, "UTC")).toBe(
      "05:07:09 am UTC 01/03/2026",
    );
  });

  it("renders the label verbatim", () => {
    expect(formatClockAtOffset(UTC_MIDNIGHT, -360, "CDT")).toContain("CDT");
  });
});

describe("clockSegmentsAtOffset", () => {
  const UTC_EVENING = Date.UTC(2026, 7, 10, 18, 16, 31);

  it("splits the digital clock into digit groups and a suffix", () => {
    const segments = clockSegmentsAtOffset(UTC_EVENING, -360, "UTC-6");
    expect(segments).toEqual({
      hour: "12",
      minute: "16",
      second: "31",
      meridiem: "pm",
      label: "UTC-6",
      date: "08/10/2026",
    });
  });

  it("rejoins into exactly the formatted clock string", () => {
    const s = clockSegmentsAtOffset(UTC_EVENING, -360, "UTC-6");
    expect(`${s.hour}:${s.minute}:${s.second} ${s.meridiem} ${s.label} ${s.date}`).toBe(
      formatClockAtOffset(UTC_EVENING, -360, "UTC-6"),
    );
  });
});

describe("manual clock correction values", () => {
  it("formats an instant as local input text at the selected offset", () => {
    expect(dateTimeLocalValue(Date.UTC(2026, 7, 17, 7, 30), 120)).toBe(
      "2026-08-17T09:30",
    );
  });

  it("converts valid local input back to a UTC instant", () => {
    expect(utcMsFromLocalValue("2026-08-17T09:30", 120)).toBe(
      Date.UTC(2026, 7, 17, 7, 30),
    );
  });

  it("rejects malformed and impossible local values", () => {
    expect(utcMsFromLocalValue("", 0)).toBeNull();
    expect(utcMsFromLocalValue("2026-02-30T09:30", 0)).toBeNull();
  });
});
