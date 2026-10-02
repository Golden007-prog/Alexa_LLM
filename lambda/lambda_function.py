# -*- coding: utf-8 -*-
"""IELTS & German Coach - an Alexa custom skill for an Echo Dot.

Say: "Alexa, open study coach" (today's plan), then
  "mock test" | "part one" | "part two" | "part three" | "feedback"
  "listening drill" | "listening drill british" | "German lesson" | "German lesson 5"
  "how am I doing" | "my exam is on <date>"

Runs as an Alexa-hosted skill (Python 3.8). See README.md.
"""

import functools
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone

from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_core.dispatch_components import (AbstractExceptionHandler,
                                              AbstractRequestHandler,
                                              AbstractRequestInterceptor)
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_core.utils import get_slot, is_intent_name, is_request_type
from ask_sdk_model.services.directive import (Header, SendDirectiveRequest,
                                              SpeakDirective)
from ask_sdk_model.ui import SimpleCard

from coach import feedback, fluency, listening, plan
from coach.content import CUE_CARDS, GERMAN_LESSONS, PART1_TOPICS
from coach.speech import ACCENTS, brk, esc, german

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Alexa-hosted pins the runtime; log it so CloudWatch shows what really runs.
logger.info("Cold start on Python %s", sys.version.split()[0])

SKILL_TITLE = "IELTS & German Coach"

# Conversation modes kept in session attributes
MENU, P1, P2, P3, LISTEN, GQUIZ = "menu", "p1", "p2", "p3", "listen", "gquiz"
SETUP_EXAM, SETUP_CUE, RETRY = "setup_exam", "setup_cue", "retry"
YES_WORDS = {"yes", "yeah", "yep", "ok", "okay", "sure", "ready", "start",
             "let's go", "go", "yes please", "let's start", "continue",
             "go ahead", "i'm ready"}
P1_TOPICS_PER_RUN, P1_QUESTIONS_PER_TOPIC = 2, 3
P2_MAX_SECONDS, P2_MAX_WORDS = 120, 320
WORDS_PER_SECOND = 2.1          # rough speaking rate for timing Part 2

# Alexa waits about 8 s for a reply. Network work in one request (progressive
# response, S3 config, LLM) must finish inside this budget, leaving margin.
REPLY_BUDGET_SECONDS = 7.0
ALEXA_API_TIMEOUT_SECONDS = 1.5

MENU_SPEECH = ("You can say: mock test, part one, part two, part three, "
               "listening drill, or German lesson.")
ACKS = ["", "Okay. ", "Thank you. ", "Right. ", "Alright. "]
GO_ON = ["Mm-hm, go on.", "Okay, keep going.", "Yes, carry on.", "Go on.",
         "Mm-hm."]


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def sess(h):
    return h.attributes_manager.session_attributes


_LOCAL_STORE = {}  # used only when no persistence adapter (local tests)


def persist(h):
    """Persistent attributes (DynamoDB on Alexa-hosted), loaded once per
    request and mutated in place."""
    try:
        return h.attributes_manager.persistent_attributes
    except Exception:
        return _LOCAL_STORE


def save_persist(h):
    try:
        h.attributes_manager.save_persistent_attributes()
    except Exception as exc:
        logger.info("Persistent attributes not saved: %s", exc)


def reply_deadline(h):
    """time.monotonic() value by which this request's reply must be ready."""
    started = h.attributes_manager.request_attributes.get("started")
    return (started or time.monotonic()) + REPLY_BUDGET_SECONDS


def request_time(h):
    ts = h.request_envelope.request.timestamp
    if ts is None:
        return datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def now_ts(h):
    return request_time(h).timestamp()


def local_today(h):
    return plan.local_date(request_time(h), h.request_envelope.request.locale)


def mark_active(h):
    """Log today as a practice day (for the streak); saved once per day."""
    p = persist(h)
    days = p.get("days") or []
    updated = plan.record_day(days, local_today(h))
    if updated != days:
        p["days"] = updated
        save_persist(h)


def ask(h, speech, reprompt, card_title=None, card_text=None):
    s = sess(h)
    s["last_speech"], s["last_reprompt"] = speech, reprompt
    rb = h.response_builder.speak(speech).ask(reprompt)
    if card_text:
        rb.set_card(SimpleCard(card_title or SKILL_TITLE, card_text))
    return rb.response


def tell(h, speech):
    save_persist(h)
    return h.response_builder.speak(speech).set_should_end_session(True).response


class TimeoutApiClient(DefaultApiClient):
    """DefaultApiClient calls `requests` with no timeout, so one stalled
    Alexa API call could eat the whole reply window."""

    def _resolve_method(self, request):
        method = super(TimeoutApiClient, self)._resolve_method(request)
        return functools.partial(method, timeout=ALEXA_API_TIMEOUT_SECONDS)


def progressive(h, text):
    """Speak while a slow AI call runs (Progressive Response API).
    Returns True if Alexa accepted it."""
    try:
        directive = SendDirectiveRequest(
            header=Header(request_id=h.request_envelope.request.request_id),
            directive=SpeakDirective(speech="<speak>%s</speak>" % text))
        h.service_client_factory.get_directive_service().enqueue(directive)
        return True
    except Exception as exc:
        logger.info("Progressive response skipped: %s", exc)
        return False


