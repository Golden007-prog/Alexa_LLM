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
    "sentences with no lists, symbols, headings or markdown. Stay under 120 "
    "words.\n"
    "Structure: first, an estimated band range for Fluency and Coherence, "
    "Lexical Resource, and Grammatical Range and Accuracy, for example "
    "'six to six point five'. Second, one specific strength. Third, the "
    "two most valuable fixes, no more: for each, quote a few words they "
    "actually said and give a better version. Be honest and examiner-strict. "
    "If the answers are very short, say that length is limiting their score."
)

# Retry targets, in the order they are offered (docs/LEARNING_DESIGN.md 4.4)
RETRY_LINKERS = ["although", "for instance", "on the other hand",
                 "as a result"]
RETRY_CHUNKS = ["in my experience", "it depends on", "the main reason is",
                "to be honest"]

# Progressive with stative verbs ("I am knowing") is a documented Indian
# English feature (Sailaja 2009) that exam English treats as an error.
# "having" and "seeing" are left out: "having lunch" and "seeing a doctor"
# are correct.
_STATIVE = re.compile(
    r"\b(?:am|is|are|was|were|i'm|he's|she's|we're|they're|you're)\s+"
    r"(knowing|understanding|believing|wanting|owning|belonging|preferring|"
    r"liking)\b")

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


def _alltext(transcript):
    return " ".join(t.get("a", "") or "" for t in transcript).lower()


def _linkers_used(text):
    return [l for l in LINKERS if re.search(r"\b%s\b" % re.escape(l), text)]


def _overused(text):
    """The plain word said most often (3+ times), or None."""
    counts = Counter(_words(text))
    overused = [w for w in PLAIN_WORDS if counts.get(w, 0) >= 3]
    if not overused:
        return None, 0
    w = max(overused, key=lambda x: counts[x])
    return w, counts[w]


def _alternatives(word):
    return [a for a in re.split(r",\s*(?:or\s+)?|\s+or\s+", PLAIN_WORDS[word])
            if a]


def stative_progressive(transcript):
    m = _STATIVE.search(_alltext(transcript))
    if not m:
        return None
    return ("You said %s. In exam English, verbs like know, understand and "
            "want usually don't take i n g: say I know, not I am knowing."
            % m.group(0))


def rule_based(transcript):
    """Short spoken tips: at most one piece of praise, then at most two
    corrections, most valuable first. Learners repair more when feedback is
    focused (docs/LEARNING_DESIGN.md 4.4)."""
    praise, fixes = [], []
    short = [t for t in transcript if t.get("part") in (1, 3)]
    if short:
        avg = sum(len(_words(t.get("a"))) for t in short) / float(len(short))
        if avg < 18:
            fixes.append(
                "Your answers averaged %d words. Aim for two or three "
                "sentences each: answer, reason, then an example." % round(avg))
        else:
            praise.append("Good answer length: about %d words each."
                          % round(avg))
    for t in (t for t in transcript if t.get("part") == 2):
        n = len(_words(t.get("a")))
        if n < 170:
            fixes.append(
                "Your Part 2 talk was about %d words. Two full minutes at a "
                "natural pace is roughly 200 to 280 words, so keep going "
                "with more detail and examples." % n)
            break
    stative = stative_progressive(transcript)
    if stative:
        fixes.append(stative)
    alltext = _alltext(transcript)
    w, n = _overused(alltext)
    if w:
        fixes.append("You said %s %d times. Try %s." % (w, n, PLAIN_WORDS[w]))
    if len(_linkers_used(alltext)) < 3:
        fixes.append("Use more linking phrases, such as on the other hand, "
                     "for instance, and as a result.")
    if not fixes and not praise:
        praise.append("Nice work. Keep practising full mocks.")
    return praise[:1] + fixes[:2]


def retry_target(transcript):
    """One checkable thing to use in a retry answer: {"say": how to ask for
    it, "label": short name for it, "accept": phrases that count}."""
    alltext = _alltext(transcript)
    w, _ = _overused(alltext)
    if w:
        alts = _alternatives(w)
        return {"say": "a stronger word than %s, like %s" % (w, alts[0]),
                "label": "a stronger word than %s" % w, "accept": alts}
    used = _linkers_used(alltext)
    if len(used) < 3:
        linker = next(l for l in RETRY_LINKERS if l not in used)
        return {"say": linker, "label": linker, "accept": [linker]}
    chunk = next((c for c in RETRY_CHUNKS if c not in alltext),
                 RETRY_CHUNKS[0])
    return {"say": chunk, "label": chunk, "accept": [chunk]}


def uses_target(text, target):
    low = (text or "").lower()
    return any(re.search(r"\b%s\b" % re.escape(a), low)
               for a in target["accept"])


def examiner_feedback(transcript, deadline=None):
    """Return (spoken_text, used_ai). deadline: see llm.generate."""
    if llm.enabled():
        prompt = ("Here is the transcript of my IELTS Speaking practice. "
                  "Give me feedback.\n\n" + format_transcript(transcript))
        text = llm.generate(SYSTEM_PROMPT, prompt, deadline=deadline)
        if text:
            return clean_llm_text(text), True
    tips = rule_based(transcript)
    note = ("" if llm.enabled() else
            " For band estimates, add an AI key as the readme explains.")
    return " ".join(tips) + note, False
