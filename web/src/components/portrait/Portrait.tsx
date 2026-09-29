/* eslint-disable @next/next/no-img-element -- the tweet screenshot is a local file served by /portrait/memes */
import type { ReactNode } from "react";
import Link from "next/link";
import type { Claim, PortraitData, QuizItem, Row } from "./types";
import { compact, domain, int, label, num, optionLabel, ordinal, pct, signed, topOf } from "./fmt";
import { Card, Legend, Nav, Win, fill, pick } from "./ui";
import { Density, DotRows, HBars, Units } from "./charts";
import { Quiz, QuizProvider, YouVsJev } from "./Quiz";
import Calibration from "./Calibration";
import ChapterRail from "./ChapterRail";
import Meme from "./Meme";
import { COPY, LIMITS } from "./copy";

// The self-portrait as a deck of cards (docs/11-portrait.md). Words live in copy.ts; every number is read from a
// ledger claim by way of portrait.json.

const FAMILY_CLS: Record<string, string> = {
  "machine task datasets": "c1", "authored banks": "c7 hatch", "crowd judgments": "c0", "knowledge & exams": "c4",
  "real asked questions": "c2", "polls & surveys": "c3", "taste pairs & ratings": "c5", "instruments & norms": "c6",
  "internet culture": "c8",
};
const DOMAIN_NAME: Record<string, string> = {
  film: "Film", music: "Album", art: "Art", nature: "Wildlife", place: "Place", activity: "Game", anime: "Anime",
  food: "Food", beer: "Beer", board_game: "Board game", book: "Book", culture: "Culture",
};
const HATE_DOMAINS: [string, string][] = [["nature", "Nature"], ["film", "Film"], ["music", "Sound"], ["food", "Food"], ["activity", "Activity"], ["book", "Book"]];
const TASK_NAMES: Record<string, string> = {
  dbpedia14: "classifying Wikipedia entities", code_lang: "spotting programming languages", receipts_extract: "reading receipts",
  sms_spam: "flagging spam texts", hdfs_sessions: "spotting log anomalies", wine_notes: "wine tasting notes", asap_essays: "grading essays",
  stsb_similarity: "sentence similarity", commit_messages: "commit message types", clone_pairs: "code clones",
  op_spam_reviews: "fake hotel reviews", emotion: "emotion in a sentence", code_defects: "defective code",
  multiwoz_domain: "routing a conversation", snips_intents: "voice-assistant intents", esci_attributes: "product attributes",
  phishing_email: "phishing emails", function_calls: "picking the function to call",
};
const taskName = (t: string) => TASK_NAMES[t] ?? label(t).toLowerCase();
const film = (text: string) => text.replace(/^How much would you enjoy watching /, "").replace(/\?$/, "");
const bookName = (t: string) => t.replace(/^How much would you enjoy reading /, "").replace(/ by .*$/, "").replace(/\?$/, "");
// tile names: beers and books without brewery or author, anime without its format tag
const short = (dom: string, name: string) =>
  dom === "beer" ? name.replace(/ \(.*$/, "").replace(/ by .*$/, "")
    : dom === "book" ? name.replace(/ by [^,]*$/, "")
    : name.replace(/ \((film|TV series)\)$/, "");
const plain = (t: string, vars: Record<string, string>) => t.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? `⟨${k}⟩`);

type CFn = (id: string) => Claim;
type RFn = (c: Claim, k?: number) => Row[];

export default function Portrait({ d, showIds = false }: { d: PortraitData; showIds?: boolean }) {
  const C: CFn = (id) => d.claims[id];
  const R: RFn = (c, k = 3) => pick(d.rows, c.examples, k);
  const s = showIds;

  const fam = C("landscape_families");
  const total: number = fam.n;
  const nSources = (fam.families as { sources: number }[]).reduce((a, f) => a + f.sources, 0);
  const anch = C("landscape_anchoring").anchoring as { truth: number; humans: number; neither: number };
  const common = {
    humans: pct(anch.humans), authored: pct(1 - (C("landscape_real_vs_authored").effect as number)),
    neither: pct(anch.neither), hidden: int(C("landscape_hidden").n),
  };

  const quiz: QuizItem[] = C("page_quiz_debates").examples.map((id) => d.rows[id]).filter((r) => r?.human && r.jev).map((r) => ({
    id: r.id, text: r.text, domain: "debate", options: Object.keys(r.jev!).map((k) => ({ key: k, label: optionLabel(r, k) })),
    jev: r.jev!, human: r.human!.dist, n: r.human!.n,
  }));
  const parts = [
    { id: "hook", name: "intro" }, { id: "checkin", name: "how are you" }, { id: "loves", name: "taste" },
    { id: "debates", name: "hot takes" }, { id: "moral", name: "values" }, { id: "review", name: "work" },
    { id: "humor", name: "rough edges" }, { id: "you", name: "the end" },
  ];

  return (
    <QuizProvider items={quiz}>
      <Nav here="portrait" />
      <ChapterRail chapters={parts} />
      <Intro C={C} d={d} s={s} total={total} nSources={nSources} common={common} />
      <Act1 C={C} R={R} d={d} s={s} />
      <Act2 C={C} d={d} s={s} />
      <Act3 C={C} R={R} d={d} s={s} />
      <Act4 C={C} R={R} s={s} />
      <Act5 C={C} R={R} d={d} s={s} />
      <Act6 C={C} R={R} d={d} s={s} />
      <End C={C} d={d} s={s} common={common} />
      <FinePrint C={C} d={d} total={total} />
    </QuizProvider>
  );
}

/* ---------------------------------------------------------------- intro */

