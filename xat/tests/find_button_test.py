"""'Find the button that does X' accuracy on a real window. Uses OpenClicky's real prompt (oc_prompt2.txt) against a full-screen
screenshot, converts the model's 0-1000 grid to pixels exactly like the app, and checks whether the point lands INSIDE the right button.
Usage: find_button_test.py screenshot.png [repeats=3]     (Calculator centred at its default spot; see TARGETS)"""
import base64, json, re, struct, sys, time, urllib.request, os
png = sys.argv[1]; reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
raw = open(png, "rb").read(); W, H = struct.unpack(">II", raw[16:24]); B64 = base64.b64encode(raw).decode()
HERE = os.path.dirname(os.path.abspath(__file__))
PROMPT = open(os.path.join(HERE, "oc_prompt2.txt")).read() + "\n\nThe screenshot is %dx%d pixels." % (W, H)
R = 24  # button radius in px (Calculator buttons are ~48 px across)
# description of the function -> truth centre (px) in a 1920x1080 screenshot, Calculator window at (510,539)
TARGETS = {
 "clears everything": ("AC", 598, 697), "deletes the last digit": ("delete", 544, 697), "turns a number into a percentage": ("%", 652, 697),
 "divides": ("÷", 706, 697), "multiplies": ("×", 706, 751), "subtracts": ("−", 706, 804), "adds numbers together": ("+", 706, 857),
 "shows the result": ("=", 706, 911), "enters zero": ("0", 598, 911), "adds a decimal point": (".", 652, 911), "flips a number between positive and negative": ("±", 544, 911),
}
def ask(q):
    body = {"model": "qwen3-vl:30b-a3b-instruct", "stream": False, "instructions": PROMPT,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": q}, {"type": "input_image", "image_url": "data:image/png;base64," + B64}]}]}
    r = urllib.request.Request("http://127.0.0.1:11434/v1/responses", json.dumps(body).encode(), {"Content-Type": "application/json", "Authorization": "Bearer ollama"})
    d = json.load(urllib.request.urlopen(r, timeout=180))
    return "".join(c.get("text", "") for o in d.get("output", []) for c in o.get("content", []) if isinstance(c, dict))
hits = tot = 0; rows = []; t0 = time.time()
for fn, (name, tx, ty) in TARGETS.items():
    errs = []; ok = 0
    for _ in range(reps):
        t = ask("Find the button that %s." % fn); m = re.search(r"\[POINT:(\d+)\s*,\s*(\d+)", t); tot += 1
        if not m: errs.append(None); continue
        px, py = int(m.group(1)) / 1000 * W, int(m.group(2)) / 1000 * H; e = ((px - tx) ** 2 + (py - ty) ** 2) ** .5
        errs.append(e); ok += e <= R
    hits += ok; got = [e for e in errs if e is not None]
    rows.append((fn, name, ok, reps, ("%.0fpx avg" % (sum(got) / len(got))) if got else "no point"))
print("%-48s %-7s %-6s %s" % ("request: find the button that ...", "target", "hits", "mean error"))
for fn, name, ok, n, e in rows: print("%-48s %-7s %d/%-4d %s" % (fn, name, ok, n, e))
print("\ninside-the-button hits: %d/%d (%.0f%%), %.0fs" % (hits, tot, 100 * hits / tot, time.time() - t0))
