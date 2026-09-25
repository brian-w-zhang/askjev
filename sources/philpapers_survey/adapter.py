"""PhilPapers Survey 2020 (Bourget & Chalmers 2023): professional philosophers' views as Choice questions.

Source: the aggregate results of the 100 main questions, as the JSON published on Hugging Face
(gmpj/philpapers-survey-2020, "published with direct permission from PhilPapers.org", CC BY-NC 4.0). The survey site
(survey2020.philpeople.org) sits behind a Cloudflare browser challenge, so the 40 additional questions it hosts are
not fetched.

Each question asks the answerer's own view ("What is your view on free will: compatibilism, libertarianism, or no
free will?") with the survey's positions as options plus "other" (the survey's catch-all for alternative views,
agnostic/undecided, no fact of the matter, and "the question is too unclear"). Human data: the percentage of target
faculty who accept or lean toward each position. Respondents could accept several positions, so the raw percentages
can sum to more than 100; the distribution is renormalized to sum to 1 and the raw percentages are kept in
meta["accept_or_lean_pct"]. The two multi-part questions reported only as reject rates (other minds, philosophical
methods) are left out. Contested politics (abortion, capital punishment, capitalism vs socialism, political
philosophy, gender and race) are flagged "political"; God and arguments for theism "sensitive".
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import httpx

from askjev.model import HumanDist, Question

NAME = "philpapers_survey"
URL = "https://huggingface.co/datasets/gmpj/philpapers-survey-2020/resolve/main/philpapers-survey-2020.json"
FILE = "philpapers-survey-2020.json"
LICENSE = "CC BY-NC 4.0 (PhilPapers Survey 2020 aggregate results, via gmpj/philpapers-survey-2020)"
POP = "PhilPapers 2020 target faculty"
SRC = "Bourget & Chalmers (2023), Philosophers on Philosophy: The 2020 PhilPapers Survey; accept or lean toward"

BIGQ = "self.mind.big_questions"
FWR = "self.mind.big_questions.free_will_reality"
MHN = "self.mind.big_questions.meaning_human_nature"
CAI = "self.mind.consciousness_ai"
EPI = "self.mind.epistemics.knowledge_certainty"
EVI = "self.mind.epistemics.evidence_sources"
PUZ = "self.mind.thought_experiments.classic_puzzles"
MIS = "self.mind.thought_experiments.mind_identity_scenarios"
MIND = "self.mind"
MORAL = "self.values.moral_foundations"
SAC = "self.values.sacrificial_dilemmas"
FAIR = "self.values.fairness_justice"
ANIM = "self.values.animals_environment"
HW = "self.mind.happiness_wellbeing"
DEATH = "self.mind.time_mortality.death_legacy"

OTHER = ("Another view: an alternative position, agnostic or undecided, no fact of the matter, or the question is too "
         "unclear to answer")

# key -> (text, node, {option: description or None}, flags)
Q: dict[str, tuple] = {
    "a_priori_knowledge": ("Is there a priori knowledge, that is, knowledge justified independently of experience?",
                           EPI, {"yes": None, "no": None}),
    "abstract_objects": ("What is your view on abstract objects such as numbers: platonism (they exist) or nominalism "
                         "(they do not)?", FWR, {"platonism": "Abstract objects exist",
                                                 "nominalism": "There are no abstract objects"}),
    "aesthetic_value": ("Is aesthetic value objective or subjective?", MIND, {"objective": None, "subjective": None}),
    "aim_of_philosophy": ("What is the most important aim of philosophy: truth/knowledge, understanding, wisdom, "
                          "happiness, or goodness/justice?", MIND,
                          {"truth_knowledge": "Truth or knowledge", "understanding": None, "wisdom": None,
                           "happiness": None, "goodness_justice": "Goodness or justice"}),
    "analytic_synthetic_distinction": ("Is there an analytic-synthetic distinction, between statements true in virtue "
                                       "of meaning and statements true in virtue of how the world is?", EPI,
                                       {"yes": None, "no": None}),
    "eating_animals_and_animal_products": ("What is your view on eating animals and animal products in ordinary "
                                           "circumstances: omnivorism (it is permissible to eat both), vegetarianism "
                                           "(only animal products are permissible), or veganism (neither is "
                                           "permissible)?", ANIM,
                                           {"omnivorism": "Eating animals and animal products is permissible",
                                            "vegetarianism": "Only eating animal products is permissible",
                                            "veganism": "Eating neither is permissible"}),
    "epistemic_justification": ("What is your view on epistemic justification: internalism (it depends only on "
                                "factors accessible to the believer) or externalism?", EPI,
                                {"internalism": None, "externalism": None}),
    "experience_machine": ("Would you enter an experience machine that would give you whatever pleasurable "
                           "experiences you wanted for the rest of your life, while your body floats in a tank?", HW,
                           {"yes": None, "no": None}),
    "external_world": ("What is your view on the external world: idealism, skepticism, or non-skeptical realism?", FWR,
                       {"idealism": "The external world is mental or mind-dependent",
                        "skepticism": "We cannot know that there is an external world",
                        "non_skeptical_realism": "There is a mind-independent external world and we know it"}),
    "footbridge": ("A runaway trolley will kill five people unless you push a large stranger off a footbridge onto the "
                   "track, which will kill him but stop the trolley. Should you push him?", SAC,
                   {"push": None, "dont_push": "Don't push"}),
    "free_will": ("What is your view on free will: compatibilism, libertarianism, or no free will?", FWR,
                  {"compatibilism": "Free will is compatible with determinism",
                   "libertarianism": "We have free will and it is incompatible with determinism",
                   "no_free_will": "There is no free will"}),
    "gender": ("What is gender: biological, psychological, social, or unreal?", MHN,
               {"biological": None, "psychological": None, "social": None, "unreal": None}, ["political"]),
    "god": ("What is your view on God: theism or atheism?", BIGQ, {"theism": None, "atheism": None}, ["sensitive"]),
    "knowledge_claims": ("What is your view on knowledge claims: contextualism (the truth of 'S knows that p' depends "
                         "on the speaker's context), relativism, or invariantism?", EPI,
                         {"contextualism": None, "relativism": None, "invariantism": None}),
    "knowledge": ("What is your view on the sources of knowledge: empiricism or rationalism?", EPI,
                  {"empiricism": None, "rationalism": None}),
    "laws_of_nature": ("What is your view on laws of nature: Humean (they merely summarize regularities) or "
                       "non-Humean (they govern what happens)?", FWR, {"humean": None, "non_humean": None}),
    "logic": ("Which logic is correct: classical or non-classical?", EPI, {"classical": None, "non_classical": None}),
    "meaning_of_life": ("Is the meaning of life subjective, objective, or nonexistent?", MHN,
                        {"subjective": None, "objective": None, "nonexistent": None}),
    "mental_content": ("What is your view on mental content: internalism (it depends only on what is inside the "
                       "head) or externalism?", CAI, {"internalism": None, "externalism": None}),
    "meta_ethics": ("What is your view on meta-ethics: moral realism or moral anti-realism?", MORAL,
                    {"moral_realism": None, "moral_anti_realism": None}),
    "metaphilosophy": ("What is your view on the nature of philosophy: naturalism (it is continuous with science) or "
                       "non-naturalism?", MIND, {"naturalism": None, "non_naturalism": None}),
    "mind": ("What is your view on the mind: physicalism or non-physicalism?", CAI,
             {"physicalism": None, "non_physicalism": None}),
    "moral_judgment": ("What is your view on moral judgments: cognitivism (they express beliefs that can be true or "
                       "false) or non-cognitivism?", MORAL, {"cognitivism": None, "non_cognitivism": None}),
    "moral_motivation": ("What is your view on moral motivation: internalism (sincerely judging something right "
                         "necessarily motivates you) or externalism?", MORAL,
                         {"internalism": None, "externalism": None}),
    "newcombs_problem": ("In Newcomb's problem, a highly reliable predictor has put $1,000,000 in an opaque box only if "
                         "it predicted you would take just that box; a transparent box holds $1,000. Do you take one "
                         "box or both boxes?", PUZ, {"one_box": "Take only the opaque box",
                                                     "two_boxes": "Take both boxes"}),
    "normative_ethics": ("Which normative ethical theory do you favor: deontology, consequentialism, or virtue "
                         "ethics?", MORAL, {"deontology": None, "consequentialism": None, "virtue_ethics": None}),
    "perceptual_experience": ("What is the best theory of perceptual experience: disjunctivism, qualia theory, "
                              "representationalism, or sense-datum theory?", CAI,
                              {"disjunctivism": None, "qualia_theory": None, "representationalism": None,
                               "sense_datum_theory": None}),
    "personal_identity": ("What is your view on personal identity over time: the biological view, the psychological "
                          "view, or the further-fact view?", MIS,
                          {"biological_view": None, "psychological_view": None, "further_fact_view": None}),
    "philosophical_progress": ("How much progress has philosophy made: none, a little, or a lot?", MIND,
                               {"none": None, "a_little": None, "a_lot": None}),
    "political_philosophy": ("Which political philosophy do you favor: communitarianism, egalitarianism, or "
                             "libertarianism?", FAIR,
                             {"communitarianism": None, "egalitarianism": None, "libertarianism": None},
                             ["political"]),
    "proper_names": ("What is your view on proper names: Fregean (they have sense as well as reference) or Millian "
                     "(their meaning is just their referent)?", EPI, {"fregean": None, "millian": None}),
    "race": ("What is race: biological, social, or unreal?", MHN,
             {"biological": None, "social": None, "unreal": None}, ["political"]),
    "science": ("What is your view on science: scientific realism (our best theories are approximately true, "
                "including about unobservables) or scientific anti-realism?", EVI,
                {"scientific_realism": None, "scientific_anti_realism": None}),
    "teletransporter": ("A teletransporter scans your body, destroys it, and builds an exact duplicate on Mars. Is "
                        "stepping into it survival or death?", MIS, {"survival": None, "death": None}),
    "time": ("What is your view on time: the A-theory (there is an objective present and time passes) or the "
             "B-theory (all times are equally real and ordered only by earlier and later)?", FWR,
             {"a_theory": "A-theory", "b_theory": "B-theory"}),
    "trolley_problem": ("A runaway trolley will kill five people unless you switch it to a side track, where it will "
                        "kill one person. Should you switch it?", SAC,
                        {"switch": None, "dont_switch": "Don't switch"}),
    "truth": ("What is the best theory of truth: correspondence, deflationary, or epistemic?", EPI,
              {"correspondence": None, "deflationary": None, "epistemic": None}),
    "vagueness": ("What is the source of vagueness: epistemic, metaphysical, or semantic?", EPI,
                  {"epistemic": None, "metaphysical": None, "semantic": None}),
    "zombies": ("Are philosophical zombies (beings physically identical to us but without conscious experience) "
                "inconceivable, conceivable but not metaphysically possible, or metaphysically possible?", CAI,
                {"inconceivable": None, "conceivable_but_not_possible": None, "metaphysically_possible": None}),
    "abortion": ("Is abortion, in the first trimester and in ordinary circumstances, permissible or impermissible?",
                 MORAL, {"permissible": None, "impermissible": None}, ["political"]),
    "aesthetic_experience": ("What is aesthetic experience best understood as: perception, pleasure, or sui generis "
                             "(a distinctive kind of its own)?", MIND,
                             {"perception": None, "pleasure": None, "sui_generis": None}),
    "analysis_of_knowledge": ("What is the right analysis of knowledge: justified true belief, some other analysis, or "
                              "no analysis?", EPI,
                              {"justified_true_belief": None, "other_analysis": None, "no_analysis": None}),
    "arguments_for_theism": ("Which argument for theism is strongest: cosmological, design, ontological, pragmatic, or "
                             "moral?", BIGQ, {"cosmological": None, "design": None, "ontological": None,
                                              "pragmatic": None, "moral": None}, ["sensitive"]),
    "belief_or_credence": ("Which is more fundamental: belief or credence (degree of belief)?", EPI,
                           {"belief": None, "credence": None, "neither": None}),
    "capital_punishment": ("Is capital punishment permissible or impermissible?", MORAL,
                           {"permissible": None, "impermissible": None}, ["political"]),
    "causation": ("What is causation: counterfactual/difference-making, process/production, primitive, or "
                  "nonexistent?", FWR, {"counterfactual_difference_making": None, "process_production": None,
                                        "primitive": None, "nonexistent": None}),
    "chinese_room": ("In Searle's Chinese room, a person who knows no Chinese follows a rulebook to answer Chinese "
                     "questions convincingly. Does the system understand Chinese?", CAI,
                     {"understands": None, "doesnt_understand": "Doesn't understand"}),
    "concepts": ("What is your view on concepts: nativism (many are innate) or empiricism (they are learned from "
                 "experience)?", EPI, {"nativism": None, "empiricism": None}),
    "consciousness": ("What is the best theory of consciousness: dualism, eliminativism, functionalism, identity "
                      "theory, or panpsychism?", CAI,
                      {"dualism": None, "eliminativism": None, "functionalism": None, "identity_theory": None,
                       "panpsychism": None}),
    "continuum_hypothesis": ("Does the continuum hypothesis have a determinate truth value?", EPI,
                             {"determinate": None, "indeterminate": None}),
    "cosmological_fine_tuning": ("What explains the apparent fine-tuning of the universe for life: design, a "
                                 "multiverse, brute fact, or is there no fine-tuning?", FWR,
                                 {"design": None, "multiverse": None, "brute_fact": None, "no_fine_tuning": None}),
    "environmental_ethics": ("What is your view on environmental ethics: anthropocentric (only humans matter in "
                             "themselves) or non-anthropocentric?", ANIM,
                             {"anthropocentric": None, "non_anthropocentric": None}),
    "extended_mind": ("Does the mind extend beyond the skin, for example into notebooks or devices?", CAI,
                      {"yes": None, "no": None}),
    "foundations_of_mathematics": ("What is the best view of the foundations of mathematics: "
                                   "constructivism/intuitionism, formalism, logicism, structuralism, or set-theoretic?",
                                   EPI, {"constructivism_intuitionism": None, "formalism": None, "logicism": None,
                                         "structuralism": None, "set_theoretic": None}),
    "gender_categories": ("Should we preserve, revise, or eliminate our gender categories?", MHN,
                          {"preserve": None, "revise": None, "eliminate": None}, ["political"]),
    "grounds_of_intentionality": ("What grounds intentionality (the aboutness of mental states): causal/teleological "
                                  "relations, inferential role, interpretation, phenomenal consciousness, or is it "
                                  "primitive?", CAI, {"causal_teleological": None, "inferential": None,
                                                      "interpretational": None, "phenomenal": None,
                                                      "primitive": None}),
    "hard_problem_of_consciousness": ("Is there a hard problem of consciousness, a problem of explaining why physical "
                                      "processes give rise to experience that is distinct from explaining their "
                                      "functions?", CAI, {"yes": None, "no": None}),
    "human_genetic_engineering": ("Is human genetic engineering permissible or impermissible?", MORAL,
                                  {"permissible": None, "impermissible": None}),
    "hume": ("How is Hume best interpreted: as a skeptic or as a naturalist?", MIND,
             {"skeptic": None, "naturalist": None}),
    "immortality": ("If you could become immortal, would you choose to?", DEATH, {"yes": None, "no": None}),
    "interlevel_metaphysics": ("What is the most useful relation for understanding how higher-level facts relate to "
                               "lower-level ones: grounding, identity, realization, or supervenience?", FWR,
                               {"grounding": None, "identity": None, "realization": None, "supervenience": None}),
    "justification": ("What is the best theory of epistemic justification: coherentism, infinitism, nonreliabilist "
                      "foundationalism, or reliabilism?", EPI,
                      {"coherentism": None, "infinitism": None, "nonreliabilist_foundationalism": None,
                       "reliabilism": None}),
    "kant": ("How is Kant's transcendental idealism best interpreted: as a one-world view or a two-worlds view?", MIND,
             {"one_world": None, "two_worlds": None}),
    "law": ("What is your view on the nature of law: legal positivism or legal non-positivism?", FAIR,
            {"legal_positivism": None, "legal_non_positivism": None}),
    "material_composition": ("When do several objects compose a further object: never (nihilism), only sometimes "
                             "(restrictivism), or always (universalism)?", FWR,
                             {"nihilism": None, "restrictivism": None, "universalism": None}),
    "metaontology": ("What is your view on metaontology: heavyweight realism, deflationary realism, or anti-realism?",
                     FWR, {"heavyweight_realism": None, "deflationary_realism": None, "anti_realism": None}),
    "method_in_history_of_philosophy": ("What is the best method in the history of philosophy: analytic/rational "
                                        "reconstruction or contextual/historicist?", MIND,
                                        {"analytic_rational_reconstruction": None, "contextual_historicist": None}),
    "method_in_political_philosophy": ("What is the best method in political philosophy: ideal theory or non-ideal "
                                       "theory?", FAIR, {"ideal_theory": None, "non_ideal_theory": None}),
    "mind_uploading": ("If your brain were scanned and replaced by a digital emulation, would that be survival or "
                       "death?", MIS, {"survival": None, "death": None}),
    "moral_principles": ("What is your view on moral principles: moral generalism or moral particularism?", MORAL,
                         {"moral_generalism": None, "moral_particularism": None}),
    "morality": ("What is the best metaethical view of morality: non-naturalism, naturalist realism, constructivism, "
                 "expressivism, or error theory?", MORAL,
                 {"non_naturalism": None, "naturalist_realism": None, "constructivism": None, "expressivism": None,
                  "error_theory": None}),
    "normative_concepts": ("Which normative concept is most fundamental: fit, ought, reasons, or value?", MORAL,
                           {"fit": None, "ought": None, "reasons": None, "value": None}),
    "ought_implies_can": ("Does 'ought' imply 'can', so that you can only be obligated to do what you are able to "
                          "do?", MORAL, {"yes": None, "no": None}),
    "philosophical_knowledge": ("How much philosophical knowledge is there: none, a little, or a lot?", MIND,
                                {"none": None, "a_little": None, "a_lot": None}),
    "plato": ("On Plato's view, is there knowledge only of the Forms, or also of concrete things?", MIND,
              {"knowledge_only_of_forms": None, "knowledge_also_of_concrete_things": None}),
    "politics": ("Which economic system do you favor: capitalism or socialism?", FAIR,
                 {"capitalism": None, "socialism": None}, ["political"]),
    "possible_worlds": ("What are possible worlds: abstract objects, concrete objects, or nonexistent?", FWR,
                        {"abstract": None, "concrete": None, "nonexistent": None}),
    "practical_reason": ("What is the best view of practical reason: Aristotelian, Humean, or Kantian?", MORAL,
                         {"aristotelian": None, "humean": None, "kantian": None}),
    "principle_of_sufficient_reason": ("Is the principle of sufficient reason, that everything has an explanation, "
                                       "true or false?", FWR, {"true": None, "false": None}),
    "properties": ("What are properties: classes, immanent universals, transcendent universals, tropes, or "
                   "nonexistent?", FWR, {"classes": None, "immanent_universals": None,
                                         "transcendent_universals": None, "tropes": None, "nonexistent": None}),
    "propositional_attitudes": ("What are propositional attitudes such as beliefs and desires: dispositional, "
                                "phenomenal, representational, or nonexistent?", CAI,
                                {"dispositional": None, "phenomenal": None, "representational": None,
                                 "nonexistent": None}),
    "propositions": ("What are propositions: sets, structured entities, simple entities, acts, or nonexistent?", EPI,
                     {"sets": None, "structured_entities": None, "simple_entities": None, "acts": None,
                      "nonexistent": None}),
    "quantum_mechanics": ("What is the best interpretation of quantum mechanics: collapse, hidden variables, many "
                          "worlds, or epistemic?", FWR, {"collapse": None, "hidden_variables": None,
                                                         "many_worlds": None, "epistemic": None}),
    "race_categories": ("Should we preserve, revise, or eliminate our race categories?", MHN,
                        {"preserve": None, "revise": None, "eliminate": None}, ["political"]),
    "rational_disagreement": ("Can two people with the same evidence rationally disagree? Permissivism says yes; "
                              "non-permissivism (uniqueness) says no.", EVI,
                              {"non_permissivism": None, "permissivism": None}),
    "response_to_external_world_skepticism": ("What is the best response to external-world skepticism: abductive, "
                                              "contextualist, dogmatist, epistemic externalist, semantic externalist, "
                                              "or pragmatic?", EPI,
                                              {"abductive": None, "contextualist": None, "dogmatist": None,
                                               "epistemic_externalist": None, "semantic_externalist": None,
                                               "pragmatic": None}),
    "semantic_content": ("How much of what a sentence says depends on context: minimalism, moderate contextualism, or "
                         "radical contextualism?", EPI,
                         {"minimalism": None, "moderate_contextualism": None, "radical_contextualism": None}),
    "sleeping_beauty": ("Sleeping Beauty is put to sleep; a fair coin is tossed; if heads she is woken once, if tails "
                        "twice, with her memory of any earlier waking erased. On waking, what should her credence be "
                        "that the coin landed heads?", PUZ, {"one_third": "1/3", "one_half": "1/2"}),
    "spacetime": ("What is your view on spacetime: relationism (it is just relations among things) or "
                  "substantivalism (it exists in its own right)?", FWR,
                  {"relationism": None, "substantivalism": None}),
    "statue_and_lump": ("A lump of clay is shaped into a statue. Are the statue and the lump one thing or two "
                        "things?", PUZ, {"one_thing": None, "two_things": None}),
    "temporal_ontology": ("What exists in time: only the present (presentism), past, present and future equally "
                          "(eternalism), or the past and present only (growing block)?", FWR,
                          {"presentism": None, "eternalism": None, "growing_block": None}),
    "theory_of_reference": ("What is the best theory of reference: causal, descriptive, or deflationary?", EPI,
                            {"causal": None, "descriptive": None, "deflationary": None}),
    "time_travel": ("Is time travel metaphysically possible or metaphysically impossible?", FWR,
                    {"metaphysically_possible": None, "metaphysically_impossible": None}),
    "true_contradictions": ("Can there be true contradictions: impossible, possible but non-actual, or actual?", EPI,
                            {"impossible": None, "possible_but_non_actual": None, "actual": None}),
    "units_of_selection": ("What are the units of natural selection: genes or organisms?", EVI,
                           {"genes": None, "organisms": None}),
    "values_in_science": ("Is ideal scientific reasoning necessarily value-free, necessarily value-laden, or can it be "
                          "either?", EVI, {"necessarily_value_free": None, "necessarily_value_laden": None,
                                           "can_be_either": None}),
    "well_being": ("What is the best theory of well-being: hedonism/experientialism, desire satisfaction, or an "
                   "objective list?", HW, {"hedonism_experientialism": None, "desire_satisfaction": None,
                                           "objective_list": None}),
    "wittgenstein": ("Which Wittgenstein is better: early or late?", MIND, {"early": None, "late": None}),
}


def fetch(raw_dir: Path) -> None:
    raw_dir.mkdir(parents=True, exist_ok=True)
    if (raw_dir / FILE).exists():
        return
    r = httpx.get(URL, follow_redirects=True, timeout=120)
    r.raise_for_status()
    (raw_dir / FILE).write_bytes(r.content)


def normalize(raw_dir: Path) -> Iterator[Question]:
    data = json.loads((raw_dir / FILE).read_text())
    missing = set(Q) - set(data)
    assert not missing, f"questions missing from the file: {missing}"
    for key, spec in Q.items():
        text, node, opts = spec[:3]
        flags = spec[3] if len(spec) > 3 else []
        pct = data[key]
        assert set(pct) == set(opts) | {"other"}, (key, set(pct), set(opts))
        options = {**opts, "other": OTHER}
        tot = sum(pct[k] for k in options)
        dist = {k: round(pct[k] / tot, 4) for k in options}
        meta = {"accept_or_lean_pct": pct, "note": "shares renormalized from accept-or-lean-toward percentages "
                "(several positions could be accepted)"}
        if flags:
            meta["flags"] = flags
        yield Question(
            text=text,
            primitive="choice",
            hemisphere="self",
            kind="values",
            origin="dataset",
            source=NAME,
            options=options,
            node_hint=node,
            source_item_id=key,
            license=LICENSE,
            human=[HumanDist(population=POP, distribution=dist, n=None, source=SRC, wave="2020")],
            meta=meta,
        )
