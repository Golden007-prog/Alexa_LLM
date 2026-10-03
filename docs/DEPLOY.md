# Deploy to your Echo Dot

The skill stays in the **development stage**: free, private to your Amazon account, and never submitted for certification. Sign in to everything below with the **same Amazon account your Echo Dot uses** (amazon.in). Keep the Echo's language on **English (India)**; the skill's dates roll over at midnight IST for that locale.

Pick one path. Path A is a one-time import through the browser. Path B uses the ASK CLI and is better for pushing updates.

## Path A: console Git import (simplest)

1. Open the [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) and click **Create Skill**.
2. **Name:** `IELTS and German Coach`. **Primary locale:** English (IN). Click **Next**.
3. **Experience:** Other → **Custom**. **Hosting:** **Alexa-hosted (Python)**. **Hosting region:** whichever of the three offered is closest to you; for India that's EU (Ireland). Click **Next**.
4. **Templates:** choose **Import skill**, paste `https://github.com/Golden007-prog/Alexa_LLM.git`, and click **Import**. The repo must be public; it is. Amazon's guide: [Import a skill from a Git repository](https://developer.amazon.com/en-US/docs/alexa/hosted-skills/alexa-hosted-skills-git-import.html).
5. **Set the invocation name.** The import resets it to `change me`, and only creates the primary locale (English (IN)), which is all your Echo needs. Go to **Build** tab → **Invocations** → **Skill Invocation Name**, type `study coach`, then **Save** → **Build skill**, and wait for "Build successful". This was observed on 3 Oct 2026: the repo's model says "study coach", but the import replaced it.
6. **Test** tab → set "Skill testing is enabled in" to **Development**. Type `open study coach` to check that it answers.
7. Say to your Echo Dot: **"Alexa, open study coach."** Then follow [DEVICE_TEST_SCRIPT.md](DEVICE_TEST_SCRIPT.md).

To update later with Path A, change the code in the console's **Code** tab and click **Deploy**, or switch to Path B.

## Path B: ASK CLI (for ongoing updates)

**Step 1: install ASK CLI and sign in.** Two commands, run them yourself:

```
npm install -g ask-cli
ask configure
```

`ask configure` opens a browser: sign in with the **same Amazon account** your Echo uses. When it asks about linking an AWS account, answer **No**; Alexa-hosted skills don't need one. You're on Node 25, which ASK CLI may not have been tested on. If `ask` misbehaves, install Node 22 LTS and retry.

**Step 2: create the skill** with Path A steps 1–6 (or `ask new`), and copy its **Skill ID**. It's under the skill name in the console's skills list, as "Copy Skill ID".

**Step 3: clone the hosted skill into a separate folder.**

```
cd "E:\Alexa NLP"
ask init --hosted-skill-id amzn1.ask.skill.YOUR-ID
```

When asked for a folder name, type `hosted-skill`. You now have `E:\Alexa NLP\hosted-skill`, a git clone of Amazon's CodeCommit repo for the skill. It is separate from this GitHub repo.

**Step 4: deploy from this repo.** Do a dry run first:

```
cd "E:\Alexa NLP\Alexa_LLM"
.\scripts\deploy-hosted.ps1 -DryRun
.\scripts\deploy-hosted.ps1
```

The script:
- refuses to run if either repo has uncommitted changes;
- mirrors `lambda/` into the hosted clone without ever touching `lambda/config.json` there;
- copies `skill-package/` and commits;
- asks before running `git push origin master`, which Alexa-hosted turns into a **development-stage** deploy;
- prints the build status.

If PowerShell blocks scripts, run it as `powershell -ExecutionPolicy Bypass -File .\scripts\deploy-hosted.ps1 -DryRun`.

**About branches.** In the hosted repo, `dev` is what the console Code tab shows, `master` is the development stage, and `prod` is live. After a CLI push to `master`, the console may say master is ahead of dev and lock its code editor. To unlock it:

