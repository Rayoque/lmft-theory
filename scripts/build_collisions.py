# -*- coding: utf-8 -*-
"""Build collisions.json. This GATES item generation (BUILD_BRIEF S5).

Two passes:
  1. Literal pass - index every concept/intervention term and role text from
     theories.json and find exact string overlaps across models.
  2. Semantic pass - EQUIV below. Authored by reading the packets, because
     three models express "authentic presence" in three different wordings and
     a naive matcher calls each one unique. Each variant cites the model whose
     source line carries that wording.

A marker is unique only if exactly one model claims it after BOTH passes.
Only unique markers are legal as the keyed answer of an inverse item.
"""
import io
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# --- Semantic equivalence classes -------------------------------------------
# canonical -> (type, {model: [variant wordings actually in that model's source]})
#
# PROPAGATE controls whether a class marks its member wordings as shared.
#   True  - the models use the SAME generic language, so any member wording is
#           ambiguous as a keyed answer. Default.
#   False - the models share only a FUNCTION; each has its own proper name
#           (genogram vs family map vs family life chronology vs trial of
#           labor). The function is worth a T2_collision item, but each named
#           term stays a legal unique answer. Without this, the four confirmed
#           unique markers in BUILD_BRIEF S5 get wrongly killed.
NO_PROPAGATE = {"family history mapping (function)"}

