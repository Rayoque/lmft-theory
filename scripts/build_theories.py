# -*- coding: utf-8 -*-
"""Resolve spec.py block indices into theories.json with verbatim sourceLines.

Every sourceLine is pulled directly out of extracted/*.json. Nothing is typed
by hand, so no sourceLine can contain text absent from the packet.
Fails loudly on any out-of-range index rather than emitting a silent blank.
"""
import io
import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec import SPEC  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
EXT = os.path.join(ROOT, "extracted")

# Typographic ligatures are a font artifact of the source PDF->docx path.
# Expanding them changes rendering only, never words.
LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl",
             "ﬃ": "ffi", "ﬄ": "ffl"}


def clean(s):
    for k, v in LIGATURES.items():
        s = s.replace(k, v)
    return unicodedata.normalize("NFC", " ".join(s.split()))


DOCS = {}
for fn in os.listdir(EXT):
    if fn.endswith(".json") and not fn.startswith("_"):
        with io.open(os.path.join(EXT, fn), encoding="utf-8") as f:
            d = json.load(f)
        idx = {}
        for b in d["blocks"]:
            if b["kind"] == "p":
                idx[b["i"]] = clean(b["text"])
            else:
                cells = []
                for row in b["rows"]:
                    for c in row:
                        if c["text"].strip():
                            cells.append(c["text"].strip())
                idx[b["i"]] = clean(" | ".join(cells))
        DOCS[d["sourceDoc"].replace("/", "-")] = idx

ERRORS = []


def line(doc, ids, ctx):
    """Join blocks ids into one verbatim sourceLine."""
    if doc not in DOCS:
        ERRORS.append("missing doc %s (%s)" % (doc, ctx))
        return ""
    parts = []
    for i in ids:
        if i not in DOCS[doc]:
            ERRORS.append("%s block %d out of range (%s)" % (doc, i, ctx))
            return ""
        parts.append(DOCS[doc][i])
    return clean(" ".join(parts))


def fact(doc, ids, ctx, text=None):
    sl = line(doc, ids, ctx)
    return {"text": text if text is not None else sl, "sourceLine": sl,
            "sourceDoc": doc, "blocks": ids}


def termfact(doc, term, ids, ctx):
    sl = line(doc, ids, ctx)
    definition = sl
    # Strip a leading "Term:" or "Term" label so definition reads clean.
    for cand in (term + ":", term.rstrip(":") + ":"):
        if sl.lower().startswith(cand.lower()):
            definition = sl[len(cand):].strip()
            break
    else:
        if sl.lower().startswith(term.lower()):
            definition = sl[len(term):].lstrip(" :–-").strip()
    # Stripping the label can leave an orphaned fragment ("of the therapy aims
    # to alter...", ". If person had ideas..."). If the remainder does not start
    # a sentence, keep the whole line instead -- a fragment reads as a broken
    # question.
    if not definition or not definition[0].isupper():
        definition = sl
    return {"term": term, "definition": definition, "sourceLine": sl,
            "sourceDoc": doc, "blocks": ids}


models = []
for mid, s in SPEC.items():
    doc = s["doc"]
    m = {"id": mid, "name": s["name"], "family": s["family"], "sourceDoc": doc}

    m["changeMechanism"] = (None if s["changeMechanism"] is None
                            else fact(doc, s["changeMechanism"], mid + ".change"))
    m["therapistRoles"] = (None if s["therapistRoles"] is None
                           else [fact(doc, g, mid + ".role") for g in s["therapistRoles"]])
    m["goals"] = (None if s["goals"] is None
                  else [fact(doc, g, mid + ".goal") for g in s["goals"]])
    m["concepts"] = [termfact(doc, t, ids, mid + ".concept") for t, ids in s["concepts"]]
    m["interventions"] = [termfact(doc, t, ids, mid + ".interv") for t, ids in s["interventions"]]

    if s["phases"] is None:
        m["phases"] = None
    else:
        m["phases"] = {ph: [fact(doc, g, mid + ".phase." + ph) for g in gs]
                       for ph, gs in s["phases"].items()}
    m["examTips"] = [fact(doc, g, mid + ".tip") for g in s["examTips"]]
    models.append(m)

if ERRORS:
    print("FAILED -- bad block references:")
    for e in ERRORS:
        print("  ", e)
    sys.exit(1)


def count(m):
    n = 0
    n += 1 if m["changeMechanism"] else 0
    n += len(m["therapistRoles"] or [])
    n += len(m["goals"] or [])
    n += len(m["concepts"]) + len(m["interventions"]) + len(m["examTips"])
    if m["phases"]:
        n += sum(len(v) for v in m["phases"].values())
    return n


total = sum(count(m) for m in models)
out = {"generatedFrom": "five .docx packets in /source, via scripts/extract.py",
       "note": "Every sourceLine is verbatim from the packet, resolved by block index. "
               "null means the source has no such section.",
       "factCount": total, "models": models}

with io.open(os.path.join(ROOT, "theories.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("%-18s %5s %5s %5s %5s %5s %5s %5s" %
      ("model", "chg", "role", "goal", "conc", "intv", "phase", "tip"))
for m in models:
    ph = "null" if m["phases"] is None else sum(len(v) for v in m["phases"].values())
    print("%-18s %5s %5s %5s %5d %5d %5s %5d" % (
        m["id"], "1" if m["changeMechanism"] else "null",
        "null" if m["therapistRoles"] is None else len(m["therapistRoles"]),
        "null" if m["goals"] is None else len(m["goals"]),
        len(m["concepts"]), len(m["interventions"]), ph, len(m["examTips"])))
print("\nTOTAL DISCRETE FACTS:", total)
