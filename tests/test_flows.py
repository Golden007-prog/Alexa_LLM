# -*- coding: utf-8 -*-
"""Offline simulation of real Alexa request envelopes through the skill.
Run:  pip install ask-sdk-core  &&  python tests/test_flows.py
  or: pytest tests
"""
import contextlib
import json
import os
import re
import socket
import sys
import threading
import time
import urllib.request
import uuid
import xml.dom.minidom
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "lambda"))

import lambda_function as lf  # noqa: E402
from coach import (feedback, fluency, listening, llm, numbers,  # noqa: E402
                   plan, srs, vocab)
from coach.content import CUE_CARDS, GERMAN_LESSONS, PHRASES  # noqa: E402
from datetime import date  # noqa: E402

# Alexa limits (SSML reference / response JSON reference)
MAX_SPEECH_CHARS = 8000
MAX_AUDIO_SECONDS, MAX_REPROMPT_SECONDS = 240, 90
MAX_RESPONSE_BYTES = 24000
MAX_CARD_CHARS = 8000
# Rough Polly pace, deliberately slow so the audio estimate errs long
EST_WORDS_PER_SECOND = 2.3
POLLY_VOICES = ["Ivy", "Joanna", "Joey", "Justin", "Kendra", "Kimberly",
                "Matthew", "Salli", "Nicole", "Russell", "Amy", "Brian",
                "Emma", "Aditi", "Raveena", "Hans", "Marlene", "Vicki"]
DIGIT_WORD = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
              "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}


def est_seconds(ssml):
    """Rough spoken length: break time plus words at a slow Polly pace."""
    pauses = sum(int(ms) for ms in re.findall(r"<break time='(\d+)ms'/>", ssml))
    return pauses / 1000.0 + len(text_of(ssml).split()) / EST_WORDS_PER_SECOND


def check_ssml(ssml, max_seconds, what):
    assert len(ssml) <= MAX_SPEECH_CHARS, "%s is %d chars" % (what, len(ssml))
    try:
        xml.dom.minidom.parseString(ssml)
    except Exception as exc:
        raise AssertionError("%s is not well-formed SSML: %s" % (what, exc))
    for ms in re.findall(r"<break time='(\d+)ms'/>", ssml):
        assert int(ms) <= 10000, "%s has a break over 10 s" % what
    spoken = text_of(ssml)
    for name in POLLY_VOICES:
        assert not re.search(r"\b%s\b" % name, spoken), \
            "%s speaks the voice name %s" % (what, name)
    secs = est_seconds(ssml)
    assert secs <= max_seconds, "%s runs about %d s" % (what, secs)


def check_response(out):
    """Every Alexa limit the skill can break, checked on each response."""
    size = len(json.dumps(out))
    assert size < MAX_RESPONSE_BYTES, "response too large: %d bytes" % size
    resp = out["response"]
    ssml = (resp.get("outputSpeech") or {}).get("ssml", "")
    if ssml:
        check_ssml(ssml, MAX_AUDIO_SECONDS, "outputSpeech")
    reprompt = ((resp.get("reprompt") or {}).get("outputSpeech") or {}) \
        .get("ssml", "")
    if reprompt:
        check_ssml(reprompt, MAX_REPROMPT_SECONDS, "reprompt")
    card = resp.get("card") or {}
    card_len = len(card.get("title") or "") + len(card.get("content") or "")
    assert card_len <= MAX_CARD_CHARS, "card is %d chars" % card_len


@contextlib.contextmanager
def black_hole():
    """A local port that accepts connections but never answers, standing in
    for a stalled network dependency."""
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(16)
    try:
        yield srv.getsockname()[1]
    finally:
        srv.close()