def slot(h, name):
    try:
        return get_slot(h, name).value
    except Exception:
        return None


def add_transcript(h, entry):
    s = sess(h)
    t = s.setdefault("transcript", [])
    t.append(entry)
    del t[:-14]  # keep the session small


# ---------------------------------------------------------------------------
# IELTS Speaking
# ---------------------------------------------------------------------------
def p1_question(s):
    p = s["p1"]
    topic = PART1_TOPICS[p["topics"][p["t"]]]
    return topic, topic["questions"][p["q"]]


def start_part1(h, mock):
    mark_active(h)
    s = sess(h)
    s["mock"] = mock
    s["mode"] = P1
    if mock:
        s["transcript"] = []
    s["p1"] = {"topics": random.sample(range(len(PART1_TOPICS)),
                                       P1_TOPICS_PER_RUN), "t": 0, "q": 0}
    topic, q = p1_question(s)
    if mock:
        intro = ("This is a full speaking test in three parts. It takes about "
                 "fifteen minutes. Answer naturally, in two or three sentences. "
                 + brk(0.5) + "Part 1. ")
    else:
        intro = "Part 1 practice. Answer in two or three sentences. "
    focus = persist(h).get("focus")
    if focus:
        intro += "Remember to try %s today. " % esc(focus["say"])
    speech = "%sLet's talk about %s. %s" % (intro, esc(topic["topic"]), esc(q))
    return ask(h, speech, esc(q))


def answer_part1(h, text):
    s = sess(h)
    p = s["p1"]
    topic, q = p1_question(s)
    add_transcript(h, {"part": 1, "q": q, "a": text})
    p["q"] += 1
    changed = False
    if p["q"] >= P1_QUESTIONS_PER_TOPIC:
        p["t"], p["q"], changed = p["t"] + 1, 0, True
    if p["t"] >= len(p["topics"]):
        if s.get("mock"):
            return start_part2(h, prefix="Thank you. That's the end of Part 1. ")
        s["mode"] = MENU
        if plan_active(s):   # part of today's plan: review right away
            return give_feedback(h, prefix="Thank you. That's the end of "
                                           "Part 1. ")
        return ask(h, "Thank you. That's the end of Part 1. Say feedback to "
                      "hear how you did, or part two to continue.",
                   "Say feedback, or part two.")
    topic, q = p1_question(s)
    if changed:
        speech = "Thank you. Now let's talk about %s. %s" % (
            esc(topic["topic"]), esc(q))
    else:
        speech = random.choice(ACKS) + esc(q)
    return ask(h, speech, esc(q))


def cue_card_text(card):
    return "%s You should say: %s, and explain %s." % (
        card["title"], ", ".join(card["points"]), card["explain"])


def start_part2(h, prefix="", rounds=False):
    """Part 2 long turn. rounds=True runs the fluency drill: the same talk
    three times in 2:00, 1:30 and 1:00 (coach/fluency.py)."""
    mark_active(h)
    s = sess(h)
    used = s.setdefault("cards_used", [])
    choices = [i for i in range(len(CUE_CARDS)) if i not in used] or \
        list(range(len(CUE_CARDS)))
    idx = random.choice(choices)
    used.append(idx)
    card = CUE_CARDS[idx]
    s["mode"] = P2
    s["p2"] = {"card": idx, "chunks": [], "first_ts": None, "first_words": 0}
    if rounds:
        s["mock"] = False
        s["p2"].update({"round": 0, "rounds": [], "first_content": []})
        prefix += ("Fluency rounds. You'll tell the same story three times: "
                   "in two minutes, ninety seconds, then one minute. Keep the "
                   "same details and get smoother each time. " + brk(0.5))
    points = ". ".join(esc(p) for p in card["points"])
    speech = (
        prefix + "Part 2. I'll give you a topic. You have one minute to prepare, "
        "then talk for one to two minutes. Here is your topic. "
        + brk(0.5) +
        "<prosody rate='90%'>" + esc(card["title"]) + " You should say: "
        + points + ". And explain " + esc(card["explain"]) + ".</prosody> "
        + "The card is also in your Alexa app. Your minute starts now."
        + brk(20) + "Forty seconds left. Remember: " + esc(card["title"])
        + brk(20) + "Twenty seconds." + brk(18)
        + "Time is up. Please start speaking now. Say I'm finished when "
          "you're done.")
    return ask(h, speech, "Please start your talk about: " + esc(card["title"]),
               "Part 2 cue card", cue_card_text(card))


def talk_seconds(h, p):
    return (now_ts(h) - p["first_ts"]) + p["first_words"] / WORDS_PER_SECOND


