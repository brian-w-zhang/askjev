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
              {d.n && <p className="op-ppl">{pc(d.people_same)} of {n0(d.n)} Redditors said the same</p>}
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
      title={<>Jev can&rsquo;t answer open questions. <mark>So I asked a million closed ones.</mark></>}
      lede={<>Jev only answers closed questions: yes or no, pick one, rate on a scale. You can&rsquo;t ask it what it&rsquo;s like.
        But you can ask it enough small things, its favorite film, what &ldquo;several&rdquo; means, whether it would pull the
        lever, that an answer to the open question starts to show. At a quarter of a second and a fraction of a cent per answer,
        there was no reason to stop at a few.</>}>
      <Box title="What this is, and isn’t">
        <dl className="why-d">
          <div><dt>Not a benchmark.</dt><dd>Nothing here adds up to a score, and nothing ranks Jev against another model. A benchmark
            asks how good a model is; this asks what it&rsquo;s like.</dd></div>
          <div><dt>Curious, and a little weird.</dt><dd>The questions nobody would put in a test, its taste, its temperament, what it
            assumes about people, often say the most.</dd></div>
          <div><dt>Next to people.</dt><dd>Wherever real people answered the same question, in a poll, a survey or a published study,
            their answer sits beside Jev&rsquo;s. Where there&rsquo;s a right answer, that&rsquo;s there too.</dd></div>
          <div><dt>Not the final word.</dt><dd>These are first looks, not settled findings. Each rests on one set of questions, one way
            of asking and one crowd of people, and some could be explained by the method as much as by Jev. Every claim links to its
            case study, which spells out where the data came from and what could bias it. Read those before quoting anything.</dd></div>
        </dl>
      </Box>
      <Box title="The method, in one breath">
        <ol className="mth">
          <li><b>Gather</b> closed questions from {s.methods.families.reduce((a, f) => a + f.sources.length, 0)} sources, keeping real people&rsquo;s answers and right answers wherever they exist.</li>
          <li><b>File</b> each one on a tree of topics, with Jev doing the filing.</li>
          <li><b>Ask</b> Jev each question four ways: as written, for &ldquo;most people&rdquo;, with the options reordered and with scales reversed.</li>
          <li><b>Compare</b> in {s.n_experiments} experiments, each a set of questions chosen to test one thing, against people or a right answer.</li>
          <li><b>Write up</b> every experiment as a case study, with its caveats and every question behind it.</li>
        </ol>
        <p className="st-note">The next two chapters show each step in detail.</p>
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
  ["Claude Opus 5.5", "wrote the synthetic questions where no dataset existed, the topic descriptions, the case studies and the meme captions, with me editing"],
  ["bge-small, run locally", "turns every question and topic into an embedding, to find similar questions for search and duplicates, the nearest topics for a quick filing, and the map's layout by meaning"],
  ["Postgres with pgvector", "stores every question, answer, crowd, embedding and call"],
  ["Python", "the pipeline: sources, screening, filing, answering, experiments"],
  ["Next.js and three.js", "this site, and the map with every question drawn as a star"],
  ["Vercel", "hosting, the AI Gateway every call to Jev goes through, and private storage for the results"],
];
const GROUPS: [string, string[]][] = [
  ["Building the map", ["describe each question", "screen for politics and sensitive content", "flag known weak spots", "place a question on the tree", "check for duplicates"]],
  ["Answering", ["answer as asked", "answer for most people"]],
  ["Judging its own experiments", ["judge an experiment", "rank experiments head to head", "rate a meme"]],
  ["On the site", ["rerank search results"]],
];

export function Jobs({ s }: { s: S }) {
  const m = s.methods;
  const q = m.jobs?.questions ?? {};
  const all = Object.values(q).reduce((a, n) => a + n, 0);
  const max = Math.log10(Math.max(...Object.values(q), 10));
  return (
    <Chapter id="jobs" kicker="Jev's jobs" field="teal"
      title={<>Jev, studying Jev</>}
      lede={<>Jev is the only model this project calls, so it did most of the work of studying itself: it filed the questions,
        screened them, answered them, judged the experiments about it, and even rated the memes on this page.</>}>
      <Box title="Every job Jev did, with the words it was sent and how many questions">
        <div className="jt">
          {GROUPS.map(([g, keys]) => (
            <div key={g} className="jt-g">
              <p className="jt-h">{g}</p>
              {keys.filter((k) => m.job_info[k]).map((k) => {
                const n = q[k] ?? 0, j = m.job_info[k];
                return (
                  <div key={k} className="jt-r">
                    <div className="jt-k"><b>{k}</b><span>{j.what}</span></div>
                    <p className="jt-ask">&ldquo;{j.ask}&rdquo;</p>
                    <div className="jt-n"><b>{n0(n)}</b><i style={{ width: `${Math.max(3, (Math.log10(Math.max(n, 1)) / max) * 100)}%` }} /></div>
                  </div>
                );
              })}
            </div>
          ))}
          <div className="jt-r jt-tot">
            <div className="jt-k"><b>all jobs</b><span>questions travel in batches, so these went out in {n0(m.jobs?.n_calls ?? 0)} calls</span></div>
            <p className="jt-ask" />
            <div className="jt-n"><b>{n0(all)}</b></div>
          </div>
        </div>
        <p className="st-note">Counted from the log of every call. The counts are questions: they add up to the total, and one call carries
          many (the four checks on a question go together). Answers with the options reordered or reversed count as &ldquo;answer as
          asked&rdquo;. Bars are on a log scale so the small jobs show.</p>
      </Box>
      <Box title="Everything that isn’t Jev">
        <dl className="nj">{NOT_JEV.map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl>
      </Box>
    </Chapter>
  );
}
