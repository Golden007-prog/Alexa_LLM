# -*- coding: utf-8 -*-
"""Offline simulation of real Alexa request envelopes through the skill.
Run:  pip install ask-sdk-core  &&  python tests/test_flows.py
"""
import json
import os
import re
import sys
import uuid
import xml.dom.minidom
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lambda"))

import lambda_function as lf  # noqa: E402
from coach import feedback, listening, llm, numbers  # noqa: E402
from coach.content import CUE_CARDS, GERMAN_LESSONS  # noqa: E402


class Sim:
    def __init__(self, locale="en-IN"):
        self.attrs = {}
        self.new = True
        self.locale = locale
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
                "apiEndpoint": "http://127.0.0.1:9", "apiAccessToken": "x"}},
            "request": request,
        }

    def send(self, request, advance=5):
        self.clock += timedelta(seconds=advance)
        request.setdefault("requestId", "amzn1.echo-api.request." + str(uuid.uuid4()))
        request["timestamp"] = self.clock.strftime("%Y-%m-%dT%H:%M:%SZ")
        request["locale"] = self.locale
        out = lf.lambda_handler(self._env(request), None)
        self.new = False
        self.attrs = out.get("sessionAttributes") or {}
        resp = out["response"]
        ssml = (resp.get("outputSpeech") or {}).get("ssml", "")
        if ssml:
            xml.dom.minidom.parseString(ssml)  # must be well-formed XML
            for m in re.finditer(r"<break time='(\d+)ms'/>", ssml):
                assert int(m.group(1)) <= 10000, "break too long"
        size = len(json.dumps(out))
        assert size < 24000, "response too large: %d bytes" % size
        return resp, ssml

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
    spoken = " ".join(numbers._DIGIT_WORDS_REV[c] for c in phone["value"])
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
    llm.generate = lambda system, prompt, max_tokens=700: (
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
    assert "Australian" in s and "Nicole" in s or "Russell" in s
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


if __name__ == "__main__":
    numbers._DIGIT_WORDS_REV = {v: k for k, v in numbers._DIGIT_WORDS.items()
                                if k in ("zero", "one", "two", "three", "four",
                                         "five", "six", "seven", "eight", "nine")}
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print("All %d tests passed" % len(tests))