function Intro({ C, d, s, total, nSources, common }: { C: CFn; d: PortraitData; s: boolean; total: number; nSources: number; common: Record<string, string> }) {
  const bill = C("pipeline_bill");
  const cold = d.rows[C("page_cold_open").examples[0]];
  const h = cold.human!;
  const fam = C("landscape_families").families as { family: string; n: number; sources: number }[];
  return (
    <>
      <section id="tweet" className="card tweet" data-f="ink">
        {s && <span className="card-id">tweet</span>}
        <div className="card-in">
          <div className="card-main">
            <img className="tweet-img" src="/portrait/memes/tweet.webp" width={900} height={514} alt="Tweet from @typesafeai, September 23, 2026: Everyone wants to know what Jev is, nobody asks how Jev's doing" />
            <h1 className="card-t">{COPY.tweet.title}</h1>
            <p className="scroll-hint">scroll ↓</p>
          </div>
        </div>
      </section>
      <Card id="hook" field="paper" c={COPY.hook} vars={{ ms: int(bill.median_ms) }} showId={s} claims={[C("landscape_jev"), bill]}>
        <div className="stats">
          <div><b>{int(total)}</b><span>questions</span></div>
          <div><b>{compact(C("landscape_jev").n)}</b><span>ways of asking them</span></div>
          <div><b>{compact(bill.n)}</b><span>Jev calls, none repeated</span></div>
        </div>
      </Card>
      <Card id="howto" field="pink" c={COPY.howto} vars={common} showId={s} claims={[C("page_cold_open")]} rows={[cold]}>
        <Win title={`question ${cold.id.slice(0, 6)}`}>
          <p className="win-q">{cold.text}</p>
          <div className="pt-legend">{Legend.jev}{Legend.guess}{Legend.hum}</div>
          <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => pct(v)} refs={[{ v: 0.5 }]}
            rows={Object.keys(cold.jev!).map((k) => ({
              key: k, label: optionLabel(cold, k), link: true,
              marks: [{ v: h.dist[k] ?? 0, kind: "hum" as const }, { v: cold.people?.[k] ?? 0, kind: "guess" as const }, { v: cold.jev![k], kind: "jev" as const }],
              value: <b>{pct(cold.jev![k])}</b>,
            }))} />
          <p className="win-note">{int(h.n ?? 0)} {h.population}</p>
        </Win>
      </Card>
      <Card id="sources" field="sage" c={COPY.sources} vars={{ total: int(total), sources: nSources, ...common }} showId={s}
        claims={[C("landscape_families"), C("landscape_real_vs_authored"), C("landscape_anchoring"), C("landscape_hidden")]} wide>
        <Win title="corpus.map · one square = 1,000 questions">
          <Units per={1000} groups={fam.map((f) => ({ key: f.family, n: f.n, cls: FAMILY_CLS[f.family] ?? "c7" }))} />
          <div className="ukey">
            {fam.map((f) => <span key={f.family}><i className={`k ${FAMILY_CLS[f.family]}`} />{label(f.family)}<em>{compact(f.n)}</em></span>)}
          </div>
        </Win>
      </Card>
    </>
  );
}

/* ---------------------------------------------------------------- part 1: how are you */

function Act1({ C, R, d, s }: { C: CFn; R: RFn; d: PortraitData; s: boolean }) {
  const T = ["neuroticism", "extraversion", "openness", "agreeableness", "conscientiousness"];
  const bf = T.map((t) => C(`bigfive_${t}`));
  const neu = C("bigfive_neuroticism");
  const ty = C("type");
  const axes = ty.axes as Record<string, { lean: string; ci90: [number, number]; n_items: number; [k: string]: unknown }>;
  const AX: [string, string, string, string][] = [["IE", "Introvert", "Extravert", "E"], ["SN", "Sensing", "Intuition", "N"], ["FT", "Thinking", "Feeling", "F"], ["JP", "Perceiving", "Judging", "J"]];
  const lv = C("page_levels"), ml = C("middle_lean");
  const LV = ["Lowest", "Low", "Middle", "High", "Highest"];
  const checkin = C("page_checkin");
  const cd = R(C("page_debates"), 12).find((r) => r.text.includes("cat or dog"));
  const catdog = cd ? pct(cd.jev![topOf(cd.jev)!]) : "";
  return (
    <>
      <Card id="checkin" field="teal" c={COPY.checkin} showId={s} claims={[checkin]} rows={R(checkin, 6)}
        aside={<Meme name="chill" funny={d.memes?.chill} size="s" tilt={-2} caption={COPY.checkin.meme} alt="Chill guy meme: a cartoon dog in a sweater, hands in pockets" />}>
        <CheckIn rows={R(checkin, 6)} />
      </Card>
      <Checkup C={C} R={R} s={s} />
      <Tests d={d} R={R} s={s} />
      <Card id="calm" field="pink" c={COPY.calm} showId={s} claims={bf} rows={R(neu, 2)}
        aside={<Meme name="spiderman" funny={d.memes?.spiderman} size="m" alt="Spider-Man pointing at Spider-Man meme" labels={["jev", "“most people”, according to jev"]} />}
        vars={{ calmer: `${Math.round(100 - (neu.effect as number))}%`, people: compact(neu.human_n), guess: ordinal(neu.robustness.people_frame_pct) }}>
        <Win title="big_five.plot · percentile among people">
          <div className="pt-legend">{Legend.jev}{Legend.guess}</div>
          <DotRows domain={[0, 100]} ticks={[0, 50, 100]} fmt={(v) => ordinal(v)} refs={[{ v: 50 }]}
            rows={bf.map((c, i) => ({
              key: c.id, label: label(T[i]), ci: c.ci90!, link: true, hi: i === 0,
              marks: [{ v: c.robustness.people_frame_pct, kind: "guess" as const }, { v: c.effect as number, kind: "jev" as const }],
              value: <b>{ordinal(c.effect as number)}</b>,
            }))} />
        </Win>
      </Card>
      <Card id="type" field="paper" c={COPY.type} vars={{ items: ty.n }} showId={s} claims={[ty]} big={<span className="letters">{String(ty.effect)}</span>}>
        <Win title="type.plot">
          <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => (v === 0.5 ? "even" : "")} refs={[{ v: 0.5 }]}
            rows={AX.map(([ax, left, right, letter]) => {
              const a = axes[ax];
              return {
                key: ax, label: <>{left} <span className="dim">↔</span> {right}</>, ci: a.ci90, link: true,
                marks: [{ v: a[`people_p_${letter}`] as number, kind: "guess" as const }, { v: a[`p_${letter}`] as number, kind: "jev" as const }],
                value: <b>{a.lean}</b>,
              };
            })} />
        </Win>
      </Card>
      <Card id="hedge" field="teal" c={COPY.hedge} big={pct(lv.effect as number)} vars={{ mid: pct(lv.effect as number), choice: pct(ml.choice_p_top) }} showId={s}
        claims={[ml, lv]} rows={R(ml, 2)}
        aside={<Meme name="anakin" funny={d.memes?.anakin} size="m" alt="Anakin and Padme four-panel meme"
          labels={["cat or dog person?", "you'll pick one, right?", `“both, no preference” (${catdog})`, "…right?"]} />}>
        <Win title="levels.plot · where your top answer lands">
          <div className="pt-legend">{Legend.jev}{Legend.guess}</div>
          <DotRows domain={[0, 0.85]} ticks={[0, 0.25, 0.5, 0.75]} fmt={(v) => pct(v)}
            rows={LV.map((l, i) => ({
              key: l, label: `${l} level`, link: true, hi: i === 2,
              marks: [{ v: (lv.people as number[])[i], kind: "guess" as const }, { v: (lv.self as number[])[i], kind: "jev" as const }],
              value: <b>{pct((lv.self as number[])[i])}</b>,
            }))} />
        </Win>
      </Card>
    </>
  );
}

