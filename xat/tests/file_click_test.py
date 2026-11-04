"""'Double click the file called X' accuracy on Finder list rows (about 20 px pitch). Offline, with OpenClicky's real prompt:
first guess vs the app's zoom refinement (480x270 crop, <32 px nudge). Ground truth: row centres from a screenshot you measure.
Usage: file_click_test.py screenshot.png rows.json [repeats=3]   rows.json = {"notes april": [x, y], ...} in screenshot pixels"""
import base64, io, json, os, re, struct, subprocess, sys, tempfile, time, urllib.request
png, rows_f = sys.argv[1], sys.argv[2]; reps = int(sys.argv[3]) if len(sys.argv) > 3 else 3
raw = open(png, "rb").read(); W, H = struct.unpack(">II", raw[16:24]); B64 = base64.b64encode(raw).decode()
ROWS = json.load(open(rows_f))
PROMPT = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "oc_prompt2.txt")).read() + "\n\nThe screenshot is %dx%d pixels." % (W, H)
ZOOM_INSTR = "Reply with only [POINT:x,y] where x,y are integers on a 0-1000 grid (0,0 top-left, 1000,1000 bottom-right of the image) at the exact center of the requested element."
def call(img_b64, text, instr, mime="png"):
    body = {"model": "qwen3-vl:30b-a3b-instruct", "stream": False, "instructions": instr,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": text}, {"type": "input_image", "image_url": "data:image/%s;base64,%s" % (mime, img_b64)}]}]}
    r = urllib.request.Request("http://127.0.0.1:11434/v1/responses", json.dumps(body).encode(), {"Content-Type": "application/json", "Authorization": "Bearer ollama"})
    d = json.load(urllib.request.urlopen(r, timeout=180))
    return "".join(c.get("text", "") for o in d.get("output", []) for c in o.get("content", []) if isinstance(c, dict))
def crop_b64(cx, cy, cw=480, ch=270):
    x0 = int(min(max(cx - cw / 2, 0), W - cw)); y0 = int(min(max(cy - ch / 2, 0), H - ch)); d = tempfile.mkdtemp()
    src, out = os.path.join(d, "s.png"), os.path.join(d, "c.png"); open(src, "wb").write(raw)
    subprocess.run(["/usr/bin/sips", "-c", str(ch), str(cw), "--cropOffset", str(y0), str(x0), src, "--out", out], capture_output=True)
    subprocess.run(["/usr/bin/sips", "--resampleWidth", str(cw * 2), out], capture_output=True)
    return base64.b64encode(open(out, "rb").read()).decode(), x0, y0, cw, ch
PITCH = 20.0
res = {"first": [0, 0], "zoom": [0, 0], "zoom2": [0, 0]}; print("%-24s %-22s %-22s %s" % ("file", "first guess (rows)", "1 zoom", "2 zooms (tighter)"))
for name, (tx, ty) in ROWS.items():
    f, z, z2 = [], [], []
    for _ in range(reps):
        t = call(B64, "Double click the file called %s." % name, PROMPT); m = re.search(r"\[POINT:(\d+)\s*,\s*(\d+)", t)
        if not m: f.append(None); z.append(None); z2.append(None); continue
        px, py = int(m.group(1)) / 1000 * W, int(m.group(2)) / 1000 * H; f.append((py - ty) / PITCH)
        cb, x0, y0, cw, ch = crop_b64(px, py)
        t2 = call(cb, "This is a zoomed crop of the screen. Point at the center of the file called %s." % name, ZOOM_INSTR); m2 = re.search(r"(\d+)\s*,\s*(\d+)", t2)
        if m2:
            zx, zy = x0 + int(m2.group(1)) / 1000 * cw, y0 + int(m2.group(2)) / 1000 * ch
            if ((zx - px) ** 2 + (zy - py) ** 2) ** .5 < 32: px, py = zx, zy       # the app's guard: refinement is a nudge only
        z.append((py - ty) / PITCH)
        cb2, x1, y1, cw2, ch2 = crop_b64(px, py, 240, 135)
        t3 = call(cb2, "This is a zoomed crop of the screen. Point at the center of the file called %s." % name, ZOOM_INSTR); m3 = re.search(r"(\d+)\s*,\s*(\d+)", t3)
        if m3:
            wx, wy = x1 + int(m3.group(1)) / 1000 * cw2, y1 + int(m3.group(2)) / 1000 * ch2
            if ((wx - px) ** 2 + (wy - py) ** 2) ** .5 < 32: px, py = wx, wy
        z2.append((py - ty) / PITCH)
    for key, vals in (("first", f), ("zoom", z), ("zoom2", z2)):
        for v in vals: res[key][1] += 1; res[key][0] += (v is not None and abs(v) < 0.5)
    fmt = lambda v: ", ".join("%+.1f" % x if x is not None else "none" for x in v)
    print("%-24s %-22s %-22s %s" % (name, fmt(f), fmt(z), fmt(z2)))
for k, (ok, n) in res.items(): print("%s: landed on the correct row %d/%d (offset < half a row)" % (k, ok, n))
