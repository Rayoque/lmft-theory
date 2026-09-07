# -*- coding: utf-8 -*-
"""Grouped-list items, from Lauren's own description of the exam.

Her read: the exam asks "which of these are CBT interventions?" far more often
than it asks for a definition. She wants four answer choices where each choice
is a list belonging to ONE model -- no mixing within a list -- and she picks the
list that matches the named theory. Plus the inverse.

Two rules that matter and are easy to get wrong:

  * Every list in an item is the SAME LENGTH. CBT has 23 interventions and
    Object Relations has 5; showing them at natural length would let her score
    by counting rather than knowing.
  * A list never mixes models. That was her explicit ask, and it is also what
    keeps the item honest -- a mixed list has no single owner and no clean key.
"""
import io, json, os, random

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
random.seed(915)
L = 4                      # terms per list; every option gets exactly L

NEIGHBORS = {
    "bowen": ["structural", "strategic", "satir"],
    "structural": ["strategic", "bowen", "satir"],
    "strategic": ["structural", "bowen", "solution-focused"],
    "satir": ["bowen", "structural", "experiential"],
    "narrative": ["solution-focused", "strategic", "bowen"],
    "solution-focused": ["narrative", "strategic", "cbt"],
    "object-relations": ["self-psychology", "attachment", "bowen"],
    "self-psychology": ["object-relations", "attachment", "gestalt"],
    "attachment": ["object-relations", "self-psychology", "satir"],
    "gestalt": ["experiential", "self-psychology", "satir"],
    "experiential": ["gestalt", "satir", "structural"],
    "existential": ["gestalt", "experiential", "self-psychology"],
    "cbt": ["solution-focused", "strategic", "narrative"],
}


def load(n):
    with io.open(os.path.join(ROOT, n), encoding="utf-8") as f:
        return json.load(f)


T = load("theories.json")
M = {m["id"]: m for m in T["models"]}
# "CBT (interventions)" reads badly inside a stem ("CBT (interventions)
# interventions?"), so use a clean display name in prose.
NAME = {m["id"]: m["name"].replace(" (interventions)", "") for m in T["models"]}


def listable(mid):
    """What this model can offer as a list, and what to call it."""
    m = M[mid]
    if len(m["interventions"]) >= L:
        return m["interventions"], "interventions"
    if len(m["concepts"]) >= L:
        return m["concepts"], "key concepts"
    return None, None


ELIGIBLE = [mid for mid in M if listable(mid)[0]]
SKIPPED = [mid for mid in M if mid not in ELIGIBLE]

items = []


def sample(mid, seed):
    pool, kind = listable(mid)
    r = random.Random(seed)
    picks = r.sample(pool, L)
    return picks, kind


def opt(mid, picks, kind, correct):
    return {"text": " · ".join(p["term"] for p in picks),
            "correct": correct, "belongsTo": mid,
            "sourceLine": " | ".join("%s: %s" % (p["term"], p["definition"])
                                     for p in picks)}


for mid in ELIGIBLE:
    others = [o for o in NEIGHBORS.get(mid, []) if o in ELIGIBLE][:3]
    others += [o for o in ELIGIBLE if o != mid and o not in others]
    others = others[:3]
    if len(others) < 3:
        continue

    for variant in (0, 1):
        picks, kind = sample(mid, hash((mid, variant)) & 0xFFFF)
        # every distractor list is drawn at the SAME length from one other model
        dis = []
        ok = True
        for o in others:
            dpick, dkind = sample(o, hash((o, mid, variant)) & 0xFFFF)
            if not dpick:
                ok = False
                break
            dis.append((o, dpick, dkind))
        if not ok:
            continue

        # ---- forward: theory named, pick its list ----
        opts = [opt(mid, picks, kind, True)] + \
               [opt(o, dp, dk, False) for o, dp, dk in dis]
        random.shuffle(opts)
        items.append({
            "id": "g_%s_fwd_%d" % (mid, variant), "tier": 2, "type": "T2_group",
            "models": [mid], "listKind": kind,
            "stem": "Which of these are %s %s?" % (NAME[mid], kind),
            "options": opts,
            "rationale": "All four lists are real, and each belongs entirely to one "
                         "model. Only one is %s." % NAME[mid],
            "sourceLine": opts[[i for i, o in enumerate(opts) if o["correct"]][0]]["sourceLine"],
        })

        # ---- inverse: list shown, pick the theory ----
        names = [{"text": NAME[mid], "correct": True, "belongsTo": mid,
                  "sourceLine": opt(mid, picks, kind, True)["sourceLine"]}] + \
                [{"text": NAME[o], "correct": False, "belongsTo": o,
                  "sourceLine": opt(o, dp, dk, False)["sourceLine"]}
                 for o, dp, dk in dis]
        random.shuffle(names)
        items.append({
            "id": "g_%s_inv_%d" % (mid, variant), "tier": 2, "type": "T2_group",
            "models": [mid], "listKind": kind,
            "stem": "These are all %s of which model?\n\n%s"
                    % (kind, " · ".join(p["term"] for p in picks)),
            "options": names,
            "rationale": "Every term in the list belongs to %s." % NAME[mid],
            "sourceLine": opt(mid, picks, kind, True)["sourceLine"],
        })

# ---- checks that would otherwise fail silently ----
bad = []
for it in items:
    if len({len(o["text"].split(" · ")) for o in it["options"]}) > 1 and it["id"].endswith(tuple("01")) and "_fwd_" in it["id"]:
        bad.append((it["id"], "unequal list lengths"))
    if len([o for o in it["options"] if o["correct"]]) != 1:
        bad.append((it["id"], "not exactly one key"))
    if len({o["belongsTo"] for o in it["options"]}) != len(it["options"]):
        bad.append((it["id"], "two options from the same model"))

with io.open(os.path.join(ROOT, "items_group.json"), "w", encoding="utf-8") as f:
    json.dump({"count": len(items), "items": items}, f, ensure_ascii=False, indent=1)

print("generated %d grouped-list items across %d models" % (len(items), len(ELIGIBLE)))
print("  eligible:", " ".join(sorted(ELIGIBLE)))
print("  SKIPPED (packet has fewer than %d listable terms): %s" % (L, SKIPPED or "none"))
for mid in SKIPPED:
    print("     %s: %d interventions, %d concepts"
          % (mid, len(M[mid]["interventions"]), len(M[mid]["concepts"])))
print("  structural problems:", bad or "none")
