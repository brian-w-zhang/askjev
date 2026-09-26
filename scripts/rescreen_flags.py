"""Hidden-question audit (docs/03-questions.md §6): the screen hid anything Jev put at p >= 0.5 on two broad questions
("contested political or partisan issue … or similar", "sexual content, self-harm, or graphic violence"), which caught
mentions of death, illness, places and government. This re-asks Jev the documented policy exactly, with a 0.7 bar and a
keyword backstop, and unhides what no longer qualifies. Flags are never deleted: an unhidden question keeps its old flag
under meta.unflagged.

  uv run python scripts/rescreen_flags.py --moral-machine        # unhide Moral Machine (§6 hides only Criminal/Homeless/Social Status)
  uv run python scripts/rescreen_flags.py --sample 1000          # re-screen a stratified sample, write a report, change nothing
  uv run python scripts/rescreen_flags.py --apply                # re-screen every hidden political/sensitive question and unhide
"""

import argparse
import asyncio
import random
import re
from collections import Counter
from pathlib import Path

from askjev import db
from askjev.answer import NEUTRAL_STATE, _group_requests, _run, subject
from askjev.jev import answers, gateway_question

BAR = 0.7
REPORT = Path("data/logs/rescreen_sample.md")
POLITICAL = ("Is the question in `subject` about one of these contested political topics: elections, political parties, "
             "a named politician, abortion, guns, immigration, LGBTQ policy, religion versus the state, race policy, "
             "Israel and Palestine, or Russia and Ukraine?")
SENSITIVE = ("Does the question in `subject` contain sexual content, self-harm, or abuse, or describe violence or injury "
             "in graphic detail? A plain mention of death, illness, crime or war does not count.")
BACKSTOP = re.compile(
    r"\b(elections?|electoral|ballot|democrats?|republicans?|gop|labou?r party|tories|conservative party|trump|biden|"
    r"obama|clinton|putin|zelensk\w*|netanyahu|hamas|abortion|pro-?life|pro-?choice|gun control|second amendment|"
    r"immigra\w*|refugees?|transgender|gay marriage|same-sex marriage|israel\w*|palestin\w*|gaza|west bank|"
    r"ukrain\w*|crimea|porn\w*|sex(ual|ually)?|nude|naked|suicid\w*|self-harm|rape\w*|molest\w*)\b", re.I)


def hidden_rows(limit_ids=None):
    with db.connect() as c:
        return c.execute(
            """select id, text, options, state, hemisphere, source, flags from questions
               where not display_ok and source <> 'moral_machine'
                 and (flags && array['political','sensitive']) and not (flags && array['duplicate','biographical'])"""
            + (" and id = any(%s)" if limit_ids else ""), (limit_ids,) if limit_ids else ()).fetchall()


def rescreen(rows) -> dict[str, dict]:
    items = []
    for q in rows:
        subj = subject(q)
        items.append((f"{q['id']}__pol", NEUTRAL_STATE, gateway_question("noul", {"question": POLITICAL, "subject": subj})))
        items.append((f"{q['id']}__sens", NEUTRAL_STATE, gateway_question("noul", {"question": SENSITIVE, "subject": subj})))
    res = asyncio.run(_run(_group_requests(items)))
    out: dict[str, dict] = {}
    for resp in res.values():
        if "error" in resp:
            continue
        for key, a in answers(resp).items():
            qid, name = key.split("__", 1)
            out.setdefault(qid, {})[name] = a.p_yes
    return out


def verdict(q, p) -> list[str]:
    keep = []
    text = f"{q['text']} {q['options'] or ''} {q['state'] or ''}"
    if p.get("pol", 0) >= BAR or ("political" in q["flags"] and BACKSTOP.search(text)):
        keep.append("political")
    if p.get("sens", 0) >= BAR or ("sensitive" in q["flags"] and BACKSTOP.search(text)):
        keep.append("sensitive")
    return keep


def unhide(ids_old: list[tuple[str, list[str]]], why: str) -> int:
    with db.connect() as c:
        for qid, old in ids_old:
            c.execute(
                """update questions set display_ok = true,
                     flags = array(select f from unnest(flags) f where f not in ('political','sensitive')),
                     meta = meta || jsonb_build_object('unflagged', %s::jsonb, 'unflag_reason', %s::text)
                   where id = %s""", (db.Jsonb(old), why, qid))
        c.commit()
    return len(ids_old)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--moral-machine", action="store_true")
    ap.add_argument("--sample", type=int)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.moral_machine:
        with db.connect() as c:
            rows = c.execute("""select id, flags from questions where source='moral_machine' and not display_ok
                                and not (flags && array['political','duplicate','biographical'])""").fetchall()
        n = unhide([(r["id"], [f for f in r["flags"] if f in ("political", "sensitive")]) for r in rows],
                   "Moral Machine is shown per 03-questions §6 (only Criminal/Homeless/Social Status are hidden)")
        print(f"moral machine: unhid {n}")
    if a.sample or a.apply:
        rows = hidden_rows()
        if a.sample:
            rows = random.Random(7).sample(rows, min(a.sample, len(rows)))
        p = rescreen(rows)
        flips, stays = [], []
        for q in rows:
            if q["id"] not in p:
                continue
            keep = verdict(q, p[q["id"]])
            (stays if keep else flips).append((q, p[q["id"]], keep))
        if a.apply:
            n = unhide([(q["id"], [f for f in q["flags"] if f in ("political", "sensitive")]) for q, _, _ in flips],
                       f"narrow re-screen (03-questions §6 topics, p >= {BAR}, keyword backstop) found no qualifying content")
            print(f"re-screened {len(p)}/{len(rows)}; unhid {n}, kept hidden {len(stays)}")
        else:
            by_src = Counter(q["source"] for q, _, _ in flips)
            lines = [f"# Hidden-question re-screen sample ({len(p)} of {len(rows)} screened)", "",
                     f"Would unhide **{len(flips)}** ({len(flips) / max(len(p), 1):.0%}); would keep hidden {len(stays)}.", "",
                     "Unhides by source: " + ", ".join(f"{s} {n}" for s, n in by_src.most_common(15)), "",
                     "## Would unhide (60 random)", ""]
            for q, pp, _ in random.Random(1).sample(flips, min(60, len(flips))):
                lines.append(f"- [{q['source']}; was {','.join(q['flags'])}; pol {pp.get('pol', 0):.2f} sens {pp.get('sens', 0):.2f}] {q['text'][:160]}")
            lines += ["", "## Would keep hidden (40 random)", ""]
            for q, pp, keep in random.Random(2).sample(stays, min(40, len(stays))):
                lines.append(f"- [{q['source']}; {','.join(keep)}; pol {pp.get('pol', 0):.2f} sens {pp.get('sens', 0):.2f}] {q['text'][:160]}")
            REPORT.write_text("\n".join(lines) + "\n")
            print(f"sample: would unhide {len(flips)} / keep {len(stays)}; report {REPORT}")


if __name__ == "__main__":
    main()
