"""Unit tests for HQTime temporal operations."""

from datetime import UTC, datetime

from app.services.include.time import HQTime


def test_hqtime_constants() -> None:
    """Verify constants."""
    assert HQTime.DAY_MILLIS == 86_400_000
    assert HQTime.MONDAY == 1
    assert HQTime.FRIDAY == 5
    assert HQTime.SUNDAY == 7
    HQTime.init()


def test_extractors() -> None:
    """Verify component extraction from epoch milliseconds."""
    # 2026-10-14 15:30:45.123 UTC (Wednesday)
    ms = HQTime.to_long(2026, 10, 14, 15, 30, 45) + 123

    assert HQTime.get_year(ms) == 2026
    assert HQTime.get_full_year(ms) == 2026
    assert HQTime.get_month(ms) == 10
    assert HQTime.get_month_original(ms) == 9  # 0-indexed
    assert HQTime.get_day(ms) == 14
    assert HQTime.get_hour(ms) == 15
    assert HQTime.get_minute(ms) == 30
    assert HQTime.get_second(ms) == 45
    assert HQTime.get_millis(ms) == 123
    assert HQTime.get_millisecond(ms) == 123
    assert HQTime.get_day_of_week(ms) == 3  # Wednesday
    assert HQTime.get_day_of_week_original(ms) == 4  # Calendar (Wed = 4)
    assert HQTime.get_day_of_year(ms) == 287
    assert HQTime.get_days_in_month(ms) == 31
    assert HQTime.get_week_of_month(ms) == 2
    assert HQTime.get_week_of_year(ms) == 42

    # Sunday test for get_day_of_week_original
    sun_ms = HQTime.to_long(2026, 10, 18, 12, 0, 0)
    assert HQTime.get_day_of_week(sun_ms) == 7
    assert HQTime.get_day_of_week_original(sun_ms) == 1  # Sunday in Calendar

    # get_ymd
    assert HQTime.get_ymd(ms) == 20261014
    assert HQTime.get_ymd(2026, 10, 14) == 20261014

    # get_hhmm
    assert HQTime.get_hhmm(ms) == 1530
    assert HQTime.get_hhmm("15:30") == 1530
    assert HQTime.get_hhmm("08:05") == 805

    # get_hms & to_hours
    assert abs(HQTime.get_hms(1, 30, 0) - 1.5) < 1e-6
    assert HQTime.to_hours(ms) == ms // 3_600_000


def test_day_boundaries() -> None:
    """Verify start and end of day normalizations."""
    ms = HQTime.to_long(2026, 10, 14, 15, 30, 45) + 500

    start_ms = HQTime.correct_day_start(ms)
    assert HQTime.get_date_in_ms(ms) == start_ms
    assert HQTime.get_hour(start_ms) == 0
    assert HQTime.get_minute(start_ms) == 0
    assert HQTime.get_second(start_ms) == 0
    assert HQTime.get_millis(start_ms) == 0

    end_ms = HQTime.correct_day_end(ms)
    assert HQTime.get_hour(end_ms) == 23
    assert HQTime.get_minute(end_ms) == 59
    assert HQTime.get_second(end_ms) == 59
    assert HQTime.get_millis(end_ms) == 999

    mt_end_ms = HQTime.correct_day_end_mt(ms)
    assert HQTime.get_hour(mt_end_ms) == 23
    assert HQTime.get_minute(mt_end_ms) == 59
    assert HQTime.get_second(mt_end_ms) == 0
    assert HQTime.get_millis(mt_end_ms) == 0


