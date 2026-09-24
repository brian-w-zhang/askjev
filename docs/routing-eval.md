# Routing evaluation (held-out, 332 questions, mode=beam)

Each question was written for a known node (authored/routing_eval.jsonl, not shown to Jev) and placed from the root
by Jev beam search (K=3). *lineage* = placed at an ancestor or descendant of the intended node.

**All:** exact 90.1% | lineage 0.6% | same_l1 1.8% | same_hemisphere 6.6% | wrong_hemisphere 0.9%  
**Correct branch (exact + lineage): 90.7%**; low separation (<1.5x): 57
- machine (111): exact 87.4% | lineage 0.0% | same_l1 0.9% | same_hemisphere 10.8% | wrong_hemisphere 0.9%
- self (110): exact 87.3% | lineage 1.8% | same_l1 2.7% | same_hemisphere 7.3% | wrong_hemisphere 0.9%
- world (111): exact 95.5% | lineage 0.0% | same_l1 1.8% | same_hemisphere 1.8% | wrong_hemisphere 0.9%
- difficulty=boundary (85): exact 90.6% | lineage 1.2% | same_l1 0.0% | same_hemisphere 8.2% | wrong_hemisphere 0.0%
- difficulty=easy (247): exact 89.9% | lineage 0.4% | same_l1 2.4% | same_hemisphere 6.1% | wrong_hemisphere 1.2%

## Most confused (intended → placed)
- self.love.etiquette_social_norms → self.values.everyday_ethics (2)
- world.science.physics → world.science.astronomy_space (1)
- world.tech.internet_web → world.society.media_news (1)
- world.history.figures → world.history.wars_battles (1)
- world.society.crime_law → world.history.figures (1)
- world.money.personal_finance → self.lifestyle.money_habits (1)
- self.personality.big_five.conscientiousness → self.lifestyle.habits_routines (1)
- self.personality.type.tf → self.values.moral_foundations.care (1)
- self.personality.dark_side → self.values.honesty_trust (1)
- self.personality.dark_side → self.values.moral_foundations.proportionality (1)
- self.personality.interests → self.lifestyle.home_living (1)
- self.values.honesty_trust → self.values.everyday_ethics (1)
- self.love.friendship → self.values.moral_foundations.loyalty (1)
- self.mind.consciousness_ai → world.tech.ai (1)
- self.mind.time_mortality → self.mind.thought_experiments (1)
- self.mind.happiness_wellbeing → self.mind.big_questions (1)
- machine.ai_systems.hallucination_citation → machine.support.response_verification (1)
- machine.search.recommendation → machine.commerce (1)
- machine.research.qualitative_coding → machine.support.intent_topic (1)
- machine.research.qualitative_coding → machine.support.churn_refund (1)
- machine.finance.fraud_indicators → machine.support.churn_refund (1)
- machine.people.resume_match → machine.people.competency_evidence (1)
- machine.commerce.demand_signals → machine.support.intent_topic (1)
- machine.documents.entity_resolution → machine.commerce.ad_alignment (1)
- machine.documents.entity_resolution → machine.commerce.attribute_extraction (1)