@contextlib.contextmanager
def env(**values):
    old = {k: os.environ.get(k) for k in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def run_within(seconds, fn):
    """Run fn in a daemon thread; return (finished, elapsed, result)."""
    box = {}

    def target():
        try:
            box["result"] = fn()
        except BaseException as exc:  # surfaced below
            box["error"] = exc

    start = time.monotonic()
    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(seconds)
    if "error" in box:
        raise box["error"]
    return not worker.is_alive(), time.monotonic() - start, box.get("result")


class Sim:
    """One simulated user. Starts from a returning user's saved state
    (setup done) unless fresh=True; store= presets saved attributes."""

    def __init__(self, locale="en-IN", api_endpoint="http://127.0.0.1:9",
                 handler=None, fresh=False, store=None):
        lf._LOCAL_STORE.clear()
        if not fresh:
            lf._LOCAL_STORE.update({"visits": 1, "setup_done": True})
        lf._LOCAL_STORE.update(store or {})
        self.attrs = {}
        self.new = True
        self.locale = locale
        self.api_endpoint = api_endpoint
        self.handler = handler or lf.lambda_handler
        self.clock = datetime(2026, 10, 4, 7, 0, 0, tzinfo=timezone.utc)
        self.session_id = "amzn1.echo-api.session." + str(uuid.uuid4())

    def _env(self, request):
        return {
            "version": "1.0",
            "session": {"new": self.new, "sessionId": self.session_id,
                        "application": {"applicationId": "amzn1.ask.skill.test"},
                        "attributes": self.attrs,
                        "user": {"userId": "amzn1.ask.account.TEST"}},
            "context": {"System": {
                "application": {"applicationId": "amzn1.ask.skill.test"},
                "user": {"userId": "amzn1.ask.account.TEST"},
                "device": {"deviceId": "dev", "supportedInterfaces": {}},
                "apiEndpoint": self.api_endpoint, "apiAccessToken": "x"}},
            "request": request,
        }

    def send(self, request, advance=5):
        self.clock += timedelta(seconds=advance)
        request.setdefault("requestId", "amzn1.echo-api.request." + str(uuid.uuid4()))
        request["timestamp"] = self.clock.strftime("%Y-%m-%dT%H:%M:%SZ")
        request["locale"] = self.locale
        out = self.handler(self._env(request), None)
        self.new = False
        self.attrs = out.get("sessionAttributes") or {}
        check_response(out)
        resp = out["response"]
        return resp, (resp.get("outputSpeech") or {}).get("ssml", "")

    def launch(self):
        return self.send({"type": "LaunchRequest"})

    def intent(self, name, advance=5, **slots):
        return self.send({"type": "IntentRequest", "intent": {
            "name": name, "confirmationStatus": "NONE",
            "slots": {k: {"name": k, "value": v, "confirmationStatus": "NONE"}
                      for k, v in slots.items()}}}, advance)

    def say(self, text, advance=8):
        return self.intent("AnswerIntent", advance, answer=text)


def text_of(ssml):
    return re.sub(r"<[^>]+>", " ", ssml)


def test_numbers():
    assert numbers.extract_numbers("the fifteenth of March") == [15]
    assert numbers.extract_numbers("twenty-first") == [21]
    assert numbers.extract_numbers("March 15th 2026") == [15, 2026]
    assert numbers.extract_numbers("thirty five guests") == [35]
    assert numbers.spoken_digits("oh seven nine double four, 1 2") == "0794412"
    assert numbers.spoken_digits("zero four triple one") == "04111"
    assert numbers.letters_only("T. H. O. R. N.") == "thorn"


def test_listening_checks():
    d = listening.make_drill("british", seed=3)
    xml.dom.minidom.parseString("<speak>%s</speak>" % d["dialog"])
    sur, phone, day, num, _choice = d["items"]
    assert listening.check(sur, " ".join(sur["value"].upper()))[0]
    assert listening.check(sur, sur["value"].lower())[0]
    assert not listening.check(sur, "smith")[0]
    spoken = " ".join(DIGIT_WORD[c] for c in phone["value"])
    assert listening.check(phone, spoken)[0]
    assert listening.check(day, "the %dth of %s" % (day["value"], day["month"]))[0]
    assert listening.check(num, "%d %s" % (num["value"], num["unit"]))[0]
    for acc in ("australian", "american"):
        d2 = listening.make_drill(acc, seed=1)
        xml.dom.minidom.parseString("<speak>%s</speak>" % d2["dialog"])
        assert d2["label"]


def test_mock_test_rule_based():
    llm._cache.clear()
    os.environ["LLM_PROVIDER"] = "none"
    sim = Sim()
    _, s = sim.launch()
    assert "mock test" in s
    _, s = sim.intent("MockTestIntent")
    assert "Part 1" in s
    for i in range(6):
        _, s = sim.say("I live in Bengaluru because my job is here and the "
                       "weather is very good for example in winter", 15)
    assert "Part 2" in text_of(s) and s.count("<break") >= 6
    # talk in chunks for ~2 minutes
    for i in range(12):
        resp, s = sim.say("the skill i want to describe is cooking which i "
                          "learned from my mother when i was a teenager and "
                          "it took a long time because", 16)
        if "Part 3" in s:
            break
    assert "Part 3" in s, s
    for i in range(3):
        resp, s = sim.say("I think young people should learn cooking because "
                          "it is very good for their health", 15)
    assert "end of the speaking test" in s or "linking" in s
    assert resp.get("card", {}).get("title") == "Speaking feedback"
    assert sim.attrs.get("mode") == "retry"      # feedback ends with a retry
    _, s2 = sim.intent("AMAZON.RepeatIntent")
    assert s2 == s


def test_ai_feedback_path():
    sim = Sim()
    sim.launch()
    sim.intent("PartOneIntent")
    for _ in range(6):
        sim.say("My hometown is Kolkata. It is famous for its food.")
    orig = llm.generate
    llm._cache.clear()
    llm._cache.update({"provider": "gemini", "api_key": "k", "model": "m",
                       "timeout_seconds": 1.0, "gemini_thinking_level": ""})
    llm.generate = lambda system, prompt, max_tokens=700, deadline=None: (
        "**Fluency** six to six point five. You said & repeated *good* a lot.")
    try:
        resp, s = sim.intent("FeedbackIntent")
    finally:
        llm.generate = orig
        llm._cache.clear()
    assert "&amp;" in s and "**" not in s and "six to six point five" in s
    assert sim.attrs.get("transcript") == []


def test_part2_finished_early():
    sim = Sim()
    sim.launch()
    sim.intent("PartTwoIntent")
    sim.say("I want to talk about my grandmother", 10)
    _, s = sim.intent("FinishedIntent")
    assert "under a minute" in s
    _, s = sim.intent("PartThreeIntent")
    assert "Part 3" in s
    _, s = sim.say("finished")  # command spoken as free text -> skip question
    assert sim.attrs["mode"] == "p3"


def test_listening_flow():
    sim = Sim()
    sim.launch()
    _, s = sim.intent("ListeningDrillIntent", accent="aussie")
    assert "Australian" in s and ("Nicole" in s or "Russell" in s)
    items = sim.attrs["listen"]["items"]
    _, s = sim.intent("AMAZON.RepeatIntent")
    assert "only hear it once" in s
    sim.say(" ".join(items[0]["value"].lower()))
    sim.say("I don't know")
    sim.say("the %d" % items[2]["value"])
    sim.say("%d" % items[3]["value"])
    _, s = sim.say("I'm not sure")
    assert "You scored 3 out of 5" in s, s


def test_german_flow():
    lf._LOCAL_STORE.clear()
    sim = Sim()
    sim.launch()
    resp, s = sim.intent("GermanLessonIntent")
    assert "German lesson 1 of 21" in s and "de-DE" in s and "Vicki" in s
    assert resp["card"]["title"].startswith("German lesson 1")
    for _ in range(5):
        item = sim.attrs["ger"]["items"][sim.attrs["ger"]["i"]]
        _, s = sim.say(item["en"])
    assert "5 out of 5" in s
    assert lf._LOCAL_STORE["german_next"] == 1
    _, s = sim.intent("GermanLessonIntent")
    assert "German lesson 2 of 21" in s
    _, s = sim.intent("GermanLessonIntent", lesson="19")
    assert "Review" in s and sim.attrs["ger"]["lesson"] == 18
    _, s = sim.intent("GermanLessonIntent", lesson="20")
    assert len(sim.attrs["ger"]["items"]) == 5


def test_every_lesson_self_consistent():
    for idx, lesson in enumerate(GERMAN_LESSONS):
        phrases = lf.lesson_phrases(idx)
        assert len(phrases) == 5, lesson["title"]
        for ph in phrases:
            assert lf.german_correct(ph, ph["en"]), (ph["de"], ph["en"])
            assert not lf.german_correct(ph, "banana"), ph["de"]


def test_cards():
    for c in CUE_CARDS:
        assert len(c["points"]) == 3 and len(c["part3"]) == 3


def test_fallback_and_help():
    sim = Sim()
    sim.launch()
    sim.intent("PartOneIntent")
    _, s = sim.intent("AMAZON.FallbackIntent")
    assert "didn't catch" in s
    _, s = sim.intent("AMAZON.HelpIntent")
    assert "two or three sentences" in s
    resp, s = sim.intent("AMAZON.StopIntent")
    assert resp.get("shouldEndSession") is True


def test_gemini_request_shape():
    captured = {}

    class FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"candidates": [{"content": {"parts": [
                {"text": "thinking...", "thought": True},
                {"text": "Band six."}]}}]}).encode()

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["body"] = json.loads(req.data.decode())
        captured["headers"] = dict(req.header_items())
        captured["timeout"] = timeout
        return FakeResp()

    orig = llm.urllib.request.urlopen
    llm.urllib.request.urlopen = fake_urlopen
    llm._cache.clear()
    llm._cache.update({"provider": "gemini", "api_key": "KEY",
                       "model": "gemini-3.5-flash-lite", "timeout_seconds": 5.5,
                       "gemini_thinking_level": ""})
    try:
        out = llm.generate("sys", "hello")
    finally:
        llm.urllib.request.urlopen = orig
        llm._cache.clear()
    assert out == "Band six."
    assert captured["url"].endswith("gemini-3.5-flash-lite:generateContent")
    assert captured["body"]["systemInstruction"]["parts"][0]["text"] == "sys"
    assert "thinkingConfig" not in captured["body"]["generationConfig"]
    assert captured["headers"].get("X-goog-api-key") == "KEY"


