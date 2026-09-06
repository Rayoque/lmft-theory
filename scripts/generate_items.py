# -*- coding: utf-8 -*-
"""Generate items.json from theories.json + collisions.json.

Anti-hallucination lock (BUILD_BRIEF S6 rule 1): options are only ever
assembled from fact objects already in theories.json, each carrying its own
belongsTo and verbatim sourceLine. There is no code path that writes option
text from anything but a fact object, so a distractor cannot be invented.

Rule 2: distractors come from NEIGHBORS, never at random.
Rule 3: a shared marker is never the keyed answer of an inverse item.
"""
import io
import json
import os
import random
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

random.seed(20260915)  # exam date; keeps regeneration reproducible

# Nearest neighbours. Bowen pulls Structural/Strategic, Narrative pulls
# Solution-Focused, Object Relations pulls Self Psychology, Gestalt pulls
# Existential and Client Centered -- per BUILD_BRIEF S6 rule 2, extended to
# all 14 by shared family.
NEIGHBORS = {
 "bowen":            ["structural", "strategic", "satir"],
 "strategic":        ["structural", "bowen", "satir"],
 "structural":       ["strategic", "bowen", "satir"],
 "satir":            ["structural", "bowen", "strategic"],
 "narrative":        ["solution-focused", "satir", "client-centered"],
 "solution-focused": ["narrative", "cbt", "satir"],
 "object-relations": ["self-psychology", "attachment"],
 "self-psychology":  ["object-relations", "attachment"],
 "attachment":       ["self-psychology", "object-relations", "client-centered"],
 "client-centered":  ["gestalt", "existential", "experiential"],
 "gestalt":          ["existential", "client-centered", "experiential"],
 "existential":      ["gestalt", "client-centered", "experiential"],
 "experiential":     ["gestalt", "existential", "satir", "structural"],
 "cbt":              ["solution-focused", "strategic", "bowen"],
}

PHASE_LABEL = {"beginning": "beginning", "middle": "middle", "end": "end"}


