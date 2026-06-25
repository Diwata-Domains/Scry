from datetime import datetime, timezone

from scry.scheduler import cron_matches


def test_wildcard():
    assert cron_matches("* * * * *", datetime(2026, 6, 25, 14, 30, tzinfo=timezone.utc))


def test_hourly_top_of_hour():
    assert cron_matches("0 * * * *", datetime(2026, 6, 25, 14, 0, tzinfo=timezone.utc))
    assert not cron_matches("0 * * * *", datetime(2026, 6, 25, 14, 30, tzinfo=timezone.utc))


def test_step_and_range_and_list():
    assert cron_matches("*/15 * * * *", datetime(2026, 6, 25, 14, 30, tzinfo=timezone.utc))
    assert not cron_matches("*/15 * * * *", datetime(2026, 6, 25, 14, 7, tzinfo=timezone.utc))
    assert cron_matches("0 9-17 * * *", datetime(2026, 6, 25, 12, 0, tzinfo=timezone.utc))
    assert cron_matches("0 0 * * 1,3,5", datetime(2026, 6, 26, 0, 0, tzinfo=timezone.utc))  # 2026-06-26 is a Friday


def test_dow_sunday_is_zero():
    # 2026-06-28 is a Sunday -> cron dow 0
    assert cron_matches("0 0 * * 0", datetime(2026, 6, 28, 0, 0, tzinfo=timezone.utc))