```
cd "E:\Alexa NLP\hosted-skill"
git checkout dev
git pull --rebase
git merge master
git push --no-verify
git checkout master
```

Never push to `prod`; that's the live stage.

**Step 5: simulate the main flows**, from `E:\Alexa NLP\hosted-skill`.

```
ask dialog --locale en-IN
```

For a repeatable run, copy `scripts/dialog-replay.template.json` to `scripts/dialog-replay.json`, put your skill ID in it, and save the conversation:

```
ask dialog --replay scripts\dialog-replay.json --save-skill-io docs\dialog-io.json
```

Paste the console transcript into `docs/DIALOG_TRANSCRIPT.md`. The listening answers in the replay won't match the random call, and that's expected: the point is that every flow answers.

## AI feedback key

Without a key the skill gives rule-based tips: answer length, Part 2 length, linking phrases, overused words, and progressive "-ing" with stative verbs. With a key, feedback adds a rough band range per criterion and two quoted fixes. **The key never goes into GitHub.**

**1. Get a Gemini key.** Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey), sign in with a Google account, and click **Create API key**. Google AI Studio offers a free tier for some models; check its rate-limits page for the current terms before relying on it. The default model, `gemini-3.5-flash-lite`, is listed as stable on [Google's models page](https://ai.google.dev/gemini-api/docs/models), and Google names it as a recommended choice for new projects.

**2. Store it in the skill's S3 bucket (preferred).** It works with both paths, and CLI deploys can't overwrite it.
1. On your PC, create a file named `llm_config.json`:
   ```json
   {
     "provider": "gemini",
     "api_key": "YOUR-KEY",
     "model": "gemini-3.5-flash-lite",
     "timeout_seconds": 5.5
   }
   ```
2. Developer Console → your skill → **Code** tab → **Media storage** (S3) at the bottom left. This opens the S3 console on the skill's bucket.
3. Open the `Media` folder → **Upload** → add `llm_config.json` → **Upload**.
4. Delete the local `llm_config.json` afterwards.
5. The config is read once per Lambda container and then cached. To make a running skill pick up a new or changed key, click **Deploy** in the Code tab (or push again), or wait about 15 minutes for idle containers to recycle.

For Claude instead, use `"provider": "anthropic"` and `"model": "claude-haiku-4-5"`, with a key from the [Claude Console](https://platform.claude.com).

**Alternative (Path A only).** In the console **Code** tab, create `lambda/config.json` with the same content and click **Deploy**. With Path B, the deploy script preserves it, but the Code tab editor may be locked (see "About branches"), so S3 is simpler.

**3. Confirm it works.** Say "part one", answer the six questions in two or three sentences each, then say "feedback".

- **Working:** you hear "Let me review your answers", then rough band ranges such as "six to six point five" and two quoted fixes.
- **Not working:** you hear the rule-based tips plus "For band estimates, add an AI key…". That means the key wasn't loaded.
- **Silent fallback:** if the call failed or ran past its time budget, you get the tips without that sentence.

**4. If it fails, read the logs.** Code tab → **CloudWatch Logs** (top bar) → choose your hosting region → the newest log stream. Look for:

| Log line | Meaning |
|---|---|
| `No S3 LLM config: …` | The file isn't at `Media/llm_config.json`. |
| `LLM HTTP 400` / `403` | A bad request or key. The next 300 characters of the error are logged; the key itself is not. |
| `LLM call failed: … timed out` | The model was too slow for the reply window. |
| `LLM skipped: only 0.8 s left` | Something earlier in the request used up the budget. |
| `Cold start on Python 3.8.x` | The runtime the skill really runs on. |

Your spoken answers, as text, are sent to the provider you configure, to generate feedback. Nothing else leaves Amazon.

## What costs money

Alexa-hosted skills are free within Amazon's usage limits. The development stage is never billed. A Gemini key may be free within Google's free tier; Claude is paid per token. No other service is used.
