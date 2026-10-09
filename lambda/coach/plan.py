# -*- coding: utf-8 -*-
"""Daily plan, exam countdown and study streak. Pure functions: the
handlers pass in today's date and the saved attributes."""

import re
from datetime import date, timedelta

from .numbers import extract_numbers

# Days roll over at local midnight, not 00:00 UTC (05:30 in India).
LOCALE_UTC_OFFSET_MINUTES = {"en-IN": 330}
MAX_DAYS_LOGGED = 60
MAX_DAYS_AHEAD = 400

MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]

# Activity ids the handlers know how to start. One list per plan day; the
# day number rotates through the list. See docs/LEARNING_DESIGN.md 4.1.
FAR = [["mock", "german"],
       ["p2rounds", "listen", "german"],
       ["listen", "p1", "german"],
       ["vocab", "p2rounds", "german"]]
NEAR = [["mock", "greview"],
        ["p2rounds", "listen", "vocab", "greview"]]
FINAL = [["listen", "vocab", "greview"]]   # no full mock right before the exam
EXAM_DAY = [["p1"]]                        # a short warm-up
AFTER_EXAM = [["german", "greview"]]


def local_date(ts_utc, locale):
    """Calendar date for a UTC request timestamp in the user's locale."""
    offset = LOCALE_UTC_OFFSET_MINUTES.get(locale or "", 0)
    return (ts_utc + timedelta(minutes=offset)).date()


def days_left(today, exam_iso):
    if not exam_iso:
        return None
    try:
        return (date.fromisoformat(exam_iso) - today).days
    except ValueError:
        return None


def review_cap(today, exam_iso):
    """Latest due date for exam material: two days before the exam, so
    every item gets one more review in time. None when there's no exam
    date or it is too close for the cap to matter."""
    left = days_left(today, exam_iso)
    if left is None or left < 3:
        return None
    return date.fromisoformat(exam_iso) - timedelta(2)


def record_day(days, today):
    """Add today to the sorted ISO-date log of active days."""
    iso = today.isoformat()
    out = sorted(set(days or []) | {iso})
    return out[-MAX_DAYS_LOGGED:]


def streak(days, today):
    """Consecutive active days ending today, or yesterday if today has no
    activity yet (so the morning before practice still shows the streak)."""
    active = set(days or [])
    day = today if today.isoformat() in active else today - timedelta(1)
    count = 0
    while day.isoformat() in active:
        count += 1
        day -= timedelta(1)
    return count


def _next_occurrence(month, day, today):
    for year in (today.year, today.year + 1):
        try:
            d = date(year, month, day)
        except ValueError:
            continue
        if d >= today:
            return d
    return None


def parse_exam_date(text, today):
    """A date from Alexa's AMAZON.DATE value or from free speech:
    'october twenty eighth', 'the 28th of October', 'in three weeks'."""
    text = (text or "").strip().lower()
    if not text:
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        try:
            found = date.fromisoformat(text)
        except ValueError:
            return None
    else:
        found = None
        rel = re.search(r"\bin\b(.*)\b(day|week)s?\b", text)
        if rel:
            nums = extract_numbers(rel.group(1)) or ([1] if "a " in rel.group(1)
                                                      else [])
            if nums:
                found = today + timedelta(
                    days=nums[0] * (7 if rel.group(2) == "week" else 1))
        else:
            month = next((i + 1 for i, m in enumerate(MONTHS)
                          if re.search(r"\b%s\b" % m, text)), None)
            nums = [n for n in extract_numbers(text) if 1 <= n <= 31]
            if month and nums:
                found = _next_occurrence(month, nums[0], today)
    if found is None or not 0 <= (found - today).days <= MAX_DAYS_AHEAD:
        return None
    return found


def todays_plan(left, plan_day):
    """Activity ids for today, given days left to the exam (None = unknown)."""
    if left is None or left > 14:
        rotation = FAR
    elif left >= 4:
        rotation = NEAR
    elif left >= 1:
        rotation = FINAL
    elif left == 0:
        rotation = EXAM_DAY
    else:
        rotation = AFTER_EXAM
    return list(rotation[plan_day % len(rotation)])
