# Device test script

Run this on the Echo Dot (or in the console's Test tab, typing instead of speaking) after each deploy. Work through the sessions in order. "Expect" describes what should happen; a ✗ in your notes plus the exact words Alexa said is the most useful bug report. Wake word omitted after the first line of each session.

Before starting: Test tab → "Skill testing is enabled in: **Development**". Device language must be **English (India)**.

## Session 1: first run and setup (fresh user)

To test the first-run path again later, delete the skill's DynamoDB item, or test from a second Amazon profile.

| # | Say | Expect |
|---|---|---|
| 1 | "Alexa, open study coach" | Welcome, then "when is your IELTS exam?" |
| 2 | "I'm not sure" | "Sorry, I didn't catch a date…" (error path: no date) |
| 3 | "October the twenty-eighth" | "Got it: Wednesday, the twenty-eighth of October, N days away." Then "When and where will you practise each day?" |
| 4 | "after breakfast at my desk" | Repeats your cue, mentions Routines, then "N days to your exam. Today: …. About N minutes. Say yes to start…" |
| 5 | "stop" | "Good luck with your practice. Bis bald!" (German voice) and the session ends |

## Session 2: today's plan and chaining

| # | Say | Expect |
|---|---|---|
| 6 | "Alexa, open study coach" | "Welcome back." Countdown, today's plan, no setup questions |
| 7 | "yes" | The first activity in the plan starts |
| 8 | Finish the activity (answer its questions) | "Next on today's plan: …. Say next when you're ready, or menu to stop." |
| 9 | "next" | The second activity starts |
| 10 | "menu" | "Main menu. You can say: …" (leaves the plan) |
| 11 | "how am I doing" | Countdown, streak, mocks, German lesson; a card titled "Your progress" in the Alexa app |

## Session 3: Speaking

| # | Say | Expect |
|---|---|---|
| 12 | "Alexa, ask study coach for part one" | Part 1 practice, a topic and the first question (one-shot) |
| 13 | Answer in two or three sentences, six times | A new question after each answer; a topic change after three |
| 14 | "repeat" (during Part 1) | The last question again, word for word |
| 15 | "skip" | The next question (the skipped one counts as "(skipped)") |
| 16 | "feedback" | "Let me review your answers" first (progressive response), then at most two fixes, then "Let's lock one in. Answer this again, and this time use …" |
| 17 | Answer using the suggested word | "Nice, you used …" |
| 18 | "part two" | Cue card read slowly; "forty seconds left", "twenty seconds", then "Time is up. Please start speaking now." About a minute of prep in total |
| 19 | Talk with natural pauses | Short "go on" replies between chunks; after about two minutes "Thank you, that's two minutes." |
| 20 | "part three" | Three discussion questions linked to that cue card |
| 21 | "fluency rounds" | Cue card and prep, then round one; after it, "Round two… in ninety seconds", then round three "in one minute", then a rough pace for each round |
| 22 | During a round: "I'm finished" | Moves straight to the next round |
| 23 | "mock test" (allow ~15 minutes) | Part 1 → Part 2 → Part 3 without asking, then feedback and the retry question |

## Session 4: Listening and vocabulary

| # | Say | Expect |
|---|---|---|
| 24 | "listening drill australian" | "Listening drill, Australian accent… Listen for: …", then a two-voice call in Australian voices |
| 25 | "repeat" | "In the exam you only hear it once, but here it is again", and the call replays |
| 26 | Spell the surname letter by letter | "Correct." or the correct spelling |
| 27 | Answer the phone number, date and number | Each marked; on the self-corrected detail, a wrong answer mentions the trap |
| 28 | For the A/B/C question, say "B" or "bee" or the option's words | Marked correctly. Choosing the rejected option explains the distractor |
| 29 | "listening drill" (twice more) | Three drills in a row use three different accents |
| 30 | "vocabulary drill" | "Make this stronger: …" |
| 31 | Answer with "very" plus a strong word | Accepted, with the nudge "You kept very, though…" |
| 32 | "I don't know" | "One option: …" plus a model; the item comes back as "Let's try this one again" two items later |

## Session 5: German

| # | Say | Expect |
|---|---|---|
| 33 | "German lesson" | "German lesson N of 21", five phrases in the German voice (slow, then normal), a tip, then a meaning quiz |
| 34 | Answer the meanings in English | "Richtig!" or "Not quite", then "Say it with me"; at the end a score; three or more out of five moves you on |
| 35 | "German lesson 99" | Clamped to the last lesson, "Introducing yourself" (error path: out of range) |
| 36 | "German review" (the day after a lesson) | Phrases due for review. Well-known ones ask you to "Say this in German", and Alexa says it can't hear German pronunciation |
| 37 | Say the German | "Here it is: … Did yours match?" (works even if Alexa misheard you) |
| 38 | "maybe" | "Just say got it, or missed it." (error path: unclear self-grade) |
| 39 | "missed it" | The phrase comes back later in the same review |

## Session 6: help, fallback and stop everywhere

| # | Say | Expect |
|---|---|---|
| 40 | "help" (in the menu, in Part 1 and in a listening drill) | A tip for that mode, then the menu options |
| 41 | "blah blah purple" (in the menu) | "Sorry, I didn't get that. You can say: …" |
| 42 | "feedback" (with nothing answered yet) | "There's nothing to review yet…" |
| 43 | "my exam is on November second" | "Got it: Monday, the second of November…" |
| 44 | "cancel" | Ends the session with the goodbye |

## What to note if something fails

- **The exact words you said and what Alexa replied.** The console's Test tab shows the JSON in and out.
- **Whether Alexa sent you to the wrong intent.** Check the Test tab's "Intent" column, or the request in the JSON input.
- **For errors or silence,** CloudWatch logs: Developer Console → your skill → **Code** tab → **CloudWatch Logs** (top bar). Pick the region your skill is hosted in.
