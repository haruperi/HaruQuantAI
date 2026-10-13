# BarAndTime — building block catalog

> Reference enumeration of the `BarAndTime` building-block snippets (37 classes): bar-relative time
> values/conditions, current (real broker) time values/conditions, trading-day and week-of-month
> flags, and two always-true/false constants. This is a lookup table; for the general building-block
> model see [`README.md`](README.md).

## How this file is organized

All classes live in `SQ.Blocks.BarAndTime`. Value blocks (`ValueBlock`) return a number (hour, day,
month, minute, raw time/date); condition blocks (`ConditionBlock`) return a boolean, usually
comparing a bar's or the current time against a configured value. "Bar-relative" blocks read the
time of a specific historical bar (via `ChartData Chart` + `int Shift`, omitted from the tables
below as boilerplate); "Current" blocks read the live broker-time clock instead and take no chart
parameter. Enum-style parameters (`Day`, `Month`) are rendered in the UI as a named dropdown
(`Sunday=0…Saturday=6`, `January=1…December=12`) but stored as `int`.

## Bar-relative time

| Display name | Class | Parameters | Description |
|---|---|---|---|
| Hour[Shift] | `BarHour` | — | Hour (0-23) of the given bar. |
| Bar[Shift] hour = Hour | `BarHourIs` | Hour: 0-23, default 0 | True if the bar's hour equals `Hour`. |
| Bar[Shift] hour > Hour | `BarHourIsBigger` | Hour: 0-23, default 0 | True if the bar's hour is greater than `Hour`. |
| Bar[Shift] hour < Hour | `BarHourIsSmaller` | Hour: 0-23, default 0 | True if the bar's hour is less than `Hour`. |
| DayOfWeek[Shift] | `BarDayOfWeek` | — | Day of week of the bar (Sunday=0 … Saturday=6). |
| Bar[Shift] day of week = Day | `BarDayOfWeekIs` | Day: enum Sunday=0…Saturday=6, default 0 | True if the bar's day of week equals `Day`. |
| Bar[Shift] day of week != Day | `BarDayOfWeekIsNot` | Day: enum Sunday=0…Saturday=6, default 0 | True if the bar's day of week is not `Day`. |
| Month[Shift] | `BarMonth` | — | Month of the bar (1=January … 12=December). |
| Bar[Shift] month = Month | `BarMonthIs` | Month: enum January=1…December=12, default 1 | True if the bar's month equals `Month`. |
| Bar[Shift] month != Month | `BarMonthIsNot` | Month: enum January=1…December=12, default 1 | True if the bar's month is not `Month`. |
| Minute[Shift] | `BarMinute` | — | Minute (0-59) of the given bar. |
| Bar[Shift] minute is Minute | `BarMinuteIs` | Minute: 0-59, default 0 | True if the bar's minute equals `Minute`. |
| Time[Shift] | `BarTime` | — | Raw time of the given bar. |
| Bar[Shift] time is Hour:Minute | `BarTimeIs` | Hour: 0-23, default 0; Minute: 0-59, default 0 | True if the bar's time equals `Hour:Minute`. |
| BarDate | `BarDate` | — | Date of the bar (broker time), comparable with `GetDate()`. |
| DayOfMonth[Shift] | `BarDayOfMonth` | — | Day of the month (1-31) of the given bar. |
| WeekOfMonth[Shift] | `BarWeekOfMonth` | — | Week of the month (1-6) of the given bar. |
| CurrentBar | `CurrentBar` | — | Index of the current bar. |

## Current (real) time

Read the live broker-time clock rather than a specific bar; these have no `Shift`/`Chart` parameter.

| Display name | Class | Parameters | Description |
|---|---|---|---|
| CurrentHour | `CurrentHour` | — | Current hour (broker time). |
| Current hour is Hour | `CurrentHourIs` | Hour: 0-23, default 0 | True if the current hour equals `Hour`. |
| CurrentDayOfWeek | `CurrentDayOfWeek` | — | Current day of week (broker time), Sunday=0 … Saturday=6. |
| Current day of week is Day | `CurrentDayOfWeekIs` | Day: enum Sunday=0…Saturday=6, default 0 | True if the current day of week equals `Day`. |
| CurrentMonth | `CurrentMonth` | — | Current month (broker time), 1=January … 12=December. |
| Current month is Month | `CurrentMonthIs` | Month: enum January=1…December=12, default 1 | True if the current month equals `Month`. |
| CurrentMinute | `CurrentMinute` | — | Current minute (broker time). |
| Current minute is Minute | `CurrentMinuteIs` | Minute: 0-59, default 0 | True if the current minute equals `Minute`. |
| CurrentTime | `CurrentTime` | — | Current time (broker time). |
| Current time is Hour:Minute | `CurrentTimeIs` | Hour: 0-23, default 0; Minute: 0-59, default 0 | True if the current time equals `Hour:Minute`. |
| CurrentDate | `CurrentDate` | — | Current date (broker time), comparable with `GetDate()`. |
| CurrentWeekOfMonth | `CurrentWeekOfMonth` | — | Current week of the month (broker time), 1-6. |

## Trading-day / week-of-month flags

| Display name | Class | Parameters | Description |
|---|---|---|---|
| IsBarOpen | `IsBarOpen` | — | True exactly once per bar, on bar open; used to gate a rule to fire only at the start of a new bar. |
| Is month first trading day | `IsMonthFirstTradingDay` | IncludeWeekends: bool, default false | True on the first trading day of the month (weekends excluded unless `IncludeWeekends` is set). |
| Is month last trading day | `IsMonthLastTradingDay` | IncludeWeekends: bool, default false | True on the last trading day of the month (weekends excluded unless `IncludeWeekends` is set). |
| First week of month | `FirstWeekOfMonth` | — | True if the current bar falls in week 1 of the month. |
| Last week of month | `LastWeekOfMonth` | — | True if the current bar falls in the same week-of-month as the last day of the month. |

## Constants

| Display name | Class | Description |
|---|---|---|
| Always True | `AlwaysTrue` | Condition that is always true. |
| Always False | `AlwaysFalse` | Condition that is always false. |

## Related

- Building-block model overview: [`README.md`](README.md)
- Comparison/logical operators these time conditions are combined with (AND/OR/Not): [`comparisons.md`](comparisons.md)
- Price levels these time windows are often paired with: [`price.md`](price.md)
- Strategy/account state (bars since entry, open positions): [`strategy-control.md`](strategy-control.md)