def answer_part2(h, text, finished=False):
    s = sess(h)
    p = s["p2"]
    rnd = p.get("round")
    max_secs = P2_MAX_SECONDS if rnd is None else fluency.ROUND_SECONDS[rnd]
    max_words = P2_MAX_WORDS * max_secs // P2_MAX_SECONDS
    if text:
        p["chunks"].append(text)
        if p["first_ts"] is None:
            p["first_ts"] = now_ts(h)
            p["first_words"] = len(text.split())
    words = sum(len(c.split()) for c in p["chunks"])
    secs = talk_seconds(h, p) if p["first_ts"] is not None else 0
    if not (finished or secs >= max_secs or words >= max_words):
        first = len(p["chunks"]) == 1
        line = random.choice(GO_ON)
        if first:
            line = "Go on. Say I'm finished when you're done."
        return ask(h, line, "Carry on, or say I'm finished.")
    card = CUE_CARDS[p["card"]]
    if rnd is not None:
        return end_fluency_round(h, p, card, words, secs)
    add_transcript(h, {"part": 2, "q": card["title"], "a": " ".join(p["chunks"]),
                       "secs": int(secs)})
    if secs >= P2_MAX_SECONDS - 5:
        msg = "Thank you, that's two minutes. "
    elif secs < 60 and words:
        msg = ("Thank you. That was under a minute. In the exam, keep going "
               "for the full two minutes. ")
    else:
        msg = "Thank you. "
    s["last_card"] = p["card"]
    if s.get("mock"):
        return start_part3(h, prefix=msg)
    s["mode"] = MENU
    return finish(h, msg, "Say part three for discussion questions on this "
                          "topic, or feedback.",
                  "Say part three, or feedback.")


def end_fluency_round(h, p, card, words, secs):
    s = sess(h)
    rnd = p["round"]
    talk = " ".join(p["chunks"])
    p["rounds"].append({"words": words, "secs": int(secs)})
    if rnd == 0:
        p["first_content"] = fluency.content_words(talk)
        add_transcript(h, {"part": 2, "q": card["title"], "a": talk,
                           "secs": int(secs)})
    if rnd + 1 < len(fluency.ROUND_SECONDS):
        p.update({"round": rnd + 1, "chunks": [], "first_ts": None,
                  "first_words": 0})
        nxt = fluency.ROUND_SPOKEN[rnd + 1]
        return ask(h, "Thank you. Round %s: tell me the same story again, with "
                      "the same details, in %s. Go." % (
                          fluency.ROUND_NAMES[rnd + 1], nxt),
                   "Start round %s: the same story, in %s." % (
                       fluency.ROUND_NAMES[rnd + 1], nxt))
    text = fluency.summary(p["rounds"], p["first_content"],
                           fluency.content_words(talk))
    last_pace = fluency.pace(words, secs)
    pers = persist(h)
    pers["p2_rounds_last"] = p["rounds"]
    pers["p2_best_pace"] = max(int(pers.get("p2_best_pace", 0)), last_pace)
    save_persist(h)
    s["last_card"] = p["card"]
    s["mode"] = MENU
    return finish(h, "Thank you. " + esc(text),
                  "Say feedback to hear about your language, or part three "
                  "for discussion questions.",
                  "Say feedback, or part three.")


def start_part3(h, prefix=""):
    mark_active(h)
    s = sess(h)
    idx = s.get("last_card")
    intro = "Part 3. Let's discuss some more general questions linked to "
    if idx is None:
        idx = random.randrange(len(CUE_CARDS))
        s["last_card"] = idx
        intro = "Part 3 practice. Give your opinion and explain it. Topic: "
    card = CUE_CARDS[idx]
    s["mode"] = P3
    s["p3"] = {"card": idx, "q": 0}
    q = card["part3"][0]
    speech = prefix + intro + esc(card["title"].replace("Describe ", "").rstrip(".")) \
        + ". " + brk(0.4) + esc(q)
    return ask(h, speech, esc(q))


def answer_part3(h, text):
    s = sess(h)
    p = s["p3"]
    card = CUE_CARDS[p["card"]]
    add_transcript(h, {"part": 3, "q": card["part3"][p["q"]], "a": text})
    p["q"] += 1
    if p["q"] < len(card["part3"]):
        q = card["part3"][p["q"]]
        return ask(h, random.choice(ACKS) + esc(q), esc(q))
    s["mode"] = MENU
    if s.get("mock"):
        s["mock"] = False
        persist(h)["mocks"] = persist(h).get("mocks", 0) + 1
        return give_feedback(h, prefix="Thank you. That is the end of the "
                                       "speaking test. ")
    return finish(h, "Thank you. That's the end of Part 3.",
                  "Say feedback, or mock test for a full test.",
                  "Say feedback, or mock test.")


