"""Tree nodes for the experiments' new questions (docs/16 pass 3): each set sits under its subject, one leaf per set.
Idempotent. Run from the repo root: `uv run python scripts/experiments/new_nodes.py`."""

from __future__ import annotations

from askjev import db
from askjev.embed import embed, to_pg

NODES = [
    ("world.society.languages.word.probability_words", "Probability and Amount Words",
     "Questions about what words like likely, probably, a few or several mean as numbers."),
    ("world.society.languages.word.adjective_intensity", "Adjective Intensity",
     "Questions about which of two related adjectives is stronger, like good versus great."),
    ("world.society.languages.word.word_humor", "Funny Words",
     "Questions about how funny single English words are on their own."),
    ("world.society.languages.sentence_inference", "What Sentences Imply",
     "Questions about whether one sentence follows from, contradicts, or leaves open another."),
    ("world.money.careers.work_context", "What Jobs Are Like",
     "Questions about the daily conditions of specific occupations: angry customers, weather, deadlines, sitting."),
    ("world.places.countries.life_ladder", "How Countries Rate Their Lives",
     "Questions about each country's average place on the Gallup life ladder."),
    ("world.places.countries.lost_wallets", "Lost Wallets Around the World",
     "Questions about how often lost wallets were returned to their owners in each country."),
    ("world.places.countries.trolley_by_country", "Trolley Dilemmas by Country",
     "Questions about how many people in each country would sacrifice one person to save five."),
    ("world.society.time_use", "How Americans Spend Their Day",
     "Questions about how much time people spend on daily activities like sleep, work and TV."),
    ("world.society.languages.word.scalar_implicature", "What Words Imply",
     "Questions about what a speaker implies by choosing a weaker word, like good suggesting not excellent."),
    ("world.society.media_news.journalism.headline_tests", "Headline A/B Tests",
     "Questions about which of two tested headlines readers clicked more."),
    ("world.health.medicine.health_state_values", "How Bad Is a Health State",
     "Questions about valuing health states against full health and death."),
    ("world.science.physics.color.color_names", "Color Names",
     "Questions about which name fits a color."),
    ("world.science.psychology_neuroscience.cognition.judgment_biases", "Judgment Biases",
     "Questions built to test classic reasoning traps such as conjunctions, base rates and random anchors."),
    ("self.personality.risk_decision_style.guessing_games", "Guessing Games",
     "Questions about strategic number games like guessing two-thirds of the average."),
    ("self.mind.thought_experiments.side_effects", "Side Effects and Intent",
     "Questions about whether a side effect someone didn't care about was brought about intentionally."),
    ("world.health.causes_of_death", "Causes of Death",
     "Questions about how many people die from specific causes."),
    ("world.money.economics.everyday_prices", "Everyday Prices",
     "Questions about what common goods and utilities cost, now and in past years."),
    ("self.mind.consciousness_ai.mind_perception", "Who Has a Mind",
     "Questions comparing characters' capacities to feel and to act."),
    ("world.science.psychology_neuroscience.emotion.colors_of_emotions", "Colors of Emotions",
     "Questions about which colors go with which feelings."),
    ("world.society.languages.word.word_association", "First Word That Comes to Mind",
     "Questions about free association to a cue word."),
    ("self.mind.consciousness_ai.ai_in_daily_life", "Views on AI in Daily Life",
     "Questions about attitudes to AI's use and impact in everyday life."),
]

if __name__ == "__main__":
    with db.connect() as conn:
        have = {r["id"]: r for r in conn.execute("select id, depth from nodes")}
        new = [n for n in NODES if n[0] not in have]
        vecs = embed([f"{label}: {desc}" for _, label, desc in new]) if new else []
        for (nid, label, desc), v in zip(new, vecs):
            parent = nid.rsplit(".", 1)[0]
            not_for = "General questions about the parent topic stay at the parent."
            conn.execute(
                """insert into nodes (id, parent_id, path, depth, hemisphere, label, description, not_for, examples, source,
                     locked, ord, choice_card, embedding)
                   values (%s,%s,(select path from nodes where id=%s) || %s::ltree,%s,%s,%s,%s,%s,'{}','experiments',false,900,%s,%s)
                   on conflict (id) do nothing""",
                (nid, parent, parent, nid.rsplit(".", 1)[-1], have[parent]["depth"] + 1, nid.split(".")[0], label, desc,
                 not_for, db.Jsonb({"label": label, "what": desc, "not_for": not_for}), to_pg(v)))
        conn.commit()
    print(f"added {len(new)} nodes: {[n[0] for n in new]}")