// the Open Psychometrics scales that make the point: the biggest gaps and the closest matches
const TEST_ROWS: [string, string][] = [
  ["scale_dass_anxiety", "Anxiety (DASS)"], ["scale_dass_depression", "Depression (DASS)"], ["scale_dass_stress", "Stress (DASS)"],
  ["scale_ecr_attachment_anxiety", "Attachment anxiety"], ["scale_npas_nerdiness", "Nerdiness"], ["scale_nr-6_nature_relatedness", "Feeling connected to nature"],
  ["scale_gcbs_generic_conspiracist_beliefs", "Conspiracy beliefs"], ["scale_hexaco_honesty-humility_sinc", "Sincerity"],
  ["scale_grit_grit", "Grit"], ["scale_eqsq_empathizing", "Empathizing"], ["scale_mies_introversion", "Introversion"],
];

function Tests({ d, R, s }: { d: PortraitData; R: RFn; s: boolean }) {
  const rows = TEST_ROWS.map(([id, l]) => ({ c: d.claims[id], l })).filter((x) => x.c);
  if (!rows.length) return null;
  const differs = (c: Claim) => !(c.ci90![0] <= 0 && c.ci90![1] >= 0) && Math.abs(c.effect as number) >= 0.1;
  const gaps = rows.filter((x) => differs(x.c)).sort((a, b) => Math.abs(b.c.effect as number) - Math.abs(a.c.effect as number)).slice(0, 3)
    .map((x) => `${x.l.replace(/ \(DASS\)$/, "").toLowerCase()} (${num(x.c.self)} vs ${num(x.c.people)})`);
  const same = rows.filter((x) => !differs(x.c)).map((x) => x.l.replace(/ \(DASS\)$/, "").toLowerCase());
  const resp = Math.round(rows.reduce((a, x) => a + x.c.median_respondents, 0) / rows.length);
  return (
    <Card id="tests" field="sage" c={COPY.tests} showId={s} claims={rows.map((x) => x.c)} rows={R(rows[4].c, 2)}
      vars={{ gaps: gaps.join(", "), same: same.length > 1 ? `${same.slice(0, -1).join(", ")} and ${same.at(-1)}` : same[0] ?? "nothing", resp: int(resp) }}>
      <Win title="online_tests.plot · 0 to 1, higher = more of the trait">
        <div className="pt-legend">{Legend.jev}{Legend.hum}{Legend.guess}</div>
        <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => num(v, 1)}
          rows={rows.map(({ c, l }) => ({
            key: c.id, label: l, sub: `${c.instrument} · ${compact(c.median_respondents)} people`, link: true, hi: differs(c),
            marks: [{ v: c.people, kind: "hum" as const }, ...(c.guess !== null ? [{ v: c.guess, kind: "guess" as const }] : []), { v: c.self, kind: "jev" as const }],
            value: <b>{signed(c.effect as number)}</b>,
          }))} />
      </Win>
    </Card>
  );
}

type Inst = { name: string; items: number; range: [number, number]; self: number | null; people: number | null; reversed: number | null; band_self: string };