def give_feedback(h, prefix=""):
    s = sess(h)
    transcript = s.get("transcript") or []
    if not transcript:
        return ask(h, prefix + "There's nothing to review yet. Say mock test, "
                               "or part one, to practise first.",
                   "Say mock test or part one.")
    sent = progressive(h, prefix + "Let me review your answers. This takes "
                                   "a few seconds.")
    text, used_ai = feedback.examiner_feedback(transcript,
                                               deadline=reply_deadline(h))
    target = feedback.retry_target(transcript)
    q = retry_question(transcript)
    s["transcript"] = []
    p = persist(h)
    hist = p.setdefault("history", [])
    hist.append({"date": local_today(h).isoformat(),
                 "ai": used_ai, "feedback": text[:600]})
    del hist[:-10]
    save_persist(h)
    # Feedback ends with a retry: learners repair more when prompted to
    # use the fix at once (docs/LEARNING_DESIGN.md 4.4).
    s["mode"] = RETRY
    s["retry"] = {"target": target, "q": q}
    ask_again = "this time use %s. %s" % (esc(target["say"]), esc(q))
    return ask(h, ("" if sent else prefix) + esc(text) + brk(0.6) +
               "Let's lock one in. Answer this again, and " + ask_again,
               "Answer again, and " + ask_again, "Speaking feedback", text)


def retry_question(transcript):
    for t in reversed(transcript):
        if t.get("part") in (1, 3) and t.get("q"):
            return t["q"]
    return random.choice(random.choice(PART1_TOPICS)["questions"])


def answer_retry(h, text, skipped=False):
    s = sess(h)
    target = (s.pop("retry", None) or {}).get("target")
    s["mode"] = MENU
    tail = ("Say mock test to go again, or menu.", "Say mock test, or menu.")
    if skipped or not target:
        return finish(h, "Okay. Skipping that one.", *tail)
    p = persist(h)
    p["focus"] = target          # reminded at the start of the next Part 1
    save_persist(h)
    label = esc(target.get("label") or target["say"])
    if feedback.uses_target(text, target):
        done = ("Nice, you used %s. That's the kind of language examiners "
                "reward." % label)
    else:
        done = ("You didn't use %s that time. Try to fit it into your answers "
                "today, and I'll remind you next time." % label)
    return finish(h, done, *tail)


# ---------------------------------------------------------------------------
# IELTS Listening drill
# ---------------------------------------------------------------------------
def start_listening(h, accent=None):
    mark_active(h)
    s = sess(h)
    drill = listening.make_drill(accent)
    s["mode"] = LISTEN
    s["listen"] = {"items": drill["items"], "i": 0, "score": 0,
                   "dialog": drill["dialog"]}
    q = drill["items"][0]["q"]
    speech = ("Listening drill, %s accent. Get a pen ready. You'll hear a "
              "phone call once, like in the exam. Write down the surname, the "
              "phone number, the date and the number. %s %s %s Question one. %s"
              % (drill["label"], brk(1.5), drill["dialog"], brk(1), esc(q)))
    return ask(h, speech, "Question one. " + esc(q))


def answer_listening(h, text):
    s = sess(h)
    L = s["listen"]
    item = L["items"][L["i"]]
    ok, fb = listening.check(item, text)
    if ok:
        L["score"] += 1
    L["i"] += 1
    if L["i"] < len(L["items"]):
        nums = ["one", "two", "three", "four"]
        q = L["items"][L["i"]]["q"]
        return ask(h, "%s %s Question %s. %s" % (fb, brk(0.4), nums[L["i"]],
                                                  esc(q)),
                   esc(q))
    s["mode"] = MENU
    total = len(L["items"])
    return finish(h, "%s %s You scored %d out of %d." % (fb, brk(0.4),
                                                         L["score"], total),
                  "Say listening drill for another call, or name an accent, "
                  "like listening drill Australian.",
                  "Say listening drill, or German lesson.")


# ---------------------------------------------------------------------------
# German lessons
# ---------------------------------------------------------------------------
def lesson_phrases(idx):
    lesson = GERMAN_LESSONS[idx]
    if lesson.get("review"):
        lo, hi = lesson["review"]
        pool = [ph for L in GERMAN_LESSONS[lo:hi + 1] for ph in L["phrases"]]
        return random.sample(pool, 5)
    return list(lesson["phrases"])


def start_german(h, number=None):
    mark_active(h)
    s = sess(h)
    p = persist(h)
    nxt = int(p.get("german_next", 0))
    idx = nxt
    if number:
        try:
            idx = int(number) - 1
        except ValueError:
            idx = nxt
    idx = max(0, min(idx, len(GERMAN_LESSONS) - 1))
    lesson = GERMAN_LESSONS[idx]
    phrases = lesson_phrases(idx)
    parts = ["German lesson %d of %d: %s. Listen, then repeat each phrase out "
             "loud in the pause. %s" % (idx + 1, len(GERMAN_LESSONS),
                                        esc(lesson["title"]), brk(0.6))]
    if lesson.get("review"):
        parts = ["German lesson %d: %s. %s" % (idx + 1, esc(lesson["title"]),
                                               brk(0.4))]
    else:
        for ph in phrases:
            parts.append("%s %s %s %s %s %s" % (
                _sentence(ph["en"]), brk(0.3), german(ph["de"], "70%"), brk(2.2),
                german(ph["de"]), brk(1.8)))
    parts.append("Tip: %s %s" % (esc(lesson["tip"]), brk(0.6)))
    quiz = random.sample(phrases, len(phrases))
    s["mode"] = GQUIZ
    s["ger"] = {"lesson": idx, "items": quiz, "i": 0, "score": 0}
    parts.append("Now a quick quiz. I'll say a German phrase. You tell me what "
                 "it means in English. Number one. %s %s What does it mean?"
                 % (brk(0.3), german(quiz[0]["de"])))
    card = "\n".join("%s = %s" % (ph["de"], ph["en"]) for ph in phrases)
    return ask(h, " ".join(parts),
               "What does %s mean?" % german(quiz[0]["de"]),
               "German lesson %d: %s" % (idx + 1, lesson["title"]), card)