def test_response_guard_rejects_bad_output():
    def out(ssml, reprompt="<speak>Say menu.</speak>", card=None):
        resp = {"outputSpeech": {"type": "SSML", "ssml": ssml},
                "reprompt": {"outputSpeech": {"type": "SSML",
                                              "ssml": reprompt}}}
        if card:
            resp["card"] = card
        return {"version": "1.0", "response": resp}

    check_response(out("<speak>Hello.</speak>"))
    bad = [
        out("<speak>%s</speak>" % ("word " * 1700)),               # > 8000 chars
        out("<speak>Hi.</speak>", reprompt="<speak><break></speak>"),
        out("<speak>Hi.</speak>", reprompt="<speak>%s</speak>"
            % ("<break time='10000ms'/>" * 10)),                   # > 90 s
        out("<speak>%s</speak>" % ("<break time='10000ms'/>" * 25)),  # > 240 s
        out("<speak><break time='12000ms'/></speak>"),
        out("<speak>I am Vicki, your coach.</speak>"),
        out("<speak>Hi.</speak>", card={"type": "Simple", "title": "t",
                                       "content": "x" * 8001}),
    ]
    for i, o in enumerate(bad):
        try:
            check_response(o)
        except AssertionError:
            continue
        raise AssertionError("bad response %d slipped through" % i)


def test_no_deprecated_sdk_calls_in_skill_code():
    import warnings
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        sim = Sim()
        sim.launch()
        sim.intent("ListeningDrillIntent", accent="british")
        sim.say("thornton")
    ours = [w for w in caught if issubclass(w.category, DeprecationWarning)
            and os.sep + "lambda" + os.sep in os.path.normpath(w.filename)]
    assert not ours, [str(w.message)[:80] for w in ours]


