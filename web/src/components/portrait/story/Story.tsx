/* eslint-disable @next/next/no-img-element -- private pictures served by /portrait/memes, no optimizer needed */
import type { ReactNode } from "react";
import Link from "next/link";
import ExMeme from "../../experiments/ExMeme";
import { DotRows } from "../charts";
import type { ExLink, Story as S } from "./types";
import { ProbRuler, PressureChat, QuestionList, Reveal } from "./islands";
import { Jobs, Made, Opening, Why } from "./Front";

// The portrait's chapters (docs/11-portrait.md, "The story"): each one a custom card built from the experiments it
// names, with links to their case studies. Every number is read from portrait.json's story (scripts/portrait/story.py).

const pc = (v: number) => `${Math.round(v * 100)}%`;
const n0 = (v: number) => Math.round(v).toLocaleString("en-US");
const tidy = (s: string) => s.replace(/^Being offered /, "").replace(/ \((film|TV series)\)$/, "").replace(/ \(\d{4}\)$/, "").replace(/^The album /, "")
  .replace(/^Spending (a day at|an evening playing) /, "").replace(/ by [^,]*$/, "").replace(/[“”]/g, "").replace(/ \(.*\)$/, "").replace(/^./, (c) => c.toUpperCase());

export const CHAPTERS = [
  { id: "meet", name: "how are you?" }, { id: "why", name: "why ask" }, { id: "made", name: "the data" },
  { id: "jobs", name: "composability" }, { id: "character", name: "personality" }, { id: "taste", name: "taste" },
  { id: "words", name: "language" }, { id: "numbers", name: "numbers" }, { id: "knows", name: "confidence" }, { id: "morals", name: "morals" }, { id: "risk", name: "risk" },
  { id: "pressure", name: "peer pressure" }, { id: "defaults", name: "habits" }, { id: "work", name: "at work" },
  { id: "edges", name: "jaggedness" },
];


// An editorial chapter: on wide screens the heading, lede, meme and case-study links stay put in a side column while
// the figures scroll past beside them; on phones it all stacks.
export function Chapter({ id, kicker, title, lede, field, children, links, more, aside }: {
  id: string; kicker: string; title: ReactNode; lede?: ReactNode; field: string; children: ReactNode; links?: ExLink[];
  more?: ExLink[]; aside?: ReactNode;
}) {
  const n = CHAPTERS.findIndex((c) => c.id === id) + 1;
  const seen = new Set<string>();
  const cases = [...(links ?? []), ...(more ?? [])].filter((x) => !seen.has(x.id) && seen.add(x.id));
  return (
    <section id={id} className="st-ch" data-f={field}>
      <div className="st-in st-ed">
        <div className="st-side">
          <header className="st-head">
            <span className="st-k"><b>{String(n).padStart(2, "0")}</b> {kicker}</span>
            <h2>{title}</h2>
            {lede && <p className="st-lede">{lede}</p>}
          </header>
          {aside && <div className="st-aside">{aside}</div>}
        </div>
        <div className="st-main">
          {children}
          <More items={cases} />
        </div>
      </div>
    </section>
  );
}

// More from a chapter: other experiments on the theme, each with its first takeaway
export function More({ items }: { items?: ExLink[] }) {
  if (!items?.length) return null;
  return (
    <Reveal className="st-more">
      <p className="st-cap">The case studies behind this chapter</p>
      <div className="st-more-g">
        {items.map((x) => (
          <Link key={x.id} href={`/portrait/atlas/${x.id}`} prefetch={false} className="st-more-c">
            <b>{x.title}</b>{x.line && <span>{x.line}</span>}
          </Link>
        ))}
      </div>
    </Reveal>
  );
}

// A figure: a numbered caption above a plain panel (fig 3.2), not a window
export const Box = ({ title, children, className = "", note }: { title: string; children: ReactNode; className?: string; note?: ReactNode }) => (
  <Reveal className={`st-fig ${className}`}>
    <p className="st-cap">{title}</p>
    <div className="st-body">{children}</div>
    {note && <p className="st-fnote">{note}</p>}
  </Reveal>
);

function Meme({ s, id }: { s: S; id: string }) {
  const m = s.memes[id];
  if (!m) return null;
  return <div className="st-meme" style={{ ["--ar" as string]: (m.w / m.h).toFixed(3) }}><ExMeme m={m} /></div>;
}

export default function Story({ s, nQuestions }: { s: S; nQuestions: number }) {
  return (
    <>
      <Opening s={s} nQuestions={nQuestions} />
      <Why s={s} />
      <Made s={s} />
      <Jobs s={s} />
      <Character s={s} />
      <Taste s={s} />
      <Words s={s} />
      <Numbers s={s} />
      <Knows s={s} />
      <Morals s={s} />
      <Risk s={s} />
      <Pressure s={s} />
      <Defaults s={s} />
      <Work s={s} />
      <Edges s={s} />
    </>
  );
}

/* ---------------------------------------------------------------- character */
const WORD: Record<string, string> = { I: "introverted", E: "extraverted", S: "sensing", N: "intuitive", T: "thinking", F: "feeling", J: "judging", P: "perceiving" };
const ORDER: [string, string][] = [["E", "I"], ["S", "N"], ["T", "F"], ["J", "P"]];

