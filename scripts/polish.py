# -*- coding: utf-8 -*-
"""Post-verification cleanup, driven by what the blind graders reported.

Applied in place on items_verified.json so option ORDER is preserved and the
blind gradings already collected stay valid. Three defects, all found by
graders reading the batches:

  a) A corrupted source line. The Humanistic packet has a garbled bullet
     "non acceptance" between "models authenticity" and "nondirective". As a
     quoted marker it asserts the opposite of Rogerian practice. Kill it.
  b) Format tell. Phase items kept the packet's "Beginning:/Middle:/End:"
     label on the keyed option only, so the answer was visible without any
     content knowledge. Strip the labels.
  c) Prefix gap in the collision index. A concept term that is a PREFIX of an
     equivalence-class variant ("Focus on moment to moment" vs the variant
     "Focus on moment to moment during therapy") never matched, so it was
     scored unique and became a keyed answer for a marker Gestalt also claims.
     Re-check with prefix matching and kill what is actually shared.
"""
import io
import json
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load(n):
    with io.open(os.path.join(ROOT, n), encoding="utf-8") as f:
        return json.load(f)


def norm(s):
    s = s.lower().replace("“", "").replace("”", "").replace("’", "'")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s).split())


C = load("collisions.json")
V = load("items_verified.json")
KL = load("kill_log.json")

# (c) prefix-aware claimant lookup
CLASS_VARIANTS = []          # (normalized variant, canonical, claimants)
for cls in C["equivalenceClasses"]:
    for v in cls["variants"]:
        CLASS_VARIANTS.append((norm(v), cls["canonical"], set(cls["claimedBy"])))
    CLASS_VARIANTS.append((norm(cls["canonical"]), cls["canonical"], set(cls["claimedBy"])))

LITERAL = {}
for mk in C["markers"]:
    LITERAL.setdefault(mk["normalized"], set(mk["claimedBy"]))


def claimants(term):
    t = norm(term)
    if not t:
        return set()
    out = set(LITERAL.get(t, set()))
    for vnorm, canon, who in CLASS_VARIANTS:
        if t == vnorm or vnorm.startswith(t + " ") or t.startswith(vnorm + " "):
            out |= who
    return out


PHASE_LABEL = re.compile(r"^\s*(beginning|early/middle|early|middle|end)\s*:\s*",
                         re.I)

kept, kills = [], []
stripped = 0

for it in V["items"]:
    # (a) corrupted source line
    if "non acceptance" in it["stem"].lower() or any(
            norm(o["text"]) == "non acceptance" for o in it["options"]):
        kills.append({"item": it, "gate": "gate5_source_integrity",
                      "reason": "quotes the corrupted packet bullet 'non acceptance', "
                                "which as written asserts the opposite of the model"})
        continue

    # (b) format tell: strip phase labels wherever they appear
    for o in it["options"]:
        new = PHASE_LABEL.sub("", o["text"])
        if new != o["text"]:
            o["text"] = new
            stripped += 1

    # (c) keyed answer actually shared once prefixes are matched
    cor = next(o for o in it["options"] if o["correct"])
    smid = cor["belongsTo"]
    if it["type"] in ("T1_marker", "T2_collision") and not it.get("intraModel"):
        cb = claimants(cor["text"])
        if len(cb) > 1 and smid in cb:
            kills.append({"item": it, "gate": "gate2_uniqueness",
                          "reason": "keyed answer %r is claimed by %s once "
                                    "equivalence-class prefixes are matched"
                                    % (cor["text"][:50], sorted(cb))})
            continue

    # a distractor that is really the same marker as the keyed answer
    dup = False
    for o in it["options"]:
        if o["correct"]:
            continue
        a, b = norm(o["text"]), norm(cor["text"])
        if a and b and (a.startswith(b + " ") or b.startswith(a + " ")):
            kills.append({"item": it, "gate": "gate4_distractor",
                          "reason": "distractor %r restates the keyed answer %r"
                                    % (o["text"][:40], cor["text"][:40])})
            dup = True
            break
    if dup:
        continue

    kept.append(it)

allkills = KL["kills"] + kills
bygate = dict(KL["byGate"])
for k in kills:
    bygate[k["gate"]] = bygate.get(k["gate"], 0) + 1
rate = 100.0 * len(allkills) / KL["generated"]

with io.open(os.path.join(ROOT, "kill_log.json"), "w", encoding="utf-8") as f:
    json.dump({"stage": KL["stage"] + " + polish", "generated": KL["generated"],
               "killed": len(allkills), "survived": len(kept),
               "killRatePct": round(rate, 1), "byGate": bygate,
               "kills": allkills}, f, ensure_ascii=False, indent=1)
with io.open(os.path.join(ROOT, "items_verified.json"), "w", encoding="utf-8") as f:
    json.dump({"stage": V["stage"] + " + polish", "count": len(kept),
               "items": kept}, f, ensure_ascii=False, indent=1)

print("polish killed %d, stripped %d phase labels, %d remain"
      % (len(kills), stripped, len(kept)))
by = {}
for k in kills:
    by[k["gate"]] = by.get(k["gate"], 0) + 1
for g in sorted(by):
    print("  %-24s %3d" % (g, by[g]))
print("cumulative kill rate %.1f%% (%d of %d)" % (rate, len(allkills), KL["generated"]))
