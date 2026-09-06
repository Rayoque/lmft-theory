# -*- coding: utf-8 -*-
"""Hand-authored vignettes and exam-tip items.

Two categories, both deliberately low-risk:

  1. The instructor's own exam guidance (examTips already in theories.json).
     BUILD_BRIEF S4 calls these the highest-value items in the corpus.
  2. Vignettes built on worked examples the packet ALREADY contains -- the
     two Experiential vignettes whose answers the source states outright,
     plus Maria/Emily, the son moved out of the chair, the crying client,
     the annoyed therapist. Using the packet's own scenarios keeps
     generation risk near zero.

Vignette scenario prose is scaffolding, not a claim about a theory. Every
OPTION is still a fact object out of theories.json with its own belongsTo
and verbatim sourceLine, so the anti-hallucination lock holds.
"""


def _term(M, mid, term):
    for c in (M[mid]["interventions"] + M[mid]["concepts"]):
        if c["term"] == term:
            return c
    raise KeyError("%s / %s not in theories.json" % (mid, term))


def _tip(M, mid, needle):
    for t in M[mid]["examTips"]:
        if needle.lower() in t["sourceLine"].lower():
            return t
    raise KeyError("no examTip in %s containing %r" % (mid, needle))


# (id, models, stem, correct(mid,term,display), [distractor(mid,term)], rationale)
VIGNETTES = [
 ("v_experiential_whole_family", ["experiential"],
  "A mother brings her child to therapy. Both are in the room. The therapist "
  "works from Experiential/Symbolic therapy.\n\nWhat is the therapist's initial "
  "intervention?",
  ("experiential", "Battle for Structure",
   "Discuss with the mother the need to include the entire family in therapy"),
  [("structural", "Joining", None), ("gestalt", "Empty chair", None),
   ("satir", "Family Sculpting", None)],
  "The packet states this answer outright: the therapist discusses with mom the "
  "need to include the entire family in therapy. That is the Battle for Structure."),

 ("v_experiential_silent_family", ["experiential"],
  "A family comes in for therapy and nobody is speaking.\n\nWhat would an "
  "Experiential/Symbolic therapist do?",
  ("experiential", "Battle for Initiative",
   "Wait silently for the family to take initiative"),
  [("structural", "Enactment", None), ("strategic", "Paradoxical Directives", None),
   ("satir", "Modeling Communication", None)],
  "The packet states this answer outright. Motivation for change must come from "
  "the family; the therapist should not be working harder than the family."),

 ("v_bowen_projection", ["bowen"],
  "Maria becomes preoccupied with her daughter Emily's emotions. When Emily "
  "cries after a bad test grade, Maria reads it as evidence that Emily is "
  "emotionally fragile. Maria begins hovering, solving problems for her, and "
  "calling teachers to complain about stressful assignments.\n\nA Bowen "
  "therapist would identify this as:",
  ("bowen", "Family Projection Process", None),
  [("structural", "Enmeshed Boundaries", None), ("satir", "Incongruent Communication", None),
   ("strategic", "Positioning", None)],
  "This is the packet's own worked example of the family projection process: "
  "the primary way parents transmit their emotional problems to a child."),

 ("v_bowen_cutoff", ["bowen"],
  "A grandmother learned to avoid conflict by emotionally shutting down. Her "
  "daughter grew up with a distant mother and became overly enmeshed with her "
  "own daughter. That granddaughter is now emotionally reactive under stress, "
  "has moved far away to escape the family, and married someone equally "
  "distant.\n\nA Bowen therapist would name this pattern:",
  ("bowen", "Multigenerational Transmission Process", None),
  [("structural", "Power Hierarchy", None), ("satir", "Family Life Chronology", None),
   ("strategic", "Restraining", None)],
  "The packet's three-generation example. Small differences in differentiation "
  "between parents and offspring lead over many generations to marked differences."),

 ("v_structural_chair", ["structural"],
  "A son habitually sits in the chair between his two parents. The therapist "
  "asks him to move to a chair on the opposite side of the room so he is not "
  "caught in the middle.\n\nThis Structural intervention is:",
  ("structural", "Boundary Making", None),
  [("bowen", "De-triangulation", None), ("satir", "Family Sculpting", None),
   ("strategic", "Ordeals", None)],
  "The packet gives this exact example under Boundary Making, a special case of "
  "enactment in which the therapist defines who is open and closed to whom."),

 ("v_gestalt_tearing_up", ["gestalt"],
  "A client begins to cry in session. Rather than saying “you seem sad,” the "
  "therapist says: “I see you tearing up, I'm wondering what you're "
  "experiencing right now.”\n\nThis illustrates which Gestalt method?",
  ("gestalt", "Phenomenological description", None),
  [("existential", "Holding", None), ("experiential", "Activating Constructive Anxiety", None),
   ("self-psychology", "Experience-Near Empathy", None)],
  "The packet contrasts these two therapist responses directly. Gestalt explains "
  "the client's experience by description instead of interpretation."),

 ("v_objrel_annoyed", ["object-relations"],
  "During sessions with a particular client, the therapist repeatedly notices "
  "that they themselves feel annoyed. On reflection the therapist recognises "
  "the annoyance did not originate with them; they have taken on and begun to "
  "identify with a feeling the client put onto them.\n\nAn Object Relations "
  "therapist would name this:",
  ("object-relations", "Projective Identification", None),
  [("self-psychology", "Mirroring Transference", None),
   ("self-psychology", "Adversarial Transference", None),
   ("attachment", "Attunement", None)],
  "The packet's own example, and it flags this as a term to look for on the "
  "exam: the therapist finds themselves feeling annoyed."),

 ("v_objrel_identification", ["object-relations"],
  "A husband has not merely taken on the idea that women should do the "
  "housework. He sees himself as head of the household, like his father, and "
  "expects his wife to treat him as his mother treated his dad.\n\nThis is:",
  ("object-relations", "Identification", None),
  [("self-psychology", "Twinship Transference", None),
   ("attachment", "Attachment Behavior System", None),
   ("self-psychology", "Idealizing Transference", None)],
  "The packet distinguishes identification from introjection with this example: "
  "he does not just take on the belief, he identifies with the person."),

 ("v_cbt_downward_arrow", ["cbt"],
  "A client says people did not like them at a party. The therapist asks what "
  "that meant to them; the client says they were not important. The therapist "
  "asks what that means about them; the client says they are worthless.\n\n"
  "Which CBT technique is the therapist using?",
  ("cbt", "Downward Arrow", None),
  [("cbt", "Socratic Questioning", None), ("cbt", "Labeling Distortions", None),
   ("cbt", "Finding Alternatives", None)],
  "Downward arrow moves down to the core belief the person holds. The packet's "
  "own party example.", True),

 ("v_cbt_reframe", ["cbt"],
  "A client says: “No one likes me. I must be boring or weird.” The therapist "
  "helps them consider: “Maybe people were shy too, or didn't know what to "
  "say.”\n\nThis is:",
  ("cbt", "Reframing", None),
  [("cbt", "Systematic Desensitization", None), ("cbt", "Behavioral Activation", None),
   ("cbt", "Successive Approximation", None)],
  "The packet's own reframing example: thinking differently about assumptions so "
  "the person feels differently.", True),

 ("v_satir_blamer", ["satir"],
  "In a family session one member consistently attacks the others, finds fault, "
  "and speaks like a boss or dictator.\n\nIn Satir's terms this communication "
  "stance is:",
  ("satir", "Blamer", None),
  [("satir", "Placater", None), ("satir", "Computer", None),
   ("satir", "Distracter", None)],
  "Satir's five communication stances. Blamer: attacking others, fault finder, "
  "dictator, boss.", True),

 ("v_satir_computer", ["satir"],
  "A family member responds to every emotional question by being super "
  "reasonable, intellectual, and distant, and is always correct.\n\nSatir would "
  "call this stance:",
  ("satir", "Computer", None),
  [("satir", "Leveler", None), ("satir", "Placater", None),
   ("satir", "Blamer", None)],
  "Computer: super reasonable, intellectual, distant, always correct.", True),

 ("v_strategic_positioning", ["strategic"],
  "A therapist tells a family their situation is completely hopeless, expecting "
  "the family to push back and insist that it is not.\n\nThis Strategic "
  "technique is:",
  ("strategic", "Positioning", None),
  [("structural", "Unbalancing", None), ("bowen", "Reframing", None),
   ("satir", "Transforming Rules", None)],
  "Positioning: the therapist takes a more exaggerated and extreme view of the "
  "problem and the family is obligated to rebel."),

 ("v_selfpsych_enactment", ["self-psychology"],
  "A therapist says: “It sounds like what's going on with your partner is "
  "similar to what happened with your father.”\n\nIn Self Psychology this is:",
  ("self-psychology", "Addressing enactments", None),
  [("object-relations", "Interpretation", None),
   ("attachment", "Explore disruptions", None),
   ("object-relations", "Confront resistance and primitive defenses", None)],
  "The packet gives this exact sentence as its example of addressing enactments: "
  "situations that played out in the past or outside, talked about in session."),

 ("v_attachment_dismissive", ["attachment"],
  "A client dismisses the importance of love and connection, idealizes their "
  "parents although actual memories do not corroborate it, dislikes looking "
  "inward, and has difficulty tolerating heightened emotions in others.\n\n"
  "This attachment pattern is:",
  ("attachment", "Dismissive/Avoidant Attachment", None),
  [("attachment", "Preoccupied/Anxious Attachment", None),
   ("attachment", "Secure Attachment", None),
   ("attachment", "Fearful/Avoidant Attachment (Disorganized)", None)],
  "Dismissive/Avoidant per the packet's description.", True),

 ("v_attachment_preoccupied", ["attachment"],
  "A client is still embroiled with anger and hurt at their parents, becomes "
  "overly dependent on attachment figures, recalls role reversal in childhood, "
  "and dreads abandonment.\n\nThis attachment pattern is:",
  ("attachment", "Preoccupied/Anxious Attachment", None),
  [("attachment", "Dismissive/Avoidant Attachment", None),
   ("attachment", "Secure Attachment", None),
   ("attachment", "Fearful/Avoidant Attachment (Disorganized)", None)],
  "Preoccupied/Anxious per the packet's description.", True),

 ("v_sft_miracle", ["solution-focused"],
  "A therapist asks: “Imagine that tomorrow morning you wake up and a miracle "
  "has happened. What would be different that will tell you a miracle has "
  "happened and your problem has been solved?”\n\nThis is:",
  ("solution-focused", "Miracle Questioning", None),
  [("narrative", "Unique Outcomes", None), ("cbt", "Finding Alternatives", None),
   ("existential", "“Imaginal death” exercises", None)],
  "The packet's own scripted example of the miracle question."),

 ("v_sft_coping", ["solution-focused"],
  "A client cannot identify any positive change. The therapist asks: “How do "
  "you keep going each day even when it feels like there is no hope?”\n\nThis "
  "is:",
  ("solution-focused", "Coping Questions", None),
  [("solution-focused", "Exception Questioning", None),
   ("solution-focused", "Scaling Questions", None),
   ("solution-focused", "Presupposing Change", None)],
  "Coping questions illustrate resources the client already has, validating "
  "difficulty without undermining their view of reality.", True),

 ("v_narrative_externalize", ["narrative"],
  "A therapist asks a series of questions designed to separate the person from "
  "the problem, so the client stops experiencing the problem as who they "
  "are.\n\nIn Narrative therapy this is:",
  ("narrative", "Externalizing the Problem", None),
  [("solution-focused", "Exception Questioning", None),
   ("satir", "Transforming Rules", None), ("client-centered", None, None)],
  "Externalizing the problem: questions designed to separate the person from "
  "the problem."),
]


