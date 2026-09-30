/* eslint-disable @next/next/no-img-element -- the tweet screenshot is a private file served by /portrait/memes */
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
            <p className="st-lede">Then {n0(nQuestions)} other things. This is what one model says about itself, the world and
              the work it&rsquo;s built for, when someone curious keeps asking.</p>
          </div>
        </div>
        <Reveal className="op-chat">
          {h.direct.map((d) => (
            <div key={d.id} className="op-ex">
              <p className="op-me">{d.q}</p>
              <p className="op-jev"><span>Jev</span>{d.a} <em>{pc(d.p)} sure</em></p>
              {d.n && <p className="op-ppl">{n0(d.n)} Redditors, asked the same: {d.people_top === d.a ? <>mostly &ldquo;{d.a}&rdquo; too ({pc(d.people_top_p ?? 0)})</> : <>mostly &ldquo;{d.people_top}&rdquo; ({pc(d.people_top_p ?? 0)}); &ldquo;{d.a}&rdquo; {pc(d.people_same)}</>}</p>}
            </div>
          ))}
        </Reveal>
        <div className="op-more">
          <Reveal className="op-check">
            <p className="op-t">And the yes-or-no check-ins</p>
            <ul>
              {h.checkin.map((c) => (
                <li key={c.q}>
                  <span className="op-q">{c.q}</span>
                  <span className="op-a"><b>{c.a}</b> <em>{pc(c.p)}</em></span>
                  <span className="op-p" title={`${pc(c.people)} of ${c.n ?? ""} Redditors`}><i style={{ width: pc(c.people) }} /><em>{pc(c.people)} of people</em></span>
                </li>
              ))}
            </ul>
          </Reveal>
          <Reveal className="op-scales">
            <p className="op-t">Says it&rsquo;s fine. The real wellbeing questionnaires, scored as for a person, say: meh.</p>
            <div className="op-g">
              {gauge.map((k) => {
                const g = sc[k];
                const f = (v: number) => ((v - g.range[0]) / (g.range[1] - g.range[0])) * 100;
                return (
                  <div key={k} className="op-gauge">
                    <span className="op-gk">{g.name} <em>{k}</em></span>
                    <div className="op-gt"><i className="p" style={{ left: `${f(g.people)}%` }} title={`for most people: ${g.people}`} /><i className="j" style={{ left: `${f(g.self)}%` }} /></div>
                    <span className="op-gv"><b>{g.self}</b> of {g.range[1]}{g.band_self ? ` · ${g.band_self}` : ""}</span>
                  </div>
                );
              })}
            </div>
            <p className="ex-legend"><span><i className="k jev" />Jev</span><span><i className="k guess" />what Jev thinks most people would say</span></p>
          </Reveal>
        </div>
      </div>
    </section>
  );
}

