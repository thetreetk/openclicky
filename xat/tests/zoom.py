import os
import base64, io, json, re, sys, urllib.request
from PIL import Image
S=os.environ.get("SCRATCH","/tmp/xat-jarvis-test")
im=Image.open(S+"/rect2.png").convert("RGB"); W,H=im.size
def ask(img, text, instr):
    buf=io.BytesIO(); img.save(buf,"PNG"); b=base64.b64encode(buf.getvalue()).decode()
    body={"model":"qwen3-vl:30b-a3b-instruct","stream":False,"instructions":instr,
          "input":[{"role":"user","content":[{"type":"input_text","text":text},{"type":"input_image","image_url":"data:image/png;base64,"+b}]}]}
    r=json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:11434/v1/responses",json.dumps(body).encode(),{"Content-Type":"application/json","Authorization":"Bearer ollama"}),timeout=120))
    t="".join(c.get("text","") for o in r.get("output",[]) for c in o.get("content",[]) if isinstance(c,dict))
    m=re.search(r"\[?POINT:(\d+)\s*,\s*(\d+)",t) or re.search(r"\[(\d+)\s*,\s*(\d+)\]",t)
    return (int(m.group(1)),int(m.group(2))) if m else None
INSTR="Reply with only [POINT:x,y] where x,y are integers on a 0-1000 grid (0,0 top-left, 1000,1000 bottom-right of the image) at the exact center of the requested element."
target=(1873,52); label=sys.argv[1] if len(sys.argv)>1 else "Share button"
base=[];zoom=[]
for i in range(5):
    p=ask(im,f"Point at the {label}.",INSTR)
    if not p: continue
    bx,by=p[0]/1000*W,p[1]/1000*H; base.append((bx,by))
    cw,ch=480,270
    x0=int(min(max(bx-cw/2,0),W-cw)); y0=int(min(max(by-ch/2,0),H-ch))
    crop=im.crop((x0,y0,x0+cw,y0+ch)).resize((960,540),Image.LANCZOS)
    q=ask(crop,f"This is a zoomed crop of the screen. Point at the center of the {label}.",INSTR)
    if q: zoom.append((x0+q[0]/1000*cw, y0+q[1]/1000*ch))
def err(pts): return [round(((x-target[0])**2+(y-target[1])**2)**0.5,1) for x,y in pts]
print("baseline errors (px):",err(base)); print("zoomed errors   (px):",err(zoom))
