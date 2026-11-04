"""'Draw a square around X' on a real web page. Ground truth = bounding boxes found in the screenshot by webpage/bbox.swift (unique colours
in webpage/page.html). Uses OpenClicky's real prompt; converts the model's 0-1000 [RECT:x1,y1,x2,y2] like the app (plus its 10x8 px padding).
Usage: webpage_box_test.py screenshot.png truth.json [repeats=3]"""
import base64, json, os, re, struct, sys, time, urllib.request
png, truth_f = sys.argv[1], sys.argv[2]; reps = int(sys.argv[3]) if len(sys.argv) > 3 else 3
raw = open(png, "rb").read(); W, H = struct.unpack(">II", raw[16:24]); B64 = base64.b64encode(raw).decode()
TRUTH = json.load(open(truth_f))
PROMPT = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "oc_prompt2.txt")).read() + "\n\nThe screenshot is %dx%d pixels." % (W, H)
NAMES = {"signup": "Sign up button", "login": "Log in button", "search": "search field", "cart1": "Add to cart button for the Cordless Drill",
         "cart2": "Add to cart button for the Socket Set", "subscribe": "Subscribe button"}
def ask(q):
    body = {"model": "qwen3-vl:30b-a3b-instruct", "stream": False, "instructions": PROMPT,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": q}, {"type": "input_image", "image_url": "data:image/png;base64," + B64}]}]}
    r = urllib.request.Request("http://127.0.0.1:11434/v1/responses", json.dumps(body).encode(), {"Content-Type": "application/json", "Authorization": "Bearer ollama"})
    d = json.load(urllib.request.urlopen(r, timeout=180))
    return "".join(c.get("text", "") for o in d.get("output", []) for c in o.get("content", []) if isinstance(c, dict))
def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0])); iy = max(0, min(a[3], b[3]) - max(a[1], b[1])); i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i; return i / u if u else 0
def cover(box, t):
    ix = max(0, min(box[2], t[2]) - max(box[0], t[0])); iy = max(0, min(box[3], t[3]) - max(box[1], t[1])); return ix * iy / ((t[2] - t[0]) * (t[3] - t[1]))
print("%-44s %-22s %-22s %s" % ("draw a square around the ...", "IoU (padded box)", "target covered", "no box"))
good = tot = 0; t0 = time.time()
for key, label in NAMES.items():
    t = TRUTH.get(key)
    if not t: print("%-44s (not found on screen)" % label); continue
    ious, covs, miss = [], [], 0
    for _ in range(reps):
        txt = ask("Draw a square around the %s." % label); tot += 1
        m = re.search(r"\[RECT:(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", txt)
        if not m: miss += 1; continue
        x1, y1, x2, y2 = [int(v) for v in m.groups()]
        b = (x1 / 1000 * W - 10, y1 / 1000 * H - 8, x2 / 1000 * W + 10, y2 / 1000 * H + 8)
        ious.append(iou(b, t)); covs.append(cover(b, t)); good += (cover(b, t) >= 0.9 and iou(b, t) >= 0.5)
    f = lambda v: "/".join("%.2f" % x for x in v) if v else "-"
    print("%-44s %-22s %-22s %d" % (label, f(ious), f(covs), miss))
print("\nboxes that cover >=90%% of the target with IoU >= 0.5: %d/%d, %.0fs" % (good, tot, time.time() - t0))