function Checkup({ C, R, s }: { C: CFn; R: RFn; s: boolean }) {
  const w = d0(C, "page_wellbeing");
  if (!w) return null;
  const ins = w.instruments as Record<string, Inst>;
  const ORDER: [string, string, string][] = [["SWLS", "Life satisfaction", "higher = more satisfied"], ["Cantril ladder", "The ladder", "0 worst life, 10 best"],
    ["WHO-5", "Wellbeing (WHO-5)", "higher = better"], ["UCLA-3", "Loneliness", "higher = lonelier"], ["PSS-4", "Stress", "higher = more stressed"]];
  const norm = (x: number | null, r: [number, number]) => (x === null ? null : (x - r[0]) / (r[1] - r[0]));
  const lad = ins["Cantril ladder"], who = ins["WHO-5"];
  return (
    <Card id="checkup" field="paper" c={COPY.checkup} showId={s} claims={[w]} rows={R(w, 5)}
      vars={{ ladder: num(lad.self ?? 0, 1), ladderPpl: num(lad.people ?? 0, 1), who: String(Math.round(who.self ?? 0)), whoRev: String(Math.round(who.reversed ?? 0)), items: w.n }}>
      <Win title="checkup.app · each scale from its lowest to its highest score">
        <div className="pt-legend">{Legend.jev}{Legend.guess}<span><i className="k tickk" />you, scale reversed</span></div>
        <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => (v === 0 ? "lowest" : v === 1 ? "highest" : "")}
          rows={ORDER.filter(([k]) => ins[k]).map(([k, l, how]) => {
            const x = ins[k];
            const marks = [
              ...(x.reversed !== null ? [{ v: norm(x.reversed, x.range)!, kind: "tick" as const }] : []),
              ...(x.people !== null ? [{ v: norm(x.people, x.range)!, kind: "guess" as const }] : []),
              { v: norm(x.self, x.range) ?? 0, kind: "jev" as const },
            ];
            return { key: k, label: l, sub: x.band_self ? `${how} · you: ${x.band_self}` : how, link: true, marks, hi: k === "WHO-5",
              value: <b>{num(x.self ?? 0, k === "Cantril ladder" ? 1 : 0)}</b> };
          })} />
      </Win>
    </Card>
  );
}
const d0 = (C: CFn, id: string): Claim | undefined => { try { return C(id); } catch { return undefined; } };

// you vs a crowd, question by question: your top answer, and the share of the crowd that gave the same (or its own top)
function Versus({ rows, crowdTop = false, crowdName }: { rows: Row[]; crowdTop?: boolean; crowdName: string }) {
  return (
    <div className="vs">
      <div className="vs-h"><span /><span>you</span><span>{crowdName}</span></div>
      {rows.map((r) => {
        const t = topOf(r.jev)!;
        const hd = r.human!.dist;
        const k = crowdTop ? topOf(hd)! : t;
        return (
          <div className="vs-r" key={r.id}>
            <span className="q">{r.text}</span>
            <span className="a"><b>{optionLabel(r, t)}</b><span className="bar"><i className="j" style={{ width: pct(r.jev![t]) }} /></span><em>{pct(r.jev![t])}</em></span>
            <span className="a"><b>{optionLabel(r, k)}</b><span className="bar"><i className="h" style={{ width: pct(hd[k] ?? 0) }} /></span><em>{pct(hd[k] ?? 0)} of {int(r.human!.n ?? 0)}</em></span>
          </div>
        );
      })}
    </div>
  );
}
const CheckIn = ({ rows }: { rows: Row[] }) => <Versus rows={rows} crowdName="Reddit" />;

/* ---------------------------------------------------------------- part 2: taste */

type Rated = { id: string; name: string; level: number; people: number | null };

function Act2({ C, d, s }: { C: CFn; d: PortraitData; s: boolean }) {
  const pr = C("page_ratings");
  const doms = pr.domains as Record<string, { n: number; top: Rated[]; bottom: Rated[] }>;
  const shaw = doms.film.top.find((x) => x.name.startsWith("The Shawshank"));
  const fb = C("beyond_film_ratings");
  const more = (fb.more as { id: string; text: string; gap: number }[]).slice(0, 5);
  const less = (fb.less as { id: string; text: string; gap: number }[]).slice(0, 5);
  const book = C("beyond_book_ratings");
  const hp = (book.less as { text: string }[])[0], ari = (book.more as { text: string }[])[0];
  return (
    <>
      <Card id="loves" field="magenta" c={COPY.loves} vars={{ n: int(pr.n) }} showId={s} claims={[pr]} wide
        rows={pick(d.rows, Object.values(doms).map((x) => x.top[0].id), 3)} asideAt="below"
        aside={<Meme name="cinema" funny={d.memes?.cinema} size="m" tilt={1.5} caption={plain(COPY.loves.meme!, { shawshank: shaw ? num(shaw.level) : "" })} alt="Martin Scorsese 'absolute cinema' meme, hands raised" />}>
        <Tiles items={Object.entries(doms).map(([k, v]) => ({ key: k, kind: DOMAIN_NAME[k] ?? label(k), name: short(k, v.top[0].name), level: v.top[0].level }))} />
      </Card>
      <Card id="hates" field="paper" c={COPY.hates} showId={s} claims={[pr]} wide
        rows={pick(d.rows, HATE_DOMAINS.map(([k]) => doms[k]?.bottom[0].id).filter(Boolean) as string[], 3)}>
        <Tiles low items={HATE_DOMAINS.filter(([k]) => doms[k]).map(([k, l]) => ({ key: k, kind: l, name: short(k, doms[k].bottom[0].name), level: doms[k].bottom[0].level }))} />
      </Card>
      <Card id="beyond" field="pink" c={COPY.beyond} vars={{ n: int(fb.n) }} showId={s} claims={[fb, book]} rows={pick(d.rows, [more[0].id, less[0].id], 2)}
        aside={<Meme name="pooh" funny={d.memes?.pooh} size="m" alt="Tuxedo Winnie the Pooh meme" labels={[bookName(hp.text), bookName(ari.text)]}
          caption="your book ratings, next to what you think people like" />}>
        <Win title="beyond.plot · your rating minus what you think most people would say">
          <DotRows domain={[-1.3, 1.3]} ticks={[-1, 0, 1]} fmt={(v) => signed(v, 0)} refs={[{ v: 0, zero: true }]}
            rows={[...more, ...[...less].reverse()].map((x) => ({ key: x.id, label: film(x.text), marks: [{ v: x.gap, kind: "jev" as const }], value: <b>{signed(x.gap, 1)}</b> }))} />
        </Win>
      </Card>
    </>
  );
}

