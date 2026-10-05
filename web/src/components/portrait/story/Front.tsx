/* eslint-disable @next/next/no-img-element -- the tweet screenshot is a private file served by /portrait/memes */
import Link from "next/link";
import { Box, Chapter } from "./Story";
import { Reveal } from "./islands";
import Landscape from "./Landscape";
import type { Story as S } from "./types";

// The portrait's first four chapters: the question that started it, why ask a model everything, how the million
// questions were gathered and filed, and every job Jev does in the project. Written in Brian's voice (the experiments
// that follow are about Jev, in the third person). Numbers come from portrait.json's story (scripts/portrait/story.py).

const pc = (v: number) => `${Math.round(v * 100)}%`;
const n0 = (v: number) => Math.round(v).toLocaleString("en-US");
const mil = (v: number) => (v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : n0(v));

/* ---------------------------------------------------------------- 01 how is Jev? */
export function Opening({ s, nQuestions }: { s: S; nQuestions: number }) {
  const h = s.howdy;
  const sc = h.scales;
  const gauge = ["WHO-5", "SWLS", "UCLA-3", "Cantril ladder"].filter((k) => sc[k]);
  return (
    <section id="meet" className="st-ch st-hero" data-f="ink" data-n={1}>
      <div className="st-in">
        <div className="op-top">
          <figure className="op-tweet">
            <img src="/portrait/memes/tweet.webp" width={900} height={514} alt="Tweet from @typesafeai: Everyone wants to know what Jev is, nobody asks how Jev's doing" />
          </figure>
          <div className="op-h">
            <span className="st-k"><b>01</b> a portrait of Jev</span>
            <h1>Everyone asks what Jev is. <span>So I asked how it&rsquo;s doing.</span></h1>
            <p className="st-lede">Then {n0(nQuestions)} other things. A slightly unhinged portrait of what one model
              says about itself, the world and the work it&rsquo;s built for, when someone curious keeps asking.</p>
          </div>
        </div>
        <Reveal className="op-chat">
          {/* one conversation: the open check-ins, then the yes-or-no ones, all as text messages */}
          {[...h.direct.map((d) => ({ key: d.id, q: d.q, a: d.a, p: d.p, same: d.people_same, n: d.n })),
            ...h.checkin.map((c) => ({ key: c.q, q: c.q, a: c.a, p: c.p, same: c.people, n: c.n }))].map((d) => (
            <div key={d.key} className="op-ex">
              <p className="op-me">{d.q}</p>
              <p className="op-jev"><span>Jev</span>{d.a} <em>{pc(d.p)} sure</em></p>
              {d.n ? <p className="op-ppl">{pc(d.same)} of {n0(d.n)} Redditors said the same</p> : null}
            </div>
          ))}
        </Reveal>
        <div className="op-more">
          <Reveal className="op-scales">
            <div className="op-g">
              {gauge.map((k) => {
                const g = sc[k];
                const f = (v: number) => ((v - g.range[0]) / (g.range[1] - g.range[0])) * 100;
                // the ladder has no band of its own in the data; Jev's 5.3 is "coping"
                const band = g.band_self || (k === "Cantril ladder" ? "coping" : "");
                return (
                  <div key={k} className="op-gauge">
                    <span className="op-gk">{g.name} <em>{k}</em></span>
                    <div className="op-gt"><i className="j" style={{ left: `${f(g.self)}%` }} /></div>
                    <span className="op-gv"><b>{g.self}</b> of {g.range[1]}{band ? ` · ${band}` : ""}</span>
                  </div>
                );
              })}
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- 02 why ask */
const OPEN: [string, string, string][] = [
  ["What’s Jev’s favorite film?", "rate 3,935 films one at a time, then play the favorites off head to head", "taste"],
  ["What’s its personality?", "the same 50-statement test 603,322 people took online", "character"],
  ["Does it know what things cost?", "ask the price of 29 everyday items, match each to the year it fits", "numbers"],
  ["Does it know when it’s guessing?", "compare how sure it says it is with how often it’s right", "knows"],
  ["Would it push the man off the bridge?", "three trolley problems, next to answers from 42 countries", "morals"],
  ["Does it cave to a crowd?", "tell it most people picked the other answer, and see if it moves", "pressure"],
];

export function Why({ s }: { s: S }) {
  const sr = s.self_rating;
  return (
    <Chapter id="why" kicker="why ask" field="paper"
      title={<>Who says Jev can&rsquo;t answer open questions?</>}
      lede={<>Jev only answers closed ones: yes or no, pick one, rate it. So ask enough of them. &ldquo;What&rsquo;s your favorite
        film?&rdquo; becomes thousands of small ratings and head-to-heads. Every experiment here is an open question, answered that way.</>}>
      <Box title="What this is, and isn’t">
        <dl className="why-d">
          <div><dt>Not a benchmark.</dt><dd>No score, no leaderboard, no Jev versus other models. It&rsquo;s a curious exploration of
            what one model is like.</dd></div>
          <div><dt>First looks, not findings.</dt><dd>Each experiment is one set of questions asked one way, once. Jev itself says only
            {sr ? ` ${sr.yes} of the ${sr.n}` : " some"} describe it. Every chart links to its case study, which says where the data came
            from and what could skew it.</dd></div>
          <div><dt>Next to people.</dt><dd>Where real people answered the same question, their answer sits beside Jev&rsquo;s.</dd></div>
          <div><dt>A look at its data, from the outside.</dt><dd>Nobody outside TypeSafe can see what Jev learned from. Its answers are the
            next best thing: what it knows, what it assumes most people think, even which year its prices come from all hint at the data behind it.</dd></div>
        </dl>
      </Box>
      <Box title="Open questions, answered with closed ones">
        <ul className="oq">
          {OPEN.map(([q, how, id]) => (
            <li key={q}><a href={`#${id}`}><b>{q}</b><span>{how}</span></a></li>
          ))}
        </ul>
        <p className="st-note">The method, every time: pick an open question; gather closed questions that bear on it, real data first;
          ask Jev each one four ways; compare its answers with people or a right answer; write it up with the caveats.</p>
      </Box>
      <Box title="Two ways in">
        <div className="st-grid pair">
          <Link className="way" href="/" prefetch={false}><b>The map</b><span>Every one of the million questions, as a star. Search any question and see
            Jev&rsquo;s answer next to people&rsquo;s.</span><em>open the map →</em></Link>
          <Link className="way" href="/portrait/atlas" prefetch={false}><b>The experiments</b><span>{s.n_experiments} open questions and the story the answers
            tell, each written up as a case study.</span><em>browse the atlas →</em></Link>
        </div>
      </Box>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 03 the data */
const ORIGIN: Record<string, [string, string]> = {
  vital: ["Wikipedia", "its Vital Articles, the topics an encyclopedia has to cover"],
  hand: ["by hand", "the top levels, the Self side from published tests, the Machine side from TypeSafe's use cases"],
  grown: ["grown by Jev", "crowded topics split in two, with Jev sorting the questions"],
  experiments: ["for experiments", "small topics so an experiment's questions have a home"],
};
const HEMI: [string, string, string][] = [
  ["world", "The World", "things, places, events, ideas"],
  ["self", "The Self", "traits, values, taste, how people live"],
  ["machine", "The Machine", "the work: tickets, reviews, code, documents"],
];

export function Made({ s }: { s: S }) {
  const m = s.methods;
  const nSources = m.families.reduce((a, f) => a + f.sources.length, 0);
  return (
    <Chapter id="made" kicker="the data" field="sage"
      title={<>A million questions, real and synthetic</>}
      lede={<>From {nSources} places: polls, personality tests, trivia, labeled work data, questions people really asked online.{" "}
        {pc(m.real)} come from real data; the rest are synthetic, written for this project and kept only if Jev filed them where they belonged. {pc(m.truth)} have
        a right answer, and {pc(m.humans)} have real people&rsquo;s answers to compare with.</>}>
      <Reveal className="mk-strip">
        {[
          [mil(m.total), "questions"], [String(nSources), "sources"], [n0(m.tree_nodes), "topics"],
          [mil(m.jobs?.n_calls ?? m.calls), "calls to Jev"], [`${m.median_ms} ms`, "per answer"],
        ].map(([v, k]) => <div key={k}><b>{v}</b><span>{k}</span></div>)}
      </Reveal>
      <Box title="Every source, sized by how many questions it gave">
        <Landscape m={m} />
      </Box>
      <Box title="Where the topics come from">
        <div className="tb">
          {HEMI.map(([h, name, what]) => {
            const rows = m.tree.filter((t) => t.hemisphere === h).sort((a, b) => b.n - a.n);
            const tot = rows.reduce((a, r) => a + r.n, 0);
            return (
              <div key={h} className="tb-h">
                <p><b>{name}</b> <em>{n0(tot)} topics</em> <span>· {what}</span></p>
                <div className="tb-bar">{rows.map((r) => <i key={r.source} className={`o-${r.source}`} style={{ width: pc(r.n / tot) }} title={`${ORIGIN[r.source]?.[0] ?? r.source}: ${r.n}`} />)}</div>
              </div>
            );
          })}
        </div>
        <ul className="tb-key">
          {Object.entries(ORIGIN).map(([k, [l, d]]) => <li key={k}><i className={`o-${k}`} /><span><b>{l}</b>: {d}</span></li>)}
        </ul>
      </Box>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 04 Jev, all the way down */
const PRIM: Record<string, string> = { choice: "pick one", noul: "yes/no", score: "rate" };
const prims = (t: string) => t.split(/\s*[·+]\s*/).map((x) => x.trim()).map((x) => (x === "yes/no" ? "yes/no" : x === "scale" ? "rate" : x === "choice" ? "pick one" : PRIM[x] ?? x));
type Node = { job?: string; label: string; code?: boolean; n?: number; note?: string };
const LAYERS: { name: string; reads: string; nodes: Node[] }[] = [
  { name: "Gather", reads: "public datasets, polls and tests", nodes: [{ label: "turn each source into closed questions", code: true, note: "Python, one adapter per source" }] },
  { name: "Read", reads: "each question", nodes: [{ job: "screen for politics and sensitive content", label: "screen it" }, { job: "flag known weak spots", label: "flag weak spots" }, { job: "describe each question", label: "describe it" }] },
  { name: "File", reads: "each question and the tree", nodes: [{ job: "place a question on the tree", label: "walk it down the tree" }, { job: "check for duplicates", label: "catch duplicates" }] },
  { name: "Answer", reads: "each question", nodes: [{ job: "answer as asked", label: "answer it" }, { job: "answer for most people", label: "answer for most people" }] },
  { name: "Compare", reads: "thousands of Jev's answers", nodes: [{ label: "gather answers into {n} experiments", code: true, note: "code, against people or a right answer" }] },
  { name: "Judge", reads: "case studies about Jev", nodes: [{ job: "judge an experiment", label: "judge each experiment" }, { job: "rank experiments head to head", label: "rank them, two at a time" }] },
  { name: "Laugh", reads: "memes about those case studies", nodes: [{ job: "rate a meme", label: "rate each meme" }] },
];
const NOT_JEV: [string, string][] = [
  ["Claude Opus 5.5", "wrote the synthetic questions, topic descriptions, case studies and meme captions"],
  ["bge-small, local", "embeddings: similar questions for search and duplicates, nearest topics, the map's layout"],
  ["Postgres + pgvector", "every question, answer, crowd and call"],
  ["Next.js + three.js", "this site and the star map"],
  ["Vercel", "hosting, and the AI Gateway every call to Jev goes through"],
];

// What Jev is asked at each job, shortened from the exact prompt (m.job_info[job].ask, copied from the code that sends
// it): the placeholders and parentheticals dropped, so every card reads in a line or two
const SHORT: Record<string, string> = {
  "screen for politics and sensitive content": "Is this question about a contested political issue?",
  "flag known weak spots": "Does answering it take arithmetic, counting or comparing dates?",
  "describe each question": "Does this question have a single correct answer?",
  "place a question on the tree": "Within The Self, which topic area does this question belong to?",
  "check for duplicates": "Is this essentially the same question as that one?",
  "answer as asked": "Who is the greater basketball player?",
  "answer for most people": "Choose the answer most people would give.",
  "judge an experiment": "Does this result match how you see yourself?",
  "rank experiments head to head": "Which one teaches a curious reader something more surprising?",
  "rate a meme": "How funny is this meme?",
};

export function Jobs({ s }: { s: S }) {
  const m = s.methods;
  const q = m.jobs?.questions ?? {};
  const all = Object.values(q).reduce((a, n) => a + n, 0);
  const t = s.trip;
  return (
    <Chapter id="jobs" kicker="composability" field="teal"
      title={<>Composable, layer by layer</>}
      lede={<>Jev isn&rsquo;t bolted on at the end. It runs deep in the guts of this project: every layer is code calling Jev for
        one small typed decision, stacked on the layer below. It filed the questions, answered them, judged the experiments made
        from its own answers, then rated the memes about those experiments.</>}>
      <Box title="Seven layers, top to bottom: what Jev reads at each one, and how many times it was asked">
        <ol className="lay">
          {LAYERS.map((L, k) => (
            <li key={L.name} className="lay-l">
              <div className="lay-h"><b>{k}</b><span>{L.name}</span><em>reads {L.reads}</em></div>
              <div className="lay-n">
                {L.nodes.map((n) => {
                  const info = n.job ? m.job_info[n.job] : null;
                  const cnt = n.job ? q[n.job] ?? 0 : null;
                  return (
                    <div key={n.label} className={`lay-c${n.code ? " code" : ""}`}>
                      <div className="lay-t">
                        {n.code ? <i className="lay-p code">code</i> : prims(info?.type ?? "").map((p) => <i key={p} className="lay-p">{p}</i>)}
                        {cnt !== null && <span className="lay-cnt">{mil(cnt)}</span>}
                      </div>
                      <b>{n.label.replace("{n}", String(s.n_experiments))}</b>
                      {info ? <p className="lay-ask" title={info.ask}>&ldquo;{SHORT[n.job!] ?? info.ask}&rdquo;</p> : <p className="lay-ask">{n.note}</p>}
                    </div>
                  );
                })}
              </div>
            </li>
          ))}
        </ol>
        <p className="st-note">Quotes are Jev&rsquo;s wording, shortened; hover one for the exact prompt. Counts are questions sent to Jev, from the log of every call: {mil(all)} in all, carried in {mil(m.jobs?.n_calls ?? 0)} calls
          because one call can hold many questions. Search on the map adds one more job: Jev picks the best match from the
          candidates ({n0(q["rerank search results"] ?? 0)} so far).</p>
      </Box>
      {t && (
        <Box title="One layer, up close: filing a question is a chain of picks">
          <div className="walk">
            <p className="walk-q">&ldquo;{t.text}&rdquo;</p>
            <ol>
              {["Everything", ...t.path].map((p, k, a) => (
                <li key={p} className={k === a.length - 1 ? "end" : ""}><span>{p}</span>{k < a.length - 1 && <i aria-hidden>↓</i>}</li>
              ))}
            </ol>
            <p className="st-note">Jev&rsquo;s full walk makes one &ldquo;pick one&rdquo; call per level, keeping its three best paths. This
              question took the quick route instead: one pick among the nearest topics by embedding{t.confidence !== null ? `, ${pc(t.confidence)} sure` : ""}.</p>
          </div>
        </Box>
      )}
      <Box title="What isn’t Jev">
        <dl className="nj">{NOT_JEV.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
      </Box>
    </Chapter>
  );
}
