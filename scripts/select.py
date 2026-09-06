# -*- coding: utf-8 -*-
"""Select the shipping bank: roughly 60 Tier 1, 90 Tier 2, remainder Tier 3.

Selection is not killing -- these items passed verification. The brief caps the
bank on purpose: the corpus is ~366 facts, she has 8 days, and a tool that
serves 356 items pretends otherwise.

Ranking, in order:
  1. items a blind grader actually saw and agreed with (verified strongest)
  2. every model represented before any model gets a second item of a type
  3. exam-tip and vignette items first -- the instructor's own flagged content
"""
import io
import json
import os
import random

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
random.seed(20260915)

TARGET = {1: 60, 2: 90, 3: 50}


def load(n):
    with io.open(os.path.join(ROOT, n), encoding="utf-8") as f:
        return json.load(f)


V = load("items_verified.json")
T = load("theories.json")
MODEL_IDS = [m["id"] for m in T["models"]]

graded = set()
bl = os.path.join(ROOT, "blind")
if os.path.isdir(bl):
    for fn in os.listdir(bl):
        if fn.startswith("answers_") and fn.endswith(".json"):
            with io.open(os.path.join(bl, fn), encoding="utf-8") as f:
                graded |= set(json.load(f).get("answers", {}))

TYPE_PRIORITY = {"T2_examtip": 0, "V_vignette": 1, "T2_collision": 2,
                 "T1_phase": 3, "T1_change": 4, "T1_marker": 5, "T3_concept": 6}


def rank(it):
    return (0 if it["id"] in graded else 1, TYPE_PRIORITY.get(it["type"], 9))


picked, per_model_type = [], {}
for tier in (1, 2, 3):
    pool = [i for i in V["items"] if i["tier"] == tier]
    random.shuffle(pool)
    pool.sort(key=rank)
    # round-robin over models so no model is crowded out
    chosen, rounds = [], 0
    while len(chosen) < TARGET[tier] and rounds < 40:
        for mid in MODEL_IDS:
            if len(chosen) >= TARGET[tier]:
                break
            for it in pool:
                if it in chosen or it["models"][0] != mid:
                    continue
                k = (mid, it["type"])
                if per_model_type.get(k, 0) > rounds:
                    continue
                chosen.append(it)
                per_model_type[k] = per_model_type.get(k, 0) + 1
                break
        rounds += 1
    picked.extend(chosen)

by_type, by_tier, by_model = {}, {}, {}
for it in picked:
    by_type[it["type"]] = by_type.get(it["type"], 0) + 1
    by_tier[it["tier"]] = by_tier.get(it["tier"], 0) + 1
    by_model[it["models"][0]] = by_model.get(it["models"][0], 0) + 1

gradedn = sum(1 for i in picked if i["id"] in graded)
out = {"note": "Verified item bank. Every option carries belongsTo and a "
               "verbatim sourceLine from the five packets.",
       "counts": {"total": len(picked), "byTier": by_tier, "byType": by_type,
                  "byModel": by_model,
                  "blindGraded": gradedn,
                  "blindGradedPct": round(100.0 * gradedn / len(picked), 1)},
       "items": picked}
with io.open(os.path.join(ROOT, "items.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print("SHIPPING BANK: %d items" % len(picked))
print("  tiers:", dict(sorted(by_tier.items())))
for k in sorted(by_type):
    print("    %-14s %3d" % (k, by_type[k]))
print("  blind-graded: %d (%.0f%%)" % (gradedn, 100.0 * gradedn / len(picked)))
missing = [m for m in MODEL_IDS if m not in by_model]
print("  models with 0 items:", missing or "none")
print("  per model:", " ".join("%s=%d" % (k, v) for k, v in sorted(by_model.items())))