def test_calendar_arithmetic() -> None:
    """Verify adding and subtracting calendar units."""
    ms = HQTime.to_long(2026, 1, 31, 10, 0, 0)

    # Adding 1 month from Jan 31 clamps to Feb 28
    feb_ms = HQTime.add_months(ms, 1)
    assert HQTime.get_month(feb_ms) == 2
    assert HQTime.get_day(feb_ms) == 28

    # Adding years
    assert HQTime.get_year(HQTime.add_years(ms, 2)) == 2028

    # Adding days, weeks, hours, minutes, seconds
    assert HQTime.add_days(ms, 2) == ms + 2 * 86_400_000
    assert HQTime.add_weeks(ms, 1) == ms + 7 * 86_400_000
    assert HQTime.add_hours(ms, 5) == ms + 5 * 3_600_000
    assert HQTime.add_minutes(ms, 30) == ms + 30 * 60_000
    assert HQTime.add_seconds(ms, 45) == ms + 45 * 1_000

    # Generic add and minus
    assert HQTime.add(ms, 5, 3) == HQTime.add_days(ms, 3)
    assert HQTime.minus(ms, 5, 3) == HQTime.add_days(ms, -3)
    assert HQTime.add(ms, 1, 1) == HQTime.add_years(ms, 1)
    assert HQTime.add(ms, 2, 2) == HQTime.add_months(ms, 2)
    assert HQTime.add(ms, 3, 1) == HQTime.add_weeks(ms, 1)
    assert HQTime.add(ms, 10, 2) == HQTime.add_hours(ms, 2)
    assert HQTime.add(ms, 12, 10) == HQTime.add_minutes(ms, 10)
    assert HQTime.add(ms, 13, 20) == HQTime.add_seconds(ms, 20)
    assert HQTime.add(ms, 99, 100) == ms + 100


def test_component_setters() -> None:
    """Verify component setters."""
    ms = HQTime.to_long(2026, 10, 14, 15, 30, 45)

    assert HQTime.get_hour(HQTime.set_hour(ms, 8)) == 8
    assert HQTime.get_minute(HQTime.set_minute(ms, 12)) == 12
    assert HQTime.get_second(HQTime.set_second(ms, 5)) == 5
    assert HQTime.get_millis(HQTime.set_milliseconds(ms, 789)) == 789
    assert HQTime.get_day(HQTime.set_day_of_month(ms, 20)) == 20
    assert HQTime.get_month(HQTime.set_month_of_year(ms, 11)) == 11

    # set_day_of_week
    t_fri = HQTime.set_day_of_week(ms, HQTime.FRIDAY)
    assert HQTime.get_day_of_week(t_fri) == HQTime.FRIDAY
    assert HQTime.get_day(t_fri) == 16

    # set_first_day_of_week
    t_mon = HQTime.set_first_day_of_week(ms)
    assert HQTime.get_day_of_week(t_mon) == HQTime.MONDAY
    assert HQTime.get_day(t_mon) == 12
    assert HQTime.get_hour(t_mon) == 0

    # set_hhmm & set_time_to_ts_time
    t_hhmm = HQTime.set_hhmm(ms, 945)
    assert HQTime.get_hour(t_hhmm) == 9
    assert HQTime.get_minute(t_hhmm) == 45
    assert HQTime.get_second(t_hhmm) == 0
    assert HQTime.set_time_to_ts_time(ms, 1420) == HQTime.set_hhmm(ms, 1420)

    # set_time
    t_time = HQTime.set_time(ms, 11, 22, 33, 444)
    assert HQTime.get_hour(t_time) == 11
    assert HQTime.get_minute(t_time) == 22
    assert HQTime.get_second(t_time) == 33
    assert HQTime.get_millis(t_time) == 444


def test_differences_and_comparisons() -> None:
    """Verify difference and comparison calculations."""
    t1 = HQTime.to_long(2026, 10, 14, 10, 0, 0)
    t2 = HQTime.to_long(2026, 10, 17, 12, 30, 0)

    assert HQTime.get_diff_in_days(t1, t2) == 3
    assert HQTime.get_days_between(t1, t2) == 3
    assert HQTime.get_days_between(t2, t1) == -3
    assert HQTime.get_minutes_between(t1, t2) == 3 * 1440 + 150
    assert HQTime.get_weeks_between(t1, t1 + 14 * 86_400_000) == 2

    # Month and year diffs
    t_next_year = HQTime.to_long(2027, 2, 14, 10, 0, 0)
    assert HQTime.get_months_between(t1, t_next_year) == 4
    assert HQTime.get_years_between(t1, t_next_year) == 1

    # Same day, month, week
    assert HQTime.is_same_day(t1, t1 + 3600_000) is True
    assert HQTime.is_same_day(t1, t2) is False
    assert HQTime.is_same_month(t1, t2) is True
    assert HQTime.is_same_month(t1, t_next_year) is False
    assert HQTime.is_same_week(t1, t1 + 86_400_000) == 1
    assert HQTime.is_same_week(t1, t1 + 10 * 86_400_000) == 0


