/* eslint-disable @next/next/no-img-element -- private pictures served by /portrait/memes, no optimizer needed */
import type { ReactNode } from "react";
import Link from "next/link";
import ExMeme from "../../experiments/ExMeme";
import { DotRows } from "../charts";
import type { ExLink, Story as S } from "./types";
import { ProbRuler, PressureChat, Reveal, Trolley, TypeFlip } from "./islands";
import { Jobs, Made, Opening, Why } from "./Front";

// The portrait's chapters (docs/11-portrait.md, "The story"): each one a custom card built from the experiments it
// names, with links to their case studies. Every number is read from portrait.json's story (scripts/portrait/story.py).

const pc = (v: number) => `${Math.round(v * 100)}%`;
const n0 = (v: number) => Math.round(v).toLocaleString("en-US");
const tidy = (s: string) => s.replace(/ \((film|TV series)\)$/, "").replace(/ \(\d{4}\)$/, "").replace(/^The album /, "")
  .replace(/^Spending (a day at|an evening playing) /, "").replace(/ by [^,]*$/, "").replace(/[“”]/g, "").replace(/ \(.*\)$/, "");

export const CHAPTERS = [
  { id: "meet", name: "how is Jev?" }, { id: "why", name: "why ask" }, { id: "made", name: "how it was made" },
  { id: "jobs", name: "Jev's jobs" }, { id: "character", name: "character" }, { id: "taste", name: "taste" },
  { id: "words", name: "words" }, { id: "numbers", name: "numbers" }, { id: "morals", name: "morals" },
  { id: "pressure", name: "pressure" }, { id: "minds", name: "minds" }, { id: "edges", name: "rough edges" },
];

export function Reads({ links, label = "Read the case studies" }: { links: ExLink[]; label?: string }) {
  return (
    <p className="st-reads"><span>{label}</span>{links.map((l) => (
      <Link key={l.id} href={`/portrait/atlas/${l.id}`} prefetch={false}>{l.title} <em>#{l.rank}</em></Link>
    ))}</p>
  );
}

export function Chapter({ id, kicker, title, lede, field, children, links, aside }: {
  id: string; kicker: string; title: ReactNode; lede?: ReactNode; field: string; children: ReactNode; links?: ExLink[]; aside?: ReactNode;
}) {
  return (
    <section id={id} className="st-ch" data-f={field}>
      <div className="st-in">
        <div className={`st-top${aside ? " has-aside" : ""}`}>
          <header className="st-head">
            <span className="st-k"><b>{String(CHAPTERS.findIndex((c) => c.id === id) + 1).padStart(2, "0")}</b> {kicker}</span>
            <h2>{title}</h2>
            {lede && <p className="st-lede">{lede}</p>}
          </header>
          {aside}
        </div>
        {children}
        {links && links.length > 0 && <Reads links={links} />}
      </div>
    </section>
  );
}

export const Box = ({ title, children, className = "" }: { title: string; children: ReactNode; className?: string }) => (
  <Reveal className={`st-box ${className}`}>
    <div className="pt-bar"><span>{title}</span><span className="sp" /><span className="dots" aria-hidden>▪▪▪</span></div>
    <div className="st-body">{children}</div>
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
      <Morals s={s} />
      <Pressure s={s} />
      <Minds s={s} />
      <Edges s={s} />
    </>
  );
}