def _sentence(text):
    """End a phrase with exactly one punctuation mark."""
    text = (text or "").strip()
    return esc(text if text[-1:] in ".?!" else text + ".")


def german_correct(item, text):
    """Correct if every word of any accepted keyword group was said."""
    words = set(w.strip(".,!?'") for w in
                (text or "").lower().replace("-", " ").split())
    return any(all(g in words for g in group) for group in item["accept"])


def answer_german(h, text):
    s = sess(h)
    G = s["ger"]
    item = G["items"][G["i"]]
    if german_correct(item, text):
        G["score"] += 1
        fb = "%s That's right, it means %s" % (german("Richtig!"), _sentence(item["en"]))
    else:
        fb = "Not quite. It means %s" % _sentence(item["en"])
    fb += " Say it with me: %s %s" % (german(item["de"]), brk(1.5))
    G["i"] += 1
    nums = ["one", "two", "three", "four", "five"]
    if G["i"] < len(G["items"]):
        nxt = G["items"][G["i"]]
        return ask(h, "%s Number %s. %s What does it mean?" % (
            fb, nums[G["i"]], german(nxt["de"])),
            "What does %s mean?" % german(nxt["de"]))
    s["mode"] = MENU
    p = persist(h)
    score, total, idx = G["score"], len(G["items"]), G["lesson"]
    if score >= 3:
        if idx >= int(p.get("german_next", 0)):
            p["german_next"] = min(idx + 1, len(GERMAN_LESSONS) - 1)
        end = "%s You scored %d out of %d. Next time, say German lesson for " \
              "lesson %d." % (german("Gut gemacht!"), score, total,
                              min(idx + 2, len(GERMAN_LESSONS)))
    else:
        end = ("You scored %d out of %d. Let's repeat this lesson next time to "
               "lock it in." % (score, total))
    save_persist(h)
    return finish(h, fb + " " + end,
                  "What next? Mock test, listening drill, or menu?",
                  "Say mock test, listening drill, or menu.")


# ---------------------------------------------------------------------------
# Today's plan, first-run setup, progress  (docs/LEARNING_DESIGN.md 4.1, 4.8)
# ---------------------------------------------------------------------------
ACTIVITIES = {
    # id: (spoken label, rough minutes, start function)
    "mock": ("a full mock test", 15, lambda h: start_part1(h, mock=True)),
    "p1": ("Part 1 questions with feedback", 5,
           lambda h: start_part1(h, mock=False)),
    "p2rounds": ("Part 2 fluency rounds", 7,
                 lambda h: start_part2(h, rounds=True)),
    "listen": ("a listening call", 4, lambda h: start_listening(h)),
    "german": ("a German lesson", 6, lambda h: start_german(h)),
}
# Planned activities not built yet fall back to their nearest neighbour.
PLAN_FALLBACK = {"greview": "german"}


def resolve_plan(ids):
    out = []
    for a in ids:
        a = a if a in ACTIVITIES else PLAN_FALLBACK.get(a)
        if a and a not in out:
            out.append(a)
    return out


def plan_pending(s):
    """The next activity id in today's plan (offered or accepted), or None."""
    pl = s.get("plan")
    if pl and pl["i"] < len(pl["items"]):
        return pl["items"][pl["i"]]
    return None


def plan_active(s):
    """True once the user has accepted today's plan. An offered plan the
    user ignored must not change how other activities end."""
    return bool((s.get("plan") or {}).get("active"))


def spoken_list(items):
    if len(items) <= 2:
        return " and ".join(items)
    return ", ".join(items[:-1]) + ", and " + items[-1]


def countdown_line(left):
    if left is None:
        return ""
    if left > 1:
        return "%d days to your exam. " % left
    if left == 1:
        return "Your exam is tomorrow. "
    if left == 0:
        return "Your exam is today. Good luck! "
    return "Your exam is done, so German is the main track now. "


def offer_today(h, prefix=""):
    s, p = sess(h), persist(h)
    today = local_today(h)
    if p.get("plan_date") != today.isoformat():
        p["plan_day"] = int(p.get("plan_day", -1)) + 1
        p["plan_date"] = today.isoformat()
        save_persist(h)
    left = plan.days_left(today, p.get("exam_date"))
    items = resolve_plan(plan.todays_plan(left, int(p.get("plan_day", 0))))
    s["plan"] = {"items": items, "i": 0, "active": False}
    s["mode"] = MENU
    days_streak = plan.streak(p.get("days"), today)
    streak = ("You're on a %d-day streak. " % days_streak
              if days_streak >= 2 else "")
    minutes = sum(ACTIVITIES[a][1] for a in items)
    speech = (prefix + countdown_line(left) + streak +
              "Today: %s. About %d minutes. Say yes to start, or ask for "
              "something else, like mock test or German lesson."
              % (spoken_list([ACTIVITIES[a][0] for a in items]), minutes))
    return ask(h, speech, "Say yes to start today's plan, or say menu.")


