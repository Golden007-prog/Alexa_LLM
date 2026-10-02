# -*- coding: utf-8 -*-
"""IELTS Listening Part 1 style drill: a phone booking in a chosen accent,
with a spelled surname, a phone number, a date, a number and a spoken
multiple-choice question. Every call has exactly one self-correction
("oh, sorry, I mean..."), as the real test likes to include, and the
multiple-choice line names a rejected option as a distractor.

All scenarios and dialogue are original."""

import random
import re

from .content import SURNAMES
from .numbers import edit_distance, extract_numbers, letters_only, spoken_digits
from .speech import ACCENTS, brk, esc, spell, voice

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

DEFAULT_OFFER = "We have three options: {a}, {b}, or {c}."
DEFAULT_PICK = "Hmm, I don't think {rejected} would suit me. I'll go for {chosen}, please."


def _sc(place, purpose, count_q, unit, short_q, lo_hi, noun, choice_q,
        options, offer=DEFAULT_OFFER, pick=DEFAULT_PICK):
    return {"place": place, "purpose": purpose, "count_q": count_q,
            "unit": unit, "short_q": short_q, "range": lo_hi,
            "choice": {"noun": noun, "q": choice_q, "options": options,
                       "offer": offer, "pick": pick}}


SCENARIOS = [
    _sc("Riverside Sports Centre", "book a badminton court",
        "How many people will be playing?", "people",
        "How many people will be playing?", (2, 6),
        "court", "Which court does the caller book?",
        ["the indoor court", "the outdoor court", "the practice hall"]),
    _sc("Harbour View Hotel", "reserve a double room",
        "And how many nights would you like to stay?", "nights",
        "How many nights is the booking for?", (2, 9),
        "room", "Which room does the caller choose?",
        ["a garden view room", "a sea view room", "a city view room"]),
    _sc("Greenway Language School", "enrol on the evening photography course",
        "Just to confirm, how many weeks would you like to sign up for?",
        "weeks", "How many weeks did the caller sign up for?", (4, 12),
        "class time", "Which class time does the caller choose?",
        ["Monday evenings", "Wednesday evenings", "Saturday mornings"],
        offer="The course runs on {a}, {b}, or {c}."),
    _sc("Westfield Community Hall", "hire the main hall for a party",
        "How many guests are you expecting?", "guests",
        "How many guests are expected?", (20, 60),
        "catering", "Which catering does the caller choose?",
        ["a buffet", "a sit-down dinner", "snacks only"],
        offer="For food, we offer {a}, {b}, or {c}."),
    _sc("Oakfield Medical Centre", "make an appointment with a doctor",
        "And how many days have you had the cough?", "days",
        "How many days has the caller had the cough?", (2, 9),
        "appointment", "Which appointment does the caller take?",
        ["a morning appointment", "an afternoon appointment",
         "a phone consultation"],
        offer="I can offer {a}, {b}, or {c}."),
    _sc("Peak Fitness Gym", "join the gym",
        "How many months would you like to sign up for?", "months",
        "How many months is the membership for?", (3, 12),
        "membership", "Which membership does the caller choose?",
        ["the off-peak membership", "the standard membership",
         "the premium membership"]),
    _sc("City Cycle Hire", "hire some bikes for the weekend",
        "How many bikes do you need?", "bikes",
        "How many bikes does the caller need?", (2, 6),
        "bikes", "Which type of bike does the caller choose?",
        ["mountain bikes", "city bikes", "electric bikes"],
        offer="We have {a}, {b}, or {c}."),
    _sc("Coastline Tours", "book a boat tour",
        "How many tickets would you like?", "tickets",
        "How many tickets does the caller want?", (2, 8),
        "tour", "Which tour does the caller book?",
        ["the morning tour", "the sunset tour", "the full-day tour"],
        offer="There's {a}, {b}, or {c}."),
    _sc("Maple Lodge Lettings", "rent a flat for the summer",
        "How many weeks would you need it for?", "weeks",
        "How many weeks does the caller need the flat for?", (3, 10),
        "flat", "Which flat does the caller choose?",
        ["the studio flat", "the one-bedroom flat", "the two-bedroom flat"],
        offer="We have {a}, {b}, or {c} available."),
    _sc("Central Station Lost Property", "report a lost bag",
        "And how many days ago did you lose it?", "days",
        "How many days ago was the bag lost?", (2, 6),
        "bag", "Which bag did the caller lose?",
        ["a black backpack", "a brown suitcase", "a blue sports bag"],
        offer="Three bags were handed in this week: {a}, {b}, and {c}.",
        pick="It's not {rejected}. Mine is {chosen}."),
    _sc("Northgate Library", "get a library card",
        "How many books would you like to borrow today?", "books",
        "How many books does the caller want to borrow?", (2, 6),
        "card", "Which card does the caller choose?",
        ["the basic card", "the student card", "the family card"],
        offer="There's {a}, {b}, or {c}."),
    _sc("Kitchen Corner Cookery School", "book a cooking class",
        "How many people is the booking for?", "people",
        "How many people is the cooking class for?", (2, 5),
        "class", "Which class does the caller book?",
        ["Italian cooking", "Thai cooking", "baking"],
        offer="This month we have {a}, {b}, or {c}."),
    _sc("AutoCare Garage", "book a car service",
        "And how many years old is the car?", "years",
        "How old is the car, in years?", (2, 9),
        "service", "Which service does the caller book?",
        ["a basic service", "a full service", "an oil change only"],
        offer="We do {a}, {b}, or {c}."),
    _sc("Regent Concert Hall", "buy tickets for Saturday's concert",
        "How many tickets would you like?", "tickets",
        "How many concert tickets does the caller want?", (2, 6),
        "seats", "Which seats does the caller choose?",
        ["seats in the stalls", "seats in the circle", "seats in the balcony"],
        offer="We still have {a}, {b}, or {c}."),
]

