# Changelog (XAT fork)

## Unreleased
- The island/pill is off on displays without a physical notch (it covered browser tab strips and opened an input surface on hover). Opt back in with `defaults write com.xat.openclicky openClickyShowIslandOnNotchlessDisplays -bool true`. Notched MacBook displays are unchanged.
- Fixes from the overnight audit (found by Claude, checked against the code): the pronoun "one" ("click the blue one") no longer demands a "1" on screen; "find X and open it" double-clicks only files, folders and icons (buttons and links get one click); "open a new document" is no longer read as a double click; a spoken choice handles negation ("not the first one, the second") and an unrelated remark no longer drops the pending choice. Known trade-off: a trailing "one" is dropped from a phrase unless it follows a numbering word (version, chapter, step, page...), so "report one" now matches "report".

## 0.1.1 (2026-11-04)
- Ambiguous click requests ask which one and accept a spoken choice; interrupted agent tasks older than 20 minutes are not auto-resumed.

## 0.1.0 (2026-11-03)
Six commits on top of upstream `e9eb06a`; see `FORK.md` for the table. Highlights: local model and voice, pointing requests stay on the voice path, Agent Mode on Hermes, text-first clicking with double click.