EQUIV = {
 "authentic presence": ("role", {
   "client-centered": ["is authentic", "models authenticity"],
   "gestalt": ["Authentic present other, showing up as a real person"],
   "existential": ["To be real and authentic other"],
   "experiential": ["Authentically being with client"],
   "satir": ["Therapist is genuine and warm"]}),

 "nondirective stance": ("role", {
   "client-centered": ["nondirective"],
   "gestalt": ["Nondirective"]}),

 "nonjudgmental stance": ("role", {
   "client-centered": ["non judgmental approach"],
   "gestalt": ["Nonjudgemental"],
   "existential": ["present nonjudgemental person"],
   "attachment": ["non-judgmental, and reliable environment"]}),

 "investigator / detective stance": ("role", {
   "bowen": ["Investigator"],
   "narrative": ["Investigator"],
   "satir": ["Resource detective"]}),

 "neutral stance": ("role", {
   "bowen": ["Neutral"],
   "object-relations": ["Neutral"]}),

 "coach / consultant / educator": ("role", {
   "bowen": ["Coach/educator", "Supervisor"],
   "solution-focused": ["Therapist is a consultant, coach"]}),

 "active / directive therapist": ("role", {
   "structural": ["Therapist is active and involved"],
   "satir": ["Active facilitator"],
   "strategic": ["Therapist delivers directives that facilitate change"]}),

 "reframing": ("intervention", {
   "bowen": ["Reframing issues as multigenerational issue"],
   "structural": ["Reframe"],
   "cbt": ["Reframing"],
   "experiential": ["Activating Constructive Anxiety: Reframing anxiety in the family"],
   "strategic": ["relabel behavior"]}),

 "experiments": ("intervention", {
   "gestalt": ["Experiments in Gestalt"],
   "cbt": ["Behavioral Experiments"]}),

 "I-statements": ("intervention", {
   "bowen": ["Teaching “I” Statements", "teaching I statements"],
   "cbt": ["I-statements"],
   "satir": ["Therapist uses “I” messages"]}),

 "homework / between-session task": ("intervention", {
   "strategic": ["Homework"],
   "cbt": ["Homework"],
   "solution-focused": ["Formula First Session Task (FFST) A homework task"],
   "bowen": ["Bibliotherapy: Assigning reading material"]}),

 "modeling": ("intervention", {
   "bowen": ["Models: Demonstrates new ways to interact and communicate"],
   "satir": ["Modeling Communication"],
   "client-centered": ["models authenticity"]}),

 "holding environment": ("intervention", {
   "object-relations": ["Establish a holding environment"],
   "self-psychology": ["Establish a therapeutic holding environment"],
   "existential": ["Concept of holding"]}),

 # "Experience-Near Empathy" deliberately NOT a variant: it is Self Psychology's
 # own proper name and BUILD_BRIEF S5 confirms it unique. Generic empathy
 # language is what collides.
 "empathy / attunement": ("role", {
   "client-centered": ["empathy is essential"],
   "self-psychology": ["empathetic attunement"],
   "attachment": ["Attunement is the key intervention"],
   "object-relations": ["exploration of client’s experience, empathy"]}),

 "transference work": ("intervention", {
   "object-relations": ["Emphasis on transference and countertransference"],
   "self-psychology": ["Allows emergence of self-object transferences"]}),

 "enactment": ("intervention", {
   "structural": ["Enactment: The actualization of transactional patterns"],
   "self-psychology": ["Addressing enactments"]}),

 "boundary work": ("intervention", {
   "structural": ["Boundary Making", "Help create flexible boundaries"],
   "experiential": ["Highlight inappropriate boundaries"]}),

 "coalitions / alignments": ("concept", {
   "structural": ["Coalitions"],
   "experiential": ["Gather information about boundaries, coalitions, roles"]}),

 "family history mapping (function)": ("intervention", {
   "bowen": ["Genogram"],
   "satir": ["Family Life Chronology"],
   "structural": ["Family Map"],
   "experiential": ["Trial of Labor"]}),

 # "Leveler" excluded: it is Satir's own named communication stance, not shared
 # language. Only the generic idea of congruence collides.
 "congruence": ("concept", {
   "client-centered": ["congruence between idealized self and actual self"],
   "satir": ["increase congruent communication"]}),

 "role-play": ("intervention", {
   "experiential": ["Role-play situations"],
   "cbt": ["involves a lot of role-playing with client"]}),

 "self-esteem": ("goal", {
   "satir": ["improve self-esteem/confidence"],
   "self-psychology": ["Developing self-cohesion and self-esteem"]}),

 "strengths and resources": ("goal", {
   "solution-focused": ["Client builds on current strengths and resources"],
   "narrative": ["Bring greater awareness to client's strengths and competencies"],
   "satir": ["Resource detective"]}),

 "here and now / present moment": ("concept", {
   "gestalt": ["Present moment awareness"],
   "client-centered": ["experience and express feelings of the here and now"],
   "existential": ["Focus on moment to moment during therapy"]}),

 "process not content": ("concept", {
   "gestalt": ["Focuses on the process"],
   "existential": ["process not content"]}),

 "psychoeducation / teaching": ("intervention", {
   "cbt": ["psychoeducation about how CBT works"],
   "bowen": ["Coach/educator", "Teach and model differentiation"]}),

 "termination work": ("intervention", {
   "object-relations": ["Work through termination and abandonment issues"],
   "self-psychology": ["Acknowledge and process issues related to termination"]}),

 "taking responsibility": ("goal", {
   "satir": ["Take Responsibility"],
   "existential": ["responsibility in the construction of their life"],
   "bowen": ["teach the family how to take responsibility"]}),

 "collaborative goal setting": ("role", {
   "narrative": ["Collaborator", "Views client as expert of their own life"],
   "cbt": ["Set collaborative goals"],
   "solution-focused": ["Therapist is a consultant, coach"]}),
}

# Confusion sets the packet itself already disambiguates. Terms stay unique to
# their model; they are simply easy to mix up and deserve T2_collision items.
CONFUSION_SETS = [
 {"name": "Psychodynamic four-way (flagged in packet)",
  "scope": ["object-relations"],
  "terms": ["Projection", "Projective Identification", "Introjection", "Identification"]},
 {"name": "Behavioral experiment vs exposure",
  "scope": ["cbt"], "terms": ["Behavioral Experiments", "Exposure"]},
 {"name": "Systematic desensitization vs anxiety management training",
  "scope": ["cbt"], "terms": ["Systematic Desensitization", "Anxiety Management Training"]},
 {"name": "Three-column vs thought record",
  "scope": ["cbt"], "terms": ["Three-Column Technique", "Thought Record"]},
 {"name": "Self-object transference types",
  "scope": ["self-psychology"],
  "terms": ["Mirroring Transference", "Twinship Transference",
            "Idealizing Transference", "Adversarial Transference"]},
 {"name": "Attachment styles",
  "scope": ["attachment"],
  "terms": ["Secure Attachment", "Preoccupied/Anxious Attachment",
            "Dismissive/Avoidant Attachment",
            "Fearful/Avoidant Attachment (Disorganized)"]},
 {"name": "Satir communication stances",
  "scope": ["satir"],
  "terms": ["Placater", "Blamer", "Computer", "Distracter", "Leveler"]},
 {"name": "Structural boundary types",
  "scope": ["structural"],
  "terms": ["Disengaged Boundaries", "Enmeshed Boundaries"]},
]