# (id, model, examTip needle, stem, correct display text, [distractor(mid,term)])
EXAMTIPS = [
 ("e_cc_no_phases", "client-centered", "No clear phases",
  "Client Centered therapy has no clear phases of treatment, and the packet "
  "says so. It also warns that the exam may still ask what a Client Centered "
  "therapist does in the initial or middle stage.\n\nWhat answer shape is "
  "correct there?",
  "Unconditional positive regard, empathy, therapist congruence, and promotion "
  "of self-acceptance",
  [("gestalt", "Empty chair"), ("experiential", "Battle for Structure"),
   ("existential", "“Imaginal death” exercises")],
  "The packet defuses this trap directly: there are no phases, but if asked, "
  "look for unconditional positive regard, empathy, congruence and promotion "
  "of self-acceptance."),

 ("e_objrel_look_for_term", "object-relations", "look for this term",
  "A therapist becomes aware of strong feelings arising in themselves about a "
  "client. The packet flags this as an exam cue and names the term to look "
  "for.\n\nHow would an Object Relations therapist handle this?",
  "Identify and process projective identification",
  [("self-psychology", "Mirroring"), ("attachment", "Attunement"),
   ("self-psychology", "Optimal Frustration")],
  "The packet says explicitly: T is aware of feeling something about the "
  "client, how would an object relations therapist handle this, look for this "
  "term."),

 ("e_attachment_exam_focus", "attachment", "On the exam",
  "The packet gives explicit exam guidance about what an attachment-based "
  "therapist focuses on.\n\nOn the exam, an attachment therapist is "
  "specifically focused on:",
  "How the person attaches in relationships and how they regulate their own "
  "emotions, exploring their early caregiver interactions",
  [("object-relations", "Splitting"), ("self-psychology", "Twinship Transference"),
   ("gestalt", "Top dog / underdog dialogue")],
  "Stated verbatim as exam guidance in the packet."),

 ("e_cbt_relaxation_initial", "cbt", "select this on test",
  "The packet flags one CBT technique with the note “select this on test” for "
  "questions about the initial phase of treatment.\n\nWhich technique belongs "
  "to the initial phase, alongside psychoeducation and thought patterns?",
  "Relaxation Training",
  [("cbt", "Thought Record"), ("cbt", "Opposite Action"),
   ("cbt", "Mastery/Pleasure Ratings")],
  "The packet marks relaxation training as initial phase and says: select this "
  "on test.", True),

 ("e_cbt_be_vs_exposure_belief", "cbt", "testing a belief",
  "A client who fears blushing in public is asked to test the belief “people "
  "will laugh if I blush in public.”\n\nThe packet says this is:",
  "Behavioral Experiments",
  [("cbt", "Exposure"), ("cbt", "Systematic Desensitization"),
   ("cbt", "Anxiety Management Training")],
  "The packet disambiguates by intention: testing a belief is a behavioural "
  "experiment.", True),

 ("e_cbt_be_vs_exposure_fear", "cbt", "reduce their fear",
  "A client who fears blushing is repeatedly exposed to blushing in order to "
  "reduce the fear of blushing itself.\n\nThe packet says this is:",
  "Exposure",
  [("cbt", "Behavioral Experiments"), ("cbt", "Opposite Action"),
   ("cbt", "Successive Approximation")],
  "Same disambiguation, opposite intention: reducing the fear itself is "
  "exposure therapy.", True),

 ("e_cbt_three_column_first", "cbt", "Initial thing that somebody would do",
  "Which CBT technique does the packet describe as the initial homework "
  "assignment, collecting the situation, the automatic thought, and the "
  "associated feelings?",
  "Three-Column Technique",
  [("cbt", "Thought Record"), ("cbt", "Self-Monitoring"),
   ("cbt", "Mastery/Pleasure Ratings")],
  "Three columns: situation, automatic thought, feelings. The packet calls it "
  "the initial thing somebody would do for homework.", True),

 ("e_cbt_thought_record_next", "cbt", "Next step of three-column",
  "Which CBT technique expands the three-column technique by adding columns "
  "for an alternative response and the resulting emotional outcome?",
  "Thought Record",
  [("cbt", "Three-Column Technique"), ("cbt", "Labeling Distortions"),
   ("cbt", "Finding Alternatives")],
  "The packet calls the thought record the next step after the three-column "
  "technique.", True),

 ("e_cbt_amt_early", "cbt", "Skill acquisition, done early",
  "The packet notes that one CBT intervention is skill acquisition done early "
  "in therapy, teaching general coping skills with a lot of imagery and "
  "relaxation practice.\n\nWhich is it?",
  "Anxiety Management Training",
  [("cbt", "Systematic Desensitization"), ("cbt", "Exposure"),
   ("cbt", "Behavioral Activation")],
  "AMT teaches general coping skills for anytime, anywhere. Systematic "
  "desensitization instead targets a specific fear hierarchy.", True),

 ("e_cbt_first_session", "cbt", "first session",
  "According to the packet, what is taught in the first CBT session, alongside "
  "psychoeducation about how CBT works?",
  "Psychoeducation on the negative triad",
  [("cbt", "Downward Arrow"), ("cbt", "Assertiveness Training"),
   ("cbt", "Problem-Solving Training")],
  "The packet places the negative triad in the first session.", True),

 ("e_bowen_three_generations", "bowen", "three generations",
  "The packet singles out one model as the only therapy concerned with the "
  "past three generations of the family.\n\nWhich model?",
  "Bowen Family Systems",
  [("structural", None), ("satir", None), ("strategic", None)],
  "Stated in the packet as a distinguishing fact: the only therapy that is "
  "concerned with the past three generations of the family."),
]