/* ---------------------------------------------------------------- 02 why ask */
export function Why({ s }: { s: S }) {
  return (
    <Chapter id="why" kicker="why ask" field="paper"
      title={<>Not a benchmark. <mark>Just curious.</mark></>}
      lede={<>Jev answers in about a quarter of a second, for a fraction of a cent. At that price you stop asking which questions
        are worth asking. Everything anyone might ask is a list that never ends, so I started with a million, and kept going
        wherever an answer was strange.</>}>
      <Box title="What this is, and isn’t">
        <dl className="why-d">
          <div><dt>There&rsquo;s no score.</dt><dd>Nothing here adds up to a number for Jev, and nothing ranks it against another model.
            A benchmark asks &ldquo;how good?&rdquo;; this asks &ldquo;what&rsquo;s it like?&rdquo;</dd></div>
          <div><dt>Weird on purpose.</dt><dd>Its favorite film, what it thinks &ldquo;several&rdquo; means, whether a stirring word
            has to be an unpleasant one. The questions nobody would put in a test are the ones that say the most.</dd></div>
          <div><dt>Next to people.</dt><dd>Wherever real people answered the same question, in a poll, a survey or a study, their
            answer sits beside Jev&rsquo;s. Where there&rsquo;s a right answer, that&rsquo;s there too.</dd></div>
          <div><dt>Every number has a receipt.</dt><dd>Each finding links to its case study, and each case study to every question
            behind it. {s.n_experiments} of them, including the ones where Jev looks odd.</dd></div>
        </dl>
      </Box>
      <Box title="A universal classifier, asked the wrong questions">
        <p className="why-p">People call Jev a universal classifier: give it any closed question and it hands back a probability for
          every answer. Fair enough. So:</p>
        <ul className="why-ask">
          <li><a href="#taste">Does a universal classifier have a Letterboxd top four?</a> <em>It does.</em></li>
          <li><a href="#numbers">Does it know what year it is?</a> <em>Sort of.</em></li>
          <li><a href="#words">Does it think &ldquo;kiki&rdquo; is spiky?</a> <em>Very.</em></li>
          <li><a href="#morals">Would it push the man off the footbridge?</a> <em>Rarely.</em></li>
          <li><a href="#pressure">Does it cave when you say everyone disagrees?</a> <em>On opinions.</em></li>
          <li><a href="#minds">Does it think it has a mind?</a> <em>For thinking, yes.</em></li>
        </ul>
      </Box>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 03 how it was made */
const ORIGIN: Record<string, [string, string]> = {
  vital: ["Wikipedia", "Vital Articles, Wikipedia's own list of the topics an encyclopedia must cover, with Wikidata entities below them"],
  hand: ["written by hand", "the top levels, the Self side from published personality and values instruments, the Machine side from TypeSafe's own use cases"],
  grown: ["grown by Jev", "crowded topics split into subtopics, with Jev assigning each question to one"],
  experiments: ["for experiments", "small topics added so an experiment's questions have a home"],
};
const HEMI: [string, string, string][] = [
  ["world", "The World", "things, places, events, ideas"],
  ["self", "The Self", "traits, values, taste, how people live"],
  ["machine", "The Machine", "the work: tickets, reviews, code, documents"],
];

export function Made({ s }: { s: S }) {
  const m = s.methods;
  const nSources = m.families.reduce((a, f) => a + f.sources.length, 0);
  const pl = m.placement;
  const jevWalk = (pl.jev ?? 0) + (pl.jev_fast ?? 0);
  return (
    <Chapter id="made" kicker="how it was made" field="sage"
      title={<>{mil(m.total)} questions, {nSources} sources, one tree</>}
      lede={<>Before any experiment, the questions had to come from somewhere real and land somewhere sensible. {pc(m.real)} come
        from real data; the rest were written for this project and kept only if they passed a blind test. {pc(m.truth)} have a
        right answer, and {pc(m.humans)} have real people&rsquo;s answers to compare with, {n0(m.human_dists)} crowds in all.</>}>
      <Reveal className="mk-strip">
        {[
          [mil(m.total), "questions answered"], [String(nSources), "sources"], [n0(m.tree_nodes), "topics"],
          [mil(m.jobs?.n_calls ?? m.calls), "calls to Jev"], [`${m.median_ms} ms`, "median answer"],
        ].map(([v, k]) => <div key={k}><b>{v}</b><span>{k}</span></div>)}
      </Reveal>
      <Box title="Every source, sized by how many questions it gave">
        <Landscape m={m} />
      </Box>
      <div className="st-grid two">
        <Box title="Where the topics come from">
          <div className="tb">
            {HEMI.map(([h, name, what]) => {
              const rows = m.tree.filter((t) => t.hemisphere === h).sort((a, b) => b.n - a.n);
              const tot = rows.reduce((a, r) => a + r.n, 0);
              return (
                <div key={h} className="tb-h">
                  <p><b>{name}</b> <em>{n0(tot)} topics</em><br /><span>{what}</span></p>
                  <div className="tb-bar">{rows.map((r) => <i key={r.source} className={`o-${r.source}`} style={{ width: pc(r.n / tot) }} title={`${ORIGIN[r.source]?.[0] ?? r.source}: ${r.n}`} />)}</div>
                </div>
              );
            })}
          </div>
          <ul className="tb-key">
            {Object.entries(ORIGIN).map(([k, [l, d]]) => <li key={k}><i className={`o-${k}`} /><span><b>{l}</b>: {d}</span></li>)}
          </ul>
        </Box>
        <Box title="What happened to every question">
          <ol className="pp">
            <li><b>Gather</b><span>{nSources} sources, each turned into closed questions with their answer options, right answers and real people&rsquo;s answers kept.</span></li>
            <li><b>Screen</b><span>Jev checked every question for contested politics and graphic content. {n0(m.screen.first_hidden)} were hidden; a narrower second look released {n0(m.screen.released)}.</span></li>
            <li><b>Place</b><span>{n0(jevWalk)} questions Jev filed itself, walking the tree from the top; the rest followed their source&rsquo;s own labels{m.placement_eval ? ` (the walk: ${m.placement_eval.split(" (")[0]})` : ""}.</span></li>
            <li><b>Test the written ones</b><span>Of {n0(m.round_trip.n)} questions written for the project, Jev, not told where they belonged, sent {pc(m.round_trip.kept)} back to the right topic. The rest were dropped.</span></li>
            <li><b>Answer, four ways</b><span>As asked, for &ldquo;most people&rdquo;, with the options reordered, and with rating scales turned upside down.</span></li>
            <li><b>Merge</b><span>{n0(m.dedupe)} near-identical questions folded into their originals.</span></li>
            <li><b>Experiment</b><span>{s.n_experiments} experiments gathered the answers into things to learn, each written up as a case study.</span></li>
          </ol>
        </Box>
      </div>
      <p className="st-note mk-note">Calls to Jev ran from {m.first_call} to {m.last_call}. Every call is cached by the exact request and never sent twice.</p>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 04 Jev's jobs */
const NOT_JEV: [string, string][] = [
  ["Claude", "wrote the questions no dataset had, the topic descriptions, the case studies and the meme captions, with me editing"],
  ["bge-small (local embeddings)", "finds similar questions: search candidates, near-duplicates, the nearest topics for a fast walk, the map's Meaning layout"],
  ["Postgres + pgvector", "every question, answer, crowd and call"],
  ["Python", "the pipeline: sources, screening, placement, answering, experiments"],
  ["Next.js + three.js", "this site and the map, with every question drawn as a star"],
  ["Vercel", "hosting, the AI Gateway that carries every call to Jev, and private storage for the results"],
];

export function Jobs({ s }: { s: S }) {
  const m = s.methods;
  const q = m.jobs?.questions ?? {};
  const jobs = Object.keys(m.job_info).map((k) => ({ k, n: q[k] ?? 0, ...m.job_info[k] })).sort((a, b) => b.n - a.n);
  const max = Math.log10(Math.max(...jobs.map((j) => j.n), 10));
  return (
    <Chapter id="jobs" kicker="Jev's jobs" field="teal"
      title={<>Jev did almost everything here, including grading its own experiments</>}
      lede={<>Jev is the only model this project calls. Beyond answering the questions, it filed them, screened them, described
        them, merged duplicates, reranked search, judged each experiment, ranked the case studies against each other and rated
        its own memes. Here is every job, with the exact words it was sent and how many times.</>}>
      <Box title="Every job Jev did, by questions sent (log scale)">
        <ul className="jb">
          {jobs.map((j, i) => (
            <li key={j.k}>
              <details open={i === 0}>
                <summary>
                  <span className="jb-k">{j.k}</span>
                  <span className="jb-t"><i style={{ width: `${Math.max(2, (Math.log10(Math.max(j.n, 1)) / max) * 100)}%` }} /></span>
                  <span className="jb-n">{mil(j.n)}</span>
                </summary>
                <div className="jb-d">
                  <p className="jb-ask"><span>Jev reads</span>&ldquo;{j.ask}&rdquo;</p>
                  <p>{j.what}</p>
                  <p className="jb-m"><em>{j.type}</em> · <code>{j.where}</code></p>
                </div>
              </details>
            </li>
          ))}
        </ul>
        <p className="st-note">Tap a job to see the exact words Jev reads. The bars count questions, and they add up: the {mil(m.jobs?.n_questions ?? 0)} questions
          across all jobs travelled in {mil(m.jobs?.n_calls ?? 0)} calls, because one call can carry many questions (the four
          checks on each question go together, for instance). Counted from the call logs; answers with the options reordered or
          reversed are counted under &ldquo;answer as asked&rdquo;.</p>
      </Box>
      <div className="st-grid two">
        <Box title="Everything that isn’t Jev">
          <dl className="nj">{NOT_JEV.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
        </Box>
        {s.trip && (() => {
          const t = s.trip!;
          const yes = (d: Record<string, number> | null) => pc(d?.yes ?? 0);
          return (
            <Box title={`one question's trip · ${t.id.slice(0, 8)}`}>
              <ol className="trip">
                <li><span>source</span>a poll on Reddit: &ldquo;{t.text}&rdquo;, {t.n ? n0(t.n) : ""} votes kept with it</li>
                <li><span>screen</span>Jev: not contested politics, not graphic, so it stays on the map</li>
                <li><span>place</span>Jev files it{t.method === "jev_fast" ? " in one step, choosing among the nearest topics" : ", walking the tree"}{t.confidence !== null ? ` (${pc(t.confidence)} sure)` : ""}: {t.path.join(" → ")}</li>
                <li><span>answer</span>asked as itself, Jev says yes {yes(t.jev)}; asked for most people, yes {yes(t.people)}</li>
                <li><span>compare</span>the {t.population ?? "voters"}: yes {yes(t.human)}</li>
                <li><span>after</span>one row in a case study, one star on the map</li>
              </ol>
              <p className="st-note"><a href={`/?q=${t.id}`}>open this question on the map →</a></p>
            </Box>
          );
        })()}
      </div>
    </Chapter>
  );
}
