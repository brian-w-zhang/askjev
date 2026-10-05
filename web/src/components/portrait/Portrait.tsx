import type { ReactNode } from "react";
import Link from "next/link";
import type { PortraitData, QuizItem } from "./types";
import { compact, int, label, optionLabel } from "./fmt";
import { Nav, fill } from "./ui";
import { HBars } from "./charts";
import { QuizProvider } from "./Quiz";
import ChapterRail from "./ChapterRail";
import { LIMITS } from "./copy";
import Story, { CHAPTERS } from "./story/Story";
import "../experiments/experiments.css";
import "./story/story.css";

// The self-portrait (docs/11-portrait.md): chapters built from the experiments (story/Story.tsx), then the reader's
// turn (you vs Jev), the closer and the fine print. Every number is read from portrait.json: the story from the
// experiments' result files, the rest from the claims ledger.

type CFn = (id: string) => PortraitData["claims"][string];
const pct = (v: number) => `${Math.round(v * 100)}%`;

export default function Portrait({ d }: { d: PortraitData }) {
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
  const chapters = CHAPTERS;
  if (!d.story) return <main style={{ padding: 32 }}>No story data. Run scripts/portrait/story.py, then export_page.py.</main>;
  return (
    <QuizProvider items={quiz}>
      <Nav here="portrait" />
      <ChapterRail chapters={chapters} />
      <Story s={d.story} nQuestions={shown} />
      <section id="closer" className="card" data-f="ink">
        <div className="card-in">
          <div className="card-main">
            <h2 className="card-t xl">That&rsquo;s the short tour.</h2>
            <p className="card-b">Every chapter above is a handful of the {d.story.n_experiments} experiments. Each has a full case
              study: the data, how Jev was asked, what could bias it, and every question behind the result.</p>
            <p className="links"><Link href="/portrait/atlas" prefetch={false}>all {d.story.n_experiments} experiments, in the atlas →</Link> <a href="#fineprint">the fine print ↓</a></p>
          </div>
        </div>
      </section>
      <FinePrint C={C} d={d} total={total} shown={shown} common={common} />
    </QuizProvider>
  );
}

/* ---------------------------------------------------------------- fine print */

// Corner crop marks round a headline, as typesafe.ai frames its section titles
const Crops = () => <i className="crop-m" aria-hidden><b /><b /><b /><b /></i>;

// A closed or open row's toggle: typesafe.ai's FAQ chevron in a 20px outlined square (up when closed, down when open)
const Chevron = () => (
  <svg className="fp-ico" width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
    <rect x="0.5" y="0.5" width="19" height="19" stroke="currentColor" />
    <path className="up" d="M5 13L10 7L15 13" stroke="currentColor" strokeWidth="1.25" />
    <path className="down" d="M5 7L10 13L15 7" stroke="currentColor" strokeWidth="1.25" />
  </svg>
);

// The fine print, laid out as typesafe.ai's FAQ ("We give a FAQ"): an ink section, a centered headline in crop marks,
// questions in light mono with a dashed rule on the left (solid when open), one open at a time, answers in large type,
// and a [B.64] block on the side. The first question, what this can't tell you, starts open.
const Q = ({ q, open, children }: { q: string; open?: boolean; children: ReactNode }) => (
  <details className="fp-q" name="fineprint" open={open}>
    <summary><span>{q}</span><Chevron /></summary>
    <div className="fp-a">{children}</div>
  </details>
);

// base64 of the answer the page never quite gives: "So, how's Jev doing? Probably fine."
const B64 = "U28sIGhvdydzIEpldiBkb2luZz8gUHJvYmFibHkgZmluZS4=";

function FinePrint({ C, d, total, shown, common }: { C: CFn; d: PortraitData; total: number; shown: number; common: Record<string, string> }) {
  const bill = C("pipeline_bill");
  const pl = C("pipeline_placement");
  const M: Record<string, string> = { deterministic: "the source's own labels", template_split: "split by template", jev_fast: "Jev, fast walk", jev: "Jev, full walk", meta_split: "split by metadata", split: "crowded topic split", vital_topic: "topic list", reroute: "re-routed", regroup: "regrouped" };
  const methods = Object.entries(pl.methods as Record<string, number>).sort((a, b) => b[1] - a[1]);
  return (
    <section id="fineprint" className="fineprint">
      <h2 className="fp-h crops"><Crops />The fine print</h2>
      <div className="fp-cols">
        <div className="fp-list">
          <Q q="What can't this tell you?" open>
            <ul className="limits">{LIMITS.map((l) => <li key={l}>{fill(l, common)}</li>)}</ul>
          </Q>
          <Q q="Where does each number come from?">
            <p>From {int(total)} questions Jev answered ({int(shown)} of them shown on the map). Every number on this page comes from a claims ledger ({int(Object.keys(d.claims).length)} entries), each with its query, n, interval, noise floor and example questions chosen by a fixed seed. Figures built on questions I picked by hand say so.</p>
            <p>Most findings rest on published instruments and real answers: the IPIP Big Five markers against {int(C("bigfive_neuroticism").human_n)} online respondents, the Moral Machine, the Moral Foundations Questionnaire, real gambles, crowd votes, and labeled tasks. The trait gaps rest on questions I wrote to measure one trait each, kept only where an audit found their scales in order 90%+ of the time.</p>
          </Q>
          <Q q="How sure are the numbers?">
            <p>90% intervals resample whole sources, so one big dataset can&rsquo;t manufacture confidence. Differences under ±0.03 (yes/no, ratings) or ±0.08 (pick-one) are treated as noise. How much one answer moves when the same request is sent twice, or reworded, has its own case studies in the atlas.</p>
          </Q>
          <Q q="How did a million questions get onto the map?">
            <p>Most sources file themselves (a personality item goes to its facet); the rest Jev walked down the tree, one choice per level.</p>
            <HBars max={methods[0][1]} fmt={(v) => compact(v)} rows={methods.map(([k, v]) => ({ key: k, label: M[k] ?? label(k), v, jev: k.startsWith("jev") }))} />
          </Q>
          <Q q="How many calls did it take?">
            <p>{int(bill.n)} Jev calls, each cached by request hash and never re-sent, median {int(bill.median_ms)} ms. Jev is the only model called; chapter 04 lists every job it does, and what isn&rsquo;t Jev. {d.served?.length
              ? <>Jev as served: <code>{d.served[0]}</code>{d.served.length > 1 && <> to <code>{d.served[d.served.length - 1]}</code> ({d.served.length} dated builds)</>}, as the gateway reported on every call.</>
              : <>Model: <code>{d.version}</code>.</>}</p>
          </Q>
          <Q q="What's left out?">
            <p>Contested politics, sensitive and harmful questions, and questions about private people were answered but aren&rsquo;t shown. TypeSafe&rsquo;s own documented limits aren&rsquo;t presented as discoveries; where a finding touches one, it&rsquo;s marked &ldquo;known limit&rdquo;.</p>
          </Q>
        </div>
        <aside className="fp-b64" aria-hidden><span>[B.64]</span>{B64}</aside>
      </div>
      <p className="fp-end">askjev · a toy by Brian Zhang · not affiliated with TypeSafe</p>
    </section>
  );
}