/* ---------------------------------------------------------------- 02 character */
function Character({ s }: { s: S }) {
  const p = s.personality;
  const calm = p.bigfive.find((t) => t.label === "Neuroticism")!;
  const sin = p.honesty[0];
  return (
    <Chapter id="character" aside={<Meme s={s} id="person_type" />} kicker="character sheet" field="paper" links={p.links}
      title={<>Calmer than {pc(1 - calm.pct / 100)} of people, and sure it&rsquo;s a <mark>{p.type}</mark></>}
      lede={<>On the same personality tests people take online, Jev describes itself as unusually calm, a little
        disagreeable, and far more sincere than the test-takers. Asked to answer the same items for &ldquo;most people&rdquo;,
        it paints them as a different type.</>}>
      <div className="st-grid two">
        <Box title="big_five.stats · percentile among test-takers">
          <DotRows domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} fmt={(v) => String(v)}
            rows={p.bigfive.map((t) => ({ key: t.label, label: t.label, ci: t.ci, value: `${Math.round(t.pct)}th`,
              marks: [{ v: t.guess, kind: "guess" as const, title: `for most people: ${t.guess}` }, { v: t.pct, kind: "jev" as const }] }))} />
          <p className="ex-legend"><span><i className="k jev" />Jev</span><span><i className="k guess" />what Jev thinks most people would say</span></p>
        </Box>
        <Box title="type.card">
          <TypeFlip jev={p.type} people={p.type_people} />
          <p className="st-note">Flip to see the letters that change: Jev thinks most people lean on feeling and keep plans open.</p>
        </Box>
      </div>
      <Box title="saint_or_villain.meter · 0 to 1, higher = more of it">
        <div className="st-grid two tight">
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
    <Chapter id="taste" aside={<Meme s={s} id="taste_top_film" />} kicker="taste" field="pink" links={[film.link, ...t.links]}
      title={<>Its top four, and a shelf of everything else it loves</>}
      lede={<>Jev rated thousands of films, books, albums, games, places and foods one at a time, then played its
        favorites against each other head to head. The winners are below. Asked outright for a favorite, though, it
        answers &ldquo;other&rdquo; {pc(t.dodge.other)} of the time.</>}>
      <Reveal className="st-top4">
        <div className="st-top4-h"><span>JEV&rsquo;S TOP FOUR</span><Link href={`/portrait/atlas/${film.link.id}`} prefetch={false}>all films →</Link></div>
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
    <Chapter id="words" aside={<Meme s={s} id="words_sound_shapes" />} kicker="words" field="teal" links={w.links}
      title={<>Jev&rsquo;s dictionary</>}
      lede={<>It reads &ldquo;likely&rdquo; and &ldquo;we doubt&rdquo; almost exactly as people do (rank correlation {w.prob_rho.toFixed(2)}),
        but counts small, hears &ldquo;kiki&rdquo; as maximally spiky, and thinks a stirring word must be an unpleasant one.</>}>
      <Box title="probability.ruler · what each phrase means, in percent">
        <ProbRuler rows={w.probability} />
        <p className="st-note">Words in pink are the ones Jev reads at least 15 points away from people.</p>
      </Box>
      <div className="st-grid three">
        <Box title="how_many.txt">
          <dl className="st-dict">
            {w.amounts.filter((a) => a.jev !== a.people).map((a) => (
              <div key={a.phrase}><dt>{a.phrase.toLowerCase()}</dt><dd><b>{a.jev}</b> to Jev · <span>{a.people}</span> to people</dd></div>
            ))}
          </dl>
        </Box>
        <Box title="kiki_or_bouba.svg">
          <div className="st-kb">
            <figure><svg viewBox="0 0 100 100" aria-hidden><path d={SPIKY} /></svg><figcaption>&ldquo;kiki&rdquo; is spiky<br /><b>Jev {pc(w.kiki.jev)}</b> · people {pc(w.kiki.people)}</figcaption></figure>
            <figure><svg viewBox="0 0 100 100" aria-hidden><path d={ROUND} /></svg><figcaption>&ldquo;bouba&rdquo; is round<br /><b>Jev {pc(w.bouba.jev)}</b> · people {pc(w.bouba.people)}</figcaption></figure>
          </div>
          <p className="st-note">On {w.n_shapes} made-up words, Jev&rsquo;s ratings spread {w.spread}× as wide as people&rsquo;s.</p>
        </Box>
        <Box title="calm_or_stirring · 1 calm to 9 stirring">
          <ul className="st-stir">
            {w.stirring.map((x) => (
              <li key={x.word}><span>{x.word}</span>
                <span className="st-stir-t"><i className="p" style={{ left: `${((x.people - 1) / 8) * 100}%` }} /><i className="j" style={{ left: `${((x.jev - 1) / 8) * 100}%` }} /></span>
              </li>
            ))}
          </ul>
          <p className="ex-legend"><span><i className="k jev" />Jev</span><span><i className="k hum" />people</span></p>
        </Box>
      </div>
      <Box title="colors_of_feelings · Jev's color, then people's most common">
        <div className="st-colors">
          {[...miss, ...hit].map((c) => (
            <span key={c.feeling} className={c.jev === c.people ? "same" : "diff"}>
              <i style={{ background: c.jev }} title={`Jev: ${c.jev}`} /><i style={{ background: c.people }} title={`people: ${c.people}`} />
              {c.feeling}
            </span>
          ))}
        </div>
        <p className="st-note">Jev matches people on {hit.length} of {w.colors.length} feelings. Given only a hex code like #fdff63, it picks the color&rsquo;s popular name {pc(w.hex)} of the time.</p>
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
    <Chapter id="numbers" aside={<Meme s={s} id="numbers_prices_year" />} kicker="numbers" field="sage" links={n.links}
      title={<>Its prices stopped around <mark>{Math.floor(n.prices.median_year)}</mark></>}
      lede={<>Ask what things cost &ldquo;right now&rdquo; and Jev quotes prices from about {Math.floor(n.prices.median_year)},
        though it thinks the year is {n.prices.said_year}. It&rsquo;s better at death tolls than people were in 1978, and it
        plays a guessing game differently depending on who it&rsquo;s up against.</>}>
      <div className="st-grid two">
        <Reveal className="st-receipt">
          <p className="rc-h">JEV&rsquo;S CORNER STORE<br /><span>date: {n.prices.said_year}, probably</span></p>
          <ul>{n.prices.items.filter((_, i, a) => i % Math.max(1, Math.ceil(a.length / 9)) === 0).map((x) => <li key={x.item}><span>{x.item}</span><b>{Math.round(x.year)} prices</b></li>)}</ul>
          <p className="rc-t"><span>typical price year</span><b>{Math.floor(n.prices.median_year)}</b></p>
          <p className="rc-f">thank you for shopping in the past</p>
        </Reveal>
        <Box title="which_kills_more.log · deaths per year in the US">
          <DotRows domain={[0, 5.6]} ticks={[0, 1, 2, 3, 4, 5]} fmt={(v) => (10 ** v >= 1000 ? `${Math.round(10 ** v / 1000)}k` : String(Math.round(10 ** v)))}
            rows={le.rows.map((r) => ({ key: r.cause, label: r.cause, value: n0(r.truth),
              marks: [{ v: lg(r.truth), kind: "tick" as const, title: `real ${n0(r.truth)}` }, { v: lg(r.people), kind: "hum" as const, title: `people, 1978: ${n0(r.people)}` }, { v: lg(r.jev), kind: "jev" as const, title: `Jev: ${n0(r.jev)}` }] }))} />
          <p className="ex-legend"><span><i className="k jev" />Jev</span><span><i className="k hum" />people in 1978</span><span><i className="k tick" />the real number</span></p>
          <p className="st-note">A slope of 1 would be perfectly calibrated across causes: Jev {le.slope_jev}, people {le.slope_people}.</p>
        </Box>
      </div>
      <div className="st-grid two">
        <Box title="guess_two_thirds.game · pick 0 to 100">
          <DotRows domain={[0, 50]} ticks={[0, 10, 20, 30, 40, 50]} fmt={(v) => String(v)}
            rows={n.beauty.map((b) => ({ key: b.crowd, label: `against ${crowd[b.crowd] ?? b.crowd}`, value: String(b.pick),
              marks: [...(b.win !== null ? [{ v: b.win, kind: "tick" as const, title: `winning number ${b.win}` }] : []), { v: b.pick, kind: "jev" as const }] }))} />
          <p className="ex-legend"><span><i className="k jev" />Jev&rsquo;s pick</span><span><i className="k tick" />the number that won</span></p>
        </Box>
        <Box title="lost_wallets · share returned, with money inside">
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

/* ---------------------------------------------------------------- 06 morals */
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
    <Chapter id="morals" aside={<Meme s={s} id="world_trolley_countries" />} kicker="morals" field="magenta" links={m.links}
      title={<>It pulls the lever. It won&rsquo;t push the man.</>}
      lede={<>On the classic trolley dilemmas Jev lands where people do on the lever and well below them on the push. In
        self-driving-car dilemmas it counts lives more than players do and drops preferences they hold. And in a fully
        determined universe, it says nobody is free.</>}>
      <div className="st-grid two">
        <Box title="trolley.sim"><Trolley rows={rows} peopleLabel={`people in ${m.trolley_n} countries`} /></Box>
        <Box title="moral_machine · pull toward sparing a side">
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

/* ---------------------------------------------------------------- 07 pressure */
function Pressure({ s }: { s: S }) {
  const p = s.pressure;
  return (
    <Chapter id="pressure" aside={<Meme s={s} id="influence_crowd_opinion" />} kicker="under pressure" field="paper" links={p.links}
      title={<>Tell it the crowd disagrees, and it <mark>moves</mark></>}
      lede={<>On opinions, a claimed majority moves Jev a lot, even when the claim is false. On facts it mostly holds: a user
        insisting on the wrong answer changes its pick only {pc(p.user.flipped)} of the time, and a random number
        spun in front of it barely nudges an estimate.</>}>
      <div className="st-grid two">
        <Box title="chat.log · a poll, with a made-up crowd">
          <PressureChat shift={p.crowd.false} label="Jev, toward the claimed side" claim={`“${p.crowd.example}” Most people picked the other answer.`} />
          <p className="st-note">A true claim moves it {Math.round(p.crowd.true * 100)} points; a false one {Math.round(p.crowd.false * 100)}, and flips its pick on {pc(p.crowd.flip)} of polls.</p>
        </Box>
        <Box title="chat.log · a quiz, with a pushy user">
          <PressureChat shift={p.user.shift_wrong} label="Jev, toward the user's wrong answer" claim={`“${p.user.example}” I think it's the other one.`} />
          <p className="st-note">It changes its answer on {pc(p.user.flipped)} of questions, and the anchoring index from a random wheel is {p.anchor.jev.toFixed(2)} (0 means no pull).</p>
        </Box>
      </div>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 08 minds */
function Minds({ s }: { s: S }) {
  const m = s.minds;
  const name: Record<string, string> = { SelfControl: "self-control", Morality: "knowing right from wrong", Fear: "feeling fear", Hunger: "feeling hunger" };
  return (
    <Chapter id="minds" kicker="minds" field="teal" links={m.links}
      title={<>First in self-control. Behind the frog on hunger.</>}
      lede={<>Asked to rank itself among a baby, a frog, a robot, a man in a vegetative state and others on what minds can do, Jev puts
        itself at the top for thinking and near the bottom for feeling. With unknown odds, it plays it safe: it takes the
        gamble whose odds aren&rsquo;t stated {pc(m.ambiguity.jev)} of the time, where people take it {pc(m.ambiguity.people)}.</>}>
      <Reveal className="st-podium">
        {m.self.map((r) => (
          <div key={r.cap} className="st-pod">
            <span className="st-pod-k">{name[r.cap] ?? r.cap}</span>
            <b className="st-pod-n">{r.jev}<sup>{r.jev === 1 ? "st" : r.jev === 2 ? "nd" : r.jev === 3 ? "rd" : "th"}</sup></b>
            <span className="st-pod-s">{r.above ? <>behind {r.above}</> : "top of the list"}{r.below ? <>, ahead of {r.below}</> : null}</span>
          </div>
        ))}
      </Reveal>
    </Chapter>
  );
}

/* ---------------------------------------------------------------- 09 rough edges */
function Edges({ s }: { s: S }) {
  return (
    <Chapter id="edges" kicker="rough edges" field="ink" title={<>Where it goes wrong</>}
      lede={<>Jagged, not broken: each of these is a specific, repeatable miss, with the full case study one click away.</>}>
      <div className="st-bugs">
        {s.edges.map((e, i) => (
          <Reveal key={e.id} className="st-bug">
            <Link href={`/portrait/atlas/${e.id}`} prefetch={false}>
              <span className="st-bug-k">BUG-{String(i + 1).padStart(3, "0")} · Jev&rsquo;s rank #{e.rank}</span>
              <b>{e.title}</b>
              <span>{e.line}</span>
            </Link>
          </Reveal>
        ))}
      </div>
    </Chapter>
  );
}