def _model(locale):
    path = os.path.join(ROOT, "skill-package", "interactionModels", "custom",
                        locale + ".json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def test_interaction_models_match_handlers():
    with open(os.path.join(ROOT, "skill-package", "skill.json"),
              encoding="utf-8") as fh:
        manifest = json.load(fh)["manifest"]
    locales = sorted(manifest["publishingInformation"]["locales"])
    assert "en-IN" in locales
    models = {loc: _model(loc) for loc in locales}
    # one shared model: any locale-specific edit must be made on purpose
    for loc in locales:
        assert models[loc] == models["en-IN"], "%s differs from en-IN" % loc
    lm = models["en-IN"]["interactionModel"]["languageModel"]
    assert lm["invocationName"] == "study coach"
    declared = {i["name"] for i in lm["intents"]}
    chains = lf.sb.runtime_configuration_builder.request_handler_chains
    handled = {c.request_handler.name for c in chains
               if hasattr(c.request_handler, "name")}
    assert declared - handled == set(), declared - handled
    assert handled - declared == set(), handled - declared
    slot_types = {t["name"] for t in lm.get("types", [])}
    for intent in lm["intents"]:
        for s in intent.get("slots", []):
            assert s["type"].startswith("AMAZON.") or s["type"] in slot_types


def test_s3_config_read_gives_up_quickly():
    llm._cache.clear()
    with black_hole() as port, env(
            S3_PERSISTENCE_BUCKET="coach-bucket",
            AWS_ENDPOINT_URL_S3="http://127.0.0.1:%d" % port,
            AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
            AWS_DEFAULT_REGION="us-east-1"):
        done, secs, cfg = run_within(6, llm._from_s3)
    assert done, "S3 config read still blocked after 6 s"
    assert secs < 3, secs
    assert cfg == {}


def test_dynamodb_stall_does_not_hang_launch():
    with black_hole() as port, env(
            DYNAMODB_PERSISTENCE_TABLE_NAME="coach-table",
            DYNAMODB_PERSISTENCE_REGION="us-east-1",
            AWS_ENDPOINT_URL_DYNAMODB="http://127.0.0.1:%d" % port,
            AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test"):
        sim = Sim(handler=lf.build_skill_builder().lambda_handler(),
                  fresh=True)
        done, secs, result = run_within(10, sim.launch)
    assert done, "launch still blocked after 10 s"
    # one failed load per request, not one per persist() call
    assert secs < 2.5, "launch took %.1f s" % secs
    # can't load progress: treat as a returning user, don't re-run setup
    assert "Today:" in result[1] and "when is your" not in result[1]


def test_llm_timeout_capped_at_5_5_seconds():
    llm._cache.clear()
    with env(LLM_PROVIDER="gemini", LLM_API_KEY="k", LLM_TIMEOUT_SECONDS="30"):
        try:
            assert llm.get_config()["timeout_seconds"] == 5.5
        finally:
            llm._cache.clear()


def test_feedback_fits_alexa_window_when_network_hangs():
    """Progressive response, S3 config and the LLM all stall. The reply
    must still land inside Alexa's ~8 s window, with rule-based tips."""
    llm._cache.clear()
    real_urlopen = llm.urllib.request.urlopen
    with black_hole() as port, env(
            S3_PERSISTENCE_BUCKET="coach-bucket",
            AWS_ENDPOINT_URL_S3="http://127.0.0.1:%d" % port,
            AWS_ACCESS_KEY_ID="test", AWS_SECRET_ACCESS_KEY="test",
            AWS_DEFAULT_REGION="us-east-1",
            LLM_PROVIDER="gemini", LLM_API_KEY="k"):
        sim = Sim(api_endpoint="https://127.0.0.1:%d" % port)
        sim.launch()
        sim.intent("PartOneIntent")
        sim.say("My hometown is Kolkata. It is famous for its food.")
        llm.urllib.request.urlopen = lambda req, timeout: real_urlopen(
            urllib.request.Request("https://127.0.0.1:%d/" % port,
                                   data=req.data, method="POST"),
            timeout=timeout)
        try:
            done, secs, result = run_within(
                12, lambda: sim.intent("FeedbackIntent"))
        finally:
            llm.urllib.request.urlopen = real_urlopen
            llm._cache.clear()
    assert done, "feedback still blocked after 12 s"
    assert secs < 7.5, "feedback took %.1f s" % secs
    _, s = result
    assert "Aim for two or three sentences" in s, s


# ---------------------------------------------------------------------------
# Daily plan, countdown, streak, progress, one-shot entry points
# ---------------------------------------------------------------------------
def test_local_date_uses_ist_for_en_in():
    late = datetime(2026, 10, 3, 20, 0, tzinfo=timezone.utc)   # 01:30 IST
    assert plan.local_date(late, "en-IN") == date(2026, 10, 4)
    assert plan.local_date(late, "en-US") == date(2026, 10, 3)


def test_parse_exam_date():
    today = date(2026, 10, 4)
    want = date(2026, 10, 28)
    for text in ("october twenty eighth", "the twenty eighth of october",
                 "28th october", "October 28", "2026-10-28",
                 "my exam is on the 28th of October"):
        assert plan.parse_exam_date(text, today) == want, text
    assert plan.parse_exam_date("in three weeks", today) == date(2026, 10, 25)
    assert plan.parse_exam_date("in 10 days", today) == date(2026, 10, 14)
    assert plan.parse_exam_date("march fifth", today) == date(2027, 3, 5)
    assert plan.parse_exam_date("the first of october", today) == \
        date(2027, 10, 1)
    for text in ("i don't know", "", "2026-W43", "february thirtieth"):
        assert plan.parse_exam_date(text, today) is None, text


def test_streak_and_day_log():
    days = []
    for d in ("2026-10-01", "2026-10-02", "2026-10-03", "2026-10-03"):
        days = plan.record_day(days, date.fromisoformat(d))
    assert days == ["2026-10-01", "2026-10-02", "2026-10-03"]
    assert plan.streak(days, date(2026, 10, 3)) == 3
    assert plan.streak(days, date(2026, 10, 4)) == 3   # not practised yet today
    assert plan.streak(days, date(2026, 10, 5)) == 0
    long_log = []
    for i in range(80):
        long_log = plan.record_day(long_log, date(2026, 1, 1) + timedelta(i))
    assert len(long_log) == plan.MAX_DAYS_LOGGED


def test_todays_plan_follows_countdown():
    far = [plan.todays_plan(20, d) for d in range(4)]
    assert ["mock" in p for p in far].count(True) == 1
    assert all(p[-1] == "german" for p in far)
    near = [plan.todays_plan(10, d) for d in range(2)]
    assert "mock" in near[0] and "listen" in near[1]
    assert "mock" not in plan.todays_plan(2, 0)
    assert plan.todays_plan(0, 0) == ["p1"]
    assert set(plan.todays_plan(-1, 0)) <= {"german", "greview"}
    assert plan.todays_plan(None, 1) == plan.todays_plan(30, 1)


def test_first_launch_runs_setup():
    sim = Sim(fresh=True)
    _, s = sim.launch()
    assert "when is your IELTS exam" in s
    _, s = sim.say("october twenty eighth")
    assert "24 days" in s and "When and where" in s
    _, s = sim.say("after breakfast at my desk")
    assert "after breakfast at my desk" in s and "Today:" in s
    assert lf._LOCAL_STORE["exam_date"] == "2026-10-28"
    assert lf._LOCAL_STORE["setup_done"] is True
    _, s = sim.launch()
    assert "when is your IELTS exam" not in s


def test_declined_plan_does_not_hijack_other_activities():
    sim = Sim()
    sim.launch()                                   # plan offered, not taken
    _, s = sim.intent("ListeningDrillIntent")
    for _ in sim.attrs["listen"]["items"]:
        _, s = sim.say("I don't know")
    assert "Next on today's plan" not in s and "Say listening drill" in s
    sim.say("yes")                                 # must not start the old plan
    assert sim.attrs["mode"] == "menu" and "plan" not in sim.attrs


def test_setup_can_be_skipped():
    sim = Sim(fresh=True)
    sim.launch()
    _, s = sim.say("hmm no idea")
    assert "didn't catch a date" in s
    sim.intent("AMAZON.NextIntent")
    _, s = sim.say("skip")
    assert "Today:" in s
    assert "exam_date" not in lf._LOCAL_STORE


def test_set_exam_date_any_time():
    sim = Sim()
    sim.launch()
    _, s = sim.intent("SetExamDateIntent", date="2026-11-02")
    assert "29 days" in s
    assert lf._LOCAL_STORE["exam_date"] == "2026-11-02"
    _, s = sim.intent("SetExamDateIntent", date="2026-W45")
    assert "didn't catch a date" in s


def test_launch_offers_plan_and_chains_activities():
    sim = Sim(store={"exam_date": "2026-10-06"})       # 2 days left
    _, s = sim.launch()
    assert "2 days to your exam" in s and "Today:" in s and "mock test" in s
    items = sim.attrs["plan"]["items"]
    assert items[0] == "listen"
    _, s = sim.say("yes")
    assert sim.attrs["mode"] == "listen" and "Listening drill" in s
    for _ in sim.attrs["listen"]["items"]:
        _, s = sim.say("I don't know")
    assert "Next on today's plan" in s
    sim.intent("AMAZON.NextIntent")
    assert sim.attrs["plan"]["i"] == 2


def test_today_intent_and_plan_done():
    sim = Sim(store={"exam_date": "2026-10-04"})       # exam day
    _, s = sim.intent("TodayIntent")
    assert "exam is today" in s and sim.attrs["plan"]["items"] == ["p1"]
    sim.say("ok")
    assert sim.attrs["mode"] == "p1"
    for _ in range(6):
        _, s = sim.say("I live in Bengaluru because my job is here")
    for _ in range(3):                                  # retry or done
        if "today's plan done" in s:
            break
        _, s = sim.intent("AMAZON.NextIntent")
    assert "today's plan done" in s, s


def test_progress_report():
    sim = Sim(store={
        "exam_date": "2026-10-16", "mocks": 2, "german_next": 5,
        "days": ["2026-10-02", "2026-10-03", "2026-10-04"],
        "p2_best_pace": 125,
        "focus": {"say": "although", "label": "although",
                  "accept": ["although"]},
        "history": [{"date": "2026-10-03", "ai": False,
                     "feedback": "Use more linking phrases. Second line."}]})
    resp, s = sim.intent("ProgressIntent")
    for want in ("12 days to your exam", "3-day streak", "2 mock tests",
                 "German lesson 6", "Use more linking phrases",
                 "about 125 words a minute", "Your focus: although"):
        assert want in s, (want, s)
    assert "Second line" not in s
    assert resp["card"]["title"] == "Your progress"


def test_progress_report_for_a_new_user():
    sim = Sim(fresh=True)
    _, s = sim.intent("ProgressIntent")
    assert "first session" in s


def test_activity_marks_today_once():
    sim = Sim()
    sim.launch()
    sim.intent("ListeningDrillIntent")
    sim.intent("GermanLessonIntent")
    assert lf._LOCAL_STORE["days"] == ["2026-10-04"]


def test_one_shot_entry_points():
    for intent, slots, want in [
            ("GermanLessonIntent", {}, "German lesson 1 of 21"),
            ("MockTestIntent", {}, "Part 1"),
            ("ListeningDrillIntent", {"accent": "british"}, "Listening drill"),
            ("TodayIntent", {}, "Today:"),
            ("ProgressIntent", {}, "streak")]:
        sim = Sim()
        assert sim.new
        _, s = sim.intent(intent, **slots)
        assert want in s, (intent, s)
    lm = _model("en-IN")["interactionModel"]["languageModel"]
    samples = {i["name"]: i["samples"] for i in lm["intents"]}
    assert "a german lesson" in samples["GermanLessonIntent"]
    assert "a mock test" in samples["MockTestIntent"]
    assert "a listening drill" in samples["ListeningDrillIntent"]
    for intent_samples in samples.values():
        for sample in intent_samples:
            assert not sample.startswith(("ask ", "for ", "to ")), sample


# ---------------------------------------------------------------------------
# Part 2 fluency rounds and focused feedback
# ---------------------------------------------------------------------------
STORY = ("the skill i want to describe is cooking which i learned from my "
         "mother when i was a teenager in kolkata")          # 20 words


def test_fluency_summary_numbers():
    r1 = {"words": 200, "secs": 120}
    r3 = {"words": 140, "secs": 60}
    ideas = ["cooking", "mother", "kolkata", "teenager", "skill", "learned",
             "describe", "school", "kitchen"]
    text = fluency.summary([r1, {"words": 150, "secs": 90}, r3],
                           first_content=ideas,
                           last_content=ideas + ["zebra"])   # 9 of 10 kept
    assert "about 100 to about 140 words a minute" in text
    assert "90 per cent" in text and "rough" in text
    assert fluency.pace(0, 0) == 0
    assert "cooking" in fluency.content_words(STORY)
    assert "which" not in fluency.content_words(STORY)


def test_fluency_summary_with_skipped_rounds():
    ideas = ["cooking", "mother"]
    text = fluency.summary([{"words": 200, "secs": 120},
                            {"words": 150, "secs": 90},
                            {"words": 0, "secs": 0}], ideas, [])
    assert "about 0" not in text and "about 100 to about 100" not in text
    assert "about 100" in text and "all three rounds" in text
    text = fluency.summary([{"words": 0, "secs": 0}] * 3, [], [])
    assert "about 0" not in text and "all three rounds" in text


def test_part2_fluency_rounds():
    sim = Sim()
    sim.launch()
    _, s = sim.intent("FluencyRoundsIntent")
    assert "three times" in s and "Part 2" in text_of(s)
    rounds_seen = []
    for _ in range(60):
        _, s = sim.say(STORY, 10)
        if "Round two" in s or "Round three" in s:
            rounds_seen.append(sim.attrs["p2"]["rounds"][-1]["secs"])
        if "words a minute" in s:
            break
    assert "words a minute" in s and "rough" in s
    secs = [r["secs"] for r in lf._LOCAL_STORE.get("p2_rounds_last", [])]
    assert len(secs) == 3
    assert secs[0] <= 130 and secs[1] <= 100 and secs[2] <= 70, secs
    assert lf._LOCAL_STORE["p2_best_pace"] > 0
    assert sim.attrs["transcript"][-1]["part"] == 2


def test_finished_moves_to_next_round():
    sim = Sim()
    sim.intent("FluencyRoundsIntent")
    sim.say(STORY, 10)
    _, s = sim.intent("FinishedIntent")
    assert "Round two" in s and "ninety seconds" in s


def test_feedback_prompt_asks_for_two_fixes():
    assert "two most valuable fixes" in feedback.SYSTEM_PROMPT
    assert "three most valuable" not in feedback.SYSTEM_PROMPT


def test_rule_based_gives_at_most_two_corrections():
    llm._cache.clear()
    with env(LLM_PROVIDER="none"):
        transcript = [
            {"part": 1, "q": "q", "a": "I am knowing it is very very good"},
            {"part": 1, "q": "q", "a": "Very nice"},
            {"part": 2, "q": "card", "a": "it was very good " * 10},
        ]
        text, used_ai = feedback.examiner_feedback(transcript)
    llm._cache.clear()
    markers = ["averaged", "Part 2 talk", "verbs like", "You said very",
               "linking phrases"]
    assert not used_ai
    assert sum(m in text for m in markers) == 2, text


def test_stative_progressive_tip():
    def tip(answer):
        return feedback.stative_progressive([{"part": 1, "a": answer}])
    assert "I know" in tip("Honestly I am knowing the answer")
    assert tip("She is understanding everything now")
    assert tip("I am having lunch with friends") is None
    assert tip("I am seeing a doctor tomorrow") is None


def test_retry_target_choice():
    overused = [{"part": 1, "q": "q", "a": "very good very nice very big"}]
    t = feedback.retry_target(overused)
    assert "extremely" in t["accept"] and "very" in t["say"]
    few_linkers = [{"part": 1, "q": "q", "a": "I like it because it is fun"}]
    assert feedback.retry_target(few_linkers)["accept"] == ["although"]
    rich = [{"part": 1, "q": "q", "a": "although however for example "
                                     "because on the other hand"}]
    assert feedback.retry_target(rich)["accept"] == ["in my experience"]
    t = feedback.retry_target(few_linkers)
    assert feedback.uses_target("I love it, although it is noisy", t)
    assert not feedback.uses_target("I love it a lot", t)


def test_feedback_retry_flow_and_focus_reminder():
    llm._cache.clear()
    with env(LLM_PROVIDER="none"):
        sim = Sim()
        sim.intent("PartOneIntent")
        for _ in range(6):
            sim.say("I like it because it is fun")
        _, s = sim.intent("FeedbackIntent")
        assert "lock one in" in s and sim.attrs["mode"] == "retry"
        _, s = sim.say("I like my city, although it is noisy")
        assert "you used" in s and sim.attrs["mode"] == "menu"
        assert lf._LOCAL_STORE["focus"]["accept"] == ["although"]
        _, s = sim.intent("PartOneIntent")
        assert "Remember to try" in s and "although" in s
    llm._cache.clear()


def test_retry_can_be_skipped_or_missed():
    llm._cache.clear()
    with env(LLM_PROVIDER="none"):
        sim = Sim()
        sim.intent("PartOneIntent")
        for _ in range(6):
            sim.say("I like it because it is fun")
        sim.intent("FeedbackIntent")
        _, s = sim.say("I like my city a lot")
        assert "didn't use" in s
        sim.intent("PartOneIntent")
        for _ in range(6):
            sim.say("I like it because it is fun")
        sim.intent("FeedbackIntent")
        _, s = sim.intent("AMAZON.NextIntent")
        assert sim.attrs["mode"] == "menu" and "Skipping" in s
    llm._cache.clear()


# ---------------------------------------------------------------------------
# Listening drill v2
# ---------------------------------------------------------------------------
def test_every_scenario_renders_with_one_trap():
    assert len(listening.SCENARIOS) >= 10
    for i in range(len(listening.SCENARIOS)):
        for accent in ("british", "australian", "american"):
            d = listening.make_drill(accent, seed=i, scenario=i)
            xml.dom.minidom.parseString("<speak>%s</speak>" % d["dialog"])
            traps = sum(d["dialog"].count(t) for t in listening.SELF_CORRECTIONS)
            assert traps == 1, (i, accent)
            kinds = [it["kind"] for it in d["items"]]
            assert kinds == ["surname", "digits", "day", "number", "choice"]
            choice = d["items"][4]
            for opt in choice["options"]:
                assert listening.esc(opt) in d["dialog"], (i, opt)
            assert choice["distractor"] != choice["value"]
            check_ssml("<speak>%s</speak>" % d["dialog"], MAX_AUDIO_SECONDS,
                       "dialog %d" % i)


def test_choice_answers():
    d = listening.make_drill("british", seed=1, scenario=7)  # boat tours
    item = d["items"][4]
    want = item["value"]
    letter = "abc"[want]
    variants = {"a": ["a", "option a", "ay"], "b": ["b", "bee", "option b"],
                "c": ["c", "see", "sea", "option c"]}[letter]
    for answer in variants + ["the answer is %s" % letter,
                              item["options"][want],
                              item["options"][want].replace("the ", "")]:
        assert listening.check(item, answer)[0], answer
    wrong = item["distractor"]
    ok, fb = listening.check(item, item["options"][wrong])
    assert not ok and "turned it down" in fb
    assert not listening.check(item, "I don't know")[0]
    sit = {"kind": "choice", "value": 1, "distractor": 0,
           "options": ["a buffet", "a sit-down dinner", "snacks only"]}
    assert listening.check(sit, "a sit down dinner")[0]
    assert listening.check(sit, "it was a dinner")[0]
    assert not listening.check(sit, "a buffet or a dinner")[0]


def test_accent_rotation_is_fair():
    recent, seq = [], []
    for k in range(12):
        d = listening.make_drill(seed=k, recent=recent)
        seq.append(d["accent"])
        recent = (recent + [d["accent"]])[-3:]
    for i in range(len(seq) - 2):
        assert len(set(seq[i:i + 3])) == 3, seq


def test_hard_spelling_uses_long_surnames():
    for k in range(20):
        d = listening.make_drill("british", seed=k, hard_spelling=True)
        assert len(d["items"][0]["value"]) >= listening.LONG_SURNAME


def test_listening_stats_rotation_and_weak_spot():
    sim = Sim(store={"accents": ["british", "american"]})
    _, s = sim.intent("ListeningDrillIntent")
    assert "Listen for" in s and "Australian" in s
    for _ in sim.attrs["listen"]["items"]:
        sim.say("no idea")
    stats = lf._LOCAL_STORE["listen_stats"]
    assert stats["surname"] == [0, 1] and stats["choice"] == [0, 1]
    assert lf._LOCAL_STORE["accents"][-1] == "australian"
    sim = Sim(store={"listen_stats": {"surname": [1, 4], "digits": [5, 0],
                                      "day": [3, 1]}})
    _, s = sim.intent("ProgressIntent")
    assert "weakest listening item is spelling names" in s
    sim.intent("ListeningDrillIntent")
    assert len(sim.attrs["listen"]["items"][0]["value"]) >= \
        listening.LONG_SURNAME


# ---------------------------------------------------------------------------
# Spaced review (Leitner + successive relearning) and the vocabulary drill
# ---------------------------------------------------------------------------
D = date(2026, 10, 4)


def test_srs_boxes_and_intervals():
    store = {}
    srs.review(store, "V01", True, D)
    assert store["V01"] == [1, 0, "2026-10-04", 1]
    assert srs.due_date(store["V01"]) == date(2026, 10, 5)
    srs.review(store, "V01", True, D + timedelta(1))
    assert store["V01"][3] == 2
    assert srs.due_date(store["V01"]) == date(2026, 10, 8)     # +3 days
    for k in range(5):
        srs.review(store, "V01", True, D + timedelta(2 + k))
    assert store["V01"][3] == srs.MAX_BOX
    srs.review(store, "V01", False, D + timedelta(9))
    assert store["V01"][1] == 1 and store["V01"][3] == 1


def test_srs_due_dates_respect_exam_cap():
    entry = [3, 0, "2026-10-04", 4]                             # +14 days
    assert srs.due_date(entry) == date(2026, 10, 18)
    assert srs.due_date(entry, cap=date(2026, 10, 10)) == date(2026, 10, 10)
    late = [3, 0, "2026-10-12", 4]                              # after the cap
    assert srs.due_date(late, cap=date(2026, 10, 10)) == date(2026, 10, 26)


def test_review_cap_two_days_before_exam():
    assert plan.review_cap(D, "2026-10-20") == date(2026, 10, 18)
    assert plan.review_cap(D, "2026-10-06") is None     # too close to cap
    assert plan.review_cap(D, None) is None


def test_srs_pick_order():
    store = {"A": [1, 0, "2026-10-01", 1],    # due 10-02: 2 days overdue
             "B": [0, 3, "2026-10-03", 1],    # due 10-04, many misses
             "C": [5, 0, "2026-10-03", 1],    # due 10-04, never missed
             "D": [2, 0, "2026-10-04", 3]}    # not due
    picks = srs.pick(store, ["A", "B", "C", "D", "E", "F"], D, 4)
    assert picks == ["A", "B", "C", "E"]
    assert srs.pick(store, ["D"], D, 3) == []
    assert srs.pick(store, ["A", "E"], D, 3, new_ok=False) == ["A"]
    assert srs.due_count(store, ["A", "B", "C", "D"], D) == 3


def test_srs_prune_keeps_weak_items():
    store = {"K%03d" % i: [5, 0, "2026-10-01", 4] for i in range(10)}
    store["WEAK"] = [0, 5, "2026-09-01", 1]
    srs.prune(store, cap=5)
    assert len(store) == 5 and "WEAK" in store


def test_vocab_items_are_well_formed():
    items = vocab.ITEMS
    assert len(items) >= 40
    assert len({it["id"] for it in items}) == len(items)
    assert len({it["topic"] for it in items}) >= 10
    for it in items:
        assert len(it["model"].split()) <= 25, it["id"]
        assert vocab.check(it, it["model"])[0], it["id"]
        assert not vocab.check(it, it["plain"])[0], it["id"]
        for word in it["accept"]:
            assert vocab.check(it, "it was %s" % word)[0], (it["id"], word)


def test_vocab_nudges_leftover_intensifier():
    weather = vocab.BY_ID["V01"]
    ok, word, nudge = vocab.check(weather, "the weather was very glorious")
    assert ok and word == "glorious" and "very" in nudge
    ok, word, nudge = vocab.check(weather, "we had glorious weather")
    assert ok and nudge == ""


def test_vocab_drill_with_relearning():
    sim = Sim()
    _, s = sim.intent("VocabDrillIntent")
    assert "stronger word" in s and sim.attrs["mode"] == "vocab"
    queue = list(sim.attrs["vocab"]["queue"])
    assert len(queue) == 5
    _, s = sim.say("I don't know")                # miss the first item
    assert "One option" in s
    assert sim.attrs["vocab"]["queue"].count(queue[0]) == 2
    seen_again = False
    for _ in range(5):
        v = sim.attrs["vocab"]
        if v["i"] < len(v["queue"]) and v["queue"][v["i"]] == queue[0] \
                and v["i"] > 0:
            seen_again = "try this one again" in s
        item = vocab.BY_ID[v["queue"][v["i"]]]
        _, s = sim.say("it was %s" % item["accept"][0])
    assert seen_again
    assert "You upgraded 5 of 6" in s, s
    st = lf._LOCAL_STORE["srs"][queue[0]]
    assert st[0] == 1 and st[1] == 1                 # one miss, one recovery
    assert lf._LOCAL_STORE["days"] == ["2026-10-04"]


# ---------------------------------------------------------------------------
# German: hear -> understand -> say, on the review engine
# ---------------------------------------------------------------------------
def test_german_phrase_ids_are_stable():
    assert PHRASES["L1P1"]["de"] == "Hallo"
    assert PHRASES["L3P2"]["de"] == "Ich heiße Anna."
    ids = [ph["id"] for L in GERMAN_LESSONS for ph in L["phrases"]]
    assert len(ids) == len(set(ids)) == len(PHRASES) == 95


def test_self_introduction_capstone():
    last = GERMAN_LESSONS[-1]
    assert "introduc" in last["title"].lower()
    des = [ph["de"] for ph in last["phrases"]]
    assert "Ich lerne Deutsch, weil ich in Deutschland arbeiten möchte." in des
    assert "weil" in last["tip"]


def test_lesson_quiz_feeds_review_engine():
    sim = Sim()
    sim.intent("GermanLessonIntent")
    for _ in range(5):
        item = sim.attrs["ger"]["items"][sim.attrs["ger"]["i"]]
        sim.say(item["en"])
    store = lf._LOCAL_STORE["srs"]
    assert sorted(store) == ["L1P%d" % i for i in range(1, 6)]
    assert all(entry[3] == 1 for entry in store.values())


def test_german_review_meaning_then_production():
    sim = Sim(store={"srs": {
        "L1P1": [1, 0, "2026-10-01", 1],      # due: meaning quiz
        "L1P2": [3, 0, "2026-09-20", 3],      # most overdue, box 3: say it
        "L1P3": [1, 0, "2026-10-04", 1]}})    # not due
    _, s = sim.intent("GermanReviewIntent")
    assert "German review" in s and sim.attrs["mode"] == "gsay"
    assert "Say this in German: good morning" in s and "judge" in s
    _, s = sim.say("good and morgan")         # whatever the recogniser hears
    assert sim.attrs["mode"] == "gself" and "Guten Morgen" in s
    _, s = sim.say("got it")
    assert sim.attrs["mode"] == "gquiz" and "Hallo" in s
    _, s = sim.say("hello")
    assert "Review done: 2 of 2" in s
    store = lf._LOCAL_STORE["srs"]
    assert store["L1P2"][3] == 4 and store["L1P1"][3] == 2
    assert store["L1P3"] == [1, 0, "2026-10-04", 1]


def test_german_review_missed_production_comes_back():
    sim = Sim(store={"srs": {"L2P3": [3, 0, "2026-09-20", 3]}})
    sim.intent("GermanReviewIntent")
    _, s = sim.intent("AMAZON.FallbackIntent")   # German not recognised
    assert sim.attrs["mode"] == "gself"
    _, s = sim.say("missed it")
    assert "Once more" in s and sim.attrs["mode"] == "gsay"
    sim.say("und dir")
    _, s = sim.say("maybe")
    assert "got it, or missed it" in s           # unclear self-grade
    _, s = sim.say("yes")
    assert "Review done: 1 of 2" in s
    assert lf._LOCAL_STORE["srs"]["L2P3"][:2] == [4, 1]


def test_german_review_falls_back_to_lessons():
    _, s = Sim().intent("GermanReviewIntent")
    assert "nothing to review yet" in s and "German lesson 1" in s
    sim = Sim(store={"srs": {"L1P1": [1, 0, "2026-10-04", 1]}})
    _, s = sim.intent("GermanReviewIntent")
    assert "Nothing is due" in s and "German lesson" in s


def test_progress_reports_german_due():
    sim = Sim(store={"german_next": 2, "srs": {
        "L1P1": [1, 0, "2026-10-01", 1], "L1P2": [1, 0, "2026-10-02", 1],
        "L1P3": [1, 0, "2026-10-04", 1], "V01": [1, 0, "2026-10-01", 1]}})
    _, s = sim.intent("ProgressIntent")
    assert "2 German phrases are due for review" in s


# ---------------------------------------------------------------------------
# Regressions from code review
# ---------------------------------------------------------------------------
def test_dynamodb_decimals_do_not_crash():
    """boto3 hands numbers back as Decimal; Decimal / float raises."""
    from decimal import Decimal as Dec
    store = {"visits": Dec(5), "mocks": Dec(2), "german_next": Dec(1),
             "plan_day": Dec(3), "p2_best_pace": Dec(120),
             "listen_stats": {"surname": [Dec(1), Dec(4)],
                              "digits": [Dec(3), Dec(0)]},
             "srs": {"V01": [Dec(1), Dec(1), "2026-10-01", Dec(1)],
                     "L1P1": [Dec(3), Dec(0), "2026-09-20", Dec(3)]}}
    for intent, mode in [("VocabDrillIntent", "vocab"),
                         ("ListeningDrillIntent", "listen"),
                         ("GermanReviewIntent", "gsay")]:
        sim = Sim(store=store)
        _, s = sim.intent(intent)
        assert sim.attrs.get("mode") == mode, (intent, s)
    _, s = Sim(store=store).intent("ProgressIntent")
    assert "spelling names" in s
    _, s = Sim(store=store).launch()
    assert "Today:" in s


def test_vocab_with_nothing_due_still_runs():
    every = {it["id"]: [1, 0, "2026-10-04", 1] for it in vocab.ITEMS}
    sim = Sim(store={"srs": every})
    _, s = sim.intent("VocabDrillIntent")
    assert "Nothing is due" in s and sim.attrs["mode"] == "vocab"
    assert len(sim.attrs["vocab"]["queue"]) == 5


def test_finished_intent_leaves_retry_and_quizzes():
    llm._cache.clear()
    with env(LLM_PROVIDER="none"):
        sim = Sim()
        sim.intent("PartOneIntent")
        for _ in range(6):
            sim.say("I like it because it is fun")
        sim.intent("FeedbackIntent")
        assert sim.attrs["mode"] == "retry"
        _, s = sim.intent("FinishedIntent")
        assert sim.attrs["mode"] == "menu" and "Skipping" in s
    llm._cache.clear()
    sim = Sim()
    sim.intent("GermanLessonIntent")
    sim.intent("FinishedIntent")
    assert sim.attrs["mode"] == "menu"


def test_completed_plan_not_offered_again_same_day():
    sim = Sim(store={"exam_date": "2026-10-04"})       # exam day: ["p1"]
    sim.launch()
    sim.say("yes")
    for _ in range(6):
        _, s = sim.say("I live in Bengaluru because my job is here")
    for _ in range(3):
        if "today's plan done" in s:
            break
        _, s = sim.intent("AMAZON.NextIntent")
    assert "today's plan done" in s
    _, s = sim.launch()
    assert "already finished today's plan" in s and "Today:" not in s


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print("All %d tests passed" % len(tests))
