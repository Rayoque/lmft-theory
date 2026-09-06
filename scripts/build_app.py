# -*- coding: utf-8 -*-
"""Inline the data into index.html.

Inlining rather than fetching makes the brief's two hard constraints trivially
true at once: it really is a single file, and it really does work offline
after first load, with no service worker and no fetch that file:// would block.
"""
import datetime
import io
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
HERE = os.path.dirname(os.path.abspath(__file__))


def load(n):
    with io.open(os.path.join(ROOT, n), encoding="utf-8") as f:
        return json.load(f)


T = load("theories.json")
I = load("items.json")

# Ship only what the app reads. Keeps the single file small enough for a phone.
slim_models = []
for m in T["models"]:
    slim_models.append({
        "id": m["id"], "name": m["name"], "family": m["family"],
        "sourceDoc": m["sourceDoc"],
        "changeMechanism": ({"text": m["changeMechanism"]["text"],
                             "sourceLine": m["changeMechanism"]["sourceLine"]}
                            if m["changeMechanism"] else None),
        "therapistRoles": (None if m["therapistRoles"] is None
                           else [{"text": f["text"]} for f in m["therapistRoles"]]),
        "goals": (None if m["goals"] is None
                  else [{"text": f["text"]} for f in m["goals"]]),
        "concepts": [{"term": c["term"], "definition": c["definition"]}
                     for c in m["concepts"]],
        "interventions": [{"term": c["term"], "definition": c["definition"]}
                          for c in m["interventions"]],
        "phases": (None if m["phases"] is None
                   else {k: [{"text": f["text"]} for f in v]
                         for k, v in m["phases"].items()}),
        "examTips": [{"sourceLine": t["sourceLine"]} for t in m["examTips"]],
    })

slim_items = [{
    "id": it["id"], "tier": it["tier"], "type": it["type"],
    "models": it["models"], "stem": it["stem"],
    "options": [{"text": o["text"], "correct": o["correct"],
                 "belongsTo": o["belongsTo"]} for o in it["options"]],
    "rationale": it["rationale"], "sourceLine": it["sourceLine"],
} for it in I["items"]]

with io.open(os.path.join(HERE, "app_template.html"), encoding="utf-8") as f:
    html = f.read()

html = (html
        .replace("__THEORIES__", json.dumps({"models": slim_models},
                                            ensure_ascii=False, separators=(",", ":")))
        .replace("__ITEMS__", json.dumps(slim_items, ensure_ascii=False,
                                         separators=(",", ":")))
        .replace("__BUILT__", datetime.date.today().isoformat()))

out = os.path.join(ROOT, "index.html")
with io.open(out, "w", encoding="utf-8") as f:
    f.write(html)

kb = os.path.getsize(out) / 1024.0
print("index.html written: %.0f KB, %d items, %d models"
      % (kb, len(slim_items), len(slim_models)))
assert "__THEORIES__" not in html and "__ITEMS__" not in html, "placeholder left"
