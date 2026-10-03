# Alexa+ options: should the coach become an add-on?

Researched on 3 October 2026 from Amazon's official Alexa+ developer pages. Where a page shows an update date, it's noted. Facts are separated from inference.

## Recommendation

**Not yet. Keep the classic custom skill as the product.** As of the docs above, an Alexa+ add-on is a US-only private preview for selected partners. No documented path exists for an individual developer in India, and a tutoring add-on would lose the controls this coach depends on: scripted pauses, a native German voice, and turn-by-turn timing. The low-cost moves are to test the classic skill under Alexa+ on the Echo Dot, and to ask Amazon through DevAssistant whether en-IN access is planned.

## Question 1: can an individual developer in India publish a non-category MCP add-on for language tutoring on en-IN?

**Today, no, as far as the documentation shows.**

- Alexa+ for Builders is described as available to select partners working directly with Amazon's team, with no public waitlist ([Alexa+ for Builders](https://developer.amazon.com/alexaplus/)).
- The add-on lifecycle starts with requesting **Private Preview** access, after which partners receive credentials and the Alexa AI CLI ([Development stages](https://developer.amazon.com/docs/alexaplus/add-ons/alexa-plus-add-on-development-stages.html), updated 10 Jul 2026). The July 2026 announcement calls the build paths "in Preview" and lists company partners ([blog, 23 Jul 2026](https://developer.amazon.com/alexaplus/blogs/2026/07/alexa-plus-new-ways-to-build-experiences)).
- Tutoring isn't one of the Category SDK categories (restaurant reservations, food ordering, home services, local booking, ticketing, ride booking). The **MCP Toolkit** is the route for everything else ([Choose the proper integration approach](https://developer.amazon.com/docs/alexaplus/add-ons/choose-the-proper-alexaplus-integration-approach.html), updated 10 Jul 2026).
- The MCP Toolkit is **available in the United States only** ([MCP Toolkit overview](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-overview.html), updated 3 Aug 2026). en-IN support for add-ons isn't documented. Alexa+ itself launched in India on 16 September 2026 as Early Access, but that is the consumer product, not developer access.
- Whether an individual's request would be approved is **unverified**. The only contact routes found were DevAssistant chat and partner Solutions Architects ([Get support](https://developer.amazon.com/docs/alexaplus/add-ons/get-support-from-amazon.html), updated 2 Sep 2026).

## Question 2: would MCP tools (`start_mock`, `get_feedback`, `german_lesson`) beat the classic skill under Alexa+?

**Facts from the MCP Toolkit pages:**
- **Server:** a remote MCP server over HTTPS (Streamable HTTP), with a round-trip latency requirement under 500 ms.
- **Auth:** OAuth 2.1 with PKCE for user-level tools ([quickstart](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-quickstart.html), [authentication](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-authentication.html)).
- **Context:** Alexa+ keeps the conversation context, and your server gets no session ID ([client lifecycle](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-toolkit-client-lifecycle.html)).
- **Speech:** the design guide says you can't script what Alexa says; Alexa+ phrases replies from your tool data ([design guide](https://developer.amazon.com/docs/alexaplus/add-ons/mcp-addon-design-guide.html), updated 21 Jul 2026). Audio input, SSML and voice selection aren't documented for add-ons.

**What that means for this coach (inference):**

| Need | Classic custom skill (today) | MCP add-on under Alexa+ |
|---|---|---|
| 2-minute Part 2 talk | Works in chunks with "go on" replies, timed from request timestamps | Probably worse: Alexa+ would transcribe and paraphrase, with no control over chunking |
| 1-minute timed prep | SSML `<break>` tags, chained | Not possible if Alexa's speech can't be scripted (SSML unverified) |
| Native German voice | Polly Vicki via `<voice>` and `<lang>` | No documented voice control |
| Listening drill (two accents, one trap, scored answers) | Full control of the dialogue audio | Can't script the call, which defeats the drill |
| Multi-turn quizzes with progress | DynamoDB plus a session state machine | Roughly equal, maybe nicer conversation; the server holds the state, keyed by the account-linked user |
| Free-form chat about mistakes | Limited to the feedback flow | Better: Alexa+ is conversational by design |

**Verdict:** for exam drills, the classic skill is the better fit, because the exam format *is* the scripted timing, accents and voices. MCP would shine for open conversation practice ("chat with me about my hometown in English"), which is a different product. That is worth revisiting if Amazon opens the MCP Toolkit to individual developers in India.

## Classic skills under Alexa+

Amazon's February 2025 announcement says custom skills stay available on the original Alexa experience and can still be updated and published. Working on Alexa+ is not automatic: skills are *considered* for direct invocation through an evaluation form ([blog, 26 Feb 2025](https://developer.amazon.com/en-US/blogs/alexa/alexa-skills-kit/2025/02/new-alexa-announce-blog)). No deprecation date for custom skills was found. How "Alexa, open study coach" routes on an Alexa+ Early Access device in en-IN is **unverified**. One unofficial report describes a one-word invocation name being misrouted. "Study coach" is two words, so test it.

## Next steps (cheap, no building)

1. On the Echo Dot with Alexa+ Early Access, say "Alexa, open study coach". Record whether it opens, mishears, or answers generatively.
2. If it misroutes, try "Alexa, launch study coach" and the one-shot "ask study coach for a German lesson". Note which work in [DEVICE_TEST_SCRIPT.md](DEVICE_TEST_SCRIPT.md).
3. Ask in DevAssistant whether MCP Toolkit access for en-IN or for individual developers is planned. Find the direct-invocation evaluation form mentioned in the 2025 blog; no direct link was found.
