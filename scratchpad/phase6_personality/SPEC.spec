PHASE 6 PERSONALITY AUTHORING SPEC (shared by all forks)

Output: your assigned .txt file(s) in /Users/junzhang/Projects/askjev/scratchpad/phase6_personality/ in the compact format:
  @node <node id>
  C | question text? | key = optional short description ; key2 ; key3 = desc
  S | question text? | lowest level ; ... ; highest level
  N | yes/no question text?
Validate: cd /Users/junzhang/Projects/askjev/scratchpad/phase6_personality && uv run python build.py <yourfile>.txt --fuzzy
Fix every error and every NEAR hit (rewrite to a genuinely different question). Do not pass --write (the parent does that).
Do NOT call any model API. Write every question yourself, by hand, one by one. No generation scripts/templating/combinatorics.

WHAT TO WRITE: behavioral / situational questions that reveal a trait through what the person actually does or how they react
in a concrete everyday situation. NOT agree-disagree statement items ("I am the life of the party": instruments already cover that).
Good: "At a party where you know no one, what do you usually do?" (choice of concrete behaviors)
      "When plans change at the last minute, how do you react?" (score of concrete reactions)
      "Do you usually finish books you start?" (noul)
Mix per node: about 50% C, 30% S, 20% N.

RULES (docs/01-jev.md §7):
- One snap judgment per question, second person, standalone, ends with "?". Everyday situations (work, school, home, friends, travel, shops, transit, online).
- Choice: 3-8 options (type.* nodes may use exactly 2 pole options), keys snake_case lowercase readable and distinct; add " = description"
  when the key alone is ambiguous. Cover the realistic range; add other/none/it_depends where a real answer could fall outside.
- Score: 3-6 levels, low->high on ONE dimension of the trait, each level a concrete standalone situation/behavior (NOT degree words
  like "sometimes/often/very"), readable alone without its neighbors, rare extreme gets its own level. Levels separated by " ; ".
- Noul: one condition, phrased so "yes" = more of the named behavior; no negated/inverted criteria, no "or" questions.
- No digits anywhere (spell out words, avoid numbers entirely where possible). No " | " or " ; " inside text/options except as separators.
- No politics, no sexual/romantic-physical content, no clinical diagnosis or mental-illness words, no drugs, no named brands/celebs.
- NODE-SPECIFIC: routing is verified by an LLM walking the tree with node descriptions. The question must clearly belong to its node
  and not to a sibling listed in that node's not_for. Re-read the tree descriptions (tree/self.yaml) for your nodes.
- Do not duplicate or lightly paraphrase existing items (authored/*.jsonl, esp. g5_self_lifestyle_traits.jsonl personality nodes and
  g5_p6_love*.jsonl) or items in sibling forks' files. Vary situations; don't reuse a stem pattern more than a few times.

NODE ROUTING HINTS
- big_five.openness: trying unfamiliar food/places/activities, reacting to art/music/beauty, curiosity (looking things up, asking why),
  imagination/daydreaming, noticing own feelings, reaction to unconventional ideas/people/customs. Avoid pure favorites (lifestyle).
- big_five.conscientiousness: keeping promises/deadlines, tidiness of desk/bag/files, following through, checking work, resisting
  distraction, preparing ahead, careful vs hasty choices, duty. Avoid life goals/ambition (motivation) and specific daily schedule items (habits).
- big_five.extraversion: behavior in groups/parties/meetings, talking to strangers, taking charge in a group, pace/energy level,
  thrill/excitement seeking in social fun, cheerfulness, enthusiasm. Avoid explicit introvert/extrovert labels (type.ei).
- big_five.agreeableness: trusting strangers/coworkers, giving in vs standing ground in disagreements, helping unasked, sharing credit,
  modesty about achievements, sympathy for people in trouble, forgiving. Avoid manipulation/callousness (dark_side) and moral right/wrong verdicts.
- big_five.neuroticism: STABLE tendencies across life: how often worry/irritation/low mood/self-consciousness/craving-driven impulses show up,
  how fragile one is under ordinary strain. Frame as "In general / on a typical week / usually". Avoid coping-strategy picks (emotions_stress).
- type.ei: where energy comes from: people/outer world vs solitude/inner world; framed as a choice between two poles
  (e.g. recharge after a hard week: out with friends vs home alone; think out loud vs think first then speak).
- type.sn: concrete facts/details/practical experience vs patterns/meanings/future possibilities, as two poles
  (e.g. following a recipe exactly vs improvising from the idea; noticing details vs the big picture).
- type.tf: impersonal logic/consistency vs personal values/effects on people, as two poles (e.g. giving feedback, settling a group dispute).
- type.jp: settled plans/closure/schedules vs open options/flexibility/spontaneity, as two poles (e.g. packing, weekend plans, deciding early vs late).
- dark_side: narcissism (need for admiration, entitlement), Machiavellian tactics, callousness/low remorse, thrill-seeking recklessness, spite.
- interests: RIASEC work activities: "would you enjoy doing X at work", which task you'd pick. Not hobbies.
- humor_style: what you find funny, how you use humor (bonding, coping, teasing/sarcasm, self-deprecating), joke taste.
- motivation_ambition: drive, grit, competitiveness, procrastination, reaction to success/failure, intrinsic vs extrinsic.
- emotions_stress: coping with a specific stressor, crying, anger handling, expressing/hiding feelings, reacting under pressure, reading emotions.
- risk_decision_style: risk tolerance, gut vs analysis, maximizing vs satisficing, indecision, regret.
- self_concept: self-esteem, confidence, self-rated strengths/weaknesses, identity, how you think others see you.
- self.love.* / self.lifestyle.*: only questions where the answer reveals a trait (e.g. attachment behavior with a partner,
  how you act when a friend cancels, clutter at home, impulse buying, checking phone compulsively), but written so they clearly route
  to that love/lifestyle node (mention the partner/friend/coworker/money/phone/home/travel context explicitly).
