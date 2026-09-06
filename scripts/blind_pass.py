# -*- coding: utf-8 -*-
"""Gate 1: blind re-answer (BUILD_BRIEF S7).

export : write batches containing ONLY stem + shuffled option letters.
         No answer key, no rationale, no belongsTo, no sourceLine, no item id
         semantics. A grader seeing a batch cannot infer the key.
ingest : read graders' answers, kill every item where the pick disagrees.

Run as its own pass, outside the generation context.
"""
import io
import json
import os
import string
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
BLIND = os.path.join(ROOT, "blind")
BATCH = 45


def load(n):
    with io.open(os.path.join(ROOT, n), encoding="utf-8") as f:
        return json.load(f)


def export():
    V = load("items_verified.json")
    items = V["items"]
    os.makedirs(BLIND, exist_ok=True)
    key = {}
    batches = [items[i:i + BATCH] for i in range(0, len(items), BATCH)]
    for bi, batch in enumerate(batches, 1):
        out = []
        for it in batch:
            letters = list(string.ascii_uppercase[:len(it["options"])])
            opts = {L: o["text"] for L, o in zip(letters, it["options"])}
            for L, o in zip(letters, it["options"]):
                if o["correct"]:
                    key[it["id"]] = L
            out.append({"id": it["id"], "stem": it["stem"], "options": opts})
        p = os.path.join(BLIND, "batch_%02d.json" % bi)
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump({"instructions":
                       "For each question pick the single best option. "
                       "Answer only from the options given. Output strict JSON: "
                       "{\"answers\":{\"<id>\":\"<LETTER>\"}, "
                       "\"ambiguous\":[\"<id>\", ...]}. "
                       "List an id under ambiguous if two or more options are "
                       "defensible.",
                       "questions": out}, f, ensure_ascii=False, indent=1)
    with io.open(os.path.join(BLIND, "_key.json"), "w", encoding="utf-8") as f:
        json.dump(key, f, indent=1)
    print("exported %d items in %d batches to blind/" % (len(items), len(batches)))


def ingest():
    V = load("items_verified.json")
    items = {it["id"]: it for it in V["items"]}
    with io.open(os.path.join(BLIND, "_key.json"), encoding="utf-8") as f:
        key = json.load(f)

    picks, ambiguous = {}, set()
    n = 0
    for fn in sorted(os.listdir(BLIND)):
        if not (fn.startswith("answers_") and fn.endswith(".json")):
            continue
        with io.open(os.path.join(BLIND, fn), encoding="utf-8") as f:
            d = json.load(f)
        picks.update(d.get("answers", {}))
        ambiguous |= set(d.get("ambiguous", []))
        n += 1

    if not n:
        print("no answers_*.json in blind/ -- run the graders first")
        sys.exit(1)

    kept, kills = [], []
    ungraded = 0
    for iid, it in items.items():
        if iid not in picks:
            ungraded += 1
            kept.append(it)          # not graded: cannot judge, keep
            continue
        if picks[iid] != key[iid]:
            kills.append({"item": it, "gate": "gate1_blind_reanswer",
                          "reason": "blind grader chose %s, key is %s"
                                    % (picks[iid], key[iid])})
        elif iid in ambiguous:
            kills.append({"item": it, "gate": "gate1_blind_reanswer",
                          "reason": "blind grader picked correctly but flagged "
                                    "two or more options as defensible"})
        else:
            kept.append(it)

    prior = load("kill_log.json")
    allkills = prior["kills"] + kills
    total = prior["generated"]
    bygate = dict(prior["byGate"])
    for k in kills:
        bygate[k["gate"]] = bygate.get(k["gate"], 0) + 1
    rate = 100.0 * len(allkills) / total

    with io.open(os.path.join(ROOT, "kill_log.json"), "w", encoding="utf-8") as f:
        json.dump({"stage": "all four gates",
                   "generated": total, "killed": len(allkills),
                   "survived": len(kept), "killRatePct": round(rate, 1),
                   "byGate": bygate, "kills": allkills},
                  f, ensure_ascii=False, indent=1)
    with io.open(os.path.join(ROOT, "items_verified.json"), "w", encoding="utf-8") as f:
        json.dump({"stage": "passed all four gates", "count": len(kept),
                   "items": kept}, f, ensure_ascii=False, indent=1)

    print("graded %d items in %d batches; ungraded %d" % (len(picks), n, ungraded))
    print("gate 1 killed %d" % len(kills))
    print("CUMULATIVE: generated %d  killed %d  survived %d  kill rate %.1f%%"
          % (total, len(allkills), len(kept), rate))
    for g in sorted(bygate):
        print("  %-24s %3d" % (g, bygate[g]))


if __name__ == "__main__":
    (export if sys.argv[1:] and sys.argv[1] == "export" else ingest)()
