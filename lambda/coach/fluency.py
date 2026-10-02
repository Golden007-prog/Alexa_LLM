# -*- coding: utf-8 -*-
"""Part 2 fluency rounds: the 4/3/2 technique adapted to IELTS timing.

The learner tells the same story three times with shrinking time limits.
Repeating one topic is what produced lasting fluency gains in de Jong &
Perfetti (2011); see docs/LEARNING_DESIGN.md 4.3. Numbers come from Alexa's
transcript and request timestamps, so they are rough and only compared
between rounds.
"""

import re

ROUND_SECONDS = [120, 90, 60]
ROUND_NAMES = ["one", "two", "three"]
ROUND_SPOKEN = ["two minutes", "ninety seconds", "one minute"]
MAX_CONTENT_WORDS = 120     # keeps the session attributes small

_STOPWORDS = set("""
about above after again also although because been before being below
between both could does doing down during each even every from further
have having here into just like made make many maybe more most much must
only other over really same should some such than that their them then
there these they thing things this those through very want went were what
when where which while will with would your yours yeah okay well
""".split())


def content_words(text):
    """Distinct meaningful words (4+ letters, not function words), in order."""
    seen, out = set(), []
    for w in re.findall(r"[a-z']+", (text or "").lower()):
        w = w.strip("'")
        if len(w) >= 4 and w not in _STOPWORDS and w not in seen:
            seen.add(w)
            out.append(w)
    return out[:MAX_CONTENT_WORDS]


def pace(words, secs):
    """Rough words per minute."""
    return int(round(words * 60.0 / secs)) if secs > 0 else 0


def summary(rounds, first_content, last_content):
    """Spoken summary after the last round. rounds: [{words, secs}]."""
    spoken = [r for r in rounds if r["words"] and r["secs"]]
    retry = (" Next time, try all three rounds: repeating the same story is "
             "what builds fluency.")
    if not spoken:
        return "I didn't hear a talk that time." + retry
    first = pace(spoken[0]["words"], spoken[0]["secs"])
    if len(spoken) < len(rounds):
        return ("Your pace was about %d words a minute, but some rounds were "
                "cut short." % first) + retry
    last = pace(rounds[-1]["words"], rounds[-1]["secs"])
    if last > first:
        text = "Your pace went from about %d to about %d words a minute" % (
            first, last)
    else:
        text = "Your pace was about %d words a minute, then about %d" % (
            first, last)
    if last_content:
        kept = set(first_content)
        share = sum(1 for w in last_content if w in kept) / float(
            len(last_content))
        text += (", and %d per cent of your round three ideas came from "
                 "round one" % int(round(share * 100)))
    return text + (". These are rough numbers from Alexa's text, so compare "
                   "the rounds, not the absolute values.")