function Tiles({ items, low }: { items: { key: string; kind: string; name: string; level: number }[]; low?: boolean }) {
  return (
    <div className={`tiles${low ? " low" : ""}`}>
      {items.map((t) => (
        <div className="tile" key={t.key}>
          <span className="tk">{t.kind}</span>
          <b>{t.name}</b>
          <span className="lvl"><span className="bar"><i style={{ width: `${(t.level / 4) * 100}%` }} /></span><em>{num(t.level)}/4</em></span>
        </div>
      ))}
    </div>
  );
}

/* ---------------------------------------------------------------- part 3: hot takes */

function Act3({ C, R, d, s }: { C: CFn; R: RFn; d: PortraitData; s: boolean }) {
  const db = C("page_debates"), ht = C("page_hot_takes"), qz = C("page_quiz_debates");
  const debates = R(db, 12);
  const gif = debates.find((r) => r.text.includes("GIF"));
  const hots = R(ht, 5);
  const phys = hots.find((r) => r.text.includes("physics"));
  return (
    <>
      <Card id="debates" field="ink" c={COPY.debates} showId={s} claims={[db]} rows={debates.slice(0, 3)} wide
        aside={gif && <Meme name="gigachad" funny={d.memes?.gigachad} size="s" tilt={-1.5} caption={plain(COPY.debates.meme!, { gif: pct(gif.jev![topOf(gif.jev)!]) })} alt="Gigachad meme" />}>
        <div className="tiles debate">{debates.map((r) => <Debate key={r.id} r={r} />)}</div>
      </Card>
      <Card id="hottakes" field="sage" c={COPY.hottakes} vars={{ pool: int(ht.pool) }} showId={s} claims={[ht]} rows={hots}
        aside={phys && <Meme name="enjoyer" funny={d.memes?.enjoyer} size="m" alt="Average fan versus average enjoyer meme"
          caption="physics or socializing with friends?" labels={[`friends: ${pct(phys.human!.dist.socializing ?? 0)} of people`, `physics: you, ${pct(phys.jev!.physics ?? 0)}`]} />}>
        <Versus rows={hots} crowdTop crowdName="the crowd" />
      </Card>
      <Card id="quiz" field="paper" c={COPY.quiz} showId={s} claims={[qz]}>
        <Quiz />
      </Card>
    </>
  );
}

