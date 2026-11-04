import os
import base64, io, json, re, time, urllib.request
from PIL import Image
S=os.environ.get("SCRATCH","/tmp/xat-jarvis-test")
prompt=open(S+"/oc_prompt2.txt").read()+"\n\nThe screenshot is 1920x1080 pixels."
im=Image.open(S+"/st.png").convert("RGB"); W,H=im.size
buf=io.BytesIO(); im.save(buf,"PNG"); b=base64.b64encode(buf.getvalue()).decode()
def call(text):
    body={"model":"qwen3-vl:30b-a3b-instruct","stream":False,"instructions":prompt,"input":[{"role":"user","content":[{"type":"input_text","text":text},{"type":"input_image","image_url":"data:image/png;base64,"+b}]}]}
    r=json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:11434/v1/responses",json.dumps(body).encode(),{"Content-Type":"application/json","Authorization":"Bearer ollama"}),timeout=180))
    return "".join(c.get("text","") for o in r.get("output",[]) for c in o.get("content",[]) if isinstance(c,dict))
def iou(a,b):
    ix=max(0,min(a[2],b[2])-max(a[0],b[0])); iy=max(0,min(a[3],b[3])-max(a[1],b[1])); i=ix*iy
    u=(a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-i; return i/u if u else 0
def cover(box,truth):  # fraction of truth area inside box
    ix=max(0,min(box[2],truth[2])-max(box[0],truth[0])); iy=max(0,min(box[3],truth[3])-max(box[1],truth[1]))
    return ix*iy/((truth[2]-truth[0])*(truth[3]-truth[1]))
targets={"Share button":(1523,38,1585,66),"Context section on the right":(1297,170,1584,230),"Search item in the sidebar":(338,116,486,142)}
print(f"{'target':32} {'overlap(IoU) 3 tries':22} {'target covered by padded box'}")
for name,t in targets.items():
    ious=[];covs=[];fails=0
    for i in range(3):
        txt=call(f"Highlight the {name}.")
        m=re.search(r"\[RECT:(\d+),(\d+),(\d+),(\d+)",txt)
        if not m: fails+=1; continue
        x1,y1,x2,y2=[int(v) for v in m.groups()]
        bx=(x1/1000*W,y1/1000*H,x2/1000*W,y2/1000*H); bx=(bx[0]-10,bx[1]-8,bx[2]+10,bx[3]+8)
        ious.append(iou(bx,t)); covs.append(cover(bx,t))
    f=lambda v:"/".join("%.2f"%x for x in v) if v else "n/a"
    print(f"{name:32} {f(ious):22} {f(covs)}  fails={fails}")
