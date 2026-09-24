# Coverage test: 1000 Quora questions (never used to build the tree)

Each question was placed from the root by Jev beam search. *Homed* = placed at depth ≥ 3 (an L2 or deeper) with
path confidence ≥ 0.5. Quora includes many open how-to questions; only topical placement is measured here.

**Homed: 89.5%** (target: < 5% orphans at L2 → ≥ 95% homed)  
Confidence ≥ 0.5: 97.4%

Final depth: L0=3, L0=27, L1=65, L2=899, L3=6
Hemisphere: world=845, self=141, machine=11, root=3

Top L1s: world.society=177, world.tech=175, world.money=126, world.science=83, world.health=72, world.arts=63, self.love=48, world.places=39, self.lifestyle=29, world.sports=27, self.mind=27, world.history=25

## Examples not homed
- 'Nodia & Company: What are the price details of the GATE Electrical 4 volume book of R.K.Kanodia?' → machine.commerce.attribute_extraction (0.41)
- 'Why do we need to be hurt when we love?' → self.love (0.7)
- 'I have a text in Arabic please translate?' → machine.support.intent_topic (0.45)
- 'Where should I start learning?' → self (0.55)
- 'Popular handyman services?' → world (0.59)
- 'How do you think they weighted elephant in olden times?' → world.history (0.76)
- 'What is trial balance and why is it prepared?' → world.money (0.79)
- 'What are some examples of chemical adaptations in animals from the tropical forest?' → world.nature (0.89)
- 'Why did you lose your virginity?' → self (0.56)
- 'Have you ever seen Quora.vn?' → world.tech.social_media (0.44)
- 'How do you measure success in a framework?' → world (0.58)
- 'How can anyone believe in the "worst man made concept" such as God, and religion?' → self.mind (0.52)
- "Company 3 months back, im currently in training. Now, I'm facing a lot of health issues, it's becoming difficult to be there. what should I do?" → self.lifestyle (0.39)
- 'Are you allergic to something?' → self (0.63)
- "What's the average number of lies humans speak per day?" → world.society (0.73)