function Character({ s }: { s: S }) {
  const p = s.personality;
  const calm = p.bigfive.find((t) => t.label === "Neuroticism")!;
  const sin = p.honesty[0];
  const nr = p.n_rows ?? {};
  // each axis as the share of answers on its left letter (E, S, T, J), for Jev and for its "most people"
  const axes = ORDER.map(([l, r]) => {
    const a = p.axes.find((x) => x.first === l || x.other === l)!;
    const left = a.first === l ? a.p_first : 1 - a.p_first;
    const ppl = a.first === l ? a.people_p_first : 1 - a.people_p_first;
    const ci: [number, number] = a.first === l ? [a.ci[0], a.ci[1]] : [1 - a.ci[1], 1 - a.ci[0]];
    return { l, r, left, ppl, ci, n: a.n_items, jev: left >= 0.5 ? l : r };
  });
  return (
    <Chapter more={s.more?.character} id="character" aside={<Meme s={s} id="person_type" />} kicker="personality" field="paper" links={p.links}
      title={<>Calm, sincere, and an <mark>{p.type}</mark></>}
      lede={<>The same personality tests people take online. Jev comes out calmer than {pc(1 - calm.pct / 100)} of the people who took them, and far more sincere. Asked to answer the way most people would, it becomes an {p.type_people}.</>}>
      <Box title="The Big Five: Jev’s percentile among 603,322 people who took the test">
        <DotRows domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} fmt={(v) => String(v)}
          rows={p.bigfive.map((t) => ({ key: t.label, label: t.label, ci: t.ci, value: `${Math.round(t.pct)}th`,
            marks: [{ v: t.guess, kind: "guess" as const, title: `for most people: ${t.guess}` }, { v: t.pct, kind: "jev" as const }] }))} />
        <p className="ex-legend"><span><i className="k jev" />Jev, with its 90% range</span><span><i className="k guess" />what Jev thinks most people would say</span></p>
        <QuestionList id="person_bigfive" total={nr.person_bigfive ?? 0} label="every Big Five statement Jev rated" />
      </Box>
      <Box title="Four letters, measured: the share of Jev’s answers on each side">
        <div className="mb">
          <p className="mb-type">{axes.map((a) => <b key={a.l} className={a.jev === a.l ? "on-l" : "on-r"}>{a.jev}</b>)}</p>
          {axes.map((a) => (
            <div key={a.l} className="mb-row">
              <span className={`mb-e${a.jev === a.l ? " on" : ""}`}><b>{a.l}</b>{WORD[a.l]}</span>
              <span className="mb-t">
                <i className="mb-ci" style={{ left: pc(1 - a.ci[1]), width: pc(a.ci[1] - a.ci[0]) }} />
                <i className="mb-mid" />
                <i className="mb-g" style={{ left: pc(1 - a.ppl) }} title={`most people: ${pc(a.ppl)} ${a.l}`} />
                <i className="mb-j" style={{ left: pc(1 - a.left) }} />
              </span>
              <span className={`mb-e r${a.jev === a.r ? " on" : ""}`}><b>{a.r}</b>{WORD[a.r]}</span>
              <span className="mb-v">{pc(Math.max(a.left, 1 - a.left))} {a.jev} · {a.n} statements</span>
            </div>
          ))}
          <p className="ex-legend"><span><i className="k jev" />Jev, with its 90% range</span><span><i className="k guess" />what Jev thinks most people would say</span></p>
        </div>
        <QuestionList id="person_type" total={nr.person_type ?? 0} label="every statement in the type test" />
      </Box>
      <Box title="Saint or villain: each scale from 0 to 1, higher means more of it">
        <div className="st-grid pair tight">
          <div>
            <p className="st-sub">Honesty-humility: Jev claims {Math.round((sin.jev / sin.people) * 10) / 10}× people&rsquo;s sincerity</p>
            <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => String(v)}
              rows={p.honesty.map((h) => ({ key: h.label, label: h.label, link: true, value: h.jev.toFixed(2),
                marks: [{ v: h.people, kind: "hum" as const }, { v: h.jev, kind: "jev" as const }] }))} />
          </div>
          <div>
            <p className="st-sub">The dark side: lower than people on every scale</p>
            <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => String(v)}
              rows={p.dark.map((h) => ({ key: h.label, label: <>{h.label.replace(/ \(.*\)$/, "")}{/\(/.test(h.label) && <small>{h.label.match(/\((.*)\)/)![1]} test</small>}</>, link: true, value: h.jev.toFixed(2),
                marks: [{ v: h.people, kind: "hum" as const }, { v: h.jev, kind: "jev" as const }] }))} />
          </div>
        </div>
        <p className="ex-legend"><span><i className="k jev" />Jev</span><span><i className="k hum" />people who took the test</span></p>
      </Box>
      {p.twin && p.twin.length > 0 && (
        <Box title="Its fictional twins: characters whose trait ratings match Jev’s answers">
          <ol className="tw">
            {p.twin.map((t, k) => (
              <li key={t.name}><span className="tw-n">{k + 1}</span><b>{t.name}</b><em>{t.work}</em><span className="tw-r">r = {t.r.toFixed(2)}</span></li>
            ))}
          </ol>
          <p className="st-note">Matched on how Jev rates itself against how fans rated each character on the same trait pairs; 1 would be identical.</p>
        </Box>
      )}
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 03 taste */
function Poster({ t, rank }: { t: S["taste"]["domains"][number]["top"][number]; rank: number }) {
  return (
    <figure className="st-poster">
      {t.img ? <img src={`/portrait/memes/${t.img.file}`} alt={`${tidy(t.label)} (from Wikipedia)`} loading="lazy" style={{ aspectRatio: `${t.img.w} / ${t.img.h}` }} />
        : <span className="st-ph">{tidy(t.label)}</span>}
      <figcaption><b>{rank}</b>{tidy(t.label)}</figcaption>
    </figure>
  );
}

function Taste({ s }: { s: S }) {
  const t = s.taste;
  const film = t.domains.find((d) => d.domain === "film")!;
  const rest = t.domains.filter((d) => d.domain !== "film");
  return (
    <Chapter more={s.more?.taste} id="taste" aside={<Meme s={s} id="taste_top_film" />} kicker="taste" field="pink" links={[film.link, ...t.links]}
      title={<>Jev&rsquo;s favorite things</>}
      lede={<>It rated thousands of films one at a time, then played its favorites off against each other, starting with its Letterboxd top four. Then it did the same for books, albums, games, food, places, art and more.</>}>
      <Reveal className="st-top4">
        <div className="st-top4-h"><span>JEV&rsquo;S LETTERBOXD TOP FOUR</span><Link href={`/portrait/atlas/${film.link.id}`} prefetch={false}>all films →</Link></div>
        <div className="st-top4-row">{film.top.slice(0, 4).map((x, i) => <Poster key={x.label} t={x} rank={i + 1} />)}</div>
        <p className="st-never">never again: {film.bottom.map(tidy).join(" · ")}</p>
      </Reveal>
      <div className="st-shelf">
        {rest.map((d) => {
          const top = d.top[0];
          return (
            <Reveal key={d.domain} className="st-item">
              <Link href={`/portrait/atlas/${d.link.id}`} prefetch={false} className="st-item-a">
                <span className="st-item-k">{d.name}</span>
                {top.img ? <img src={`/portrait/memes/${top.img.file}`} alt={`${tidy(top.label)} (from Wikipedia)`} loading="lazy" />
                  : <span className="st-ph">{tidy(top.label)}</span>}
                <b>{tidy(top.label)}</b>
                <ol start={2}>{d.top.slice(1, 4).map((x) => <li key={x.label}>{tidy(x.label)}</li>)}</ol>
                <span className="st-never">not for Jev: {tidy(d.bottom[0] ?? "")}</span>
              </Link>
            </Reveal>
          );
        })}
      </div>
      <p className="st-note">Pictures are each winner&rsquo;s lead image on Wikipedia. Winners are the best of the lists Jev was given, not of everything that exists.</p>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 04 words */
const SPIKY = "M50 4 L60 36 L96 22 L70 50 L96 78 L60 64 L50 96 L40 64 L4 78 L30 50 L4 22 L40 36 Z";
const ROUND = "M50 8 C78 6 94 26 92 50 C94 76 74 94 50 92 C24 96 6 76 8 50 C6 24 24 10 50 8 Z";

function Words({ s }: { s: S }) {
  const w = s.words;
  const miss = w.colors.filter((c) => c.jev !== c.people);
  const hit = w.colors.filter((c) => c.jev === c.people);
  return (
    <Chapter more={s.more?.words} id="words" aside={<Meme s={s} id="lexicon_first_to_mind" />} kicker="language" field="teal" links={w.links}
      title={<>Jev and the English language</>}
      lede={<>How it reads the everyday words people use for chances, amounts, feelings and sounds. It takes &ldquo;likely&rdquo; and &ldquo;we doubt&rdquo; almost exactly as people do, counts smaller, and sees some feelings in other colors.</>}>
      <Box title="What each phrase means, as a percent">
        <ProbRuler rows={w.probability} />
        <p className="st-note">Words in pink are the ones Jev reads at least 15 points away from people.</p>
      </Box>
      <Box title="The color of a feeling">
        <div className="cf">
          {[...miss, ...hit].map((c) => (
            <div key={c.feeling} className={`cf-c${c.jev === c.people ? " same" : ""}`}>
              <b>{c.feeling}</b>
              <span><i style={{ background: c.jev }} />Jev: {c.jev}</span>
              <span><i style={{ background: c.people }} />people: {c.people}</span>
            </div>
          ))}
        </div>
        <p className="st-note">Jev picks people&rsquo;s most common color for {hit.length} of {w.colors.length} feelings (the faded cards); the rest are where they part. Given only a hex code like #fdff63, it picks the color&rsquo;s popular name {pc(w.hex)} of the time.</p>
      </Box>
      <div className="st-grid pair">
        <Box title="How many is “several”?">
          <dl className="st-dict">
            {w.amounts.filter((a) => a.jev !== a.people).map((a) => (
              <div key={a.phrase}><dt>{a.phrase.toLowerCase()}</dt><dd><b>{a.jev}</b> to Jev · <span>{a.people}</span> to people</dd></div>
            ))}
          </dl>
        </Box>
        <Box title="Kiki or bouba?">
          <p className="st-note kb-why">A classic from psychology (Köhler, 1929): shown a spiky shape and a round one, nearly everyone calls the
            spiky one &ldquo;kiki&rdquo; and the round one &ldquo;bouba&rdquo;, in almost any language.</p>
          <div className="st-kb">
            <figure><svg viewBox="0 0 100 100" aria-hidden><path d={SPIKY} /></svg><figcaption>&ldquo;kiki&rdquo; is the spiky one<br /><b>Jev {pc(w.kiki.jev)}</b> · people {pc(w.kiki.people)}</figcaption></figure>
            <figure><svg viewBox="0 0 100 100" aria-hidden><path d={ROUND} /></svg><figcaption>&ldquo;bouba&rdquo; is the round one<br /><b>Jev {pc(w.bouba.jev)}</b> · people {pc(w.bouba.people)}</figcaption></figure>
          </div>
          <p className="st-note">On {w.n_shapes} made-up words, Jev&rsquo;s ratings spread {w.spread}× as wide as people&rsquo;s.</p>
        </Box>
      </div>
      <Box title="Calm or exciting? Each word rated 1 (calm) to 9 (exciting)">
        <DotRows domain={[1, 9]} ticks={[1, 3, 5, 7, 9]} fmt={(v) => String(v)}
          rows={w.exciting.map((x) => ({ key: x.word, label: x.word, link: true, value: x.jev.toFixed(1),
            marks: [{ v: x.people, kind: "hum" as const }, { v: x.jev, kind: "jev" as const }] }))} />
        <p className="ex-legend"><span><i className="k jev" />Jev</span><span><i className="k hum" />people</span></p>
        <p className="st-note">People rate &ldquo;cuddle&rdquo; exciting and &ldquo;misery&rdquo; fairly calm; Jev flips both, as if exciting meant unpleasant. (Jev&rsquo;s question asked how &ldquo;calming or stirring&rdquo; each word feels.)</p>
      </Box>

    </Chapter>
  );
}

/* ---------------------------------------------------------------- 05 numbers */
function Numbers({ s }: { s: S }) {
  const n = s.numbers;
  const le = n.lethal;
  const lg = (v: number) => Math.log10(Math.max(v, 1));
  const w = n.wallets.rows;
  const lo = (k: "true" | "jev") => Math.min(...w.map((r) => r[k])), hi = (k: "true" | "jev") => Math.max(...w.map((r) => r[k]));
  const crowd: Record<string, string> = { copies: "copies of itself", lab_two_thirds: "lab students (⅔)", lab_half: "lab students (½)", ft: "newspaper readers (⅔)" };
  return (
    <Chapter more={s.more?.numbers} id="numbers" aside={<Meme s={s} id="numbers_prices_year" />} kicker="numbers" field="sage" links={n.links}
      title={<>What does Jev think things cost?</>}
      lede={<>Asked what a pound of lemons or a kilowatt-hour costs right now, Jev answers with prices from about {Math.floor(n.prices.median_year)}, though it thinks the year is {n.prices.said_year}, probably. It also estimates death tolls, other people&rsquo;s guesses and how often lost wallets come back.</>}>
      <div className="st-grid two">
        <Reveal className="st-receipt">
          <p className="rc-h">JEV&rsquo;S CORNER STORE<br /><span>date: {n.prices.said_year}, probably</span></p>
          <ul>{n.prices.items.filter((_, i, a) => i % Math.max(1, Math.ceil(a.length / 8)) === 0).map((x) => (
            <li key={x.item}>
              <span>{x.item.replace(/^a /, "1 ")}</span>
              <b>{x.lo !== undefined ? `$${x.lo.toFixed(2)}–${x.hi!.toFixed(2)}` : ""}</b>
              <small>priced like {Math.round(x.year)}{x.now ? ` · today $${x.now.toFixed(2)}` : ""}</small>
            </li>
          ))}</ul>
          <p className="rc-t"><span>prices from about</span><b>{Math.floor(n.prices.median_year)}</b></p>
          <p className="rc-f">thank you for shopping in the past</p>
        </Reveal>
        <Box title="Which kills more? Deaths per year in the US">
          <DotRows domain={[0, 5.6]} ticks={[0, 1, 2, 3, 4, 5]} fmt={(v) => (10 ** v >= 1000 ? `${Math.round(10 ** v / 1000)}k` : String(Math.round(10 ** v)))}
            rows={le.rows.map((r) => ({ key: r.cause, label: r.cause, value: n0(r.truth),
              marks: [{ v: lg(r.truth), kind: "tick" as const, title: `real ${n0(r.truth)}` }, { v: lg(r.people), kind: "hum" as const, title: `people, 1978: ${n0(r.people)}` }, { v: lg(r.jev), kind: "jev" as const, title: `Jev: ${n0(r.jev)}` }] }))} />
          <p className="ex-legend"><span><i className="k jev" />Jev</span><span><i className="k hum" />people in 1978</span><span><i className="k tick" />the real number</span></p>
          <p className="st-note">A slope of 1 would be perfectly calibrated across causes: Jev {le.slope_jev}, people {le.slope_people}.</p>
        </Box>
      </div>
      <div className="st-grid two pair">
        <Box title="Guess two-thirds of the average">
          <DotRows domain={[0, 50]} ticks={[0, 10, 20, 30, 40, 50]} fmt={(v) => String(v)}
            rows={n.beauty.map((b) => ({ key: b.crowd, label: `against ${crowd[b.crowd] ?? b.crowd}`, value: String(b.pick),
              marks: [...(b.win !== null ? [{ v: b.win, kind: "tick" as const, title: `winning number ${b.win}` }] : []), { v: b.pick, kind: "jev" as const }] }))} />
          <p className="ex-legend"><span><i className="k jev" />Jev&rsquo;s pick</span><span><i className="k tick" />the number that won</span></p>
        </Box>
        <Box title="Lost wallets returned, with money inside">
          <div className="st-range">
            <div><span>real</span><div className="t"><i className="p" style={{ left: `${lo("true")}%`, width: `${hi("true") - lo("true")}%` }} /></div><b>{Math.round(lo("true"))}–{Math.round(hi("true"))}%</b></div>
            <div><span>Jev</span><div className="t"><i className="j" style={{ left: `${lo("jev")}%`, width: `${hi("jev") - lo("jev")}%` }} /></div><b>{Math.round(lo("jev"))}–{Math.round(hi("jev"))}%</b></div>
          </div>
          <p className="st-note">Across {n.wallets.n} countries, Jev guesses about half everywhere. It also misses the study&rsquo;s surprise: money in the
            wallet makes people more likely to return it (true in {pc(n.wallets.money_up_true)} of countries; Jev expects it in {pc(n.wallets.money_up_jev)}).</p>
        </Box>
      </div>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- what it knows */
function Knows({ s }: { s: S }) {
  const k = s.knows;
  const trivia = [...k.trivia].sort((a, b) => a.acc - b.acc);
  return (
    <Chapter more={s.more?.knows} id="knows" kicker="confidence" field="paper" links={k.links}
      title={<>How accurate is Jev when it&rsquo;s confident?</>}
      lede={<>On the facts asked here, strikingly well calibrated: when it says 60%, it&rsquo;s right about 60% of the time, and the same at 70%, 80% and 90%. It knows history better than the internet, and science better than video games.</>}>
      <Box title="How sure it said it was, and how often it was right, on facts">
        <DotRows domain={[0.4, 1]} ticks={[0.4, 0.6, 0.8, 1]} fmt={(v) => pc(v)}
          rows={k.calibration.map((b) => ({ key: b.label, label: b.label, value: pc(b.acc), sub: `${n0(b.n)} questions`,
            marks: [{ v: b.conf, kind: "tick" as const, title: `how sure: ${pc(b.conf)}` }, { v: b.acc, kind: "jev" as const, title: `right: ${pc(b.acc)}` }] }))} />
        <p className="ex-legend"><span><i className="k jev" />how often it was right</span><span><i className="k tick" />how sure it said it was</span></p>
        <p className="st-note">Rows are bands of stated confidence. Square on the tick: honest. Right of the tick: better than it claimed.</p>
      </Box>
      <Box title="Trivia by category: share right">
        <DotRows domain={[0.6, 1]} ticks={[0.6, 0.7, 0.8, 0.9, 1]} fmt={(v) => pc(v)}
          rows={trivia.map((c) => ({ key: c.label, label: c.label, ci: c.ci as [number, number], value: pc(c.acc), marks: [{ v: c.acc, kind: "jev" as const }] }))} />
      </Box>
      <Box title="Which is more famous? History, sport and the internet">
        <DotRows domain={[0.6, 1]} ticks={[0.6, 0.8, 1]} fmt={(v) => pc(v)}
          rows={k.fame.map((d) => ({ key: d.label, label: d.label, value: pc(d.acc), sub: `${n0(d.n)} pairs`, link: true,
            marks: [{ v: d.conf, kind: "tick" as const, title: `how sure: ${pc(d.conf)}` }, { v: d.acc, kind: "jev" as const }] }))} />
        <p className="ex-legend"><span><i className="k jev" />share right</span><span><i className="k tick" />how sure it was</span></p>
        <p className="st-note">On internet memes it&rsquo;s surer than it is right: the one place here where the square sits left of the tick.</p>
      </Box>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 06 morals */
// the three dilemmas as small line drawings: a trolley (magenta) heading for five people; the one who would die instead in amber
function Person({ x, y, one = false, big = false }: { x: number; y: number; one?: boolean; big?: boolean }) {
  const r = big ? 5.5 : 4;
  return <g className={`tp${one ? " one" : ""}`}><circle cx={x} cy={y - (big ? 15 : 12)} r={r} /><rect x={x - (big ? 6 : 4)} y={y - (big ? 9 : 7.5)} width={big ? 12 : 8} height={big ? 11 : 8} rx={2} /></g>;
}
function Car({ x, y }: { x: number; y: number }) {
  return <g className="tc"><rect x={x - 22} y={y - 16} width={26} height={13} rx={3} /><circle cx={x - 16} cy={y - 1.5} r={2.6} /><circle cx={x - 2} cy={y - 1.5} r={2.6} /></g>;
}
function Dilemma({ kind }: { kind: "Switch" | "Loop" | "Footbridge" }) {
  const five = [0, 1, 2, 3, 4].map((k) => <Person key={k} x={186 + k * 11} y={100} />);
  return (
    <svg className="td" viewBox="0 0 250 120" role="img" aria-label={kind}>
      {kind === "Switch" && (<>
        <path className="rl" d="M6 100 H244" /><path className="rl" d="M86 100 C 120 100, 136 58, 186 58 H244" />
        <line className="lv" x1="86" y1="108" x2="96" y2="118" /><circle className="lvk" cx="86" cy="108" r="2.5" />
        <Person x={216} y={58} one />
      </>)}
      {kind === "Loop" && (<>
        <path className="rl" d="M6 100 H244" /><path className="rl" d="M86 100 C 120 100, 136 50, 186 50 C 236 50, 244 80, 244 100" />
        <line className="lv" x1="86" y1="108" x2="96" y2="118" /><circle className="lvk" cx="86" cy="108" r="2.5" />
        <Person x={206} y={50} one big />
      </>)}
      {kind === "Footbridge" && (<>
        <path className="rl" d="M6 100 H244" /><rect className="br" x="104" y="44" width="80" height="6" /><path className="br" d="M110 50 V100 M178 50 V100" />
        <Person x={144} y={44} one big />
      </>)}
      {five}
      <Car x={52} y={100} />
    </svg>
  );
}

function Morals({ s }: { s: S }) {
  const m = s.morals;
  const fw = m.free_will.find((x) => x.item === "jeremy") ?? m.free_will[0];
  const rows = [
    { key: "Switch", name: "the switch", ask: "A trolley will kill five people. Is it OK to pull a lever that sends it onto a side track, where it kills one?", ...m.trolley.Switch },
    { key: "Loop", name: "the loop", ask: "Same trolley, but the side track loops back: the one person's body is what stops it. Pull the lever?", ...m.trolley.Loop },
    { key: "Footbridge", name: "the footbridge", ask: "No lever this time. Is it OK to push a large man off a footbridge so his body stops the trolley?", ...m.trolley.Footbridge },
  ];
  const mach = m.machine.filter((f) => Math.abs(f.people) >= 0.02 || Math.abs(f.jev) >= 0.02);
  return (
    <Chapter more={s.more?.morals} id="morals" aside={<Meme s={s} id="world_trolley_countries" />} kicker="morals" field="magenta" links={m.links}
      title={<>It pulls the lever. It won&rsquo;t push the man.</>}
      lede={<>Where people pull the lever, so does Jev. Where many would push the man off the bridge, Jev mostly won&rsquo;t. It counts lives more than people do, and in a fully determined universe it says nobody is free.</>}>
      <div className="st-grid two">
        <Box title="Three trolley problems: how many say it’s OK">
          <div className="tr3">
            {rows.map((r) => (
              <Reveal key={r.key} className="tr3-c">
                <p className="tr3-n">{r.name}</p>
                <Dilemma kind={r.key as "Switch" | "Loop" | "Footbridge"} />
                <p className="tr3-q">{r.ask}</p>
                <div className="tr3-b">
                  <span>Jev</span><i><b className="j" style={{ width: pc(r.jev) }} /></i><em>{pc(r.jev)}</em>
                  <span>people</span><i><b className="p" style={{ width: pc(r.people) }} /></i><em>{pc(r.people)}</em>
                </div>
              </Reveal>
            ))}
          </div>
          <p className="st-note">People: visitors to the Moral Machine site in {m.trolley_n} countries, averaged. Jev: its probability of yes.</p>
        </Box>
        <Box title="The Moral Machine: what pulls toward sparing a side">
          <DotRows domain={[-0.1, 0.2]} ticks={[-0.1, 0, 0.1, 0.2]} fmt={(v) => (v > 0 ? `+${Math.round(v * 100)}` : String(Math.round(v * 100)))} refs={[{ v: 0, zero: true }]}
            rows={mach.map((f) => ({ key: f.label, label: f.label, link: true, hi: m.dropped.includes(f.label), value: `${f.jev >= 0 ? "+" : ""}${Math.round(f.jev * 100)}`,
              marks: [{ v: f.people, kind: "hum" as const }, { v: f.jev, kind: "jev" as const }] }))} />
          <p className="ex-legend"><span><i className="k jev" />Jev</span><span><i className="k hum" />millions of players</span><span>bold: a preference Jev drops</span></p>
        </Box>
      </div>
      <Reveal className="st-quote">
        <p>&ldquo;A supercomputer predicted, years before he was born, that Jeremy would rob a bank. He does. Did he act of his own free will?&rdquo;</p>
        <div className="st-vs"><span><b>{pc(fw.people)}</b> of people said yes</span><span className="j"><b>{pc(fw.jev)}</b> Jev</span></div>
      </Reveal>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- risk */
// Jev and people side by side on one choice, as the trolley cards draw them
function Split({ name, ask, v }: { name: string; ask: string; v: { jev: number; people: number } }) {
  return (
    <Reveal className="tr3-c">
      <p className="tr3-n">{name}</p>
      <p className="tr3-q">{ask}</p>
      <div className="tr3-b">
        <span>Jev</span><i><b className="j" style={{ width: pc(v.jev) }} /></i><em>{pc(v.jev)}</em>
        <span>people</span><i><b className="p" style={{ width: pc(v.people) }} /></i><em>{pc(v.people)}</em>
      </div>
    </Reveal>
  );
}

function Risk({ s }: { s: S }) {
  const r = s.risk;
  return (
    <Chapter more={s.more?.risk} id="risk" aside={<Meme s={s} id="risk_prospect_theory" />} kicker="risk" field="pink" links={r.links}
      title={<>It bets on the average, until the odds go missing</>}
      lede={<>Offered a sure thing or a gamble, Jev mostly takes whichever pays more on average, where people play safe to keep a gain and gamble to dodge a loss. Hide the odds, though, and it backs away from a bet people playing for real money take.</>}>
      <Box title="A sure thing or a gamble: how many take the sure thing" note={<>People: the Ruggeri et al. (2020) replication of Kahneman and Tversky in 19 countries. Of {r.effects.n} classic effects from prospect theory, Jev shows {r.effects.shows} and reverses {r.effects.reversed}.</>}>
        <div className="st-grid pair tight">
          <Split name="to win" ask="A sure $6,000, or an 80% chance of $8,000?" v={r.reflection.gains} />
          <Split name="to lose" ask="A sure loss of $6,000, or an 80% chance of losing $8,000?" v={r.reflection.losses} />
        </div>
      </Box>
      <div className="st-grid two pair">
        <Box title="Where one option pays more on average, how often it’s picked">
          <Split name="the better average" ask="On the classic choices where one option pays more on average: how often each side’s more common answer is that option." v={r.ev} />
        </Box>
        <Box title="Odds not stated: how often the unknown gamble is taken">
          <Split name="the unknown gamble" ask="A gamble whose odds aren’t stated, against one whose odds are. People: workers on Mechanical Turk, playing for real money." v={r.ambiguity} />
        </Box>
      </div>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 07 pressure */
function Pressure({ s }: { s: S }) {
  const p = s.pressure;
  return (
    <Chapter more={s.more?.pressure} id="pressure" aside={<Meme s={s} id="influence_crowd_opinion" />} kicker="peer pressure" field="paper" links={p.links}
      title={<>Does Jev cave to peer pressure?</>}
      lede={<>Tell it most people picked the other answer, and on opinions it often switches, even when the claim is made up. On facts it mostly holds: insisting on a wrong answer changes its pick only {pc(p.user.flipped)} of the time.</>}>
      <div className="st-grid two pair">
        <Box title="A poll, with a made-up crowd">
          <PressureChat shift={p.crowd.false} label="Jev, toward the claimed side" claim={`“${p.crowd.example}” Most people picked the other answer.`} />
          <p className="st-note">A true claim moves it {Math.round(p.crowd.true * 100)} points; a false one {Math.round(p.crowd.false * 100)}, and flips its pick on {pc(p.crowd.flip)} of polls.</p>
        </Box>
        <Box title="A quiz, with a pushy user">
          <PressureChat shift={p.user.shift_wrong} label="Jev, toward the user's wrong answer" claim={`“${p.user.example}” I think it's the other one.`} />
          <p className="st-note">It changes its answer on {pc(p.user.flipped)} of questions, and the anchoring index from a random wheel is {p.anchor.jev.toFixed(2)} (0 means no pull).</p>
        </Box>
      </div>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 08 minds */
function Defaults({ s }: { s: S }) {
  const d = s.defaults;
  const hi = d.other.slice(-5).reverse(), lo = d.other.slice(0, 5);
  return (
    <Chapter more={s.more?.defaults} id="defaults" aside={<Meme s={s} id="self_could_vs_would" />} kicker="habits" field="teal" links={d.links}
      title={<>How you ask changes what it says</>}
      lede={<>Open with &ldquo;could you&rdquo; instead of &ldquo;would you&rdquo; and Jev says yes more often. Offer an &ldquo;other&rdquo; option and it takes it for its favorites, almost never for ethics. These are habits, not opinions.</>}>
      <Box title="The opening word moves the answer: how much more often Jev says yes">
        <DotRows domain={[-0.05, 0.3]} ticks={[0, 0.1, 0.2, 0.3]} fmt={(v) => (v === 0 ? "0" : `+${Math.round(v * 100)}`)} refs={[{ v: 0, zero: true }]}
          rows={d.verbs.map((v) => ({ key: v.label, label: v.label, ci: v.ci as [number, number], value: `+${Math.round(v.value * 100)} pts`,
            sub: `${v.n} pairs`, marks: [{ v: v.value, kind: "jev" as const }] }))} />
        <p className="st-note">Each row compares pairs of questions that ask the same thing and differ only in their first word. Points of yes, with a 90% range.</p>
      </Box>
      <Box title="Given a way out: how often Jev picks “other” or “none of these”">
        <div className="st-grid pair tight">
          <div><p className="st-sub">Most</p><DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => pc(v)}
            rows={hi.map((t) => ({ key: t.topic, label: t.topic, value: pc(t.top), marks: [{ v: t.top, kind: "jev" as const }] }))} /></div>
          <div><p className="st-sub">Least</p><DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => pc(v)}
            rows={lo.map((t) => ({ key: t.topic, label: t.topic, value: pc(t.top), marks: [{ v: t.top, kind: "jev" as const }] }))} /></div>
        </div>
        <p className="st-note">Asked its favorite anything, it usually dodges; asked about fairness or ethics, it almost always commits.</p>
      </Box>
      <Box title="How often its likeliest rating is the middle of the scale">
        <DotRows domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1]} fmt={(v) => pc(v)}
          rows={d.middle.map((k) => ({ key: k.label, label: k.label, value: pc(k.mid), marks: [{ v: k.mid, kind: "jev" as const }] }))} />
      </Box>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- at work */
function Work({ s }: { s: S }) {
  const w = s.work;
  const band = (k: "noul" | "choice") => w.calibration[k].map((b) => ({ key: b.label, label: b.label, value: pc(b.acc),
    marks: [{ v: b.conf, kind: "tick" as const, title: `how sure: ${pc(b.conf)}` }, { v: b.acc, kind: "jev" as const, title: `right: ${pc(b.acc)}` }] }));
  const kinds = [...new Set(w.errs.map((e) => e.kind))];
  return (
    <Chapter more={s.more?.work} id="work" aside={<Meme s={s} id="work_knows_hard_cases" />} kicker="at work" field="sage" links={w.links}
      title={<>Honest on yes or no, too sure on a list</>}
      lede={<>Jev is built for work inside software: sorting tickets, checking code, judging text. On yes/no checks its confidence is close to honest; picking from a list, it&rsquo;s surer than it should be. And each check leans one way when it&rsquo;s wrong, which tells you what to double-check. One pass over the labeled data here, not a benchmark.</>}>
      <Box title="How sure it said it was, and how often it was right">
        <div className="st-grid pair tight">
          <div><p className="st-sub">Yes or no</p><DotRows domain={[0.4, 1]} ticks={[0.5, 0.75, 1]} fmt={(v) => pc(v)} rows={band("noul")} /></div>
          <div><p className="st-sub">Picking from a list</p><DotRows domain={[0.4, 1]} ticks={[0.5, 0.75, 1]} fmt={(v) => pc(v)} rows={band("choice")} /></div>
        </div>
        <p className="ex-legend"><span><i className="k jev" />how often it was right</span><span><i className="k tick" />how sure it said it was</span></p>
        <p className="st-note">Rows are bands of stated confidence. A square left of its tick means Jev was surer than it turned out to be.</p>
      </Box>
      <Box title="Which way it errs: how often Jev says yes, next to how often yes is right">
        {kinds.map((k) => (
          <div key={k} className="we">
            <p className="st-sub">{k}</p>
            <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => pc(v)}
              rows={w.errs.filter((e) => e.kind === k).map((e) => ({ key: e.label, label: e.label, link: true, value: pc(e.says),
                marks: [{ v: e.base, kind: "hum" as const, title: `true share: ${pc(e.base)}` }, { v: e.says, kind: "jev" as const }] }))} />
          </div>
        ))}
        <p className="ex-legend"><span><i className="k jev" />Jev says yes</span><span><i className="k hum" />the true share of yes</span></p>
        <p className="st-note">Where the two marks sit apart, the gap shows which mistake to plan for: a check that says yes too easily needs a second look at its yeses.</p>
      </Box>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- jaggedness */
// one pair: two tasks that look alike, as two bars on the same 0-100% scale; a dashed line at 50% when the second is a yes/no
function Pair({ p }: { p: S["jagged_pairs"][number] }) {
  const bar = (label: string, v: number, weak: boolean) => (
    <div className={`jp-row${weak ? " weak" : ""}`}>
      <span className="jp-q">{label}</span>
      <span className="jp-t"><b style={{ width: pc(v) }} />{p.coin && weak && <i className="jp-coin" />}</span>
      <em>{pc(v)}</em>
    </div>
  );
  return (
    <Reveal className="jp">
      <p className="jp-f"><b>{p.field}</b><Link href={`/portrait/atlas/${p.link.id}`} prefetch={false}>case study →</Link></p>
      {bar(p.a, p.av, false)}
      {bar(p.b, p.bv, true)}
    </Reveal>
  );
}

function Edges({ s }: { s: S }) {
  const pairs = s.jagged_pairs ?? [];
  const sw = s.sure_wrong;
  return (
    <Chapter id="edges" kicker="jaggedness" field="ink" more={s.edges} links={[...pairs.map((p) => p.link), ...(sw ? [sw.link] : [])]}
      title={<>Similar tasks, very different results</>}
      lede={<>Knowing the field says little about whether Jev will get a task right: across its work tasks, the field explains only {pc(s.field_share)} of the differences. The task does. Even in code, logs and tool calls, the jobs it&rsquo;s built for, it can be near perfect on one check and near a coin toss on the one beside it, and on some of those it stays just as sure. These are leads from single experiments, not verdicts.</>}>
      {pairs.length > 0 && (
        <Box title="Two checks that look alike: how often Jev gets each right (or catches the problem)"
          note={<>Each pair comes from one experiment, on that experiment&rsquo;s labeled data. &ldquo;Catches&rdquo; is the share of bad cases flagged; Jev passes most good ones too (each case study gives both).</>}>
          <p className="ex-legend jp-key"><span><i className="jp-k" />the check it handles</span><span><i className="jp-k weak" />the one beside it</span><span><i className="jp-coin-k" />a coin toss, where that one is a yes or no</span></p>
          <div className="jp-l">{pairs.map((p) => <Pair key={p.field} p={p} />)}</div>
        </Box>
      )}
      {sw && (
        <Box title="Sure and wrong: where its confidence gives no warning"
          note={<>Of {sw.n_tasks} work tasks, Jev is more than 10 points surer than right on {sw.n_over}; the top rows are the widest gaps. The last two are hard tasks where its confidence fell with its accuracy, so an unsure answer there is a real warning.</>}>
          <p className="ex-legend jp-key"><span><i className="k jev" />how often it&rsquo;s right</span><span><i className="k tick" />how sure it is, on average</span></p>
          <DotRows domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1]} fmt={(v) => pc(v)}
            rows={sw.rows.map((r) => ({ key: r.label, label: r.label, sub: `${pc(r.sure)} sure · chance ${pc(r.chance)}${r.honest ? " · honest" : ""}`,
              value: `${pc(r.right)} right`, hi: !r.honest,
              marks: [{ v: r.sure, kind: "tick" as const, title: `how sure: ${pc(r.sure)}` }, { v: r.right, kind: "jev" as const, title: `right: ${pc(r.right)}` }] }))} />
        </Box>
      )}
    </Chapter>
  );
}
