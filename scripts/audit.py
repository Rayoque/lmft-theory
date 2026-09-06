# -*- coding: utf-8 -*-
"""Three deterministic audits of the SHIPPED bank. No model calls."""
import io, json, os, re, unicodedata, collections
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..")
L={"\ufb00":"ff","\ufb01":"fi","\ufb02":"fl","\ufb03":"ffi","\ufb04":"ffl"}
def clean(s):
    for k,v in L.items(): s=s.replace(k,v)
    return unicodedata.normalize("NFC"," ".join(s.split()))
def norm(s):
    s=clean(s).lower().replace("\u201c","").replace("\u201d","").replace("\u2019","'")
    return " ".join(re.sub(r"[^a-z0-9 ]+"," ",s).split())

I=json.load(io.open(os.path.join(ROOT,"items.json"),encoding="utf-8"))
# Build the corpus from the extracted BLOCKS, in document order. The .txt
# rendering carries "[0233]" line-number prefixes that would splice digits into
# the middle of any quote spanning two blocks.
raw=[]
for fn in sorted(os.listdir(os.path.join(ROOT,"extracted"))):
    if not fn.endswith(".json") or fn.startswith("_"): continue
    d=json.load(io.open(os.path.join(ROOT,"extracted",fn),encoding="utf-8"))
    for b in d["blocks"]:
        if b["kind"]=="p": raw.append(b["text"])
        else: raw.extend(c["text"] for row in b["rows"] for c in row if c["text"].strip())
CORPUS=norm(" ".join(raw))

# 1. END-TO-END TRACEABILITY: sourceLine must appear in the raw packet text,
#    not merely in theories.json. This is the anti-hallucination claim's proof.
orphan=[]
for it in I["items"]:
    for o in it["options"]:
        if norm(o["sourceLine"]) not in CORPUS:
            orphan.append((it["id"],o["text"][:40]))
print("1. END-TO-END TRACEABILITY (option sourceLine present in raw packet text)")
print("   options checked:",sum(len(x["options"]) for x in I["items"]))
print("   NOT found in packets:",len(orphan))
for x in orphan[:5]: print("     ",x)

# 2. ANSWER POSITION BALANCE (the option-A bug must be gone)
pos=collections.Counter()
for it in I["items"]:
    pos[[i for i,o in enumerate(it["options"]) if o["correct"]][0]]+=1
n=len(I["items"])
print("\n2. ANSWER POSITION BALANCE across %d items"%n)
for k in sorted(pos): print("   %s: %3d (%.0f%%)"%("ABCD"[k],pos[k],100.0*pos[k]/n))
mx=max(pos.values())/float(n)
print("   verdict:","PASS - no positional tell" if mx<0.33 else "SKEWED (%.0f%% in one slot)"%(mx*100))

# 3. LENGTH TELL: can she score by picking the longest/shortest option?
longest=shortest=0
for it in I["items"]:
    ls=[len(o["text"]) for o in it["options"]]
    ci=[i for i,o in enumerate(it["options"]) if o["correct"]][0]
    if ls[ci]==max(ls): longest+=1
    if ls[ci]==min(ls): shortest+=1
print("\n3. LENGTH TELL across %d items (chance = 25%%)"%n)
print("   correct option is LONGEST : %3d (%.0f%%)"%(longest,100.0*longest/n))
print("   correct option is SHORTEST: %3d (%.0f%%)"%(shortest,100.0*shortest/n))
worst=max(longest,shortest)/float(n)
print("   verdict:","PASS - no exploitable tell" if worst<0.40 else
      "EXPLOITABLE: %.0f%% beats chance badly"%(worst*100))
bad=[it["id"] for it in I["items"]
     if len(max(it["options"],key=lambda o:len(o["text"]))["text"])>3*
        (sum(len(o["text"]) for o in it["options"])/4.0)
     and max(it["options"],key=lambda o:len(o["text"]))["correct"]]
print("   items where correct option is >3x mean length:",len(bad))
for x in bad[:6]: print("     ",x)
