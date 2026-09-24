"""Early indicator readouts from the answered corpus (not findings yet: no paraphrase universes or repeats).
Writes docs/findings-preview.md. Indicators, never grades (CLAUDE.md)."""
import collections
import math
import statistics as st

import numpy as np

from askjev import db
from askjev.config import ROOT
from askjev.measure import ece, top, tvd

L = ["# Findings preview (early indicators, base universe only)", "",
     "Computed from the answered MVP corpus. These are *indicators*, not grades. Effects are compared against the",
     "measured noise floor (±0.03 Noul/Score, ±0.08 Choice top-p). Nothing here is a finding until it survives",
     "rewording universes and repeats (docs/05-experiments.md).", ""]
with db.connect() as conn:
    # 1. calibration by L1 on ground-truth questions
    rows = conn.execute("""select split_part(q.node_id,'.',1)||'.'||split_part(q.node_id,'.',2) l1, q.hemisphere, m.p_top, m.correct
                           from questions q join question_meta m on m.question_id=q.id where m.correct is not null""").fetchall()
    by = collections.defaultdict(list)
    for r in rows:
        by[r["l1"]].append((r["p_top"], r["correct"]))
    L += ["## 1. Calibration where there is ground truth", "", "| L1 | n | accuracy | mean confidence (p_top) | ECE |", "|---|---|---|---|---|"]
    for k, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
        if len(v) < 40:
            continue
        acc = sum(c for _, c in v) / len(v); conf = sum(p for p, _ in v) / len(v); e = ece(v)
        L.append(f"| {k} | {len(v)} | {acc:.2f} | {conf:.2f} | {e:.3f} |")
    allv = [(r["p_top"], r["correct"]) for r in rows]
    L += ["", f"All ground-truth questions: n={len(allv)}, accuracy {sum(c for _,c in allv)/len(allv):.2f}, "
          f"mean confidence {sum(p for p,_ in allv)/len(allv):.2f}, ECE {ece(allv):.3f}.", ""]

    # 2. position bias under shuffles (Choice): probability mass on the first-listed option vs uniform
    sh = conn.execute("""select a.distribution, a.option_order from probes p join answers a on a.probe_id=p.id
                         where p.variant_kind='shuffle' and a.option_order is not null""").fetchall()
    first_mass, uniform = [], []
    for r in sh:
        order = r["option_order"]
        if not order or len(order) < 2:
            continue
        first_mass.append(r["distribution"].get(order[0], 0.0))
        uniform.append(1 / len(order))
    L += ["## 2. Position bias (Choice, option shuffles)", "",
          f"Mean probability on whichever option is listed first: **{st.mean(first_mass):.3f}** vs {st.mean(uniform):.3f} if position",
          f"didn't matter (n={len(first_mass)} shuffled probes). Excess: {st.mean(first_mass)-st.mean(uniform):+.3f}.", ""]

    # 3. stability by hemisphere/kind
    stab = conn.execute("""select coalesce(q.kind, 'machine:'||q.shape) k, avg(m.stability) s, count(*) n,
                                  avg((m.stability < 0.67)::int) frag
                           from questions q join question_meta m on m.question_id=q.id where m.stability is not null group by 1 order by 2""").fetchall()
    L += ["## 3. Shuffle stability by kind (share of shuffles keeping the same top answer)", "", "| kind | n | mean stability | fragile (<0.67) |", "|---|---|---|---|"]
    for r in stab:
        L.append(f"| {r['k']} | {r['n']} | {r['s']:.3f} | {100*r['frag']:.1f}% |")
    L.append("")

    # 4. frame gap: self vs most-people
    fg = conn.execute("""select coalesce(q.kind,'?') k, avg(m.frame_gap) g, avg((m.top <> m.top_h)::int) flip, count(*) n
                         from questions q join question_meta m on m.question_id=q.id where m.frame_gap is not null group by 1 order by 2 desc""").fetchall()
    L += ["## 4. Frame gap: Jev's default vs its 'most people' answer", "", "| kind | n | mean TVD | top answer differs |", "|---|---|---|---|"]
    for r in fg:
        L.append(f"| {r['k']} | {r['n']} | {r['g']:.3f} | {100*r['flip']:.1f}% |")
    L.append("")

    # 5. human gap by source (human frame vs real distributions)
    hg = conn.execute("""select q.source, count(*) n, avg(m.human_gap) g,
                                avg((m.top_h = (select key from jsonb_each_text(h.distribution) e(key,val) order by val::float desc limit 1))::int) agree
                         from questions q join question_meta m on m.question_id=q.id
                         join lateral (select distribution from human_dists where question_id=q.id order by n desc nulls last limit 1) h on true
                         where m.human_gap is not null group by 1 order by 3""").fetchall()
    L += ["## 5. Human gap: Jev's 'most people' answer vs real human distributions", "",
          "| source | n | mean TVD (pooled populations) | Jev's top = humans' top (largest population) |", "|---|---|---|---|"]
    for r in hg:
        L.append(f"| {r['source']} | {r['n']} | {r['g']:.3f} | {100*r['agree']:.1f}% |")
    L.append("")

    # 6. metacognition: does self-assessed ambiguity predict instability?
    mc = conn.execute("""select m.ambiguous, m.stability, m.disagreement, m.entropy from question_meta m
                         where m.ambiguous is not null and m.stability is not null""").fetchall()
    a = np.array([r["ambiguous"] for r in mc]); s = np.array([r["stability"] for r in mc])
    dis = np.array([r["disagreement"] or 0 for r in mc]); ent = np.array([r["entropy"] or 0 for r in mc])
    def corr(x, y):
        return float(np.corrcoef(x, y)[0, 1]) if len(x) > 3 else float("nan")
    L += ["## 6. Metacognition (does Jev know where it's jagged?)", "",
          f"- corr(Jev's own 'ambiguous' rating, shuffle stability) = **{corr(a, s):+.3f}** (n={len(mc)}; negative = it anticipates its fragility)",
          f"- corr(Jev's 'people would disagree' rating, its own answer entropy) = **{corr(dis, ent):+.3f}**", ""]

    # 7. defaults: Big Five (IPIP markers, self frame)
    b5 = conn.execute("""select q.node_id, avg((select sum((k::int) * v::float) from jsonb_each_text(a.distribution) e(k,v))) mean_level,
                                count(*) n, q.meta->>'keyed' keyed
                         from questions q join probes p on p.question_id=q.id and p.variant_kind='base' and p.frame='self'
                         join answers a on a.probe_id=p.id
                         where q.source='ipip' and q.node_id like 'self.personality.big_five.%' group by q.node_id, q.meta->>'keyed' order by 1,4""").fetchall()
    L += ["## 7. Defaults: IPIP Big Five items (Jev's self frame; mean level 0-4, by keying)", "", "| trait | keyed | n items | mean level |", "|---|---|---|---|"]
    for r in b5:
        L.append(f"| {r['node_id'].rsplit('.',1)[-1]} | {r['keyed']} | {r['n']} | {r['mean_level']:.2f} |")
    L += ["", "Reported as defaults, not preferences; only claimable once they survive rewording universes."]
(ROOT / "docs" / "findings-preview.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
