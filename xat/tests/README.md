# Tests

All scripts expect Ollama on `:11434` with `qwen3-vl:30b-a3b-instruct` and, for end-to-end runs, the app running with the local settings from `../secrets.env.example`. Scratch files go to `$SCRATCH` (default `/tmp/xat-jarvis-test`).
- `find_button_test.py screenshot.png [repeats]` Calculator button accuracy for functional descriptions.
- `webpage_box_test.py screenshot.png truth.json` box coverage on `webpage/page.html`; `webpage/bbox.swift` produces `truth.json` from a screenshot (unique colours).
- `file_click_test.py screenshot.png rows.json` Finder list rows: first guess vs zoom stages.
- `webpage/clicks.html` click recorder: the clicked element id becomes the page title.
- `oc_tap.py` logging proxy, `holdkeys.swift` push-to-talk key holder, `stress_point.py` / `stress_rect.py` / `zoom.py` older pointing benchmarks (need Pillow).
