# IELTS & German Coach (Alexa skill)

A private Alexa skill for an Echo Dot: IELTS Speaking mock tests with examiner-style feedback, IELTS Listening Part 1 drills in British, Australian and American voices, and 20 beginner German lessons spoken by a native German voice.

```
"Alexa, open study coach"
   "mock test"                  full Part 1 + 2 + 3, then feedback
   "part one" / "part two" / "part three"
   "feedback"                   review everything since the last feedback
   "listening drill"            random accent;  "listening drill australian"
   "German lesson"              next lesson;    "German lesson 7"
   "repeat" · "next" (skip) · "menu" · "stop"
```

It stays in **development mode**, so it is free and only works on devices registered to your Amazon account. No certification needed.

## Install (about 15 minutes)

You need the **same Amazon account** your Echo Dot uses (amazon.in) to sign in to the [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask).

### Option A: import from GitHub (recommended)

1. Push this folder to a **public** GitHub repo, e.g. `github.com/<you>/ielts-german-coach`. Do not commit `lambda/config.json` (it is in `.gitignore`).
2. Developer Console → **Create Skill**.
   - Name: `IELTS and German Coach`. Primary locale: **English (IN)**.
   - Type: **Custom**. Hosting: **Alexa-hosted (Python)**.
3. On the template step choose **Import skill**, paste `https://github.com/<you>/ielts-german-coach.git`, and continue. ([Amazon's import guide](https://developer.amazon.com/en-US/docs/alexa/hosted-skills/alexa-hosted-skills-git-import.html))
4. When it opens: **Build** tab → **Build skill** (wait for "Build successful").
5. **Test** tab → set "Skill testing is enabled in" to **Development**. Type `open study coach` to check it answers.
6. Say to your Echo Dot: **"Alexa, open study coach."**

### Option B: copy-paste (no GitHub)

1. Create the skill as in step 2 above, but pick the **Start from Scratch** template.
2. **Build → Interaction Model → JSON Editor**: paste `skill-package/interactionModels/custom/en-IN.json`, then **Save** and **Build skill**.
3. **Code** tab: replace `lambda_function.py` and `requirements.txt` with the ones here, create a `coach` folder with the six files from `lambda/coach/`, then **Deploy**.
4. Continue from step 5 above.

## Turn on AI examiner feedback (optional, recommended)

Without a key the skill still works and gives rule-based tips (answer length, Part 2 length, linking phrases, overused words). With a key you get band estimates per criterion and three quoted fixes.

1. Get a key: Gemini from [Google AI Studio](https://aistudio.google.com/apikey) (has a free tier), or Claude from the [Claude Console](https://platform.claude.com).
2. In the Developer Console **Code** tab, create `lambda/config.json`:

```json
{
  "provider": "gemini",
  "api_key": "YOUR-KEY",
  "model": "gemini-3.5-flash-lite",
  "timeout_seconds": 5.5
}
```

   For Claude use `"provider": "anthropic"` and `"model": "claude-haiku-4-5"`.
3. Click **Deploy**.

The Code tab lives in your private Alexa-hosted repo, so the key never reaches GitHub. Your spoken answers (as text) are sent to that provider for feedback.

Alexa gives a skill about 8 seconds to reply. The skill says "Let me review your answers" while it waits, gives the model 5.5 seconds, and falls back to rule-based tips if it runs out. Keep a fast model.

## Honest limits

- **Pronunciation isn't scored.** The skill receives Alexa's text transcript, never your audio. Fillers ("umm") are usually dropped, so fluency looks better than it is. Record yourself on your phone too.
- **Part 2 comes in chunks.** Alexa stops listening when you pause, so the skill replies "go on" between chunks and stops you at two minutes. Speaking without pausing is the goal anyway.
- **German answers are in English.** The skill runs in an English locale, so it checks what German phrases *mean*, not how you say them.
- **Band estimates are rough.** Treat them as direction, not a prediction.

## Change things

- Invocation name: Build tab → Invocations → Skill Invocation Name.
- Questions, cue cards and German lessons: `lambda/coach/content.py`.
- Progress (German lesson number, feedback history) is saved in the skill's DynamoDB table, which Alexa-hosted skills include.

## Test locally

```
pip install ask-sdk-core
python tests/test_flows.py
```

The tests feed real Alexa request envelopes through the handler and check SSML validity, response size and every flow.