def norm(s):
    s = s.lower().replace("“", "").replace("”", "").replace("’", "'")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())


def main():
    with io.open(os.path.join(ROOT, "theories.json"), encoding="utf-8") as f:
        T = json.load(f)

    # --- pass 1: literal term index
    claims = {}   # norm term -> {"display":..,"type":..,"models":set()}
    for m in T["models"]:
        mid = m["id"]
        for kind, key in (("concept", "concepts"), ("intervention", "interventions")):
            for c in m[key]:
                n = norm(c["term"])
                if not n:
                    continue
                e = claims.setdefault(n, {"display": c["term"], "type": kind,
                                          "models": set()})
                e["models"].add(mid)
        for r in (m["therapistRoles"] or []):
            n = norm(r["text"])
            if not n or len(n) > 60:
                continue
            e = claims.setdefault(n, {"display": r["text"], "type": "role",
                                      "models": set()})
            e["models"].add(mid)

    # --- pass 2: semantic overlay
    variant_to_class = {}
    for canon, (ctype, bymodel) in EQUIV.items():
        if canon in NO_PROPAGATE:
            continue  # function-level class: members keep their own uniqueness
        for mid, variants in bymodel.items():
            for v in variants:
                variant_to_class.setdefault(norm(v), canon)

    # a marker inherits its class's claimants
    markers = []
    for n, e in sorted(claims.items()):
        models = set(e["models"])
        canon = variant_to_class.get(n)
        if canon:
            models |= set(EQUIV[canon][1].keys())
        markers.append({
            "marker": e["display"], "normalized": n, "type": e["type"],
            "claimedBy": sorted(models),
            "unique": len(models) == 1,
            "equivalenceClass": canon,
        })

    # equivalence classes as their own marker entries
    for canon, (ctype, bymodel) in sorted(EQUIV.items()):
        markers.append({
            "marker": canon, "normalized": norm(canon), "type": ctype,
            "claimedBy": sorted(bymodel.keys()),
            "unique": len(bymodel) == 1,
            "equivalenceClass": canon,
        })

    eqout = [{"canonical": c,
              "type": t,
              "variants": sorted({v for vs in bm.values() for v in vs}),
              "claimedBy": sorted(bm.keys()),
              "byModel": {k: v for k, v in sorted(bm.items())}}
             for c, (t, bm) in sorted(EQUIV.items())]

    uniq = [m for m in markers if m["unique"]]
    shared = [m for m in markers if not m["unique"]]

    out = {"note": "unique:true markers are the ONLY legal keyed answers for "
                   "inverse (T1_marker) items. See BUILD_BRIEF S5 / S6 rule 3.",
           "counts": {"markers": len(markers), "unique": len(uniq),
                      "shared": len(shared), "equivalenceClasses": len(eqout),
                      "confusionSets": len(CONFUSION_SETS)},
           "markers": sorted(markers, key=lambda x: (not x["unique"], x["marker"])),
           "equivalenceClasses": eqout,
           "confusionSets": CONFUSION_SETS}

    with io.open(os.path.join(ROOT, "collisions.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    print("markers=%d  unique=%d  shared=%d  equivClasses=%d  confusionSets=%d"
          % (len(markers), len(uniq), len(shared), len(eqout), len(CONFUSION_SETS)))
    print("\n--- SHARED (illegal as inverse-item answers) ---")
    for m in sorted(shared, key=lambda x: -len(x["claimedBy"])):
        print("  %-46s %s" % (m["marker"][:46], ", ".join(m["claimedBy"])))


if __name__ == "__main__":
    main()
