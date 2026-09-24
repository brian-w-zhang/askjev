# Routing evaluation (held-out, 332 questions, mode=fast)

Each question was written for a known node (authored/routing_eval.jsonl, not shown to Jev) and placed from the root
by Jev beam search (K=3). *lineage* = placed at an ancestor or descendant of the intended node.

**All:** exact 84.9% | lineage 2.7% | same_l1 4.5% | same_hemisphere 6.6% | wrong_hemisphere 1.2%  
**Correct branch (exact + lineage): 87.7%**; low separation (<1.5x): 11
- machine (111): exact 84.7% | lineage 2.7% | same_l1 3.6% | same_hemisphere 8.1% | wrong_hemisphere 0.9%
- self (110): exact 76.4% | lineage 4.5% | same_l1 8.2% | same_hemisphere 10.0% | wrong_hemisphere 0.9%
- world (111): exact 93.7% | lineage 0.9% | same_l1 1.8% | same_hemisphere 1.8% | wrong_hemisphere 1.8%
- difficulty=boundary (85): exact 85.9% | lineage 2.4% | same_l1 2.4% | same_hemisphere 9.4% | wrong_hemisphere 0.0%
- difficulty=easy (247): exact 84.6% | lineage 2.8% | same_l1 5.3% | same_hemisphere 5.7% | wrong_hemisphere 1.6%

## Most confused (intended → placed)
- self.love.friendship → self.values.everyday_ethics.friends_dating_social (2)
- machine.documents.taxonomy_classification → machine.support.intent_topic (2)
- world.food.dishes_ingredients → self.lifestyle.food_preferences (1)
- world.places.physical_geography → world.nature.geology (1)
- world.science.physics → world.science.astronomy_space (1)
- world.tech.social_media → world.money.careers (1)
- world.history.figures → world.history.wars_battles (1)
- world.money.personal_finance → self.lifestyle.money_habits (1)
- self.personality.big_five.conscientiousness → self.lifestyle.habits_routines (1)
- self.personality.big_five.extraversion → self.personality.type.ei (1)
- self.personality.big_five.neuroticism → self.personality.emotions_stress (1)
- self.personality.dark_side → self.values.honesty_trust (1)
- self.personality.dark_side → self.values.moral_foundations.proportionality (1)
- self.lifestyle.money_habits → self.personality.risk_decision_style (1)
- self.values.fairness_justice → self.values.moral_foundations.proportionality (1)
- self.values.life_values → self.personality (1)
- self.values.life_values → self.love.family_parenting (1)
- self.values.honesty_trust → self.values.everyday_ethics (1)
- self.values.everyday_ethics → self.love.romance_partnership (1)
- self.love.dating_attraction → self.values.everyday_ethics.friends_dating_social (1)
- self.mind.big_questions → self.personality.big_five.agreeableness (1)
- self.mind.big_questions → self.mind.thought_experiments (1)
- self.mind.consciousness_ai → world.tech.ai (1)
- self.mind.epistemics → self.mind.memories_life_story (1)
- self.mind.time_mortality → self.mind.thought_experiments (1)
