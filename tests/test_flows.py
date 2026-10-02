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
from coach import feedback, listening, llm, numbers  # noqa: E402
from coach.content import CUE_CARDS, GERMAN_LESSONS  # noqa: E402

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
    def __init__(self, locale="en-IN", api_endpoint="http://127.0.0.1:9",
                 handler=None):
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
    sur, phone, day, num = d["items"]
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
    assert sim.attrs.get("mode") == "menu"
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
    _, s = sim.say("%d" % items[3]["value"])
    assert "You scored 3 out of 4" in s, s


def test_german_flow():
    lf._LOCAL_STORE.clear()
    sim = Sim()
    sim.launch()
    resp, s = sim.intent("GermanLessonIntent")
    assert "German lesson 1 of 20" in s and "de-DE" in s and "Vicki" in s
    assert resp["card"]["title"].startswith("German lesson 1")
    for _ in range(5):
        item = sim.attrs["ger"]["items"][sim.attrs["ger"]["i"]]
        _, s = sim.say(item["en"])
    assert "5 out of 5" in s
    assert lf._LOCAL_STORE["german_next"] == 1
    _, s = sim.intent("GermanLessonIntent")
    assert "German lesson 2 of 20" in s
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
        sim = Sim(handler=lf.build_skill_builder().lambda_handler())
        done, secs, result = run_within(10, sim.launch)
    assert done, "launch still blocked after 10 s"
    assert secs < 4.5, "launch took %.1f s" % secs
    assert "mock test" in result[1]


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


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print("All %d tests passed" % len(tests))