def load(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


T = load("theories.json")
C = load("collisions.json")
M = {m["id"]: m for m in T["models"]}
NAME = {k: v["name"] for k, v in M.items()}

MARK = {}
for mk in C["markers"]:
    MARK.setdefault(mk["normalized"], mk)


def norm(s):
    s = s.lower().replace("“", "").replace("”", "").replace("’", "'")
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", s).split())


def is_unique(term):
    mk = MARK.get(norm(term))
    return bool(mk and mk["unique"])


def identity_line(mid):
    """A defining verbatim line for a model, used as the sourceLine when the
    option text is a model NAME (inverse items)."""
    m = M[mid]
    if m["changeMechanism"]:
        return m["changeMechanism"]["sourceLine"]
    return m["interventions"][0]["sourceLine"]


def opt(text, correct, belongs, sourceline):
    return {"text": text, "correct": correct, "belongsTo": belongs,
            "sourceLine": sourceline}


ITEMS = []
SEEN = set()


def add(iid, tier, itype, models, stem, options, rationale, sourceline,
        marker=None, intra=False):
    if iid in SEEN:
        return
    # never emit an item whose options collapse to duplicates
    texts = [o["text"].strip().lower() for o in options]
    if len(set(texts)) != len(texts):
        return
    if sum(1 for o in options if o["correct"]) != 1:
        return
    random.shuffle(options)
    SEEN.add(iid)
    it = {"id": iid, "tier": tier, "type": itype, "models": models,
          "stem": stem, "options": options, "rationale": rationale,
          "sourceLine": sourceline}
    if marker:
        it["marker"] = marker
    if intra:
        # Deliberate intra-model discrimination (the psychodynamic four-way,
        # CBT's own disambiguations). Distractors ARE same-model by design;
        # the stem carries a specific definition so exactly one term fits.
        # Verifier gate 4 honours this flag. See BUILD_BRIEF S5 closing note.
        it["intraModel"] = True
    ITEMS.append(it)


def pick(pool, n, exclude_texts):
    out = []
    for f in pool:
        t = f.get("text") or f.get("definition") or ""
        if not t.strip() or t.strip().lower() in exclude_texts:
            continue
        if t.strip().lower() in {o.strip().lower() for o in out}:
            continue
        out.append(t)
        if len(out) >= n:
            break
    return out


def neighbour_facts(mid, getter, n=3):
    """Collect (text, belongsTo, sourceLine) from nearest neighbours only."""
    out = []
    for nb in NEIGHBORS[mid]:
        for f in getter(M[nb]) or []:
            t = (f.get("text") or "").strip()
            if t:
                out.append((t, nb, f["sourceLine"]))
    random.shuffle(out)
    return out


# ---------------------------------------------------------------- T1_change
for mid, m in M.items():
    cm = m["changeMechanism"]
    if not cm:
        continue  # CBT: source has no theory of change. Do not synthesize.
    # forward: name the model, pick its change mechanism
    ds = neighbour_facts(mid, lambda x: [x["changeMechanism"]] if x["changeMechanism"] else [])
    opts = [opt(cm["text"], True, mid, cm["sourceLine"])]
    used = {cm["text"].strip().lower()}
    for t, nb, sl in ds:
        if t.strip().lower() in used:
            continue
        opts.append(opt(t, False, nb, sl))
        used.add(t.strip().lower())
        if len(opts) == 4:
            break
    if len(opts) == 4:
        add("t1_%s_change_fwd" % mid, 1, "T1_change", [mid],
            "According to %s, how does change occur?" % m["name"],
            opts,
            "%s locates change in this mechanism. The other options are the change "
            "mechanisms of nearby models." % m["name"],
            cm["sourceLine"])

    # inverse: give the mechanism, name the model
    nbs = [n for n in NEIGHBORS[mid] if M[n]["changeMechanism"]][:3]
    if len(nbs) >= 3:
        opts = [opt(m["name"], True, mid, cm["sourceLine"])]
        for nb in nbs:
            opts.append(opt(M[nb]["name"], False, nb, identity_line(nb)))
        add("t1_%s_change_inv" % mid, 1, "T1_change", [mid],
            "Which model holds that change occurs in this way?\n\n“%s”" % cm["text"],
            opts,
            "This is %s's stated theory of change." % m["name"],
            cm["sourceLine"])

# ---------------------------------------------------------------- T1_marker
for mid, m in M.items():
    pool = [c for c in (m["interventions"] + m["concepts"]) if is_unique(c["term"])]
    random.shuffle(pool)
    nbs = NEIGHBORS[mid][:3]
    if len(nbs) < 3:
        nbs = (NEIGHBORS[mid] + [x for x in M if x != mid and x not in NEIGHBORS[mid]])[:3]
    for c in pool[:3]:
        opts = [opt(m["name"], True, mid, c["sourceLine"])]
        for nb in nbs:
            opts.append(opt(M[nb]["name"], False, nb, identity_line(nb)))
        add("t1_%s_marker_%s" % (mid, re.sub(r"[^a-z0-9]+", "", norm(c["term"]))[:18]),
            1, "T1_marker", [mid],
            "“%s” is a signature term of which model?" % c["term"],
            opts,
            "%s belongs to %s and is not claimed by any other model in the packet."
            % (c["term"], m["name"]),
            c["sourceLine"], marker=c["term"])

# ------------------------------------------------------- T1_marker (roles)
# The learner named this shape explicitly: "it gives you what theory has a
# supervisor role, and I would have to say Bowen." Roles are the most
# collision-ridden field in the corpus, so only roles that survive
# collisions.json as unique are legal here -- which is the whole point.
for mid, m in M.items():
    roles = [r for r in (m["therapistRoles"] or [])
             if is_unique(r["text"]) and 3 < len(r["text"]) < 90]
    nbs = NEIGHBORS[mid][:3]
    if len(nbs) < 3:
        nbs = (NEIGHBORS[mid] + [x for x in M if x != mid and x not in NEIGHBORS[mid]])[:3]
    for r in roles[:2]:
        opts = [opt(m["name"], True, mid, r["sourceLine"])]
        for nb in nbs:
            opts.append(opt(M[nb]["name"], False, nb, identity_line(nb)))
        add("t1_%s_role_%s" % (mid, re.sub(r"[^a-z0-9]+", "", norm(r["text"]))[:18]),
            1, "T1_marker", [mid],
            "Which model describes the therapist's role this way?\n\n“%s”"
            % r["text"],
            opts,
            "“%s” is listed under %s's therapist role and is not claimed by "
            "another model in the packet." % (r["text"], m["name"]),
            r["sourceLine"], marker=r["text"])

# ---------------------------------------------------------------- T1_phase
for mid, m in M.items():
    if not m["phases"]:
        continue  # Client Centered / Gestalt / Existential: source states none
    for ph, facts in m["phases"].items():
        if not facts:
            continue
        # Learner named phases of treatment as the highest-value domain, so
        # take up to two distinct actions per phase rather than one.
        for fi, f in enumerate(facts[:2]):
            ds = []
            for nb in NEIGHBORS[mid]:
                nbm = M[nb]
                if not nbm["phases"]:
                    continue
                for g in nbm["phases"].get(ph, []):
                    ds.append((g["text"], nb, g["sourceLine"]))
            random.shuffle(ds)
            opts = [opt(f["text"], True, mid, f["sourceLine"])]
            used = {f["text"].strip().lower()}
            for t, nb, sl in ds:
                if t.strip().lower() in used:
                    continue
                opts.append(opt(t, False, nb, sl))
                used.add(t.strip().lower())
                if len(opts) == 4:
                    break
            if len(opts) == 4:
                add("t1_%s_phase_%s_%d" % (mid, ph, fi), 1, "T1_phase", [mid],
                    "In the %s phase of treatment, what would a %s therapist do?"
                    % (PHASE_LABEL[ph], m["name"]), opts,
                    "This is drawn from %s's %s phase. The distractors are the "
                    "same phase in neighbouring models."
                    % (m["name"], PHASE_LABEL[ph]),
                    f["sourceLine"])

# ------------------------------------------------------------ T2_collision
for cls in C["equivalenceClasses"]:
    claimants = cls["claimedBy"]
    if len(claimants) < 2:
        continue
    # The keyed answer must not BE the shared marker, or the stem contradicts
    # itself: "X shares 'enactment' with Y, so which IS distinctive of X?
    # -> Enactment". Flagged by a blind grader.
    banned = [norm(cls["canonical"])] + [norm(v) for v in cls["variants"]]

    def echoes_marker(term):
        """True if the term restates the shared marker. Exact match is not
        enough: "Models" vs marker "modeling" reads as self-contradictory too,
        and the variant "Models: Demonstrates new ways..." starts with it."""
        t = norm(term)
        for b in banned:
            if t == b or b.startswith(t + " ") or t.startswith(b + " "):
                return True
            if t.split(" ")[0][:5] == b.split(" ")[0][:5]:
                return True
        return False

    for mid in claimants:
        m = M[mid]
        uniq = [c for c in (m["interventions"] + m["concepts"])
                if is_unique(c["term"]) and not echoes_marker(c["term"])]
        if not uniq:
            continue
        random.shuffle(uniq)
        target = uniq[0]
        others = [x for x in claimants if x != mid]
        ds = []
        for o in others:
            for c in (M[o]["interventions"] + M[o]["concepts"]):
                if is_unique(c["term"]):
                    ds.append((c["term"], o, c["sourceLine"]))
        random.shuffle(ds)
        opts = [opt(target["term"], True, mid, target["sourceLine"])]
        used = {target["term"].strip().lower()}
        for t, nb, sl in ds:
            if t.strip().lower() in used:
                continue
            opts.append(opt(t, False, nb, sl))
            used.add(t.strip().lower())
            if len(opts) == 4:
                break
        if len(opts) == 4:
            shared_with = ", ".join(NAME[x] for x in others)
            add("t2_coll_%s_%s" % (mid, re.sub(r"[^a-z0-9]+", "", norm(cls["canonical"]))[:16]),
                2, "T2_collision", [mid] + others,
                "%s share the marker “%s” with %s, so that marker cannot "
                "tell them apart. Which of these IS distinctive of %s?"
                % (m["name"], cls["canonical"], shared_with, m["name"]),
                opts,
                "“%s” is claimed by %s, so it discriminates nothing. "
                "%s is unique to %s."
                % (cls["canonical"], ", ".join(NAME[x] for x in claimants),
                   target["term"], m["name"]),
                target["sourceLine"], marker=cls["canonical"])

# ------------------------------------------------------- T2 confusion sets
for cs in C["confusionSets"]:
    mid = cs["scope"][0]
    m = M[mid]
    byterm = {c["term"]: c for c in (m["interventions"] + m["concepts"])}
    terms = [t for t in cs["terms"] if t in byterm]
    if len(terms) < 3:
        continue
    for t in terms:
        c = byterm[t]
        opts = [opt(t, True, mid, c["sourceLine"])]
        for o in terms:
            if o == t:
                continue
            opts.append(opt(o, False, mid, byterm[o]["sourceLine"]))
            if len(opts) == 4:
                break
        if len(opts) == 4:
            add("t2_conf_%s_%s" % (mid, re.sub(r"[^a-z0-9]+", "", norm(t))[:18]),
                2, "T2_collision", [mid],
                "Within %s: which term matches this description?\n\n“%s”"
                % (m["name"], c["definition"]),
                opts,
                "The packet distinguishes these explicitly (%s)." % cs["name"],
                c["sourceLine"], marker=t, intra=True)

# ---------------------------------------------------------------- T3_concept
for mid, m in M.items():
    pool = list(m["concepts"]) + list(m["interventions"])
    random.shuffle(pool)
    same = {c["term"]: c for c in pool}
    for c in pool:
        if not c["definition"] or len(c["definition"]) < 40:
            continue
        # distractors: other terms from the SAME model first, then neighbours
        ds = [(o["term"], mid, o["sourceLine"]) for o in pool if o["term"] != c["term"]]
        for nb in NEIGHBORS[mid]:
            for o in (M[nb]["concepts"] + M[nb]["interventions"]):
                ds.append((o["term"], nb, o["sourceLine"]))
        random.shuffle(ds)
        opts = [opt(c["term"], True, mid, c["sourceLine"])]
        used = {c["term"].strip().lower()}
        for t, nb, sl in ds:
            if t.strip().lower() in used:
                continue
            opts.append(opt(t, False, nb, sl))
            used.add(t.strip().lower())
            if len(opts) == 4:
                break
        if len(opts) == 4:
            add("t3_%s_%s" % (mid, re.sub(r"[^a-z0-9]+", "", norm(c["term"]))[:20]),
                3, "T3_concept", [mid],
                "Which term does the packet define this way?\n\n“%s”"
                % c["definition"],
                opts,
                "Definition is verbatim from the %s section." % m["name"],
                c["sourceLine"], marker=c["term"], intra=True)


def main():
    # merge hand-authored vignettes + exam-tip items
    try:
        from handauthored import build as build_hand
        hand = build_hand(M, NAME, opt, identity_line)
        # build_hand constructs each item with the correct option FIRST.
        # Shuffle here or every hand-authored item is keyed to A -- caught by a
        # blind grader who noticed 14 consecutive A answers.
        for it in hand:
            random.shuffle(it["options"])
        ITEMS.extend(hand)
    except ImportError:
        pass

    by = {}
    for it in ITEMS:
        by[it["type"]] = by.get(it["type"], 0) + 1
    tiers = {}
    for it in ITEMS:
        tiers[it["tier"]] = tiers.get(it["tier"], 0) + 1

    out = {"note": "Every option carries belongsTo and a verbatim sourceLine. "
                   "Distractors are real content from neighbouring models.",
           "counts": {"total": len(ITEMS), "byType": by, "byTier": tiers},
           "items": ITEMS}
    with io.open(os.path.join(ROOT, "items_raw.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("GENERATED", len(ITEMS), "raw items")
    for k in sorted(by):
        print("  %-14s %3d" % (k, by[k]))
    print("  tiers:", dict(sorted(tiers.items())))


if __name__ == "__main__":
    main()