def start_next_planned(h):
    s = sess(h)
    nxt = plan_pending(s)
    if not nxt:
        return go_menu(h)
    s["plan"]["i"] += 1
    s["plan"]["active"] = True
    return ACTIVITIES[nxt][2](h)


def finish(h, done, tail, reprompt, card_title=None, card_text=None):
    """End an activity: offer the next planned one, or the usual options."""
    s = sess(h)
    if not plan_active(s):
        return ask(h, "%s %s" % (done, tail), reprompt, card_title, card_text)
    nxt = plan_pending(s)
    if nxt:
        label = ACTIVITIES[nxt][0]
        return ask(h, "%s %s Next on today's plan: %s. Say next when you're "
                      "ready, or menu to stop." % (done, brk(0.4), label),
                   "Say next for %s, or menu." % label, card_title, card_text)
    s.pop("plan", None)
    return ask(h, "%s %s That's today's plan done. Nice work, see you "
                  "tomorrow. Say menu if you want more practice, or stop."
               % (done, brk(0.4)), MENU_SPEECH, card_title, card_text)


def start_setup(h, prefix=""):
    sess(h)["mode"] = SETUP_EXAM
    return ask(h, prefix + "First, when is your IELTS exam? Say a date, like "
                           "October the twenty-eighth, or say skip.",
               "When is your IELTS exam? Say a date, or say skip.")


def _date_words(d):
    return "%s, the <say-as interpret-as='ordinal'>%d</say-as> of %s" % (
        d.strftime("%A"), d.day, d.strftime("%B"))


def save_exam_date(h, text):
    """Store the exam date; return confirmation SSML, or None if no date."""
    today = local_today(h)
    d = plan.parse_exam_date(text, today)
    if d is None:
        return None
    p = persist(h)
    p["exam_date"] = d.isoformat()
    save_persist(h)
    left = (d - today).days
    when = {0: "that's today", 1: "that's tomorrow"}.get(
        left, "%d days away" % left)
    return "Got it: %s, %s. " % (_date_words(d), when)


NO_DATE = ("Sorry, I didn't catch a date. Say it like: October the "
           "twenty-eighth. Or say skip.")


def ask_practice_cue(h, prefix=""):
    sess(h)["mode"] = SETUP_CUE
    return ask(h, prefix + "When and where will you practise each day? For "
                           "example: after breakfast, at my desk. Or say skip.",
               "When and where will you practise? Or say skip.")


def finish_setup(h, cue=None):
    p = persist(h)
    p["setup_done"] = True
    prefix = "No problem. "
    if cue:
        cue = cue.strip().rstrip(".")[:80]
        p["practice_cue"] = cue
        prefix = ("Great. Your plan: %s, say: Alexa, open study coach. An Alexa "
                  "Routine in the Alexa app can do that for you at the same "
                  "time each day. " % esc(cue))
    save_persist(h)
    return offer_today(h, prefix + brk(0.4))


def setup_answer(h, text):
    if sess(h).get("mode") == SETUP_EXAM:
        confirm = save_exam_date(h, text)
        if confirm is None:
            return ask(h, NO_DATE, NO_DATE)
        return ask_practice_cue(h, confirm)
    return finish_setup(h, text)


def set_exam_date(h):
    confirm = save_exam_date(h, slot(h, "date") or "")
    if confirm is None:
        return ask(h, NO_DATE, NO_DATE)
    if sess(h).get("mode") == SETUP_EXAM:
        return ask_practice_cue(h, confirm)
    return ask(h, confirm + "Say today's plan to start, or " + MENU_SPEECH,
               MENU_SPEECH)


def progress(h):
    p = persist(h)
    today = local_today(h)
    days = p.get("days") or []
    hist = p.get("history") or []
    if not (days or hist or p.get("mocks") or p.get("german_next")):
        text = ("No practice logged yet, so this is your first session. "
                "Finish one activity today to start your streak. Say today's "
                "plan to begin.")
        return ask(h, esc(text), MENU_SPEECH, "Your progress", text)
    lines = [countdown_line(plan.days_left(today, p.get("exam_date"))).strip()]
    n = plan.streak(days, today)
    lines.append({0: "No streak right now: practise today to start one.",
                  1: "Your streak is one day. Come back tomorrow to grow it."}
                 .get(n, "You're on a %d-day streak." % n))
    mocks = int(p.get("mocks", 0))
    lines.append("%d mock test%s done." % (mocks, "" if mocks == 1 else "s")
                 if mocks else "No full mock test yet.")
    if p.get("p2_best_pace"):
        lines.append("Best Part 2 pace: about %d words a minute, a rough "
                     "figure." % int(p["p2_best_pace"]))
    if p.get("focus"):
        lines.append("Your focus: %s." % p["focus"].get("label",
                                                         p["focus"]["say"]))
    lines.append("German lesson %d of %d is next." % (
        int(p.get("german_next", 0)) + 1, len(GERMAN_LESSONS)))
    if hist:
        first = hist[-1].get("feedback", "").split(". ")[0].rstrip(".")[:160]
        lines.append("Last feedback: %s." % first)
    text = " ".join(line for line in lines if line)
    return ask(h, esc(text) + " Say today's plan to keep going.",
               "Say today's plan, or menu.", "Your progress", text)