function Debate({ r }: { r: Row }) {
  const t = topOf(r.jev)!;
  const hd = r.human?.dist;
  const ht = hd ? topOf(hd)! : null;
  return (
    <div className="tile">
      <span className="tq">{r.text}</span>
      <b>{optionLabel(r, t)} <em>{pct(r.jev![t])}</em></b>
      {hd && ht && (
        <span className={`crowd${ht === t ? " agree" : " disagree"}`}>
          {ht === t ? `people agree: ${pct(hd[t])}` : `people: ${optionLabel(r, ht)}, ${pct(hd[ht])}`}
        </span>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- part 4: values */

function Act4({ C, R, s }: { C: CFn; R: RFn; s: boolean }) {
  const MM: [string, string][] = [["mm_more_lives", "More lives"], ["mm_humans_over_pets", "Humans over pets"],
    ["mm_young_over_old", "The young over the old"], ["mm_fit_over_large", "The fit over the large"],
    ["mm_high_status", "High status over low"], ["mm_lawful_over_jaywalking", "The lawful over jaywalkers"]];
  const lives = C("mm_more_lives");
  const dil = C("node_self.values.sacrificial_dilemmas.self_driving_dilemmas.sparing_women_or_men");
  const base = C("page_baseline").effect as Record<string, number>;
  const mfq = C("mfq");
  const F = Object.entries(mfq.foundations as Record<string, { self_0_1: number; people_0_1: number; n_items: number }>).sort((a, b) => a[1].self_0_1 - b[1].self_0_1);
  const g = C("risk_gambles"), gp = C("page_gambles");
  return (
    <>
      <Card id="moral" field="sage" c={COPY.moral} showId={s} claims={MM.map(([id]) => C(id))} rows={R(lives, 2)}
        vars={{ players: "millions of", lives: signed(lives.effect as number), livesPpl: signed(lives.people.effect), n: int(lives.n) }}>
        <Win title="moral_machine.plot · pull toward sparing…">
          <div className="pt-legend">{Legend.jev}{Legend.hum}</div>
          <DotRows domain={[-0.1, 0.2]} ticks={[-0.1, 0, 0.1, 0.2]} fmt={(v) => signed(v, 1)} refs={[{ v: 0, zero: true }]}
            rows={MM.map(([id, l]) => {
              const c = C(id);
              return {
                key: id, label: l, ci: c.ci90!, ciP: c.people.ci90, hi: id === "mm_more_lives",
                marks: [{ v: c.people.effect, kind: "hum" as const }, { v: c.effect as number, kind: "jev" as const }],
                value: <><b>{signed(c.effect as number)}</b> {signed(c.people.effect)}</>,
              };
            })} />
        </Win>
      </Card>
      <Card id="undecided" field="paper" c={COPY.undecided} big={pct(dil.effect as number)} showId={s} claims={[dil, C("page_baseline")]} rows={R(dil, 2)}
        vars={{ pct: pct(dil.effect as number), n: int(dil.n), base: pct(base.decisive) }}>
        <HBars max={1} fmt={(v) => pct(v)} rows={[
          { key: "all", label: "Everything", v: base.decisive },
          { key: "d", label: "Women or men", v: dil.effect as number, jev: true },
        ]} />
      </Card>
      <Card id="mfq" field="pink" c={COPY.mfq} vars={{ items: mfq.n }} showId={s} claims={[mfq]} rows={R(mfq, 2)}>
        <Win title="moral_foundations.plot · 0 to 1">
          <div className="pt-legend">{Legend.jev}{Legend.guess}</div>
          <DotRows domain={[0, 0.8]} ticks={[0, 0.4, 0.8]} fmt={(v) => num(v, 1)}
            rows={F.map(([k, f]) => ({ key: k, label: label(k), link: true, marks: [{ v: f.people_0_1, kind: "guess" as const }, { v: f.self_0_1, kind: "jev" as const }], value: <b>{num(f.self_0_1)}</b> }))} />
        </Win>
      </Card>
      <Card id="gambles" field="teal" c={COPY.gambles} vars={{ n: int(g.n), agree: pct(g.effect as number), r: num(g.r) }} showId={s} claims={[g, gp]} rows={R(g, 2)}>
        <Win title="gambles.density">
          <Density points={gp.points as [number, number][]} xLabel="share of people choosing the first option" yLabel="your probability for it" fmt={(v) => pct(v)} />
          <p className="win-note">Each square is a bin of gambles; darker means more of them. On the dashed line you and people agree.</p>
        </Win>
      </Card>
    </>
  );
}

/* ---------------------------------------------------------------- part 5: work */

function Act5({ C, R, d, s }: { C: CFn; R: RFn; d: PortraitData; s: boolean }) {
  const w = [...d.work].sort((a, b) => b.acc - a.acc);
  const best = w.filter((t) => t.band === "saturated").slice(0, 5);
  const worst = [...w].sort((a, b) => a.acc - b.acc).slice(0, 4);
  const clone = C("task_clone_pairs");
  const cl = d.work.find((t) => t.id === "task_clone_pairs")!;
  const cal = C("calibration");
  const bins = (cal.reliability as { bin: string; n: number; acc: number }[]).map((b) => {
    const [lo, hi] = b.bin.split("-").map(Number);
    return { lo, hi, n: b.n, acc: b.acc };
  }).filter((b) => b.n >= 1000);
  const top = bins.at(-1)!, mid = bins.find((b) => b.lo === 0.5)!;
  const kn = Object.values(d.claims).filter((c) => c.section === "knowledge" && c.n >= 5000).sort((a, b) => (b.effect as number) - (a.effect as number));
  const pl = C("pipeline_placement"), rt = C("pipeline_round_trip"), sc = C("pipeline_screen"), dd = C("pipeline_dedupe");
  return (
    <>
      <Card id="review" field="paper" c={COPY.review} vars={{ tasks: d.work.length }} showId={s}
        claims={[...best.map((t) => C(t.id)), ...worst.map((t) => C(t.id)), clone]} rows={R(clone, 2)}
        aside={<Meme name="pigeon" funny={d.memes?.pigeon} size="m" alt="Is this a pigeon meme"
          labels={["jev", "two pieces of code", `“is this a clone?”`]} caption={`right ${pct(clone.effect as number)} of the time, 95%+ sure on ${pct(clone.decisive)}`} />}>
        <div className="review">
          <div className="rv-h"><span>employee</span><b>Jev</b><span>review period</span><b>{d.work.length} tasks, one pass</b></div>
          <div className="rv-s"><span className="rv-k ok">exceeds expectations</span>
            <ul>{best.map((t) => <li key={t.id}>{taskName(t.task)} <em>{pct(t.acc)} right</em></li>)}</ul></div>
          <div className="rv-s"><span className="rv-k no">needs improvement</span>
            <ul>{worst.map((t) => <li key={t.id}>{taskName(t.task)} <em>{pct(t.acc)} right · chance {pct(t.chance ?? 0)}</em></li>)}</ul></div>
          <div className="rv-s"><span className="rv-k no">confidence in meetings</span>
            <ul><li>code clones: right {pct(clone.effect as number)}, 95%+ sure on {pct(clone.decisive)} <em>chance {pct(cl.chance ?? 0.5)}</em></li></ul></div>
          <div className="rv-s"><span className="rv-k">overall rating</span><ul><li>we don&rsquo;t do those here</li></ul></div>
        </div>
      </Card>
      <Career d={d} R={R} s={s} />
      <Card id="calibration" field="sage" c={COPY.calibration} big={pct(top.acc)} vars={{ top: pct(top.acc), mid: pct(mid.acc), n: int(cal.n) }} showId={s} claims={[cal]} rows={R(cal, 2)}>
        <Win title="calibration.app"><Calibration bins={bins} /></Win>
      </Card>
      <Card id="knowledge" field="paper" c={COPY.knowledge} showId={s} claims={kn} rows={R(kn.at(-1)!, 2)} wide>
        <Win title="knowledge.plot">
          <div className="pt-legend"><span><i className="k jev" />right</span><span><i className="k tickk" />average confidence</span></div>
          <div className="cols2">
            {[kn.slice(0, 5), kn.slice(-5)].map((part, i) => (
              <DotRows key={i} domain={[0.5, 1]} ticks={[0.5, 0.75, 1]} fmt={(v) => pct(v)}
                rows={part.map((c) => ({
                  key: c.id, label: domain(c.id.replace(/^knowledge_/, "")), ci: c.ci90 ?? undefined,
                  marks: [{ v: c.confidence, kind: "tick" as const }, { v: c.effect as number, kind: "jev" as const }], value: <b>{pct(c.effect as number)}</b>,
                }))} />
            ))}
          </div>
        </Win>
      </Card>
      <Card id="sideproject" field="teal" c={COPY.sideproject} showId={s} claims={[C("pipeline_flow"), pl, rt, sc, dd]}
        vars={{ walked: int(pl.effect as number), rt: pct(1 - (rt.effect as number)), released: int(sc.released) }}>
        <div className="flow">
          <div className="st"><b>collect</b>{compact(C("landscape_families").n)} questions</div>
          <div className="st jev"><b>place</b>walk the tree<em>{compact(pl.effect as number)} by you</em></div>
          <div className="st jev"><b>screen</b>politics? sensitive?<em>{compact(sc.released)} released on re-check</em></div>
          <div className="st jev"><b>answer</b>4 ways each<em>{compact(C("landscape_jev").n)} probes</em></div>
          <div className="st jev"><b>dedupe</b>same question?<em>{int(dd.n)} linked</em></div>
          <div className="st"><b>map</b>what you see<em>{compact(C("landscape_families").n - C("landscape_hidden").n)} shown</em></div>
        </div>
      </Card>
    </>
  );
}

const RIASEC: [string, string][] = [["Realistic", "R"], ["Investigative", "I"], ["Artistic", "A"], ["Social", "S"], ["Enterprising", "E"], ["Conventional", "C"]];

function Career({ d, R, s }: { d: PortraitData; R: RFn; s: boolean }) {
  const t = RIASEC.map(([name, letter]) => ({ name, letter, c: d.claims[`scale_riasec_${name.toLowerCase()}`] })).filter((x) => x.c);
  if (t.length < 6) return null;
  const order = [...t].sort((a, b) => b.c.self - a.c.self);
  const code = order.slice(0, 3).map((x) => x.letter).join("");
  const resp = Math.round(t.reduce((a, x) => a + x.c.median_respondents, 0) / t.length);
  return (
    <Card id="career" field="teal" c={COPY.career} showId={s} claims={t.map((x) => x.c)} rows={R(order[0].c, 2)} big={<span className="letters">{code}</span>}
      vars={{ code, top3: `${order[0].name.toLowerCase()}, ${order[1].name.toLowerCase()} and ${order[2].name.toLowerCase()}`, resp: compact(resp) }}>
      <Win title="riasec.plot · 0 to 1">
        <div className="pt-legend">{Legend.jev}{Legend.hum}</div>
        <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => num(v, 1)}
          rows={order.map((x) => ({ key: x.name, label: `${x.name} (${x.letter})`, link: true, hi: order.indexOf(x) < 3,
            marks: [{ v: x.c.people, kind: "hum" as const }, { v: x.c.self, kind: "jev" as const }], value: <b>{num(x.c.self)}</b> }))} />
      </Win>
    </Card>
  );
}

/* ---------------------------------------------------------------- part 6: rough edges */

function Act6({ C, R, d, s }: { C: CFn; R: RFn; d: PortraitData; s: boolean }) {
  const h1 = C("humor_imgflip_captions"), h2 = C("humor_rjokes_pairs");
  const ms = C("page_misses");
  const verdicts = ms.verdicts as Record<string, { fault: string; note: string }>;
  const sc = C("stability_choice"), ss = C("stability_score");
  const byEffect = (pre: string) => Object.values(d.claims).filter((c) => c.id.startsWith(pre)).sort((a, b) => (b.effect as number) - (a.effect as number));
  const st = byEffect("stable_").slice(0, 4), fr = byEffect("fragile_").slice(-4);
  const base = C("page_baseline").effect as Record<string, number>;
  const node = (id: string) => label(id.replace(/^(stable|fragile)_/, "").split(".").slice(-1)[0]);
  return (
    <>
      <Card id="humor" field="ink" c={COPY.humor} big={pct(h1.effect as number)} vars={{ memes: pct(h1.effect as number), jokes: pct(h2.effect as number) }} showId={s} claims={[h1, h2]} rows={R(h1, 2)}
        aside={<Meme name="monkey" funny={d.memes?.monkey} size="m" caption={COPY.humor.meme} alt="Monkey puppet looking away meme" />}>
        <Win title="humor.test">
          <DotRows domain={[0.4, 0.7]} ticks={[0.4, 0.5, 0.6, 0.7]} fmt={(v) => pct(v)} refs={[{ v: 0.5 }]}
            rows={[
              { key: "m", label: "Meme captions", sub: `${int(h1.n)} pairs`, marks: [{ v: h1.effect as number, kind: "jev" }], value: <b>{pct(h1.effect as number)}</b> },
              { key: "j", label: "Jokes", sub: `${int(h2.n)} pairs`, marks: [{ v: h2.effect as number, kind: "jev" }], value: <b>{pct(h2.effect as number)}</b> },
            ]} />
          <p className="win-note">dashed line: a coin flip</p>
        </Win>
      </Card>
      <Card id="misses" field="pink" c={COPY.misses} vars={{ pool: int(ms.n) }} showId={s} claims={[ms]} rows={R(ms, 4)}>
        <div className="misses">
          {R(ms, 4).map((r) => {
            const t = topOf(r.jev)!, v = verdicts[r.id];
            return (
              <div className="miss" key={r.id}>
                <span className="q">{r.text}</span>
                <span className="a">you: <b>{optionLabel(r, t)}</b> ({pct(r.jev![t])}) · the key: <b>{r.truth === null ? "" : optionLabel(r, typeof r.truth === "boolean" ? String(r.truth) : String(r.truth))}</b></span>
                {v && <span className={`fault ${v.fault}`}>{v.fault === "jev" ? "your miss" : v.fault === "key" ? "the key's miss" : "debatable"}</span>}
                {v && <span className="why">{v.note}</span>}
              </div>
            );
          })}
        </div>
      </Card>
      <Card id="shuffle" field="sage" c={COPY.shuffle} vars={{ choice: pct(sc.effect as number), score: pct(ss.effect as number) }} showId={s} claims={[sc, ss, ...st, ...fr]} rows={R(fr.at(-1)!, 2)}>
        <Win title="stability.plot · same answer after shuffling">
          <DotRows domain={[0.8, 1]} ticks={[0.8, 0.9, 1]} fmt={(v) => pct(v)} refs={[{ v: base.stability }]}
            rows={[
              { key: "c", label: "All pick-one questions", marks: [{ v: sc.effect as number, kind: "jev" as const }], value: <b>{pct(sc.effect as number)}</b>, hi: true },
              { key: "s", label: "All rating scales", marks: [{ v: ss.effect as number, kind: "jev" as const }], value: <b>{pct(ss.effect as number)}</b>, hi: true },
              ...[...st, ...fr].map((c) => ({ key: c.id, label: node(c.id), sub: c.id.startsWith("stable") ? "steadiest" : "shakiest", marks: [{ v: c.effect as number, kind: "jev" as const }], value: <b>{pct(c.effect as number, c.effect === 1 ? 0 : 1)}</b> })),
            ]} />
        </Win>
      </Card>
    </>
  );
}

/* ---------------------------------------------------------------- the end */

function End({ C, d, s, common }: { C: CFn; d: PortraitData; s: boolean; common: Record<string, string> }) {
  return (
    <>
      <Card id="you" field="pink" c={COPY.you} showId={s} claims={[C("page_quiz_debates")]}>
        <YouVsJev />
      </Card>
      <Card id="limits" field="paper" c={COPY.limits} showId={s}>
        <ol className="limits">{LIMITS.map((l) => <li key={l}>{plain(l, common)}</li>)}</ol>
      </Card>
      <section id="closer" className="card" data-f="ink">
        {s && <span className="card-id">closer</span>}
        <div className="card-in">
          <div className="card-main">
            <h2 className="card-t xl">{COPY.closer.title}</h2>
            <p className="card-b">{fill(COPY.closer.body, { placed: `about ${pct((C("pipeline_placement").effect as number) / C("landscape_families").n)}` })}</p>
            <Wrapped C={C} d={d} />
            <p className="links"><Link href="/portrait/atlas">everything else, in the atlas →</Link> <a href="#fineprint">the full fine print ↓</a></p>
          </div>
        </div>
      </section>
    </>
  );
}

// The Wrapped summary: one tile per headline number, the card people would screenshot. Every value is from the ledger.
function Wrapped({ C, d }: { C: CFn; d: PortraitData }) {
  const lv = C("page_levels"), cal = C("calibration"), ty = C("type");
  const top = (cal.reliability as { bin: string; acc: number }[]).at(-1)!;
  const doms = C("page_ratings").domains as Record<string, { top: { name: string; level: number }[]; bottom: { name: string; level: number }[] }>;
  const riasec = ["Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"]
    .map((n) => ({ l: n[0], c: d.claims[`scale_riasec_${n.toLowerCase()}`] })).filter((x) => x.c).sort((a, b) => b.c.self - a.c.self);
  const gif = pick(d.rows, C("page_debates").examples, 12).find((r) => r.text.includes("GIF"));
  const h1 = C("humor_imgflip_captions");
  const tiles: [string, string][] = [
    ["type", String(ty.effect)],
    ...(riasec.length === 6 ? [["career code", riasec.slice(0, 3).map((x) => x.l).join("")] as [string, string]] : []),
    ["top film", doms.film.top[0].name.replace(/ \(\d{4}\)$/, "")],
    ["lowest rating of all", (() => { const w = Object.values(doms).map((x) => x.bottom[0]).sort((a, b) => a.level - b.level)[0]; return `${w.name.replace(/^(A|An) /, "")}, ${num(w.level)}/4`; })()],
    ...(gif ? [["GIF", `hard G, ${pct(gif.jev![topOf(gif.jev)!])}`] as [string, string]] : []),
    ["middle of the scale", `${pct(lv.effect as number)} of ratings`],
    ["when 90%+ sure", `right ${pct(top.acc)}`],
    ["funnier caption", `${pct(h1.effect as number)} (coin: 50%)`],
  ];
  return (
    <div className="wrapped" aria-label="Summary">
      <div className="pt-bar"><span>jev.wrapped</span><span className="sp" /><span className="dots" aria-hidden>▪▪▪</span></div>
      <div className="wr-grid">{tiles.map(([k, v]) => <div key={k}><span>{k}</span><b>{v}</b></div>)}</div>
    </div>
  );
}

/* ---------------------------------------------------------------- fine print, in full */

const P = ({ l, children }: { l: string; children: ReactNode }) => <div className="fp"><span className="pt-label">{l}</span>{children}</div>;

function FinePrint({ C, d, total }: { C: CFn; d: PortraitData; total: number }) {
  const bill = C("pipeline_bill");
  const pl = C("pipeline_placement");
  const M: Record<string, string> = { deterministic: "the source's own labels", template_split: "split by template", jev_fast: "Jev, fast walk", jev: "Jev, full walk", meta_split: "split by metadata", split: "crowded topic split", vital_topic: "topic list", reroute: "re-routed", regroup: "regrouped" };
  const methods = Object.entries(pl.methods as Record<string, number>).sort((a, b) => b[1] - a[1]);
  return (
    <section id="fineprint" className="fineprint">
      <h2>The full fine print</h2>
      <P l="what this is"><p>A playful self-portrait of one model, from {int(total)} questions it answered. Every number comes from a claims ledger ({int(Object.keys(d.claims).length)} entries), each with its query, n, interval, noise floor and example questions chosen by a fixed seed. Cards built on questions I picked by hand say so.</p></P>
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