LETTERS = ["A", "B", "C"]
# Single letters are recognised badly on their own; accept what Alexa
# usually hears instead (docs/LEARNING_DESIGN.md 4.6).
LETTER_WORDS = [{"a", "ay", "eh", "option a", "letter a"},
                {"b", "be", "bee", "option b", "letter b"},
                {"c", "see", "sea", "si", "option c", "letter c"}]
SELF_CORRECTIONS = ("Oh, sorry, no. I mean", "Actually, no, make that")
LONG_SURNAME = 9            # letters; used when spelling is a weak spot

_DIGIT_NAMES = ["zero", "one", "two", "three", "four", "five", "six",
                "seven", "eight", "nine"]


def pick_accent(recent, rng):
    """Fair rotation: an accent not used in the recent list, else the one
    used longest ago."""
    recent = list(recent or [])
    fresh = [a for a in ACCENTS if a not in recent]
    if fresh:
        return rng.choice(fresh)
    return recent[0]


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


def choice_question(item):
    opts = item["options"]
    return "%s A, %s. B, %s. Or C, %s." % (item["q"], opts[0], opts[1], opts[2])


def make_drill(accent=None, seed=None, recent=None, hard_spelling=False,
               scenario=None):
    rng = random.Random(seed)
    if accent not in ACCENTS:
        accent = pick_accent(recent, rng)
    acc = ACCENTS[accent]
    voices = list(acc["voices"])
    rng.shuffle(voices)
    staff, caller = voices[0], voices[1]
    lang = acc["lang"]

    sc = SCENARIOS[scenario] if scenario is not None else rng.choice(SCENARIOS)
    names = [n for n in SURNAMES if len(n) >= LONG_SURNAME] if hard_spelling \
        else SURNAMES
    surname = rng.choice(names)
    phone_digits, phone_spoken = _phone(accent, rng)
    month = rng.choice(MONTHS)
    day = rng.randint(3, 28)
    wrong_day = day + rng.choice([-2, -1, 1, 2])
    lo, hi = sc["range"]
    count = rng.randint(lo + 1, hi)
    wrong_count = count - 1 if count - 1 >= lo else count + 1
    correct_date = rng.random() < 0.5   # which detail gets the self-correction
    ch = sc["choice"]
    chosen = rng.randrange(3)
    rejected = rng.choice([i for i in range(3) if i != chosen])
    opts = ch["options"]

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
        lines.append(s(caller, "%s. %s %s." % (
            _cap(_date_words(wrong_day, month, accent)), SELF_CORRECTIONS[0],
            _date_words(day, month, accent))))
    else:
        lines.append(s(caller, "%s, please." % _cap(_date_words(day, month, accent))))
    lines.append(s(staff, esc(sc["count_q"])))
    if correct_date:
        lines.append(s(caller, "%d %s." % (count, sc["unit"])))
    else:
        lines.append(s(caller, "%d. %s %d." % (wrong_count, SELF_CORRECTIONS[1],
                                               count)))
    lines.append(s(staff, esc(ch["offer"].format(a=opts[0], b=opts[1],
                                                 c=opts[2]))))
    lines.append(s(caller, esc(ch["pick"].format(rejected=opts[rejected],
                                                 chosen=opts[chosen]))))
    lines.append(s(staff, "Perfect. That's all sorted for you. Goodbye."))

    items = [
        {"kind": "surname", "value": surname,
         "q": "What is the caller's surname? Spell it, letter by letter."},
        {"kind": "digits", "value": phone_digits,
         "q": "What is the contact number?"},
        {"kind": "day", "value": day, "month": month,
         "q": "What date is it for?"},
        {"kind": "number", "value": count, "unit": sc["unit"],
         "distractor": wrong_count if not correct_date else None,
         "q": sc["short_q"]},
        {"kind": "choice", "value": chosen, "options": opts,
         "distractor": rejected, "q": ch["q"]},
    ]
    preview = ("the surname, the phone number, the date, the number of %s, "
               "and which %s" % (sc["unit"], ch["noun"]))
    return {"accent": accent, "label": acc["label"], "preview": preview,
            "dialog": "".join(lines), "items": items}


def _tokens(text):
    return re.findall(r"[a-z]+", (text or "").lower().replace("-", " "))


def _distinctive(options):
    """Per option, the words no other option shares: 'the sunset tour' ->
    {'sunset'}. Saying any of them names that option."""
    sets = [set(_tokens(o)) - {"a", "an", "the", "in", "only"} for o in options]
    return [s - set().union(*(o for j, o in enumerate(sets) if j != i))
            for i, s in enumerate(sets)]


def _choice_answer(item, text):
    """Index of the option the learner picked, or None if unclear."""
    tokens = _tokens(text)
    words = set(tokens)
    scores = [len(d & words) for d in _distinctive(item["options"])]
    best = max(scores)
    if best:
        return scores.index(best) if scores.count(best) == 1 else None
    phrases = words | {" ".join(tokens[i:i + 2])
                       for i in range(len(tokens) - 1)}
    found = [i for i, letter in enumerate(LETTER_WORDS) if letter & phrases]
    return found[0] if len(found) == 1 else None


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
    if kind == "choice":
        got = _choice_answer(item, text)
        want = item["value"]
        answer = "%s, %s" % (LETTERS[want], esc(item["options"][want]))
        if got == want:
            return True, "Correct, %s." % answer
        extra = ""
        if got == item.get("distractor"):
            extra = (" %s was mentioned, but the caller turned it down. "
                     "Distractors like that are common in the exam."
                     % _cap(esc(item["options"][got])))
        return False, "Not quite. It was %s.%s" % (answer, extra)
    return False, ""