# ---------------------------------------------------------------------------
# Routing free-form answers
# ---------------------------------------------------------------------------
COMMANDS = {
    "feedback": "feedback", "give me feedback": "feedback",
    "how did i do": "feedback",
    "i'm finished": "finished", "im finished": "finished",
    "i am finished": "finished", "finished": "finished", "i'm done": "finished",
    "i am done": "finished", "done": "finished", "that's all": "finished",
    "repeat": "repeat", "menu": "menu", "main menu": "menu",
    "next": "next", "skip": "next", "next question": "next",
}


def route_answer(h, text):
    s = sess(h)
    mode = s.get("mode", MENU)
    norm = (text or "").lower().strip(" .!?")
    cmd = COMMANDS.get(norm)
    if cmd == "feedback":
        return give_feedback(h)
    if cmd == "repeat":
        return do_repeat(h)
    if cmd == "menu":
        return go_menu(h)
    if cmd == "finished":
        return do_next(h) if mode in (P1, P3, RETRY) else _finished(h)
    if cmd == "next":
        return do_next(h)
    if mode == P1:
        return answer_part1(h, text)
    if mode == P2:
        return answer_part2(h, text)
    if mode == P3:
        return answer_part3(h, text)
    if mode == LISTEN:
        return answer_listening(h, text)
    if mode == GQUIZ:
        return answer_german(h, text)
    if mode in (SETUP_EXAM, SETUP_CUE):
        return setup_answer(h, text)
    if mode == RETRY:
        return answer_retry(h, text)
    if plan_pending(s) and norm in YES_WORDS:
        return start_next_planned(h)
    return ask(h, "Sorry, I didn't get that. " + MENU_SPEECH, MENU_SPEECH)


def go_menu(h):
    s = sess(h)
    s["mode"] = MENU
    s.pop("plan", None)   # leaving the menu way means leaving today's plan
    return ask(h, "Main menu. " + MENU_SPEECH, MENU_SPEECH)


def do_repeat(h):
    s = sess(h)
    if s.get("mode") == LISTEN:
        L = s["listen"]
        q = L["items"][L["i"]]["q"]
        return ask(h, "In the exam you only hear it once, but here it is "
                      "again. %s %s %s" % (L["dialog"], brk(0.8), esc(q)),
                   esc(q))
    speech = s.get("last_speech")
    if not speech:
        return go_menu(h)
    return ask(h, speech, s.get("last_reprompt") or MENU_SPEECH)


def do_next(h):
    s = sess(h)
    mode = s.get("mode", MENU)
    if mode == SETUP_EXAM:          # "skip" the exam date
        return ask_practice_cue(h, "Okay. You can tell me later: say, my exam "
                                   "is on, then the date. ")
    if mode == SETUP_CUE:
        return finish_setup(h)
    if mode == RETRY:
        return answer_retry(h, "", skipped=True)
    if mode == MENU and plan_pending(s):
        return start_next_planned(h)
    if mode == P1:
        return answer_part1(h, "(skipped)")
    if mode == P3:
        return answer_part3(h, "(skipped)")
    if mode == P2:
        return answer_part2(h, "", finished=True)
    if mode == LISTEN:
        return answer_listening(h, "")
    if mode == GQUIZ:
        return answer_german(h, "")
    return go_menu(h)


