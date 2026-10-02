# -*- coding: utf-8 -*-
"""IELTS Listening Part 1 style drill: a phone booking in a chosen accent,
with spelled names, phone numbers, a date and a number - plus one
self-correction, as the real test likes to include."""

import random

from .content import SURNAMES
from .numbers import edit_distance, extract_numbers, letters_only, spoken_digits
from .speech import ACCENTS, brk, esc, spell, voice

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

SCENARIOS = [
    {"place": "Riverside Sports Centre", "purpose": "book a badminton court",
     "count_q": "How many people will be playing?", "unit": "people",
     "short_q": "How many people will be playing?", "range": (2, 6)},
    {"place": "Harbour View Hotel", "purpose": "reserve a double room",
     "count_q": "And how many nights would you like to stay?",
     "unit": "nights", "short_q": "How many nights is the booking for?",
     "range": (2, 9)},
    {"place": "Greenway Language School",
     "purpose": "enrol on the evening photography course",
     "count_q": "Just to confirm, how many weeks would you like to sign up for?",
     "unit": "weeks", "short_q": "How many weeks did the caller sign up for?",
     "range": (4, 12)},
    {"place": "Westfield Community Hall", "purpose": "hire the main hall for a party",
     "count_q": "How many guests are you expecting?", "unit": "guests",
     "short_q": "How many guests are expected?", "range": (20, 60)},
]

_DIGIT_NAMES = ["zero", "one", "two", "three", "four", "five", "six",
                "seven", "eight", "nine"]


def _say_number_group(group, accent):
    """Read a digit group the way that accent's speakers usually do."""
    words = []
    i = 0
    while i < len(group):
        d = group[i]
        name = "oh" if (d == "0" and accent != "american") else _DIGIT_NAMES[int(d)]
        if accent != "american" and i + 1 < len(group) and group[i + 1] == d:
            words.append("double " + name)
            i += 2
            continue
        words.append(name)
        i += 1
    return ", ".join(words)


def _phone(accent, rng):
    if accent == "american":
        digits = "".join(str(rng.randint(2, 9)) for _ in range(3)) + \
            "".join(str(rng.randint(0, 9)) for _ in range(7))
        groups = [digits[:3], digits[3:6], digits[6:]]
    elif accent == "australian":
        digits = "04" + "".join(str(rng.randint(0, 9)) for _ in range(8))
        groups = [digits[:4], digits[4:7], digits[7:]]
    else:
        digits = "07" + "".join(str(rng.randint(0, 9)) for _ in range(9))
        groups = [digits[:5], digits[5:8], digits[8:]]
    spoken = "<break time='350ms'/>".join(
        _say_number_group(g, accent) for g in groups)
    return digits, spoken


def _date_words(day, month, accent):
    ordinal = "<say-as interpret-as='ordinal'>%d</say-as>" % day
    if accent == "american":
        return "%s %s" % (month, ordinal)
    return "the %s of %s" % (ordinal, month)


def _cap(text):
    return text[:1].upper() + text[1:]


def make_drill(accent=None, seed=None):
    rng = random.Random(seed)
    if accent not in ACCENTS:
        accent = rng.choice(list(ACCENTS))
    acc = ACCENTS[accent]
    voices = list(acc["voices"])
    rng.shuffle(voices)
    staff, caller = voices[0], voices[1]
    lang = acc["lang"]

    sc = rng.choice(SCENARIOS)
    surname = rng.choice(SURNAMES)
    phone_digits, phone_spoken = _phone(accent, rng)
    month = rng.choice(MONTHS)
    day = rng.randint(3, 28)
    wrong_day = day + rng.choice([-2, -1, 1, 2])
    lo, hi = sc["range"]
    count = rng.randint(lo + 1, hi)
    wrong_count = count - 1 if count - 1 >= lo else count + 1
    correct_date = rng.random() < 0.5   # which detail gets the self-correction

    def s(who, text):
        return voice(who, lang, text) + brk(0.5)

    lines = [
        s(staff, "Good morning, %s. How can I help?" % esc(sc["place"])),
        s(caller, "Hi there. I'd like to %s, please." % esc(sc["purpose"])),
        s(staff, "Of course. Can I take your surname?"),
        s(caller, "Yes, it's %s. That's %s." % (esc(surname), spell(surname))),
        s(staff, "%s. Thank you. And a contact number?" % spell(surname)),
        s(caller, "Sure. It's %s." % phone_spoken),
        s(staff, "Lovely. And which date is it for?"),
    ]
    if correct_date:
        lines.append(s(caller, "%s. Oh, sorry, no. I mean %s." % (
            _cap(_date_words(wrong_day, month, accent)),
            _date_words(day, month, accent))))
    else:
        lines.append(s(caller, "%s, please." % _cap(_date_words(day, month, accent))))
    lines.append(s(staff, esc(sc["count_q"])))
    if correct_date:
        lines.append(s(caller, "%d %s." % (count, sc["unit"])))
    else:
        lines.append(s(caller, "%d. Actually, no, make that %d." % (
            wrong_count, count)))
    lines.append(s(staff, "Perfect. That's all booked for you. Goodbye."))

    items = [
        {"kind": "surname", "value": surname,
         "q": "What is the caller's surname? Spell it, letter by letter."},
        {"kind": "digits", "value": phone_digits,
         "q": "What is the contact number?"},
        {"kind": "day", "value": day, "month": month,
         "q": "What date is the booking for?"},
        {"kind": "number", "value": count, "unit": sc["unit"],
         "distractor": wrong_count if not correct_date else None,
         "q": sc["short_q"]},
    ]
    return {"accent": accent, "label": acc["label"],
            "dialog": "".join(lines), "items": items}


def check(item, text):
    """Return (correct, ssml_feedback)."""
    kind = item["kind"]
    if kind == "surname":
        got = letters_only(text)
        want = item["value"].lower()
        if got == want:
            return True, "Correct."
        if got and edit_distance(got, want) <= 1:
            return True, "Close enough, but check your spelling: %s." % spell(want)
        return False, "Not quite. It was %s, spelled %s." % (
            esc(item["value"]), spell(want))
    if kind == "digits":
        got = spoken_digits(text)
        if got == item["value"]:
            return True, "Correct."
        return False, "Not quite. The number was <say-as interpret-as='digits'>%s</say-as>." % item["value"]
    if kind == "day":
        if item["value"] in extract_numbers(text):
            return True, "Correct."
        return False, "Not quite. It was the <say-as interpret-as='ordinal'>%d</say-as> of %s. Listen for corrections like oh, sorry, I mean." % (
            item["value"], item["month"])
    if kind == "number":
        nums = extract_numbers(text)
        if nums and nums[-1] == item["value"]:
            return True, "Correct."
        extra = ""
        if item.get("distractor") is not None and item["distractor"] in nums:
            extra = " The caller changed their mind. Watch out for that trap."
        return False, "Not quite. The answer was %d %s.%s" % (
            item["value"], esc(item.get("unit", "")), extra)
    return False, ""
