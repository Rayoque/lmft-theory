# -*- coding: utf-8 -*-
"""Gate 1, second pass: opaque-id batches over the shipped bank.

The first pass exposed real item ids, which encode the model
("t1_bowen_role_supervisor") and so leaked the answer. These batches use
q001-style ids instead, so a grader has nothing but the stem and options.

Kills are applied to items.json (the shipped 200) and the app is rebuilt.
"""
import io, json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
def load(n):
    with io.open(os.path.join(ROOT, n), encoding="utf-8") as f: return json.load(f)

KEY = load("blind/_key_opaque.json")     # opaque id -> [real id, correct letter]
I, KL = load("items.json"), load("kill_log.json")

picks, ambig, files = {}, set(), 0
for fn in sorted(os.listdir(os.path.join(ROOT, "blind"))):
    if fn in ("answers_10.json", "answers_11.json"):
        d = load("blind/" + fn)
        picks.update(d.get("answers", {})); ambig |= set(d.get("ambiguous", []))
        files += 1
if not files:
    print("no answers_10/11 yet"); raise SystemExit(1)

verdict = {}
for oid, pick in picks.items():
    if oid not in KEY: continue
    real, correct = KEY[oid]
    if pick != correct:
        verdict[real] = ("disagreed", "grader chose %s, key is %s" % (pick, correct))
    elif oid in ambig:
        verdict[real] = ("ambiguous", "grader picked correctly but flagged 2+ defensible options")

kept, kills = [], []
for it in I["items"]:
    v = verdict.get(it["id"])
    if v:
        kills.append({"item": it, "gate": "gate1_blind_reanswer_opaque",
                      "reason": v[1], "subtype": v[0]})
    else:
        kept.append(it)

dis = sum(1 for k in kills if k["subtype"] == "disagreed")
amb = sum(1 for k in kills if k["subtype"] == "ambiguous")
print("graded %d opaque items in %d batches" % (len(picks), files))
print("  DISAGREEMENTS with the key : %d  <- these would be mis-keyed items" % dis)
print("  flagged ambiguous          : %d" % amb)
print("  shipped bank %d -> %d" % (len(I["items"]), len(kept)))

allk = KL["kills"] + kills
bg = dict(KL["byGate"])
for k in kills: bg[k["gate"]] = bg.get(k["gate"], 0) + 1
with io.open(os.path.join(ROOT, "kill_log.json"), "w", encoding="utf-8") as f:
    json.dump({"stage": KL["stage"] + " + opaque gate 1", "generated": KL["generated"],
               "killed": len(allk), "survived": len(kept),
               "killRatePct": round(100.0*len(allk)/KL["generated"], 1),
               "byGate": bg, "kills": allk}, f, ensure_ascii=False, indent=1)

c = I["counts"]; c["total"] = len(kept)
c["byTier"] = {}; c["byType"] = {}
for it in kept:
    c["byTier"][str(it["tier"])] = c["byTier"].get(str(it["tier"]), 0) + 1
    c["byType"][it["type"]] = c["byType"].get(it["type"], 0) + 1
with io.open(os.path.join(ROOT, "items.json"), "w", encoding="utf-8") as f:
    json.dump({"note": I["note"], "counts": c, "items": kept}, f, ensure_ascii=False, indent=1)
print("  cumulative kill rate %.1f%%" % (100.0*len(allk)/KL["generated"]))
