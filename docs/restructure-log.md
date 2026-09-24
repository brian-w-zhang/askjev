# Restructure log (round 2, Phase 6 scale)

Proposals from `askjev restructure` (clusters) → authored labels → `apply` (Jev re-route + accept rules:
split: each child ≥ 20 questions, median separation ≥ 1.5×, < 10% sibling moves; group: ≥ 80% of member questions
routed to their own group).

- `group__world.places.countries.json`: ACCEPTED group of world.places.countries: {'agreement': 1.0, 'n': 80, 'groups': {'africa': 9, 'asia': 16, 'europe': 8, 'americas': 6, 'oceania': 1}}
- `group__world.science.astronomy_space.json`: ACCEPTED group of world.science.astronomy_space: {'agreement': 0.9838709677419355, 'n': 62, 'groups': {'solar_system_bodies': 15, 'stars_cosmos': 11, 'rockets_spaceflight': 5}}
- `group__world.science.chemistry.json`: ACCEPTED group of world.science.chemistry: {'agreement': 1.0, 'n': 66, 'groups': {'elements_metals': 15, 'chemistry_concepts': 18}}
- `group__world.science.physics.json`: ACCEPTED group of world.science.physics: {'agreement': 1.0, 'n': 70, 'groups': {'matter_energy': 11, 'particles_forces': 13, 'physicists': 6, 'time_units': 5}}
- `group__world.tech.engineering_inventions.json`: ACCEPTED group of world.tech.engineering_inventions: {'agreement': 0.9426229508196722, 'n': 122, 'groups': {'energy_power': 10, 'materials': 10, 'agriculture_living': 8, 'infrastructure': 5, 'machines_engines': 11, 'optics_instruments': 11, 'electrical_general': 6}}
- `split__self.lifestyle.would_you_rather.json`: ACCEPTED split of self.lifestyle.would_you_rather: {'counts': {'pain_danger_death': 220, 'characters_pop_culture': 180, 'food_gross_outs': 129, 'body_appearance': 140}, 'median_separation': 49.0, 'sibling_move_rate': 0.0}
- `split__self.love.dating_attraction.json`: ACCEPTED split of self.love.dating_attraction: {'counts': {'dating_rules_of_thumb': 156, 'dating_choices': 314}, 'median_separation': 99.0, 'sibling_move_rate': 0.0}
- `split__self.love.etiquette_social_norms.json`: ACCEPTED split of self.love.etiquette_social_norms: {'counts': {'everyday_manners': 267, 'social_rules_of_thumb': 1401}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.love.family_parenting.json`: ACCEPTED split of self.love.family_parenting: {'counts': {'family_rules_of_thumb': 753, 'family_situations': 333}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.love.friendship.json`: ACCEPTED split of self.love.friendship: {'counts': {'friendship_habits': 134, 'friend_conflicts': 103, 'friendship_rules_of_thumb': 435}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.love.romance_partnership.json`: ACCEPTED split of self.love.romance_partnership: {'counts': {'relationship_rules_of_thumb': 529, 'relationship_choices': 405}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.love.workplace_community.json`: ACCEPTED split of self.love.workplace_community: {'counts': {'community_rules_of_thumb': 142, 'neighbors_roommates': 65, 'coworkers_contacts': 159}, 'median_separation': 99.0, 'sibling_move_rate': 0.0}
- `split__self.mind.big_questions.json`: ACCEPTED split of self.mind.big_questions: {'counts': {'meaning_human_nature': 99, 'free_will_reality': 67}, 'median_separation': 99.0, 'sibling_move_rate': 0.0}
- `split__self.mind.epistemics.json`: ACCEPTED split of self.mind.epistemics: {'counts': {'evidence_sources': 77, 'knowledge_certainty': 129}, 'median_separation': 32.16666666666667, 'sibling_move_rate': 0.0}
- `split__self.mind.luck_fate.json`: ACCEPTED split of self.mind.luck_fate: {'counts': {'luck_and_fate': 82, 'superstitions_omens': 102}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.mind.thought_experiments.json`: ACCEPTED split of self.mind.thought_experiments: {'counts': {'mind_identity_scenarios': 179, 'classic_puzzles': 47}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.mind.time_mortality.json`: ACCEPTED split of self.mind.time_mortality: {'counts': {'death_legacy': 86, 'aging_lifespan': 69}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.personality.big_five.agreeableness.json`: ACCEPTED split of self.personality.big_five.agreeableness: {'counts': {'kindness_cooperation': 84, 'trust_modesty_temper': 71}, 'median_separation': 49.0, 'sibling_move_rate': 0.0}
- `split__self.personality.big_five.conscientiousness.json`: ACCEPTED split of self.personality.big_five.conscientiousness: {'counts': {'drive_self_discipline': 63, 'order_caution': 87}, 'median_separation': 99.0, 'sibling_move_rate': 0.0}
- `split__self.personality.big_five.extraversion.json`: ACCEPTED split of self.personality.big_five.extraversion: {'counts': {'body_language_voice': 42, 'sociability_energy': 205}, 'median_separation': 31.666666666666668, 'sibling_move_rate': 0.0}
- `split__self.personality.big_five.neuroticism.json`: ACCEPTED split of self.personality.big_five.neuroticism: {'counts': {'temper_moodiness': 65, 'fear_worry': 24, 'self_consciousness': 29, 'impulses_coping': 30}, 'median_separation': 99.0, 'sibling_move_rate': 0.0}
- `split__self.personality.big_five.openness.json`: ACCEPTED split of self.personality.big_five.openness: {'counts': {'ideas_imagination': 137, 'convention_politics': 35}, 'median_separation': 32.333333333333336, 'sibling_move_rate': 0.0}
- `split__self.personality.emotions_stress.json`: ACCEPTED split of self.personality.emotions_stress: {'counts': {'mindfulness_awareness': 47, 'coping_expressing': 31, 'recent_stress_mood': 37, 'empathy_social_reading': 41}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.personality.humor_style.json`: ACCEPTED split of self.personality.humor_style: {'counts': {'joke_ratings': 100, 'humor_habits_tastes': 59}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.values.animals_environment.json`: ACCEPTED split of self.values.animals_environment: {'counts': {'animal_rules_of_thumb': 122, 'animal_nature_dilemmas': 28}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.values.everyday_ethics.family_conflicts.json`: ACCEPTED split of self.values.everyday_ethics.family_conflicts: {'counts': {'family_stories': 2548, 'family_action_judgments': 506}, 'median_separation': 99.0, 'sibling_move_rate': 0.0}
- `split__self.values.everyday_ethics.friends_dating_social.json`: ACCEPTED split of self.values.everyday_ethics.friends_dating_social: {'counts': {'social_stories': 4486, 'quick_social_judgments': 789}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.values.everyday_ethics.json`: REJECTED split of self.values.everyday_ethics: {'counts': {'whos_in_the_wrong': 995, 'action_judgments': 3182, 'moral_rules_of_thumb': 618}, 'median_separation': 100.0, 'sibling_move_rate': 0.85}
- `split__self.values.honesty_trust.json`: ACCEPTED split of self.values.honesty_trust: {'counts': {'honesty_rules_of_thumb': 165, 'honesty_dilemmas': 27}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.values.life_values.json`: ACCEPTED split of self.values.life_values: {'counts': {'personal_priorities': 24, 'life_rules_of_thumb': 223}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__self.values.moral_foundations.care.json`: ACCEPTED split of self.values.moral_foundations.care: {'counts': {'wellbeing_help_seeking': 254, 'safety_fear': 82}, 'median_separation': 99.0, 'sibling_move_rate': 0.0}
- `split__world.arts.books.json`: ACCEPTED split of world.arts.books: {'counts': {'authors': 485, 'specific_books': 794}, 'median_separation': 23.0, 'sibling_move_rate': 0.0}
- `split__world.arts.film.json`: ACCEPTED split of world.arts.film: {'counts': {'specific_films': 688, 'filmmakers_actors': 254}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__world.arts.music.json`: ACCEPTED split of world.arts.music: {'counts': {'musicians_bands': 1014, 'albums_songs': 532}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__world.arts.television.json`: ACCEPTED split of world.arts.television: {'counts': {'cartoons_anime': 245, 'tv_series': 506}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__world.future.sports_entertainment.json`: ACCEPTED split of world.future.sports_entertainment: {'counts': {'entertainment': 58, 'sports': 92}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__world.future.technology.json`: ACCEPTED split of world.future.technology: {'counts': {'tech_leaders': 36, 'emerging_tech': 23, 'companies_products': 71}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__world.places.travel.json`: ACCEPTED split of world.places.travel: {'counts': {'visas_passports': 48, 'transport_lodging': 114}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}
- `split__world.society.crime_law.json`: ACCEPTED split of world.society.crime_law: {'counts': {'gun_laws': 90, 'legal_where': 152}, 'median_separation': 99.0, 'sibling_move_rate': 0.0}
- `split__world.sports.soccer.json`: ACCEPTED split of world.sports.soccer: {'counts': {'world_cup': 142, 'rules': 37}, 'median_separation': 100.0, 'sibling_move_rate': 0.0}

**Accepted 39, rejected 1, skipped (unlabeled) 26.**
