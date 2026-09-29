import type { ReactNode } from "react";
import Link from "next/link";
import type { PortraitData, QuizItem } from "./types";
import { compact, int, label, optionLabel } from "./fmt";
import { Card, Nav, fill } from "./ui";
import { HBars } from "./charts";
import { Quiz, QuizProvider, YouVsJev } from "./Quiz";
import ChapterRail from "./ChapterRail";
import { COPY, LIMITS } from "./copy";
import Story, { CHAPTERS } from "./story/Story";
import "../experiments/experiments.css";
import "./story/story.css";

// The self-portrait (docs/11-portrait.md): chapters built from the experiments (story/Story.tsx), then the reader's
// turn (you vs Jev), the limits and the fine print. Every number is read from portrait.json: the story from the
// experiments' result files, the rest from the claims ledger.

type CFn = (id: string) => PortraitData["claims"][string];
const pct = (v: number) => `${Math.round(v * 100)}%`;

export default function Portrait({ d, showIds = false }: { d: PortraitData; showIds?: boolean }) {
  const C: CFn = (id) => d.claims[id];
  const fam = C("landscape_families");
  const total: number = fam.n;
  const shown = total - (C("landscape_hidden").n as number);
  const anch = C("landscape_anchoring").anchoring as { truth: number; humans: number; neither: number };
  const common = { humans: pct(anch.humans), authored: pct(1 - (C("landscape_real_vs_authored").effect as number)) };
  const quiz: QuizItem[] = C("page_quiz_debates").examples.map((id) => d.rows[id]).filter((r) => r?.human && r.jev).map((r) => ({
    id: r.id, text: r.text, domain: "debate", options: Object.keys(r.jev!).map((k) => ({ key: k, label: optionLabel(r, k) })),
    jev: r.jev!, human: r.human!.dist, n: r.human!.n,
  }));
  const chapters = [...CHAPTERS, { id: "you", name: "your turn" }];
  if (!d.story) return <main style={{ padding: 32 }}>No story data. Run scripts/portrait/story.py, then export_page.py.</main>;
  return (
    <QuizProvider items={quiz}>
      <Nav here="portrait" />
      <ChapterRail chapters={chapters} />
      <Story s={d.story} nQuestions={shown} />
      <Card id="you" field="pink" c={{ ...COPY.you, kicker: "10 · your turn", title: "You vs Jev: guess what people said, then see where Jev landed." }} showId={showIds} claims={[C("page_quiz_debates")]}>
        <div className="st-quiz"><Quiz /><YouVsJev /></div>
      </Card>
      <Card id="limits" field="paper" c={COPY.limits} showId={showIds}>
        <ol className="limits">{LIMITS.map((l) => <li key={l}>{fill(l, common)}</li>)}</ol>
      </Card>
      <section id="closer" className="card" data-f="ink">
        <div className="card-in">
          <div className="card-main">
            <h2 className="card-t xl">That&rsquo;s the short tour.</h2>
            <p className="card-b">Every chapter above is a handful of the {d.story.n_experiments} experiments. Each has a full case
              study: the data, how Jev was asked, what could bias it, and every question behind the result.</p>
            <p className="links"><Link href="/portrait/atlas" prefetch={false}>all {d.story.n_experiments} experiments, in the atlas →</Link> <a href="#fineprint">the full fine print ↓</a></p>
          </div>
        </div>
      </section>
      <FinePrint C={C} d={d} total={total} shown={shown} />
    </QuizProvider>
  );
}

/* ---------------------------------------------------------------- fine print, in full */

const P = ({ l, children }: { l: string; children: ReactNode }) => <div className="fp"><span className="pt-label">{l}</span>{children}</div>;

function FinePrint({ C, d, total, shown }: { C: CFn; d: PortraitData; total: number; shown: number }) {
  const bill = C("pipeline_bill");
  const pl = C("pipeline_placement");
  const M: Record<string, string> = { deterministic: "the source's own labels", template_split: "split by template", jev_fast: "Jev, fast walk", jev: "Jev, full walk", meta_split: "split by metadata", split: "crowded topic split", vital_topic: "topic list", reroute: "re-routed", regroup: "regrouped" };
  const methods = Object.entries(pl.methods as Record<string, number>).sort((a, b) => b[1] - a[1]);
  return (
    <section id="fineprint" className="fineprint">
      <h2>The full fine print</h2>
      <P l="what this is"><p>A playful self-portrait of one model, from {int(total)} questions it answered ({int(shown)} of them shown on the map). Every number comes from a claims ledger ({int(Object.keys(d.claims).length)} entries), each with its query, n, interval, noise floor and example questions chosen by a fixed seed. Cards built on questions I picked by hand say so.</p></P>
      <P l="evidence"><p>Most cards rest on published instruments and real answers: the IPIP Big Five markers against {int(C("bigfive_neuroticism").human_n)} online respondents, the Moral Machine, the Moral Foundations Questionnaire, real gambles, crowd votes, and labeled tasks. The trait gaps rest on questions I wrote to measure one trait each, kept only where an audit found their scales in order 90%+ of the time. Themes found by embedding similarity live in the atlas.</p></P>
      <P l="intervals and noise"><p>90% intervals resample whole sources, so one big dataset can&rsquo;t manufacture confidence. Differences under ±0.03 (yes/no, ratings) or ±0.08 (pick-one) are treated as noise.</p></P>
      <P l="robustness"><p>Every question was asked as written, for “most people”, with options reordered, and with rating scales reversed. No rewordings were sent for this page.</p></P>
      <P l="how the map was filed">
        <HBars max={methods[0][1]} fmt={(v) => compact(v)} rows={methods.map(([k, v]) => ({ key: k, label: M[k] ?? label(k), v, jev: k.startsWith("jev") }))} />
      </P>
      <P l="the bill"><p>{int(bill.n)} Jev calls, each cached by request hash and never re-sent, median {int(bill.median_ms)} ms. Jev is the only model called. Everything else (the written questions, the audits, the words on this page) was made by me with Claude, with a local embedding model for similarity.</p></P>
      <P l="what stays off"><p>Contested politics, sensitive and harmful questions, and questions about private people were answered but aren&rsquo;t shown. TypeSafe&rsquo;s own documented limits aren&rsquo;t presented as discoveries. Jev version: <code>{d.version}</code>.</p></P>
      <p className="fp-end">askjev · a toy by Brian Zhang · not affiliated with TypeSafe · indicators, not a benchmark</p>
    </section>
  );
}
