# -*- coding: utf-8 -*-
"""Speaking feedback: an AI examiner when a key is configured, otherwise
rule-based tips from the transcript. Both see text only - never audio."""

import re
from collections import Counter

from . import llm
from .speech import clean_llm_text

SYSTEM_PROMPT = (
    "You are an experienced IELTS Speaking examiner coaching a candidate "
    "from India whose exam is less than a month away. You receive only an "
    "automatic speech-recognition transcript of their answers. You cannot "
    "hear them, so do not rate pronunciation, and remember that fillers and "
    "pauses are usually missing from the transcript.\n"
    "Your reply will be read aloud by a smart speaker. Write plain spoken "
    "sentences with no lists, symbols, headings or markdown. Stay under 150 "
    "words.\n"
    "Structure: first, an estimated band range for Fluency and Coherence, "
    "Lexical Resource, and Grammatical Range and Accuracy, for example "
    "'six to six point five'. Second, one specific strength. Third, the "
    "three most valuable fixes: for each, quote a few words they actually "
    "said and give a better version. Be honest and examiner-strict. If the "
    "answers are very short, say that length is limiting their score."
)

LINKERS = [
    "however", "although", "because", "for example", "for instance",
    "on the other hand", "in addition", "whereas", "as a result",
    "therefore", "moreover", "personally", "in my opinion", "to be honest",
    "i would say", "while", "since", "so that", "which means", "despite",
]

PLAIN_WORDS = {
    "good": "beneficial, rewarding, or valuable",
    "very": "extremely, remarkably, or incredibly",
    "nice": "pleasant, enjoyable, or charming",
    "big": "huge, substantial, or significant",
    "bad": "harmful, unpleasant, or disappointing",
    "important": "crucial, essential, or vital",
    "thing": "aspect, factor, or issue",
    "things": "aspects, factors, or issues",
    "really": "genuinely, truly, or particularly",
    "interesting": "fascinating, intriguing, or thought-provoking",
    "happy": "delighted, content, or thrilled",
}


def _words(text):
    return re.findall(r"[a-z']+", (text or "").lower())


def format_transcript(transcript):
    lines = []
    for t in transcript:
        label = "Part %s" % t.get("part")
        extra = ""
        if t.get("secs"):
            extra = " (spoke for about %d seconds)" % int(t["secs"])
        lines.append("%s. Examiner: %s\nCandidate%s: %s" % (
            label, t.get("q", ""), extra, t.get("a", "") or "(no answer)"))
    return "\n\n".join(lines)


def rule_based(transcript):
    """Return a list of short spoken tips."""
    tips = []
    short = [t for t in transcript if t.get("part") in (1, 3)]
    if short:
        avg = sum(len(_words(t.get("a"))) for t in short) / float(len(short))
        if avg < 18:
            tips.append(
                "Your answers averaged %d words. Aim for two or three "
                "sentences each: answer, reason, then an example." % round(avg))
        else:
            tips.append("Good answer length: about %d words each." % round(avg))
    longs = [t for t in transcript if t.get("part") == 2]
    for t in longs:
        n = len(_words(t.get("a")))
        if n < 170:
            tips.append(
                "Your Part 2 talk was about %d words. Two full minutes at a "
                "natural pace is roughly 200 to 280 words, so keep going "
                "with more detail and examples." % n)
    alltext = " ".join(t.get("a", "") for t in transcript).lower()
    used = [l for l in LINKERS if re.search(r"\b%s\b" % re.escape(l), alltext)]
    if len(used) < 3:
        tips.append("Use more linking phrases, such as on the other hand, "
                    "for instance, and as a result.")
    counts = Counter(_words(alltext))
    overused = [w for w in PLAIN_WORDS if counts.get(w, 0) >= 3]
    if overused:
        w = max(overused, key=lambda x: counts[x])
        tips.append("You said %s %d times. Try %s." % (
            w, counts[w], PLAIN_WORDS[w]))
    if not tips:
        tips.append("Nice work. Keep practising full mocks.")
    return tips


def examiner_feedback(transcript):
    """Return (spoken_text, used_ai)."""
    if llm.enabled():
        prompt = ("Here is the transcript of my IELTS Speaking practice. "
                  "Give me feedback.\n\n" + format_transcript(transcript))
        text = llm.generate(SYSTEM_PROMPT, prompt)
        if text:
            return clean_llm_text(text), True
    tips = rule_based(transcript)[:3]
    note = ("" if llm.enabled() else
            " For band estimates, add an AI key as the readme explains.")
    return " ".join(tips) + note, False