# ---------------------------------------------------------------------------
# Request handlers
# ---------------------------------------------------------------------------
class Launch(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        h = handler_input
        p = persist(h)
        p["visits"] = int(p.get("visits", 0)) + 1
        sess(h)["mode"] = MENU
        save_persist(h)
        if not p.get("setup_done"):
            return start_setup(h, prefix=(
                "Welcome to your IELTS and German coach. I run speaking mock "
                "tests, listening drills and German lessons, and plan each "
                "day's practice for you. "))
        return offer_today(h, prefix="Welcome back. ")


class Intent(AbstractRequestHandler):
    """Dispatch table for simple intents."""
    def __init__(self, name, fn):
        self.name, self.fn = name, fn

    def can_handle(self, handler_input):
        return is_intent_name(self.name)(handler_input)

    def handle(self, handler_input):
        return self.fn(handler_input)


def _answer(h):
    return route_answer(h, slot(h, "answer") or "")


def _finished(h):
    if sess(h).get("mode") == P2:
        return answer_part2(h, "", finished=True)
    return ask(h, "Okay. Say feedback to hear how you did, or " + MENU_SPEECH,
               MENU_SPEECH)


def _fallback(h):
    s = sess(h)
    mode = s.get("mode", MENU)
    if mode == P2:  # keep a long talk flowing even if a chunk wasn't understood
        return answer_part2(h, "")
    if mode in (P1, P3, LISTEN, GQUIZ, SETUP_EXAM, SETUP_CUE, RETRY):
        return ask(h, "Sorry, I didn't catch that. " +
                   (s.get("last_reprompt") or ""),
                   s.get("last_reprompt") or MENU_SPEECH)
    return ask(h, "Sorry, I didn't get that. " + MENU_SPEECH, MENU_SPEECH)


def _help(h):
    mode = sess(h).get("mode", MENU)
    tips = {
        P1: "Answer the question in two or three sentences. Say next to skip it.",
        P2: "Keep talking about your topic. Say I'm finished when you're done.",
        P3: "Give your opinion, explain why, and give an example. Say next to skip.",
        LISTEN: "Answer the question about the phone call. Say repeat to hear "
                "the call again.",
        GQUIZ: "Tell me what the German phrase means in English. Say next to skip.",
        SETUP_EXAM: "Tell me your IELTS exam date, like October the "
                    "twenty-eighth, or say skip.",
        SETUP_CUE: "Tell me when and where you'll practise, like after "
                   "breakfast at my desk, or say skip.",
        RETRY: "Answer the question again, using the phrase I suggested. "
               "Say skip to move on.",
    }
    tip = tips.get(mode, "")
    return ask(h, (tip + " " if tip else "") + MENU_SPEECH + " You can also "
               "say feedback at any time.", MENU_SPEECH)


def _stop(h):
    return tell(h, "Good luck with your practice. " + german("Bis bald!"))


class StampStart(AbstractRequestInterceptor):
    """Record when handling began, for reply_deadline()."""

    def process(self, handler_input):
        handler_input.attributes_manager.request_attributes["started"] = \
            time.monotonic()


class SessionEnded(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        save_persist(handler_input)
        return handler_input.response_builder.response


class Errors(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        return handler_input.response_builder.speak(
            "Sorry, something went wrong. Say menu to start again.").ask(
            MENU_SPEECH).response


def _part2(h):
    sess(h)["mock"] = False
    return start_part2(h)


def _part3(h):
    sess(h)["mock"] = False
    return start_part3(h)


def _listening(h):
    accent = (slot(h, "accent") or "").lower()
    aliases = {"uk": "british", "english": "british", "britain": "british",
               "aussie": "australian", "australia": "australian",
               "us": "american", "usa": "american", "canadian": "american"}
    accent = aliases.get(accent, accent)
    return start_listening(h, accent if accent in ACCENTS else None)


def build_skill_builder():
    adapter = None
    table = os.environ.get("DYNAMODB_PERSISTENCE_TABLE_NAME")
    if table:
        try:
            import boto3
            from ask_sdk_dynamodb.adapter import DynamoDbAdapter
            from botocore.config import Config
            # Same-region DynamoDB answers in milliseconds; botocore's
            # 60 s defaults with retries would blow the reply window.
            adapter = DynamoDbAdapter(
                table_name=table, create_table=False,
                dynamodb_resource=boto3.resource(
                    "dynamodb",
                    region_name=os.environ.get("DYNAMODB_PERSISTENCE_REGION"),
                    config=Config(connect_timeout=1, read_timeout=1,
                                  retries={"max_attempts": 0})))
        except Exception as exc:
            logger.warning("DynamoDB persistence disabled: %s", exc)
    sb = CustomSkillBuilder(persistence_adapter=adapter,
                            api_client=TimeoutApiClient())
    sb.add_request_handler(Launch())
    for name, fn in [
        ("MockTestIntent", lambda h: start_part1(h, mock=True)),
        ("PartOneIntent", lambda h: start_part1(h, mock=False)),
        ("PartTwoIntent", _part2),
        ("PartThreeIntent", _part3),
        ("FeedbackIntent", give_feedback),
        ("FinishedIntent", _finished),
        ("ListeningDrillIntent", _listening),
        ("GermanLessonIntent", lambda h: start_german(h, slot(h, "lesson"))),
        ("FluencyRoundsIntent", lambda h: start_part2(h, rounds=True)),
        ("TodayIntent", offer_today),
        ("ProgressIntent", progress),
        ("SetExamDateIntent", set_exam_date),
        ("AnswerIntent", _answer),
        ("MenuIntent", go_menu),
        ("AMAZON.NavigateHomeIntent", go_menu),
        ("AMAZON.RepeatIntent", do_repeat),
        ("AMAZON.NextIntent", do_next),
        ("AMAZON.HelpIntent", _help),
        ("AMAZON.FallbackIntent", _fallback),
        ("AMAZON.StopIntent", _stop),
        ("AMAZON.CancelIntent", _stop),
    ]:
        sb.add_request_handler(Intent(name, fn))
    sb.add_request_handler(SessionEnded())
    sb.add_global_request_interceptor(StampStart())
    sb.add_exception_handler(Errors())
    return sb


sb = build_skill_builder()
lambda_handler = sb.lambda_handler()