def build(M, NAME, opt, identity_line):
    out = []

    for entry in VIGNETTES:
        if len(entry) == 6:
            iid, models, stem, cor, dis, rat = entry
            intra = False
        else:
            iid, models, stem, cor, dis, rat, intra = entry
        cmid, cterm, cdisp = cor
        cf = _term(M, cmid, cterm)
        opts = [opt(cdisp or cterm, True, cmid, cf["sourceLine"])]
        ok = True
        for dmid, dterm, _ in dis:
            if dterm is None:
                opts.append(opt(NAME[dmid], False, dmid, identity_line(dmid)))
                continue
            try:
                df = _term(M, dmid, dterm)
            except KeyError:
                ok = False
                break
            opts.append(opt(dterm, False, dmid, df["sourceLine"]))
        if not ok or len(opts) != 4:
            continue
        it = {"id": iid, "tier": 2, "type": "V_vignette",
              "models": models + [d[0] for d in dis if d[0] not in models],
              "stem": stem, "options": opts, "rationale": rat,
              "sourceLine": cf["sourceLine"]}
        if intra:
            it["intraModel"] = True
        out.append(it)

    for entry in EXAMTIPS:
        if len(entry) == 7:
            iid, mid, needle, stem, cdisp, dis, rat = entry
            intra = False
        else:
            iid, mid, needle, stem, cdisp, dis, rat, intra = entry
        tip = _tip(M, mid, needle)
        opts = [opt(cdisp, True, mid, tip["sourceLine"])]
        ok = True
        for dmid, dterm in dis:
            if dterm is None:
                opts.append(opt(NAME[dmid], False, dmid, identity_line(dmid)))
                continue
            try:
                df = _term(M, dmid, dterm)
            except KeyError:
                ok = False
                break
            opts.append(opt(dterm, False, dmid, df["sourceLine"]))
        if not ok or len(opts) != 4:
            continue
        it = {"id": iid, "tier": 2, "type": "T2_examtip",
              "models": [mid] + [d[0] for d in dis if d[0] != mid],
              "stem": stem, "options": opts, "rationale": rat,
              "sourceLine": tip["sourceLine"]}
        if intra:
            it["intraModel"] = True
        out.append(it)

    return out
