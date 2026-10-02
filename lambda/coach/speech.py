# -*- coding: utf-8 -*-
"""SSML helpers. Output strings are SSML fragments WITHOUT the <speak> root;
the ASK SDK's .speak() wraps them."""

import re
from xml.sax.saxutils import escape

# Amazon Polly voices supported in Alexa skills (Alexa SSML reference).
# A voice from another locale must be wrapped in <lang> with its locale.
ACCENTS = {
    "british": {"label": "British", "lang": "en-GB",
                "voices": ["Amy", "Brian", "Emma"]},
    "australian": {"label": "Australian", "lang": "en-AU",
                   "voices": ["Nicole", "Russell"]},
    "american": {"label": "North American", "lang": "en-US",
                 "voices": ["Joanna", "Matthew"]},
}

GERMAN_VOICE = "Vicki"   # de-DE voices: Hans, Marlene, Vicki


def esc(text):
    """Escape plain text for SSML."""
    return escape(text or "", {'"': "&quot;"})


def brk(seconds):
    """A pause. Alexa allows at most 10 seconds per <break>."""
    out = []
    remaining = float(seconds)
    while remaining > 0:
        chunk = min(10.0, remaining)
        out.append("<break time='%dms'/>" % int(chunk * 1000))
        remaining -= chunk
    return "".join(out)


def voice(name, lang, text_ssml):
    """Speak an SSML fragment with a Polly voice in a given locale."""
    return "<voice name='%s'><lang xml:lang='%s'>%s</lang></voice>" % (
        name, lang, text_ssml)


def german(text, rate=None):
    """German text in a native German voice. rate e.g. '75%' for slow."""
    inner = esc(text)
    if rate:
        inner = "<prosody rate='%s'>%s</prosody>" % (rate, inner)
    return voice(GERMAN_VOICE, "de-DE", inner)


def spell(word):
    return "<say-as interpret-as='spell-out'>%s</say-as>" % esc(word.upper())


_MD = re.compile(r"[*#_`>\[\]]")


def clean_llm_text(text, max_chars=1400):
    """Make model output safe and pleasant to speak: strip markdown,
    collapse whitespace, cap length at a sentence boundary."""
    text = _MD.sub("", text or "")
    text = re.sub(r"^\s*[-•]\s*", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        cut = text[:max_chars]
        end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
        text = cut[:end + 1] if end > 200 else cut
    return text
