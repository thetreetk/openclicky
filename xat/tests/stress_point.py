import os
import base64, io, json, re, time, urllib.request
from PIL import Image
S=os.environ.get("SCRATCH","/tmp/xat-jarvis-test")
prompt=open(S+"/oc_prompt2.txt").read()+"\n\nThe screenshot is 1920x1080 pixels."
im=Image.open(S+"/st.png").convert("RGB"); W,H=im.size
def call(img,text,instr):
    buf=io.BytesIO(); img.save(buf,"PNG"); b=base64.b64encode(buf.getvalue()).decode()
    body={"model":"qwen3-vl:30b-a3b-instruct","stream":False,"instructions":instr,"input":[{"role":"user","content":[{"type":"input_text","text":text},{"type":"input_image","image_url":"data:image/png;base64,"+b}]}]}
    r=json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:11434/v1/responses",json.dumps(body).encode(),{"Content-Type":"application/json","Authorization":"Bearer ollama"}),timeout=180))
    return "".join(c.get("text","") for o in r.get("output",[]) for c in o.get("content",[]) if isinstance(c,dict))
INSTR2="Reply with only [POINT:x,y] where x,y are integers on a 0-1000 grid (0,0 top-left, 1000,1000 bottom-right of the image) at the exact center of the requested element."
targets={"Apple menu":(27,14),"clock":(1835,14),"Share button":(1553,52),"New item in the sidebar":(378,95),"Search item in the sidebar":(387,129),"Scheduled item in the sidebar":(398,231),"Customize item in the sidebar":(400,265),"Compact session button":(1523,581)}
rows=[];t0=time.time()
for name,(tx,ty) in targets.items():
    eb=[];ez=[];fail=0
    for i in range(3):
        t=call(im,f"Point at the {name}.",prompt)
        m=re.search(r"\[POINT:(\d+)\s*,\s*(\d+)",t)
        if not m: fail+=1; continue
        bx,by=int(m.group(1))/1000*W,int(m.group(2))/1000*H
        eb.append(((bx-tx)**2+(by-ty)**2)**0.5)
        cw,ch=480,270; x0=int(min(max(bx-cw/2,0),W-cw)); y0=int(min(max(by-ch/2,0),H-ch))
        crop=im.crop((x0,y0,x0+cw,y0+ch)).resize((960,540),Image.LANCZOS)
        t2=call(crop,f"This is a zoomed crop of the screen. Point at the center of the {name}.",INSTR2)
        m2=re.search(r"(\d+)\s*,\s*(\d+)",t2)
        if m2:
            zx,zy=x0+int(m2.group(1))/1000*cw,y0+int(m2.group(2))/1000*ch
            ez.append(((zx-tx)**2+(zy-ty)**2)**0.5)
    f=lambda v: ("%.0f"%(sum(v)/len(v))+"px (max %.0f)"%max(v)) if v else "n/a"
    rows.append((name,f(eb),f(ez),fail))
print(f"{'target':32} {'first guess avg error':24} {'zoomed avg error':22} fails")
for r in rows: print(f"{r[0]:32} {r[1]:24} {r[2]:22} {r[3]}")
print("total %.0fs"%(time.time()-t0))
