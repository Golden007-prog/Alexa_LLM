# -*- coding: utf-8 -*-
"""Turn speech-recognition text into numbers and digit strings."""

import re

_UNITS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    # ordinals
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
    "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18,
    "nineteenth": 19,
}
_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
    "twentieth": 20, "thirtieth": 30, "fortieth": 40, "fiftieth": 50,
}
_DIGIT_WORDS = {
    "zero": "0", "oh": "0", "o": "0", "nought": "0", "nil": "0",
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9",
}


def _tokens(text):
    text = (text or "").lower().replace("-", " ")
    return re.findall(r"[a-z]+|\d+(?:st|nd|rd|th)?", text)


def extract_numbers(text):
    """All whole numbers in the text, in order.
    'the fifteenth of March' -> [15]; 'twenty five' -> [25]; '3 people' -> [3]
    """
    out = []
    toks = _tokens(text)
    i = 0
    while i < len(toks):
        t = toks[i]
        m = re.match(r"^(\d+)(?:st|nd|rd|th)?$", t)
        if m:
            out.append(int(m.group(1)))
        elif t in _TENS:
            val = _TENS[t]
            if i + 1 < len(toks) and toks[i + 1] in _UNITS \
                    and 0 < _UNITS[toks[i + 1]] < 10:
                val += _UNITS[toks[i + 1]]
                i += 1
            out.append(val)
        elif t in _UNITS:
            out.append(_UNITS[t])
        elif t == "hundred" and out:
            out[-1] *= 100
        i += 1
    return out


def spoken_digits(text):
    """A spoken phone number as a digit string.
    'oh seven nine double four 1 2' -> '0794412'"""
    digits = []
    repeat = 1
    for t in _tokens(text):
        if t == "double":
            repeat = 2
            continue
        if t == "triple":
            repeat = 3
            continue
        if t.isdigit():
            if repeat > 1 and len(t) == 1:
                digits.append(t * repeat)
            else:
                digits.append(t)
        elif t in _DIGIT_WORDS:
            digits.append(_DIGIT_WORDS[t] * repeat)
        repeat = 1
    return "".join(digits)


def letters_only(text):
    """'T. H. O. R. N.' or 'thorn' -> 'thorn'"""
    return re.sub(r"[^a-z]", "", (text or "").lower())


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1,
                           prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
