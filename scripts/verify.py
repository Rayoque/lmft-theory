# -*- coding: utf-8 -*-
"""Deterministic verification gates 2-4 (BUILD_BRIEF S7).

Runs standalone against items_raw.json. Gate 1 (blind re-answer) is a
separate pass -- see scripts/blind_pass.py -- because self-grading inside the
generation context is theatre.

  Gate 2  Uniqueness      keyed marker claimed by >1 model with no disambiguator
  Gate 3  Traceability    an option sourceLine absent from theories.json
  Gate 4  Distractor validity
                          (a) distractor belongsTo == the stem's own model
                          (b) distractor's marker is ALSO claimed by the stem's
                              model, i.e. arguably correct for the named theory

Every rejection is written to kill_log.json with the failing gate.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load(n):
    with io.open(os.path.join(ROOT, n), encoding="utf-8") as f:
        return json.load(f)


T, C, RAW = load("theories.json"), load("collisions.json"), load("items_raw.json")
M = {m["id"]: m for m in T["models"]}
NAME = {k: v["name"] for k, v in M.items()}


def norm(s):
    s = s.lower().replace("“", "").replace("”", "").replace("’", "'")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s).split())


# every sourceLine legitimately present in theories.json
LEGIT = set()
for m in T["models"]:
    buckets = [m["concepts"], m["interventions"], m["examTips"],
               m["therapistRoles"] or [], m["goals"] or []]
    if m["changeMechanism"]:
        buckets.append([m["changeMechanism"]])
    if m["phases"]:
        buckets.extend(m["phases"].values())
    for b in buckets:
        for f in b:
            LEGIT.add(norm(f["sourceLine"]))

MARK = {}
for mk in C["markers"]:
    MARK.setdefault(mk["normalized"], mk)


def claimed_by(term):
    mk = MARK.get(norm(term))
    return set(mk["claimedBy"]) if mk else set()


def stem_model(it):
    """The model the stem names / keys on."""
    for o in it["options"]:
        if o["correct"]:
            return o["belongsTo"]
    return None


kills, kept = [], []

for it in RAW["items"]:
    intra = it.get("intraModel", False)
    smid = stem_model(it)
    fails = []

    # ---- Gate 2: uniqueness of the keyed marker
    mk = it.get("marker")
    if mk:
        cb = claimed_by(mk)
        if len(cb) > 1:
            named = smid and NAME[smid].lower() in it["stem"].lower()
            # a specific verbatim definition in the stem is also a disambiguator
            hasdef = "“" in it["stem"] and len(it["stem"]) > 120
            if it["type"] == "T1_marker":
                fails.append(("gate2_uniqueness",
                              "inverse item keyed to shared marker %r claimed by %s"
                              % (mk, sorted(cb))))
            elif not (named or hasdef or intra):
                fails.append(("gate2_uniqueness",
                              "shared marker %r (%s) with no disambiguator in stem"
                              % (mk, sorted(cb))))

    # ---- Gate 3: traceability
    for o in it["options"]:
        if not o.get("sourceLine") or norm(o["sourceLine"]) not in LEGIT:
            fails.append(("gate3_traceability",
                          "option %r has a sourceLine absent from theories.json"
                          % o["text"][:60]))
            break

    # ---- Gate 4: distractor validity
    # intraModel items (term<->definition, the psychodynamic four-way, CBT's own
    # disambiguations) use same-model distractors ON PURPOSE. There the
    # disambiguator is the verbatim definition in the stem, not the model name,
    # so 4a/4b do not apply -- but the definition must actually be there.
    if intra:
        # Structural check only: the stem must actually carry descriptive
        # content (a quoted definition, or a substantive scenario) rather than
        # a bare "which term?". Whether that content is SPECIFIC enough to pick
        # exactly one term is a semantic judgement no string check can make --
        # that is gate 1's job.
        quoted = re.search(r"“([^”]{60,})”", it["stem"])
        if not quoted and len(it["stem"]) < 100:
            fails.append(("gate4_distractor",
                          "intraModel item has same-model distractors but the "
                          "stem carries too little content to disambiguate them"))
    else:
        for o in it["options"]:
            if o["correct"]:
                continue
            if o["belongsTo"] == smid:
                fails.append(("gate4_distractor",
                              "distractor %r belongsTo the stem's own model (%s)"
                              % (o["text"][:50], smid)))
                break
            # arguably-correct: distractor's marker also claimed by stem model
            cb = claimed_by(o["text"])
            if smid and len(cb) > 1 and smid in cb:
                fails.append(("gate4_distractor",
                              "distractor %r is ALSO claimed by %s, so it is "
                              "arguably correct for the named theory"
                              % (o["text"][:50], smid)))
                break

    if fails:
        kills.append({"item": it, "gate": fails[0][0], "reason": fails[0][1],
                      "allFailures": [{"gate": g, "reason": r} for g, r in fails]})
    else:
        kept.append(it)

total = len(RAW["items"])
rate = 100.0 * len(kills) / total if total else 0

bygate = {}
for k in kills:
    bygate[k["gate"]] = bygate.get(k["gate"], 0) + 1

with io.open(os.path.join(ROOT, "kill_log.json"), "w", encoding="utf-8") as f:
    json.dump({"stage": "deterministic gates 2-4",
               "generated": total, "killed": len(kills), "survived": len(kept),
               "killRatePct": round(rate, 1), "byGate": bygate,
               "kills": kills}, f, ensure_ascii=False, indent=1)

with io.open(os.path.join(ROOT, "items_verified.json"), "w", encoding="utf-8") as f:
    json.dump({"stage": "passed deterministic gates 2-4",
               "count": len(kept), "items": kept}, f, ensure_ascii=False, indent=1)

print("generated %d  killed %d  survived %d  kill rate %.1f%%"
      % (total, len(kills), len(kept), rate))
for g in sorted(bygate):
    print("  %-22s %3d" % (g, bygate[g]))
print()
bytype = {}
for it in kept:
    bytype[it["type"]] = bytype.get(it["type"], 0) + 1
print("survivors by type:", dict(sorted(bytype.items())))
print("\n--- sample kills ---")
for k in kills[:8]:
    print("  [%s] %s" % (k["gate"], k["reason"][:110]))