def test_formatting_and_parsing() -> None:
    """Verify string serialization and parsing."""
    ms = HQTime.to_long(2026, 10, 14, 15, 30, 45)

    assert HQTime.to_full_datetime_string(ms) == "2026.10.14 15:30:45"
    assert HQTime.to_full_date_minute_string(ms) == "2026.10.14 15:30"
    assert HQTime.to_date_minute_string(ms) == "2026.10.14 15:30"
    assert HQTime.to_date_string(ms) == "2026.10.14"
    assert HQTime.to_ui_date_string(ms) == "2026.10.14"
    assert HQTime.format_date(ms) == "2026.10.14"
    assert HQTime.format_date_quick(ms) == "2026.10.14"
    assert HQTime.format_datetime(ms) == "2026.10.14 15:30:45"
    assert HQTime.format_time(ms) == "15:30:45"
    assert HQTime.to_hhmm_string(ms) == "15:30"
    assert HQTime.to_full_time(ms) == "15:30:45.000"

    # get_log_time
    log_time = HQTime.get_log_time(include_date=True, include_millis=True)
    assert len(log_time) > 10

    # Parsing
    parsed_ms = HQTime.parse_date_to_millis("2026.10.14 15:30:45")
    assert parsed_ms == ms
    parsed_date_only = HQTime.parse_date_to_millis("2026-10-14")
    assert parsed_date_only == HQTime.to_long(2026, 10, 14)
    custom_parsed = HQTime.parse_to_millis("14/10/2026 15:30:45", "dd/MM/yyyy HH:mm:ss")
    assert custom_parsed == ms

    # to_time & to_date
    dt = HQTime.to_time(ms)
    assert isinstance(dt, datetime)
    assert dt == datetime(2026, 10, 14, 15, 30, 45, tzinfo=UTC)
    assert HQTime.to_date(ms) == dt


def test_specialized_temporal_utilities() -> None:
    """Verify specialized market and calendar operations."""
    assert HQTime.hhmm_to_minutes(1430) == 14 * 60 + 30
    assert HQTime.minutes_to_hhmm(870) == 1430

    ms = HQTime.to_long(2026, 10, 14, 9, 30, 0)
    assert HQTime.get_time_as_ts_time(ms) == 930
    assert HQTime.to_number_time(ms) == 930
    assert HQTime.get_ts_diff_in_minutes(930, 1015) == 45

    # terminal DOW conversion
    assert HQTime.dow_to_metatrader(HQTime.SUNDAY) == 0
    assert HQTime.dow_to_metatrader(HQTime.MONDAY) == 1
    assert HQTime.dow_to_metatrader(HQTime.SATURDAY) == 6

    # DOW to string
    assert HQTime.dow_to_string(HQTime.MONDAY) == "Monday"
    assert HQTime.dow_to_string(HQTime.FRIDAY) == "Friday"
    assert HQTime.dow_to_string(99) == ""

    # times_in_same_minute
    assert HQTime.times_in_same_minute(ms, ms + 15_000) is True
    assert HQTime.times_in_same_minute(ms, ms + 65_000) is False
    assert HQTime.times_in_same_minute(10, 10) is True

    # get_datetime
    assert HQTime.get_datetime(ms) == 202610140930

    # get_local_current_time_in_ms
    assert HQTime.get_local_current_time_in_ms() > 0

    # get_duration_text
    duration = 90_061_000  # 1 day, 1 hour, 1 min, 1 sec
    text = HQTime.get_duration_text(duration)
    assert "1d" in text and "1h" in text and "1m" in text and "1s" in text
