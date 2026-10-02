# Learning design: how the coach helps you learn faster

This document turns learning research into concrete features for the IELTS & German Coach. It was written on 3 October 2026 for one learner: an IELTS exam (Speaking and Listening) less than four weeks away, plus German from zero to A1. Every technique below is mapped to a voice flow, the state it needs, and what the skill can honestly check, given that an Alexa skill receives speech-recognition **text** and never audio.

Evidence is marked by how well it was verified. **High** means the source was read directly (abstract or full text) with numbers confirmed. **Medium** means confirmed through a secondary summary. **Low** means unverified, or my own inference from the evidence; those are labelled so they never read as findings.

## 1. The short version

1. **Make every activity a retrieval attempt.** Asking before telling beats re-reading or re-listening by a medium-to-large margin, and it is the single strongest lever available. *(High)*
2. **Space reviews to the exam date, and relearn missed items in the same session.** Review a missed item again until it is correct once, then bring it back after 1, 3 and 7 days, with a final pass 2 to 4 days before the exam. *(High for the principle, Low for the exact 25-day gaps)*
3. **Repeat the same Part 2 talk under shrinking time.** The 4/3/2 technique reliably speeds up speech. Gains on new topics are weaker, so repeat first and rotate topics after. *(Medium)*
4. **Give one or two corrections, then make the learner try again.** Prompts that push a retry produce more repair than simply restating the right version. *(Medium; the "one or two" cap is Low, a design choice)*
5. **Teach and reuse chunks**, such as "in my experience" or "it depends on", for band-7 vocabulary. Formulaic language raises perceived proficiency. *(Medium)*
6. **German moves from understanding to saying.** New phrases are first quizzed for meaning (checked automatically), then for production (self-graded, because the skill cannot hear German). *(Medium)*
7. **Launch straight into "today's session".** Routines can only *open* a skill, so the skill itself should know what is due today. *(High for the platform fact)*
8. **Fix a daily time and place, and show an exam countdown.** If-then plans have a reliable effect. Real habits take about two months, so four weeks is still the pre-habit phase. *(High)*

## 2. What the research says

