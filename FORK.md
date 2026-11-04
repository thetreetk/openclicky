# OpenClicky, XAT fork: fully local brain, voice, pointer and clicking

> Unofficial fork of [jasonkneen/openclicky](https://github.com/jasonkneen/openclicky) (MIT), itself derived from [farzaa/clicky](https://github.com/farzaa/clicky) (MIT).
> Not affiliated with either. Upstream's `README.md` and licence are unchanged; this file and `xat/` are additions, plus the Swift changes listed below.

## What this fork is for
Run OpenClicky with **no cloud services and no subscription**: a local vision model (Ollama) for answers, pointing, boxes and clicking, a local voice (Kokoro),
and optionally a local agent (Hermes) for Agent Mode. It keeps the upstream behaviour when none of the new settings are present.

## Branches
| Branch | Contents |
|---|---|
| `main` | mirror of upstream `main` |
| `hermes-backend` (default) | upstream + six commits + `FORK.md` + `xat/` |

Base commit: `e9eb06a`. Sync: `git fetch upstream && git rebase upstream/main` on `hermes-backend`. The larger files touched are `CompanionManager.swift`, `CompanionManager+AIResponsePipeline.swift` and `CodexAgentSession.swift`, which upstream edits often, so expect to resolve conflicts by hand and re-run the tests.

## Commits
| # | Commit | What it does |
|---|---|---|
| 1 | build under the `com.xat` identity | bundle and app-group identifiers, so it builds under another Apple identity (the upstream team ID is left untouched; build unsigned) |
| 2 | local OpenAI-compatible model and local voice | `OPENAI_BASE_URL`, `OPENCLICKY_OPENAI_MODEL`, `OPENCLICKY_LOCAL_TTS_URL/VOICE`; 0-1000 grid to pixel conversion for points, boxes and scribbles; box padding; zoomed second look (`LocalPointRefiner`); local Kokoro speech with trailing silence so playback is not cut; caption below the box |
| 3 | Codex Agent Mode on the local model | model override in the five places that name a model; custom Codex provider; the sync script that provisions the runtime |
| 4 | pointing requests stay on the voice path | "find / locate / show me / where is ... the button / menu / icon / tab / field" is answered by the fast voice + pointer path instead of Agent Mode (which cannot point) |
| 5 | Agent Mode on Hermes | `OPENCLICKY_HERMES_URL` / `OPENCLICKY_HERMES_KEY` send agent tasks to a Hermes chat-completions API; no Codex runtime needed |
| 6 | reliable clicking on the local model | targets that are visible text (file names, labels, links) are found by reading the screen with Vision OCR; the model is only the fallback and gets the same grid conversion and a two-stage zoom; "double click X", "find X and double click it", "open the file called X" are real clicks; direct clicks never become agent tasks |

## Configure
Copy `xat/secrets.env.example` to `~/.config/openclicky/secrets.env` (mode 600). Typical local stack: Ollama with `qwen3-vl:30b-a3b-instruct` on `:11434` (keep it loaded; a cold reload costs 10-30 s),
Kokoro on `:8880`. Defaults to set once: `openClickyTTSProvider=microsoft_edge` (that slot now calls the local voice), `isTutorModeEnabled=0` (tutor mode speaks unprompted), `isClickyCursorEnabled=1`, `hasCompletedOnboarding=1`.
Computer use is **off** by default (an upstream choice): turn it on in settings or `defaults write <bundle id> openClickyNativeComputerUseEnabled -bool true`, and grant Accessibility.

## Build
`xcodebuild -project cursor-buddy.xcodeproj -scheme cursor-buddy -configuration Debug -destination 'platform=macOS' CODE_SIGNING_ALLOWED=NO CODE_SIGN_IDENTITY="" build`, then open the built app. Hold Control+Option to talk.

## Tests (`xat/tests`)
Offline scripts use the app's real prompt (`oc_prompt2.txt`) against a screenshot and grade against ground truth; `oc_tap.py` is a logging proxy that records the model's private `[POINT]`/`[RECT]` tags (the overlay is hidden from screen capture); `holdkeys.swift` holds the push-to-talk keys for end-to-end runs; `webpage/` is a test page with unique-colour elements and a click recorder.

| Check (author's machine, Apple silicon) | Result |
|---|---|
| "Find the button that does X" on Calculator (11 buttons x 3, functional descriptions) | 33/33 inside the correct button, 3-9 px mean error |
| Highlight boxes on a web page (6 elements x 3) | 16/18 cover the target (>=90%) with IoU >= 0.5; coverage 100% on 5 of 6 elements |
| Same requests by real voice | routed to the voice path, pointer and box produced in ~0.5 s once the model is warm |
| Website clicks (buttons, links, 18 px close icon, banner buttons, "Add to cart for the Socket Set") | all landed on the right element |
| File find and double click (7 similarly named files, incl. `report_final` vs `report_final_v2`) | 7/7 opened the right file |
| Finder rows at 20 px pitch, model only: first guess / one zoom / two zooms | 15/21 / 19/21 / 21/21 (OCR makes this moot for named files) |

## Known limits
- Ambiguous requests ("Add to cart" with two identical buttons) click one without asking.
- No scrolling: a target below the fold is reported as not found.
- A vision model can still invent labels on dense screens; text-first targeting avoids that for anything with readable text.
- Agent tasks that cannot finish are auto-resumed on every launch; stop stray ones (restart the agent backend) before testing voice.

## Licence and credit
MIT, as upstream (`LICENSE`). Credit to Jason Kneen (OpenClicky) and Farza Majeed (Clicky) and their contributors. Changes here are by [@thetreetk](https://github.com/thetreetk).