| Technique | Finding | Confidence | Use in the coach |
|---|---|---|---|
| Retrieval practice | Testing beats restudy: g ≈ 0.63 with feedback, and larger at retention of a day or more ([Rowland 2014](https://doi.org/10.1037/a0037559)). Once an item was recalled, more testing helped a week later and more restudy did not ([Karpicke & Roediger 2008](https://www.science.org/doi/abs/10.1126/science.1152408)). | High | Every drill asks first, then tells |
| Spacing | The best gap grows with the retention interval. It was roughly 20–40% of the delay for a 1-week test and 5–10% for a 1-year test ([Cepeda et al. 2008](https://laplab.ucsd.edu/articles/Cepeda%20et%20al%202008_psychsci.pdf); [meta-analysis 2006](https://www.yorku.ca/ncepeda/publications/CPVWR2006.html)). | High (principle); Low (applied to 25 days) | Intervals of 1, 3, 7 and 12 days, capped by the exam date |
| Successive relearning | Practise to one correct recall, then relearn to one correct in later sessions. One relearning session gave d = 1.82 over initial learning alone ([Rawson & Dunlosky 2022](https://journals.sagepub.com/doi/full/10.1177/09637214221100484)). | High | A missed item is re-asked later in the same session |
| Interleaving | It helps when categories are confusable. For word lists, blocking did as well or better ([Brunmair & Richter 2019](https://doi.org/10.1037/bul0000209)). | Medium | Interleave only confusable pairs (du/Sie, der/die/das), not plain vocabulary |
| Feedback timing | Both immediate and delayed feedback help, and the evidence on which is better is mixed ([Butler & Roediger 2008](https://link.springer.com/article/10.3758/MC.36.3.604)). | Medium | Always give the correct answer after a miss |
| Productive recall | Productive (L1→L2) practice builds productive knowledge, and receptive practice builds receptive knowledge ([Webb 2009](https://journals.sagepub.com/doi/10.1177/0033688209343854)). | High | German goes from meaning quiz to "say it in German" |
| 4/3/2 repetition | Repeating a talk under shrinking time limits improved fluency. Posttest gains held only for learners who repeated the same topic ([de Jong & Perfetti 2011](https://sites.pitt.edu/~perfetti/PDF/de%20Jong%20Language%20Learning.pdf)). | Medium | Part 2 repetition rounds |
| Planning time | Planning raises fluency at 1 minute, but complexity only at about 10 minutes (Mehnert 1998, [secondary](https://link.springer.com/article/10.1186/s40862-016-0015-6)). | Medium | Keep the real 1-minute Part 2 prep, and expect fluency gains from it, not richer language |
| Fluency measures | Speech rate and mean length of run best predict rated fluency ([Kormos & Dénes 2004](https://research.lancaster-university.uk/en/publications/exploring-measures-and-perceptions-of-fluency-in-the-speech-of-se/)). | Medium | Report rough words per minute only, and compare rounds rather than absolute values |
| Corrective feedback | Recasts are the most common feedback but lead to the least learner repair ([Lyster & Ranta 1997](https://eric.ed.gov/?id=EJ539354)). Explicit feedback helps more short term and implicit feedback lasts better ([Li 2010](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9922.2010.00561.x)). | Medium | One or two fixes, followed by a retry prompt |
| Formulaic chunks | Learners taught to notice chunks were rated more proficient (Boers et al. 2006, [record](https://benjamins.com/online/ebop/publications/44877)). | Medium | Chunk bank and a "use it" challenge |
| Metacognitive listening | Predict, listen, then check, beat a control group, and weaker listeners gained most ([Vandergrift & Tafaghodtari 2010](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9922.2009.00559.x)). | High | Preview the questions before the call |
| Shadowing | It improved listening scores only for low-proficiency learners ([Hamada 2016](https://eric.ed.gov/?id=EJ1084744)). | Medium | Optional, not core |
| Implementation intentions | "When X, I will Y" plans had d = 0.65 across 94 tests ([Gollwitzer & Sheeran 2006](https://doi.org/10.1016/S0065-2601(06)38002-1)). | High | Ask "when and where will you practise?" on first run |
| Habit timeline | Habits took a median of 66 days to plateau, with a range of 18–254 ([Lally et al. 2010](https://doi.org/10.1002/ejsp.674)). | High | Streak plus countdown; don't promise automaticity in four weeks |
| Practice testing and distributed practice | Rated the two highest-utility techniques, while rereading and highlighting were rated low ([Dunlosky et al. 2013](https://pubmed.ncbi.nlm.nih.gov/26173288/)). | High | Confirms that no activity should be listen-only |

## 3. What a text-only coach can and cannot check

The skill sees Alexa's transcript. Fillers like "umm" are usually dropped, and there is no timing inside an utterance. Only the request timestamps exist, and they include Alexa's own speech and network time.

**Can check automatically:** spelled names, digits, dates and numbers in listening; A/B/C answers; the English meaning of a German phrase; whether a target word or chunk appears in an answer ("use 'although'"); answer length; repeated plain words; linking phrases; a rough Part 2 pace (words divided by elapsed seconds), compared across rounds rather than as an absolute; and a few grammar patterns with low false-positive risk.

**Must not pretend to check:** pronunciation (including ü, ö and ch); real pauses, hesitation or intonation; filler counts, since the speech recognizer removes most fillers; spoken German, because the English (India) recognizer transcribes German into English look-alikes; and any IELTS band beyond a clearly labelled rough estimate.

## 4. Feature designs

Each design gives the reason, the voice flow, the state, and how it is tested. Persistent state lives in the DynamoDB item; the whole item stays under 20 KB, far below DynamoDB's 400 KB limit. Session state counts toward the response, and the tests keep every response under a self-imposed 24 KB.

### 4.1 Today's session (smart launch)

**Why.** Routines can only open a skill. A Routine's "Custom" action may not pass "ask study coach for…" through (unverified, and one user reports it fails). So the useful behaviour is a launch that already knows what is due. A fixed daily slot is also the habit cue (§2, implementation intentions).

**Flow.**
```
User:   Alexa, open study coach.            (or a 7 a.m. Routine)
Alexa:  Day 12 to your exam. Today: a Part 2 round, one listening call,
        and three minutes of German review. About fifteen minutes. Ready?
User:   Yes.
Alexa:  (starts Part 2 rounds; when they finish) Next, a listening call...
```
On first run the skill asks "When is your exam?" (an AMAZON.DATE slot) and "When and where will you practise each day?" The second answer is repeated back as an if-then plan, and the skill suggests creating a Routine at that time.

**Plan rule (deterministic).** The plan depends on days left:
- More than 14 days left: rotate four days of mock test / Part 2 rounds + feedback / two listening calls / chunk drill, plus about 5 minutes of German.
- 4 to 14 days left: alternate a full mock with Part 2 rounds + listening, with chunk review from the scheduler. German drops to review only, about 3 minutes, because the exam comes first.
- 1 to 3 days left: a light day with weak-item review and one listening call. There is no full mock on the last day.
- After the exam: German becomes the main track.

"Menu" still reaches everything.

**State.** `exam_date` (ISO date), `practice_cue` (short text), `plan_day` (int), and session `plan` (list of activity ids) with `plan_i`.

**Tests.**
- A launch with no exam date asks for it.
- Plans for 20, 10 and 2 days left contain the expected activity types.
- Finishing an activity chains to the next one.
- "Menu" exits the plan.

### 4.2 One retrieval engine for everything

**Why.** It combines retrieval, spacing and successive relearning (§2). One engine serves German phrases, chunks and vocabulary upgrades, and weak listening item types.

**Algorithm: Leitner boxes, not FSRS.** FSRS beats SM-2 in its own benchmark on Anki-scale histories ([benchmark](https://expertium.github.io/Benchmark.html)). Its 21 parameters are tuned on large review logs, and there is no evidence it helps with roughly 300 items over four weeks. Leitner is about 40 lines, easy to explain, and easy to test.

- `srs[id] = [correct, wrong, last_seen, box]`, for example `"L3P2": [4, 1, "2026-10-05", 3]`. This keeps the brief's `[correct, wrong, last_seen]` and adds the box.
- Box intervals are 1, 3, 7 and 14 days. A correct answer moves the item up one box. A wrong answer sends it to box 1, and the item is re-asked two items later in the same session until it is correct once.
- Due date = `last_seen + interval`. It is capped at the exam date minus 2 days for IELTS items, so everything comes up once more before the exam.
- Picking items: most overdue first, then lowest box, then highest wrong rate. Only items already taught are eligible.
- Size: about 30 bytes per item, so 300 items is about 9 KB. The cap is 400 entries, dropping the most-mastered first.

**Tests.**
- The box moves on correct and wrong answers.
- Due dates respect the exam cap.
- A missed item is re-asked in the same session.
- Nothing untaught is picked.
- The store size stays under the cap.
- Dates use the request timestamp in IST for en-IN, so the day doesn't roll over at 05:30.

### 4.3 Part 2 repetition rounds (4/3/2 adapted)

**Why.** Repeating the same content under shrinking time builds fluency (§2, de Jong & Perfetti 2011). The real Part 2 is 1–2 minutes, so the rounds are **2:00, 1:30 and 1:00** instead of 4/3/2.

**Flow.**
```
Alexa:  (cue card, 1-minute prep, as today) ... Start speaking now.
User:   (talks in chunks; "go on" replies as today)
Alexa:  Thank you. Round two: tell me the same story again, with the same
        details, in ninety seconds. Go.
...
Alexa:  Round three, one minute. Same story, as smoothly as you can.
...
Alexa:  Your pace went from about 95 to about 125 words a minute, and you
        kept 84 per cent of your round-one words. That's the fluency gain.
        (Pace is a rough estimate from Alexa's text, best compared between rounds.)
```

**Checks.**
- Rough words per minute = words / talk seconds, using the existing `talk_seconds()`.
- "Kept content" = overlap of content words between round 1 and round 3.
- Every round has a hard stop, by word count or time, as today.

**State.** Session `p2.round` and `p2.rounds = [{words, secs}]`. Persistent `p2_best_wpm` is kept for progress.

**Tests.** Three rounds run in order; each round stops at its own limit; the summary numbers come out correctly from simulated chunks; the summary includes the "rough" wording.

### 4.4 Focused feedback with a retry

**Why.** One or two corrections, then a prompt to try again, gets more repair than a list of fixes (§2, Lyster & Ranta; Li).

**Flow.**
```
Alexa:  (feedback, now limited to two fixes) ...
        Let's lock one in. Answer this again, and use "although" this time:
        Do you prefer living in a city or the countryside?
User:   I prefer the city, although it is noisy ...
Alexa:  Nice, you used "although". That's the kind of linking examiners reward.
```

**Rules.**
- The retry target is chosen deterministically, so it can be checked: an unused linker, the stronger replacement for a repeated plain word, or a chunk from the chunk bank.
- The LLM prompt asks for at most two fixes. The retry target never comes from the LLM, so the check never depends on parsing model output.
- One new rule-based tip, with a source: progressive with stative verbs ("I am knowing", "I am understanding", "I am wanting") is a documented Indian-English feature that exam English treats as an error (Sailaja 2009, [record](https://archive.org/details/indianenglish0000sail)). "Having" is excluded because "having lunch" is correct.
- Article use is not flagged, because the false-positive risk is too high.

**State.** Persistent `focus` holds the last target, so the next session's Part 1 opens with "Remember to try 'although' today."

**Tests.**
- The target is chosen from the transcript.
- The retry passes when the target is used and fails when it isn't.
- The stative-progressive tip fires on "I am knowing" but not on "I am having lunch".
- The AI prompt includes the two-fix limit.

### 4.5 Chunk and vocabulary drill (Phase 3 item 3, upgraded)

**Why.** Producing an answer before hearing the model (retrieval), learning chunks rather than single words (Boers), and reusing them later (spacing).

**Flow.**
```
Alexa:  Make this stronger: "The weather was very good."
User:   The weather was glorious.
Alexa:  Great: "glorious" is band-seven vocabulary. A band-seven answer:
        "We had glorious weather, warm but not too humid." Next one...
```

**Content.** 40+ original items across common Part 1 topics, each with `{plain, weak, accept[], model, topic}`. Accepted upgrades are matched by word (pleasant, glorious, superb…). If the weak word is still present, the answer is accepted with a nudge: "you kept 'very', try dropping it". A miss goes back into the engine (§4.2).

**Tests.** Each item accepts its upgrades and rejects the weak original; all 40+ items have a model sentence under 25 words; items go through the engine.

### 4.6 Listening drill v2 (Phase 3 item 4)

**Why.** Predict, listen, check (§2, Vandergrift & Tafaghodtari). In the real test you read the questions first, so the drill previews them. Weak item types come back more often.

**Changes.**
- 10+ original scenarios: doctor's surgery, gym membership, bike hire, tour booking, accommodation enquiry, lost property, library card, cooking class, car service, concert tickets, and others.
- A spoken multiple-choice item. "A", "B" and "C" are recognised badly when spoken alone, so "be", "bee", "see", "sea", "option B", and the option's own words are also accepted.
- A preview before the call: "Listen for: the surname, the phone number, the date, and which option they choose."
- Exactly one "oh, sorry, I mean…" trap per call, as today.
- Fair accent rotation: persistent `accents` holds the last three used, and the least recently used accent is picked.
- Per-type stats `listen_stats[kind] = [correct, wrong]`. The weakest type is always included and the surname gets harder (longer names) when spelling is weak.

**Tests.**
- Every scenario renders well-formed SSML.
- Every call has exactly one trap.
- Multiple choice accepts the letter variants and rejects wrong ones.
- Rotation never repeats an accent until all three have been used.
- The weak type is included.

### 4.7 German: hear → understand → say (Phase 3 item 2)

**Why.** Receptive practice first, then productive (§2, Webb 2009). The meaning check is automatic. Saying German can only be self-graded, and the skill says so.

**Stages for each phrase (`srs` box).**
- **Box 1–2:** the meaning quiz, as today. Alexa says the German and you answer the meaning in English, which is checked automatically.
- **Box 3+:** production. Alexa says the English and you say it in German. Alexa plays the German, then asks "Did yours match? Say got it or missed it." The skill tells you plainly: "I can't hear German pronunciation, so you're the judge here."
- **Self-grading:** comparing against a model you just heard is more reliable than predicting your own memory. Self-grades are still marked, and a self-graded success moves the item up only one box at a time.

**Content.** Keep the 20 lessons, which already make 90 phrases plus 2 review lessons. Add a "self-introduction" capstone that builds on the Goethe A1 theme "Person" ([official word list](https://www.goethe.de/pro/relaunch/prf/de/A1_SD1_Wortliste_02.pdf)). It uses frames you say aloud: "Ich heiße…", "Ich komme aus…", "Ich wohne in…", "Ich arbeite als…", "Ich lerne Deutsch, weil…". Nouns are always taught with their article.

**Tests.**
- Stage switches at box 3.
- "Got it" and "missed it" route correctly in production mode, and "yes" or "no" as a Part 1 answer still counts as an answer.
- Ids `L{lesson}P{phrase}` are stable.
- Review draws only from taught lessons.

### 4.8 Progress and habit (Phase 3 item 1, extended)

**Flow.**
```
User:   How am I doing?
Alexa:  Twelve days to your exam. You're on a five-day streak. Three mock tests
        done. Best Part 2 pace about 125 words a minute. Your weakest listening
        item is spelling names. German: lesson 6, eleven phrases due for review.
        Last feedback: try more linking phrases like although.
```
The same summary goes on a card.

**Streak rule.** `days` is the list of ISO dates with any activity in IST, capped at 60 entries. The streak counts back from today, or from yesterday if nothing has been done yet today.

## 5. What not to build, and why

- **Pronunciation scores, filler counts, pause analysis:** the skill never gets audio, and fillers are mostly removed from the transcript (§3).
- **Band predictions beyond a rough, labelled range:** no validation exists for estimates based on the transcript.
- **FSRS:** no evidence it helps at this scale or within this time (§4.2). It could be revisited if the item count grows a lot.
- **Shadowing as a core IELTS listening drill:** it helped only lower-proficiency listeners (§2). It could be an optional German pronunciation warm-up, explicitly not scored.
- **Auto-checked German speaking:** the English (India) recognizer can't transcribe it, so it is self-graded (§4.7).

## 6. Platform facts that differ from the original brief

These were checked against Amazon's developer docs on 3 October 2026.

- **Response size:** the current limit is **120 KB** ([JSON reference](https://developer.amazon.com/en-US/docs/alexa/custom-skills/request-and-response-json-reference.html), updated 17 Aug 2026), not 24 KB. The tests keep 24 KB as a self-imposed budget, because smaller responses are faster.
- **Python 3.8:** new Alexa-hosted Python skills still get Python 3.8 ([hosted skills](https://developer.amazon.com/en-US/docs/alexa/hosted-skills/build-a-skill-end-to-end-using-an-alexa-hosted-skill.html)). AWS has deprecated `python3.8`, will block new functions from 1 Feb 2027 and will block updates from 3 Mar 2027 ([Lambda runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)). Amazon says it manages the runtime, so CI tests both 3.8 and 3.12. The skill logs `sys.version` at cold start so the real runtime shows up in CloudWatch.
- **Free-form capture:** Amazon recommends `AMAZON.SearchQuery` and advises against custom catch-all slot types ([slot reference](https://developer.amazon.com/en-US/docs/alexa/custom-skills/slot-type-reference.html)). SearchQuery needs a carrier phrase in every sample, such as "my answer is …", which would break natural answers and Part 2 chunks. The skill keeps the catch-all `{answer}` design. If on-device testing shows truncation or misrouting, the fallback is SearchQuery with short carrier phrases plus the existing command routing.
- **Routines:** the Skills action opens the skill. Passing an utterance through the Custom action is unverified, which is why §4.1 exists. One-shot phrases ("ask study coach for a German lesson") still work by voice. Sample utterances should not include "ask… for" ([invocation doc](https://developer.amazon.com/en-US/docs/alexa/custom-skills/understanding-how-users-invoke-custom-skills.html)).
- **Reminders API:** a daily reminder is possible with the `alexa::alerts:reminders:skill:readwrite` permission and a daily repeat rule ([overview](https://developer.amazon.com/en-US/docs/alexa/smapi/alexa-reminders-overview.html)). Whether it works for en-IN in the development stage is unverified, so it is listed as optional, after a device test.
- **Progressive responses:** up to 5 per request, each spoken within a 30-second limit, and they share the ~8 s window ([doc](https://developer.amazon.com/en-US/docs/alexa/custom-skills/send-the-user-a-progressive-response.html)). The skill uses one, within its 7 s budget.
- **Alexa+:** there is no official statement on how classic custom skills are routed under Alexa+ in en-IN. One unofficial report describes a one-word invocation name being misrouted. "Study coach" is two words; this needs testing on the device.

## 7. Proposed Phase 3 build order

The brief's order is progress, German review, vocabulary, listening, one-shot launches, CI. With the exam under four weeks away, this order puts IELTS impact first and keeps the shared pieces ahead of the features that need them:

1. **CI on 3.8 and 3.12, plus vermin** (small; it protects every later change). *Brief item 6.*
2. **Today's session + exam countdown + progress and streak** (medium). *Items 1 and 5; one-shot samples included.*
3. **Part 2 repetition rounds + focused feedback with retry** (medium). *New, research-driven.*
4. **Listening drill v2** (medium to large). *Item 4.*
5. **Retrieval engine + chunk and vocabulary drill** (medium). *Item 3.*
6. **German hear → understand → say on the same engine** (medium). *Item 2.*

Proposals 7–9 from the brief (LLM follow-up questions, per-answer quick tips, a bridge from Hindi or English) still apply. The quick-tip mode would reuse §4.4's deterministic targets.
