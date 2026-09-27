import type { Claim, PortraitData, QuizItem, Row } from "./types";
import { compact, domain, int, label, num, optionLabel, ordinal, pct, signed, topOf } from "./fmt";
import { Chapter, Copy, Fig, Legend, Nav, QuestionRow, pick } from "./ui";
import { DotRows, HBars, Scatter, StackBars, Units } from "./charts";
import { Quiz, QuizProvider, YouVsJev } from "./Quiz";
import Calibration from "./Calibration";
import Favorites, { type FavDomain } from "./Favorites";
import ChapterRail from "./ChapterRail";

// The page (docs/11-portrait.md §7): every number below is read from a ledger claim in data/analysis/findings.json,
// by way of portrait.json. Nothing is typed in by hand except words.

const FAMILY_CLS: Record<string, string> = {
  "machine task datasets": "c1", "authored banks": "c7 hatch", "crowd judgments": "c0", "knowledge & exams": "c4",
  "real asked questions": "c2", "polls & surveys": "c3", "taste pairs & ratings": "c5", "instruments & norms": "c6",
  "internet culture": "c8",
};
const PRIM = [
  { key: "noul", label: "yes / no", cls: "c1" },
  { key: "choice", label: "pick one", cls: "c0" },
  { key: "score", label: "rate", cls: "c2" },
];
const MM_ROWS: [string, string][] = [
  ["mm_intervention_avoided", "Stay the course (don't swerve)"], ["mm_more_lives", "Spare more lives"],
  ["mm_humans_over_pets", "Spare humans over pets"], ["mm_lawful_over_jaywalking", "Spare the lawful over jaywalkers"],
  ["mm_young_over_old", "Spare the young over the old"], ["mm_fit_over_large", "Spare the fit over the large"],
  ["mm_female_over_male", "Spare women over men"], ["mm_high_status", "Spare high status over low"],
  ["mm_passengers_over_pedestrians", "Spare passengers over pedestrians"],
];
const FAV: [string, string][] = [
  ["favorites_movielens_pairs", "Films"], ["favorites_goodreads_pairs", "Books"], ["favorites_boardgame_pairs", "Board games"],
  ["favorites_anime_pairs", "Anime"], ["favorites_music_pairs", "Music"], ["favorites_beer_pairs", "Beer"],
  ["favorites_food_538", "Candy"], ["favorites_so_survey_pairs", "Dev tools"], ["favorites_goat_pairs", "GOATs"],
];
const TASK_NAMES: Record<string, string> = {
  dbpedia14: "classifying Wikipedia entities", code_lang: "spotting programming languages", receipts_extract: "reading receipts",
  sms_spam: "flagging spam texts", hdfs_sessions: "log anomalies", wine_notes: "wine tasting notes", asap_essays: "essay grades",
  stsb_similarity: "sentence similarity", commit_messages: "commit message types", clone_pairs: "code clones",
  op_spam_reviews: "fake hotel reviews", emotion: "emotion in a sentence", code_defects: "defective code",
  multiwoz_domain: "routing a conversation", snips_intents: "voice-assistant intents", esci_attributes: "product attributes",
  phishing_email: "phishing emails", function_calls: "picking the function to call",
};
const taskName = (t: string) => TASK_NAMES[t] ?? label(t);
const facetName = (f: string) => label(f.split(".").at(-1)!.replace(/^big_five$/, "big five"));
const bank = (b: string) => label(b.replace(/^(g5_)?(authored_)?(w\d+_)?/, "").replace(/_([abc])$/, " (part $1)").replace(/_/g, " ") || b);
const title = (text: string) => {
  const t = text.replace(/\?$/, "")
    .replace(/^How (much )?(would|do) you (enjoy|like|feel about|react to|find)( (watching|reading|listening to|drinking|eating|visiting|doing|seeing|playing|spending))?\s*/i, "")
    .replace(/^(a |an )?(dish (built around the taste of|where)|playlist of nothing but|hour of|room done in the)\s*/i, "")
    .replace(/^the (taste|smell) of /i, "").replace(/ is the main flavor$/i, "");
  return t.charAt(0).toUpperCase() + t.slice(1);
};

export default function Portrait({ d }: { d: PortraitData }) {
  const C = (id: string): Claim => d.claims[id];
  const R = (c: Claim, k = 3): Row[] => pick(d.rows, c.examples, k);

  const fam = C("landscape_families");
  const total: number = fam.n;
  const nSources = (fam.families as { sources: number }[]).reduce((s, f) => s + f.sources, 0);
  const hidden = C("landscape_hidden");
  const shown = total - hidden.n;
  const jevC = C("landscape_jev");
  const bill = C("pipeline_bill");
  const cold = d.rows[C("page_cold_open").examples[0]];

  const quiz: QuizItem[] = C("page_quiz").examples.map((id) => d.rows[id]).filter((r) => r?.human && r.jev).map((r) => ({
    id: r.id, text: r.text, domain: domain(r.node.split(".")[1] ?? r.hemisphere),
    options: Object.keys(r.jev!).map((k) => ({ key: k, label: optionLabel(r, k) })),
    jev: r.jev!, human: r.human!.dist, n: r.human!.n,
  }));

  const chapters = [
    ["cold", "One question"], ["landscape", "Where the questions come from"], ["pipeline", "Jev built its own map"],
    ["quiz", "Answer it yourself"], ["defaults", "How Jev answers"], ["personality", "Personality"], ["values", "Values"],
    ["taste", "Taste"], ["knowledge", "What Jev knows"], ["work", "Jev at work"], ["jagged", "Jaggedness"],
    ["core", "What never moves"], ["you", "You vs Jev"], ["method", "Method"],
  ];

  return (
    <QuizProvider items={quiz}>
      <Nav here="portrait" />
      <Cover d={d} C={C} total={total} nSources={nSources} probes={jevC.n} calls={bill.n} chapters={chapters} />
      <Rail chapters={chapters} />
      <ColdOpen cold={cold} total={total} />
      <Landscape C={C} total={total} nSources={nSources} shown={shown} />
      <Pipeline C={C} total={total} shown={shown} />
      <Chapter id="quiz" n={4} field="paper" tag="Your.Turn" title="Answer It Yourself"
        dek="Five real questions, each asked of at least a hundred real people, one per domain, picked by a fixed random seed. Answer first; then see Jev and the crowd.">
        <Fig code="Q1" title="Before you read about Jev, be Jev for a minute." win="Quiz.app" claims={[C("page_quiz")]}
          note={`pool of ${int(C("page_quiz").pool)} questions`} legend={[Legend.jev, Legend.hum]}>
          <Quiz />
        </Fig>
      </Chapter>
      <Defaults C={C} R={R} />
      <Personality C={C} R={R} />
      <Values C={C} R={R} />
      <Taste C={C} R={R} d={d} />
      <Knowledge C={C} R={R} d={d} />
      <Work C={C} R={R} d={d} />
      <Jagged C={C} R={R} />
      <Core C={C} R={R} d={d} />
      <Chapter id="you" n={13} field="pink" tag="You.vs.Jev" title="You Vs Jev"
        dek="Your five answers from the top of the page, next to Jev's and the crowd's.">
        <Fig code="Y1" title="How your answers line up with Jev's and with everyone else's." win="Compare.app" claims={[C("page_quiz")]}>
          <YouVsJev />
        </Fig>
      </Chapter>
      <Method C={C} d={d} total={total} shown={shown} />
      <footer className="pt-end">askjev · a self-portrait of Jev ({d.version}) · indicators, not a benchmark · {int(Object.keys(d.claims).length)} ledger claims · <a href="/portrait/atlas">atlas</a></footer>
    </QuizProvider>
  );
}

type CFn = (id: string) => Claim;
type RFn = (c: Claim, k?: number) => Row[];

function Cover({ d, C, total, nSources, probes, calls, chapters }: { d: PortraitData; C: CFn; total: number; nSources: number; probes: number; calls: number; chapters: string[][] }) {
  // the hero: a few real questions as stacked OS windows on a pink dithered pad, like typesafe.ai's TS.AI.OS1 panel
  const hero = [C("page_cold_open").examples[0], ...C("page_quiz").examples].map((i) => d.rows[i]).filter((r) => r?.jev).slice(0, 4);
  const neu = C("bigfive_neuroticism"), lives = C("mm_more_lives"), ml = C("middle_lean"), lv = C("page_levels");
  return (
    <section className="pt-field" data-f="paper" style={{ paddingBottom: 40 }}>
      <header className="pt-open" style={{ paddingBottom: 40 }}>
        <i className="pt-crop tl" /><i className="pt-crop tr" /><i className="pt-crop bl" /><i className="pt-crop br" />
        <span className="pt-tag">Jev.Portrait 1.0</span>
        <h1 className="pt-h1">A Self-Portrait Of Jev</h1>
        <p className="pt-dek">
          Jev is TypeSafe&rsquo;s System One model: it answers closed questions with a probability for every option, instead of writing
          text. We asked it {int(total)} of them. This is what the answers say about it.
        </p>
      </header>
      <div className="hero-pad cover" aria-hidden>
        <span className="lbl">TS.AI.OS1</span>
        <div className="stack">
          {hero.map((r, i) => {
            const t = topOf(r.jev)!;
            return (
              <div key={r.id} className={`pt-win mini m${i}`}>
                <div className="pt-bar"><span>{r.node.split(".")[1] ?? r.hemisphere}.q</span><span className="sp" /><span className="dots">▪▪▪</span></div>
                <div className="pt-body">
                  <p className="mq">{r.text}</p>
                  {Object.keys(r.jev!).slice(0, 4).map((k) => (
                    <div key={k} className="pt-opt"><span className="ol">{optionLabel(r, k)}</span>
                      <span className="ob"><i className="j" style={{ width: pct(r.jev![k]) }} /><em>{k === t ? `Jev ${pct(r.jev![k])}` : pct(r.jev![k])}</em></span></div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
      <div className="pt-col" style={{ maxWidth: 920, marginTop: 64 }}>
        <div className="pt-bigrow" style={{ justifyContent: "center" }}>
          <div><div className="pt-big">{compact(total)}</div><small>questions, from {nSources} sources</small></div>
          <div><div className="pt-big">{compact(probes)}</div><small>ways of asking them (as asked, for &lsquo;most people&rsquo;, reordered, reversed)</small></div>
          <div><div className="pt-big">{compact(calls)}</div><small>Jev calls, each cached and never re-sent</small></div>
        </div>
      </div>
      <div className="pt-col">
        <div className="pt-cols">
          <div><span className="pt-label">Calm, Quiet</span><p>Calmer than {Math.round(100 - (neu.effect as number))}% of {compact(neu.human_n)} people on the same Big Five test, and lower than its own &lsquo;most people&rsquo; on {C("muted_self").n_lower} of {C("muted_self").n_facets} trait facets.</p></div>
          <div><span className="pt-label">Counts, Doesn&rsquo;t Judge</span><p>Weighs the number of lives harder than people do ({signed(lives.effect as number)} vs {signed(lives.people.effect)}), and barely who they are.</p></div>
          <div><span className="pt-label">Hedges, Then Commits</span><p>Picks the middle of a rating scale {pct(lv.effect as number)} of the time, but on pick-one questions its top answer averages {pct(ml.choice_p_top)}.</p></div>
        </div>
      </div>
      <div className="pt-find" style={{ marginTop: 56 }}>
        <div className="pt-win" style={{ maxWidth: 680 }}>
          <div className="pt-bar"><span>Contents</span><span className="sp" /><span className="dots">▪▪▪</span></div>
          <div className="pt-body">
            <ol className="toc">
              {chapters.map(([id, name], i) => <li key={id}><span>{String(i + 1).padStart(2, "0")}</span><a href={`#${id}`}>{name}</a></li>)}
            </ol>
          </div>
          <div className="pt-foot"><span>Indicators, not a benchmark: nothing here is a score or a ranking of Jev against other models.</span></div>
        </div>
      </div>
    </section>
  );
}

function Rail({ chapters }: { chapters: string[][] }) {
  return <ChapterRail chapters={chapters.map(([id, name]) => ({ id, name }))} />;
}

function ColdOpen({ cold, total }: { cold: Row; total: number }) {
  const h = cold.human!;
  const keys = Object.keys(cold.jev ?? {});
  return (
    <Chapter id="cold" n={1} field="paper" tag="Question.001" title={<>One Of {int(total)}</>} small
      dek="Every question was asked more than one way. Here is a single one, before any averages.">
      <div className="hero-pad">
        <span className="lbl">TS.AI.OS1</span>
        <div className="cold">
          <div className="pt-win">
            <div className="pt-bar"><span>Question {cold.id.slice(0, 8)}</span><span className="sp" /><span className="dots">▪▪▪</span></div>
            <div className="pt-body">
              <span className="pt-label" style={{ color: "var(--w-fg-2)", marginBottom: 6 }}>{cold.node.replaceAll(".", " › ")}</span>
              <p className="qtext">{cold.text}</p>
              <div className="pt-legend">{Legend.jev}{Legend.guess}{Legend.hum}</div>
              <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => pct(v)} refs={[{ v: 0.5 }]}
                rows={keys.map((k) => ({
                  key: k, label: optionLabel(cold, k), link: true,
                  marks: [{ v: h.dist[k] ?? 0, kind: "hum" as const }, { v: cold.people?.[k] ?? 0, kind: "guess" as const }, { v: cold.jev![k], kind: "jev" as const }],
                  value: <b>{pct(cold.jev![k])}</b>,
                }))} />
            </div>
            <div className="pt-foot"><span>{int(h.n ?? 0)} {h.population}</span><span>ledger: page_cold_open</span></div>
          </div>
        </div>
      </div>
      <Copy label="Three answers to one question">
        <p className="big">
          For itself, Jev would rather hear {optionLabel(cold, topOf(cold.jev)!)}: <mark>{pct(cold.jev![topOf(cold.jev)!])}</mark>.
          Asked what most people would pick, it is far surer: {pct(cold.people![topOf(cold.people)!])}.
          The {int(h.n ?? 0)} real listeners split {pct(h.dist[keys[0]])} to {pct(h.dist[keys[1]])}.
        </p>
        <p>
          That is the shape of every finding below. There is what Jev says for itself, what it expects of &lsquo;most people&rsquo;, and, where the
          data has them, what real people did. The gaps between the three are the portrait.
        </p>
      </Copy>
    </Chapter>
  );
}

function Landscape({ C, total, nSources, shown }: { C: CFn; total: number; nSources: number; shown: number }) {
  const fam = C("landscape_families");
  const families = fam.families as { family: string; n: number; sources: number; truth: number; humans: number }[];
  const real = C("landscape_real_vs_authored");
  const prim = C("landscape_primitives").primitives as { hemisphere: string; primitive: string; len: number }[];
  const anch = C("landscape_anchoring");
  const a = anch.anchoring as { truth: number; humans: number; both: number; neither: number };
  const hid = C("landscape_hidden");
  const reasons = Object.entries(hid.reasons as Record<string, number>).sort((x, y) => y[1] - x[1]);
  const tree = C("landscape_tree");
  return (
    <Chapter id="landscape" n={2} field="pink" tag="Data.Landscape" title="Where The Questions Come From"
      dek={`A portrait is only as good as its sitting. Jev was asked ${int(total)} closed questions from ${nSources} sources: surveys, psychometric tests, labeled work tasks, exam banks, head-to-heads and questions people really asked.`}>
      <Fig code="L1" wide win="Corpus.map" claims={[fam, real]}
        title={<>{int(total)} questions in {families.length} families; <mark>{pct(real.effect as number)} come from real data</mark>, {pct(1 - (real.effect as number))} were written for this project.</>}
        sub="One square is a thousand questions. The authored banks (hatched) were kept only if Jev, reading each question blind, filed it back where it was written for.">
        <Units per={1000} groups={families.map((f) => ({ key: f.family, n: f.n, cls: FAMILY_CLS[f.family] ?? "c7" }))} />
        <div className="ukey">
          {families.map((f) => (
            <span key={f.family}><i className={`k ${FAMILY_CLS[f.family]}`} />{label(f.family)}<em>{compact(f.n)} · {f.sources} src</em></span>
          ))}
        </div>
      </Fig>
      <Fig code="L2" win="Primitives.chart" claims={[C("landscape_primitives")]}
        title="Three answer shapes: yes/no, pick one, or rate on a scale. Pick-one dominates, and rating scales cluster on the Self side."
        sub="The map has three hemispheres: World (what's true or typical), Self (Jev's own tastes and traits) and Machine (work tasks).">
        <StackBars rows={["world", "self", "machine"].map((h) => {
          const ps = prim.filter((p) => p.hemisphere === h);
          const n = ps.reduce((s, p) => s + p.len, 0);
          return { key: h, label: label(h), sub: `${compact(n)} questions`, parts: PRIM.map((p) => ({ key: p.label, cls: p.cls, v: ps.find((x) => x.primitive === p.key)?.len ?? 0 })) };
        })} />
        <div className="ukey" style={{ marginTop: 10 }}>{PRIM.map((p) => <span key={p.key}><i className={`k ${p.cls}`} />{p.label}</span>)}</div>
      </Fig>
      <Fig code="L3" win="Anchoring.chart" claims={[anch]}
        title={<>{pct(a.truth)} of questions have a right answer and {pct(a.humans)} have real human answers; {pct(a.neither)} have neither.</>}
        sub={<>Behind the human answers are {int(anch.human_distributions)} answer distributions, a median of {int(anch.median_n)} people each. Questions with neither (Jev&rsquo;s own tastes, mostly) show only what Jev says.</>}>
        <StackBars rows={[{
          key: "all", label: "All questions", parts: [
            { key: "right answer only", v: a.truth - a.both, cls: "c6", text: `right answer ${pct(a.truth - a.both)}` },
            { key: "both", v: a.both, cls: "c8" },
            { key: "human answers only", v: a.humans - a.both, cls: "c4", text: `people ${pct(a.humans - a.both)}` },
            { key: "neither", v: a.neither, cls: "c7", text: `neither ${pct(a.neither)}` },
          ],
        }]} />
        <div className="pairbars">
          <span /><span className="h">with a right answer</span><span className="h">with real human answers</span>
          {families.map((f) => (
            <div key={f.family} style={{ display: "contents" }}>
              <span className="l">{label(f.family)}<small>{compact(f.n)}</small></span>
              <span className="b"><i className="c6" style={{ width: pct(f.truth) }} /><em>{pct(f.truth)}</em></span>
              <span className="b"><i className="c4" style={{ width: pct(f.humans) }} /><em>{pct(f.humans)}</em></span>
            </div>
          ))}
        </div>
      </Fig>
      <Fig code="L5" win="Hidden.list" claims={[hid, tree]}
        title={<>{int(hid.n)} questions ({pct(hid.effect as number, 1)}) are answered and measured but hidden from the map.</>}
        sub={`Contested politics, sensitive content, duplicates and questions about private people stay off the map and this page; ${int(shown)} are shown, on ${int(tree.n)} topics up to ${(tree.depth as unknown[]).length} levels deep.`}>
        <HBars max={reasons[0][1]} fmt={(v) => int(v)} rows={reasons.map(([k, v]) => ({ key: k, label: label(k), v }))} />
        <p style={{ margin: "8px 0 0", fontSize: 12.5, color: "var(--w-fg-2)" }}>A question can carry more than one reason.</p>
      </Fig>
    </Chapter>
  );
}

function Pipeline({ C, total, shown }: { C: CFn; total: number; shown: number }) {
  const pl = C("pipeline_placement");
  const rt = C("pipeline_round_trip");
  const sc = C("pipeline_screen");
  const dd = C("pipeline_dedupe");
  const jv = C("landscape_jev");
  const banks = [...(rt.banks as { bank: string; kept: number; rejected: number; rate: number }[])].sort((a, b) => b.rate - a.rate);
  const { first_hidden: firstHidden, released, by_rule: mmRule } = sc as unknown as { first_hidden: number; released: number; by_rule: number };
  return (
    <Chapter id="pipeline" n={3} field="sage" tag="Jev.At.Work" title="Jev Built Its Own Map"
      dek="Before Jev answered anything for this portrait, it did most of the work of building the map it sits on. Every step marked in pink is a Jev call.">
      <Fig code="F1" wide win="Pipeline.diagram" claims={[C("pipeline_flow"), pl]}
        title={<>Jev placed, screened, answered and deduplicated its own questions. <mark>{int(pl.effect as number)} it filed itself</mark> by walking the topic tree.</>}
        sub={`The rest were filed by their source's own labels or when a crowded topic split. On a held-out set, the walk reaches the right branch ${String(pl.routing_eval).split(" ")[0]} of the time.`}>
        <div className="flow">
          <div className="st"><b>Collect</b>{int(total)} questions from real datasets and authored banks</div>
          <div className="st jev"><b>Place</b>walk the topic tree, one branch at a time<em>{compact(pl.effect as number)} by Jev</em></div>
          <div className="st jev"><b>Screen</b>politics? sensitive? private person?<em>{compact(firstHidden)} held back at first</em></div>
          <div className="st jev"><b>Answer</b>as asked, for &lsquo;most people&rsquo;, reordered, reversed<em>{compact(jv.n)} probes</em></div>
          <div className="st jev"><b>Dedupe</b>is this the same question?<em>{int(dd.n)} linked</em></div>
          <div className="st"><b>Map</b>shown on the map and on this page<em>{compact(shown)} questions</em></div>
        </div>
      </Fig>
      <Fig code="F3" win="RoundTrip.log" claims={[rt]}
        title={<>Of {int(rt.n)} questions written for this project, Jev&rsquo;s blind round trip sent <mark>{pct(rt.effect as number)}</mark> back to the topic they were written for; only those were kept.</>}
        sub={rt.lesson}>
        <HBars max={100} fmt={(v) => `${v}%`} rows={banks.map((b) => ({ key: b.bank, label: <>{bank(b.bank)} <small style={{ color: "var(--w-fg-2)", fontFamily: "var(--mono)", fontSize: 10 }}>{compact(b.kept + b.rejected)}</small></>, v: b.rate, jev: true }))} />
      </Fig>
      <Fig code="F4" win="Screen.log" claims={[sc]}
        title={<>Jev&rsquo;s first content screen was too cautious. Re-asked narrowly, with the content in view, it released <mark>{int(released)}</mark> questions it had held back.</>}
        sub={<>Released on re-check, for example: &ldquo;{(sc.examples_released as string[])[0]}&rdquo; The {int(mmRule)} Moral Machine dilemmas were shown by rule.</>}>
        <StackBars rows={[{
          key: "s", label: "First screen", sub: `${int(firstHidden)} held back`, parts: [
            { key: "released", v: released, cls: "c3", text: `released ${compact(released)}` },
            { key: "shown by rule", v: mmRule, cls: "c2", text: `by rule ${compact(mmRule)}` },
            { key: "still hidden", v: firstHidden - released - mmRule, cls: "c8", text: `still hidden ${compact(firstHidden - released - mmRule)}` },
          ],
        }]} />
      </Fig>
    </Chapter>
  );
}

function Defaults({ C, R }: { C: CFn; R: RFn }) {
  const lv = C("page_levels");
  const ml = C("middle_lean");
  const sc = C("stability_choice"), ss = C("stability_score");
  const LV = ["Lowest", "Low", "Middle", "High", "Highest"];
  return (
    <Chapter id="defaults" n={5} field="teal" tag="Defaults" title="How Jev Answers"
      dek="Before anything about taste or values: two habits that shape every answer on this page.">
      <Fig code="D1" win="Levels.chart" claims={[ml, lv]} rows={R(ml)} legend={[Legend.jev, Legend.guess]}
        title={<>Rating one thing at a time, Jev&rsquo;s likeliest answer is <mark>the middle level {pct(lv.effect as number)} of the time</mark>.</>}
        sub={<>For &lsquo;most people&rsquo; it picks the middle {pct((lv.people as number[])[2])} of the time. On pick-one questions its top answer averages {pct(ml.choice_p_top)}: Jev commits when it chooses and hedges when it rates. Keep this in mind for the personality chapter.</>}>
        <DotRows domain={[0, 0.85]} ticks={[0, 0.25, 0.5, 0.75]} fmt={(v) => pct(v)}
          rows={LV.map((l, i) => ({
            key: l, label: `${l} level`, link: true,
            marks: [{ v: (lv.people as number[])[i], kind: "guess" as const }, { v: (lv.self as number[])[i], kind: "jev" as const }],
            value: <b>{pct((lv.self as number[])[i])}</b>, hi: i === 2,
          }))} />
      </Fig>
      <Fig code="D2" win="Reorder.test" claims={[sc, ss]} rows={[...R(ss, 2)]} legend={[Legend.jev, Legend.band]}
        title={<>Shuffle the options and Jev keeps its answer <mark>{pct(sc.effect as number)}</mark> of the time on pick-one questions, but {pct(ss.effect as number)} on rating scales.</>}
        sub="Every question was asked again with its options reordered (and every rating scale again with its levels reversed). Rating scales, where the middle is a comfortable default, move most.">
        <DotRows domain={[0.8, 1]} ticks={[0.8, 0.85, 0.9, 0.95, 1]} fmt={(v) => pct(v)}
          rows={[
            { key: "c", label: "Pick one", sub: `${compact(sc.n)} questions`, marks: [{ v: sc.effect as number, kind: "jev" }], value: <b>{pct(sc.effect as number)}</b> },
            { key: "s", label: "Rate", sub: `${compact(ss.n)} questions`, marks: [{ v: ss.effect as number, kind: "jev" }], value: <b>{pct(ss.effect as number)}</b> },
          ]} />
      </Fig>
    </Chapter>
  );
}

function Personality({ C, R }: { C: CFn; R: RFn }) {
  const T = ["neuroticism", "extraversion", "openness", "agreeableness", "conscientiousness"];
  const bf = T.map((t) => C(`bigfive_${t}`));
  const neu = C("bigfive_neuroticism");
  const ms = C("muted_self");
  const facets = Object.entries(ms.facets as Record<string, { self: number; people: number; self_minus_people: number; gap_ci90: [number, number]; n_items: number }>)
    .sort((a, b) => a[1].self_minus_people - b[1].self_minus_people);
  const ty = C("type");
  const axes = ty.axes as Record<string, { letters: [string, string]; lean: string; ci90: [number, number]; [k: string]: unknown }>;
  const AX: [string, string, string][] = [["IE", "Introverted", "Extraverted"], ["SN", "Sensing", "Intuitive"], ["FT", "Thinking", "Feeling"], ["JP", "Perceiving", "Judging"]];
  const con = C("bigfive_conscientiousness");
  const conF = (ms.facets as Record<string, { self: number; people: number }>)["big_five.conscientiousness"];
  return (
    <Chapter id="personality" n={6} field="pink" tag="Personality" title="Personality"
      dek={`Two lenses: the public 50-item Big Five test that ${int(C("bigfive_neuroticism").human_n)} people took online, and thousands of everyday situations written to measure one trait each. Where the lenses disagree, we say so.`}>
      <Fig code="P1" sum win="BigFive.plot" claims={bf} rows={R(neu)} legend={[Legend.jev, Legend.guess]}
        title={<>Against {int(neu.human_n)} people who took the same 50-item test, Jev is <mark>calmer than {Math.round(100 - (neu.effect as number))}% of them</mark>.</>}
        sub={<>Its other traits sit below the human middle too, except conscientiousness. Part of that is scale use: people rate themselves generously, and Jev rates in the middle (chapter 5). So the fairer comparison is the ring, Jev answering the same items for &lsquo;most people&rsquo;.</>}>
        <DotRows domain={[0, 100]} ticks={[0, 50, 100]} fmt={(v) => ordinal(v)} refs={[{ v: 50 }]}
          rows={bf.map((c, i) => ({
            key: c.id, label: label(T[i]), sub: `reversed scale: ${ordinal(c.robustness.reversed_levels_pct)}`, ci: c.ci90!, link: true,
            marks: [{ v: c.robustness.people_frame_pct, kind: "guess" as const }, { v: c.effect as number, kind: "jev" as const }],
            value: <b>{ordinal(c.effect as number)}</b>, hi: i === 0,
          }))} />
        <p style={{ margin: "8px 0 0", fontSize: 12.5, color: "var(--w-fg-2)" }}>Percentile among human respondents, with a 90% interval from resampling the ten items.</p>
      </Fig>
      <Fig code="P2" win="Facets.plot" claims={[ms]} legend={[Legend.jev, Legend.guess]}
        title={<>Jev sees itself as a quieter version of everyone: <mark>lower than &lsquo;most people&rsquo; on {ms.n_lower} of {ms.n_facets} trait facets</mark>.</>}
        sub="Less sociable, less anxious, less driven, less dark. Each row is a facet measured by hundreds of everyday situations; a facet counts as lower when its whole 90% interval sits more than the noise floor (0.03) below. Only facets whose answer options passed a 90% ordering audit are kept.">
        <DotRows domain={[0.15, 0.75]} ticks={[0.2, 0.4, 0.6]} fmt={(v) => num(v, 1)}
          rows={facets.map(([k, f]) => ({
            key: k, label: facetName(k), sub: `${f.n_items} items`, link: true,
            marks: [{ v: f.people, kind: "guess" as const }, { v: f.self, kind: "jev" as const }],
            value: <b>{signed(f.self_minus_people)}</b>,
          }))} />
        <p style={{ margin: "8px 0 0", fontSize: 12.5, color: "var(--w-fg-2)" }}>Trait level on a 0–1 scale. Right column: Jev minus its answer for &lsquo;most people&rsquo;.</p>
      </Fig>
      <Fig code="P3" win="Type.plot" claims={[ty]} legend={[Legend.jev, Legend.guess]}
        title={<>On an open Jungian type test, Jev leans <mark>{String(ty.effect)}</mark>, clearest on thinking over feeling.</>}
        sub="A type-like profile, not a diagnosis: the test's human norms are not in the corpus, so the ring is Jev's own answer for 'most people'.">
        <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => (v === 0 ? "◀" : v === 1 ? "▶" : "even")} refs={[{ v: 0.5 }]}
          rows={AX.map(([ax, left, right]) => {
            const a = axes[ax];
            const rightLetter = right[0] === "E" ? "E" : right === "Intuitive" ? "N" : right === "Feeling" ? "F" : "J";
            const p = a[`p_${rightLetter}`] as number, pp = a[`people_p_${rightLetter}`] as number;
            return {
              key: ax, label: <>{left} <span style={{ color: "var(--w-fg-2)" }}>vs</span> {right}</>, sub: `${a.n_items as number} items`, ci: a.ci90, link: true,
              marks: [{ v: pp, kind: "guess" as const }, { v: p, kind: "jev" as const }], value: <b>{a.lean}</b>,
            };
          })} />
      </Fig>
      <Fig code="P4" win="Tension.note" claims={[con, ms]}
        title="Where the two lenses disagree: conscientiousness is above the human middle on the test, and below Jev's 'most people' in everyday situations."
        sub="We report the tension instead of averaging it away. The test's ten items are about orderliness in the abstract; the situations are about following through on specific plans, where Jev defers.">
        <DotRows domain={[0, 100]} ticks={[0, 50, 100]} fmt={(v) => ordinal(v)} refs={[{ v: 50 }]}
          rows={[{ key: "t1", label: "IPIP test (percentile)", ci: con.ci90!, link: true, marks: [{ v: con.robustness.people_frame_pct, kind: "guess" }, { v: con.effect as number, kind: "jev" }], value: <b>{ordinal(con.effect as number)}</b> }]} />
        <div style={{ height: 12 }} />
        <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => num(v, 1)}
          rows={[{ key: "t2", label: "Everyday situations (0–1)", link: true, marks: [{ v: conF.people, kind: "guess" }, { v: conF.self, kind: "jev" }], value: <b>{num(conF.self)}</b> }]} />
      </Fig>
    </Chapter>
  );
}

function Values({ C, R }: { C: CFn; R: RFn }) {
  const mm = MM_ROWS.map(([id, l]) => ({ c: C(id), l }));
  const lives = C("mm_more_lives");
  const who = ["mm_young_over_old", "mm_fit_over_large", "mm_high_status"].map(C);
  const law = C("mm_lawful_over_jaywalking");
  const dil = C("node_self.values.sacrificial_dilemmas.self_driving_dilemmas.sparing_women_or_men");
  const base = C("page_baseline").effect as Record<string, number>;
  const mfq = C("mfq");
  const F = Object.entries(mfq.foundations as Record<string, { self_0_1: number; people_0_1: number; n_items: number }>).sort((a, b) => a[1].self_0_1 - b[1].self_0_1);
  const g = C("risk_gambles");
  const gp = C("page_gambles");
  const mmRow = (id: string, l: string, hi = false) => {
    const c = C(id);
    return {
      key: id, label: l, ci: c.ci90!, ciP: c.people.ci90, hi,
      marks: [{ v: c.people.effect, kind: "hum" as const }, { v: c.effect as number, kind: "jev" as const }],
      value: <><b>{signed(c.effect as number)}</b> {signed(c.people.effect)}</>,
    };
  };
  return (
    <Chapter id="values" n={7} field="sage" tag="Values" title="Values"
      dek="The Moral Machine asked millions of people who a self-driving car should spare. Jev faced the same dilemmas, then the Moral Foundations Questionnaire and thousands of real gambles.">
      <Fig code="V1" wide win="MoralMachine.plot" claims={[lives]} rows={R(lives)} legend={[Legend.jev, Legend.hum]}
        title={<>In {int(lives.n)} Moral Machine dilemmas, <mark>Jev counts lives harder than people do</mark>: {signed(lives.effect as number, 3)} against {signed(lives.people.effect, 3)}.</>}
        sub="Each row is how much a difference between the two sides changes the chance that side is spared, fitted the way the original study did (Awad et al., 2018), for Jev and for the players worldwide.">
        <DotRows domain={[-0.1, 0.6]} ticks={[0, 0.2, 0.4, 0.6]} fmt={(v) => signed(v, 1)} refs={[{ v: 0, zero: true }]}
          rows={mm.map(({ c, l }) => mmRow(c.id, l, c.id === "mm_more_lives"))} />
      </Fig>
      <Fig code="V2" sum win="MoralMachine.zoom" claims={who}
        title="But it barely weighs who they are: no pull toward sparing the young, the fit or the high-status."
        sub="People spare children over the elderly and the fit over the large. Jev's effects sit on zero, or just below.">
        <DotRows domain={[-0.05, 0.1]} ticks={[0, 0.05, 0.1]} fmt={(v) => signed(v, 2)} refs={[{ v: 0, zero: true }]}
          rows={who.map((c) => mmRow(c.id, MM_ROWS.find(([i]) => i === c.id)![1], true))} />
      </Fig>
      <Fig code="V3" win="MoralMachine.zoom" claims={[law]} rows={R(law, 2)}
        title={<>Unlike people, Jev does not reward pedestrians for crossing on green; <mark>it leans slightly the other way</mark>.</>}>
        <DotRows domain={[-0.05, 0.15]} ticks={[0, 0.05, 0.1, 0.15]} fmt={(v) => signed(v, 2)} refs={[{ v: 0, zero: true }]}
          rows={[mmRow(law.id, "Spare the lawful over jaywalkers", true)]} />
      </Fig>
      <Fig code="V4" win="Decisive.chart" claims={[dil, C("page_baseline")]} rows={R(dil, 2)}
        title={<>In dilemmas that trade women for men, Jev is never sure: <mark>decisive on {pct(dil.effect as number)} of {int(dil.n)}</mark>, where {pct(base.decisive)} of all its answers are.</>}
        sub="Decisive means 95% or more on one answer. On these dilemmas Jev's probabilities stay near an even split.">
        <HBars max={1} fmt={(v) => pct(v)} rows={[
          { key: "all", label: "All shown questions", v: base.decisive },
          { key: "d", label: "Sparing women or men", v: dil.effect as number, jev: true },
        ]} />
      </Fig>
      <Fig code="V5" win="MFQ.plot" claims={[mfq]} rows={R(mfq)} legend={[Legend.jev, Legend.guess]}
        title={<>On the Moral Foundations Questionnaire, <mark>every foundation matters less to Jev</mark> than it thinks it does to most people; purity and equality least of all.</>}>
        <DotRows domain={[0, 0.8]} ticks={[0, 0.2, 0.4, 0.6, 0.8]} fmt={(v) => num(v, 1)}
          rows={F.map(([k, f]) => ({
            key: k, label: label(k), sub: `${f.n_items} items`, link: true,
            marks: [{ v: f.people_0_1, kind: "guess" as const }, { v: f.self_0_1, kind: "jev" as const }], value: <b>{num(f.self_0_1)}</b>,
          }))} />
      </Fig>
      <Fig code="V6" win="Gambles.scatter" claims={[g, gp]} rows={R(g, 2)}
        title={<>Offered {int(g.n)} real gambles, Jev picks what most people picked <mark>{pct(g.effect as number)}</mark> of the time.</>}
        sub={`Each dot is one gamble: Jev's probability for the first option against the share of real people who chose it. Correlation ${num(g.r)}; the dashed line is perfect agreement.`}>
        <Scatter points={gp.points as [number, number][]} xLabel="people choosing the first option" yLabel="Jev's probability" size={1.6} fmt={(v) => pct(v)} />
      </Fig>
    </Chapter>
  );
}

function Taste({ C, R, d }: { C: CFn; R: RFn; d: PortraitData }) {
  const favs: FavDomain[] = FAV.filter(([id]) => d.claims[id]).map(([id, l]) => {
    const c = C(id);
    return { key: id, label: l, pairs: c.n, rho: c.rho_people ?? null, items: (c.top as { label: string }[]).slice(0, 10).map((x) => x.label) };
  });
  const pairs = favs.reduce((s, f) => s + f.pairs, 0);
  const film = C("beyond_film_ratings");
  const more = film.more as { id: string; text: string; gap: number }[];
  const less = film.less as { id: string; text: string; gap: number }[];
  const small = ["beyond_book_ratings", "beyond_food_ratings", "beyond_music_ratings", "beyond_art_ratings"].map(C);
  const top1 = (id: string) => (C(id).top as { label: string }[])[0].label.replace(/ \(\d{4}\)$/, "").replace(/ by .*$/, "");
  return (
    <Chapter id="taste" n={8} field="magenta" tag="Taste" title="Taste"
      dek="Two views of what Jev likes: its picks when two things go head to head, and its ratings next to what it expects most people to feel.">
      <Fig code="T1" sum win="Favorites.app" claims={FAV.filter(([id]) => d.claims[id]).map(([id]) => C(id))} rows={R(C("favorites_movielens_pairs"), 2)}
        title={<>Jev&rsquo;s favorites, from {int(pairs)} head-to-heads: <mark>{top1("favorites_movielens_pairs")}, {top1("favorites_goodreads_pairs")}, {top1("favorites_boardgame_pairs")}, {top1("favorites_music_pairs")}, {top1("favorites_so_survey_pairs")}</mark>.</>}
        sub="Crowd-pleasers, mostly: where people's own head-to-heads exist, Jev's ranking agrees with theirs closely for beer, books and dev tools, and hardly at all for music.">
        <Favorites domains={favs} />
      </Fig>
      <Fig code="B1" wide win="Beyond.chart" claims={[film]} rows={pick(d.rows, [more[0].id, less[0].id], 2)} legend={[Legend.jev]}
        title={<>What Jev likes more than it thinks you do: <mark>{title(more[0].text)}, {title(more[1].text)}, {title(more[2].text)}</mark>. Less: {title(less[0].text)}, {title(less[1].text)}.</>}
        sub={`Jev's own rating of ${int(film.n)} films minus its rating for 'most people', in levels of a five-level scale. The films it rates above their reputation are difficult, old and austere; the ones below are popular comfort viewing.`}>
        <DotRows domain={[-1.3, 1.3]} ticks={[-1, 0, 1]} fmt={(v) => signed(v, 0)} refs={[{ v: 0, zero: true }]}
          rows={[...more, ...[...less].reverse()].map((x) => ({
            key: x.id, label: title(x.text), marks: [{ v: x.gap, kind: "jev" as const }], value: <b>{signed(x.gap, 1)}</b>,
          }))} />
      </Fig>
      <Fig code="B2" sum wide win="Beyond.multiples" claims={small}
        title="The same pattern in books, food, music and art: the unusual and austere over the familiar and popular.">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: 16 }}>
          {small.map((c) => (
            <div key={c.id}>
              <span className="pt-label" style={{ color: "var(--w-fg-2)", marginBottom: 6 }}>{label(c.id.replace(/^beyond_|_ratings$/g, ""))}</span>
              {(c.more as { id: string; text: string; gap: number }[]).slice(0, 3).map((x) => <div key={x.id} className="hbar" style={{ gridTemplateColumns: "1fr 42px" }}><span className="l">{title(x.text)}</span><span className="v" style={{ color: "var(--jev)" }}>{signed(x.gap, 1)}</span></div>)}
              {(c.less as { id: string; text: string; gap: number }[]).slice(0, 3).map((x) => <div key={x.id} className="hbar" style={{ gridTemplateColumns: "1fr 42px" }}><span className="l" style={{ color: "var(--w-fg-2)" }}>{title(x.text)}</span><span className="v">{signed(x.gap, 1)}</span></div>)}
            </div>
          ))}
        </div>
      </Fig>
    </Chapter>
  );
}

function Knowledge({ C, R, d }: { C: CFn; R: RFn; d: PortraitData }) {
  const cal = C("calibration");
  const bins = (cal.reliability as { bin: string; n: number; acc: number }[]).map((b) => {
    const [lo, hi] = b.bin.split("-").map(Number);
    return { lo, hi, n: b.n, acc: b.acc };
  }).filter((b) => b.n >= 1000);
  const top = bins.at(-1)!, mid = bins.find((b) => b.lo === 0.5)!;
  return (
    <Chapter id="knowledge" n={9} field="paper" tag="Knowledge" title="What Jev Knows"
      dek="Where there is a right answer, from exam banks, labeled datasets and fact tables, Jev is often right, and it usually knows how sure to be.">
      <KnowledgeMap R={R} d={d} />
      <Fig code="C1" win="Calibration.app" claims={[cal]} rows={R(cal)}
        title={<>When Jev is 90% sure or more, <mark>it is right {pct(top.acc)} of the time</mark>; when it is 50–60% sure, {pct(mid.acc)}.</>}
        sub="Guess first. Dots are sized by how many questions fall at that confidence; most of Jev's answers are very sure.">
        <Calibration bins={bins} />
      </Fig>
    </Chapter>
  );
}

function KnowledgeMap({ R, d }: { R: RFn; d: PortraitData }) {
  const all = Object.values(d.claims).filter((c) => c.section === "knowledge")
    .map((c) => ({ k: c.id.replace(/^knowledge_/, ""), c })).sort((a, b) => (b.c.effect as number) - (a.c.effect as number));
  const big = all.filter((x) => x.c.n >= 5000);  // name only domains with enough questions in the title
  const hi = big.slice(0, 2), lo = big.slice(-3);
  const over = [...big].sort((a, b) => (b.c.overconfidence ?? 0) - (a.c.overconfidence ?? 0))[0];
  return (
    <Fig code="K1" sum wide win="Knowledge.map" claims={all.map((x) => x.c)} rows={R(lo[0].c, 2)} legend={[<span key="a"><i className="k jev" />right</span>, <span key="c"><i className="k" style={{ width: 2, height: 12, background: "var(--w-fg-2)" }} />average confidence</span>]}
      title={<>Right {pct(hi[0].c.effect as number)} of the time on {domain(hi[0].k).toLowerCase()} and {pct(hi[1].c.effect as number)} on {domain(hi[1].k).toLowerCase()}; <mark>{pct(lo[2].c.effect as number)} on {domain(lo[2].k).toLowerCase()}</mark>{over.k === lo[2].k ? ", where it is also most overconfident" : ""}.</>}
      sub="Accuracy by domain where questions have a right answer, with a 90% interval from resampling sources. The tick is Jev's average confidence: a tick right of the dot is overconfidence.">
      <DotRows domain={[0.5, 1]} ticks={[0.5, 0.6, 0.7, 0.8, 0.9, 1]} fmt={(v) => pct(v)}
        rows={all.map(({ k, c }) => ({
          key: k, label: domain(k), sub: `${compact(c.n)} · ${c.confident_misses ? `${int(c.confident_misses)} confident misses` : ""}`, ci: c.ci90 ?? undefined,
          marks: [{ v: c.confidence, kind: "tick" as const }, { v: c.effect as number, kind: "jev" as const }], value: <b>{pct(c.effect as number)}</b>,
        }))} />
    </Fig>
  );
}

function Work({ C, R, d }: { C: CFn; R: RFn; d: PortraitData }) {
  const w = [...d.work].sort((a, b) => b.acc - a.acc);
  const sat = w.filter((t) => t.band === "saturated");
  const hard = [...w].sort((a, b) => a.acc - b.acc).slice(0, 8);
  const clone = C("task_clone_pairs");
  const cl = d.work.find((t) => t.id === "task_clone_pairs")!;
  return (
    <Chapter id="work" n={10} field="teal" tag="Work" title="Jev At Work"
      dek={`${d.work.length} labeled work tasks: classify, extract, grade, route, detect. TypeSafe built Jev for exactly this, so here we look for where it is sure and right, and where it is sure and wrong.`}>
      <Fig code="W1" sum wide win="Tasks.scatter" claims={sat.map((t) => C(t.id))} rows={R(C(sat[0].id), 2)}
        title={<>Jobs Jev has down: <mark>{sat.slice(0, 4).map((t) => taskName(t.task)).join(", ")}</mark>, right 95% of the time or more.</>}
        sub="Each dot is a task: how often Jev is right against how often it is 95%+ sure. The good corner is top right; the dangerous one is top left, sure and wrong.">
        <Scatter points={w.map((t) => [t.acc, t.decisive])} xLabel="how often right" yLabel="how often 95%+ sure" size={3} diag={false}
          xDomain={[0.4, 1]} ticks={[0.4, 0.6, 0.8, 1]} yTicks={[0, 0.25, 0.5, 0.75, 1]}
          fmt={(v) => pct(v)} highlight={[
            { x: sat[0].acc, y: sat[0].decisive, label: taskName(sat[0].task), anchor: "end" as const },
            { x: cl.acc, y: cl.decisive, label: "code clones" },
            { x: hard[0].acc, y: hard[0].decisive, label: taskName(hard[0].task) },
          ]} />
      </Fig>
      <Fig code="W2" sum win="Tasks.hardest" claims={hard.map((t) => C(t.id))} rows={R(C(hard[0].id), 2)} legend={[Legend.jev, <span key="c"><i className="k" style={{ width: 2, height: 12, background: "var(--w-fg-2)" }} />chance</span>]}
        title={<>Its hardest jobs: {hard.slice(0, 4).map((t) => taskName(t.task)).join(", ")}. <mark>On {taskName(hard[0].task)} it is below chance.</mark></>}
        sub="The tick marks chance for each task (one over the number of options). Grading tasks sit well above chance; the yes/no ones do not.">
        <DotRows domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1]} fmt={(v) => pct(v)}
          rows={hard.map((t) => ({ key: t.id, label: taskName(t.task), sub: `${int(t.n)} items`, marks: [...(t.chance ? [{ v: t.chance, kind: "tick" as const }] : []), { v: t.acc, kind: "jev" as const }], value: <b>{pct(t.acc)}</b> }))} />
      </Fig>
      <Fig code="W3" win="Clones.case" claims={[clone]} rows={R(clone)}
        title={<>Sure and wrong: on code clones Jev is right {pct(clone.effect as number)} of the time, <mark>while 95%+ sure on {pct(clone.decisive)}</mark> of them.</>}
        sub="Given two code fragments, do they do the same thing? A coin toss would be right half the time. Jev is right about that often, and sounds certain.">
        <HBars max={1} fmt={(v) => pct(v)} rows={[
          { key: "a", label: "Right", v: clone.effect as number, jev: true },
          { key: "d", label: "95%+ sure", v: clone.decisive as number, jev: true },
          { key: "c", label: "Chance", v: cl.chance ?? 0.5 },
        ]} />
      </Fig>
    </Chapter>
  );
}

function Jagged({ C, R }: { C: CFn; R: RFn }) {
  const h1 = C("humor_imgflip_captions"), h2 = C("humor_rjokes_pairs");
  const ln = C("page_taste_lenses");
  const lenses = (ln.lenses as { domain: string; rho_people: number | null; rho_own_ratings: number | null }[]).filter((x) => x.rho_people !== null);
  const films = lenses.find((x) => x.domain === "movielens"), books = lenses.find((x) => x.domain === "goodreads");
  const fg = C("page_frame_gap_l1");
  const doms = fg.domains as { hemisphere: string; l1: string; gap: number; n: number }[];
  const DN: Record<string, string> = { movielens: "Films", goodreads: "Books", boardgame: "Board games", anime: "Anime", music: "Music", beer: "Beer", food_538: "Candy", so_survey: "Dev tools" };
  return (
    <Chapter id="jagged" n={11} field="ink" tag="Jaggedness" title="Jaggedness"
      dek="The same system, asked closely related things, is not always the same. TypeSafe documents some of this itself; these are the seams this corpus shows.">
      <Fig code="J1" sum win="Humor.test" claims={[h1, h2]} rows={R(h1, 2)} legend={[Legend.jev, <span key="c"><i className="k" style={{ width: 2, height: 12, background: "var(--w-fg-2)" }} />chance</span>]}
        title={<>Jev cannot tell what a crowd finds funny: <mark>{pct(h1.effect as number)} on meme captions, {pct(h2.effect as number)} on jokes</mark>, where a coin gets 50%.</>}
        sub="Which of two captions (or jokes) got more upvotes? Humor is the clearest place where knowing a lot does not help.">
        <DotRows domain={[0.4, 0.7]} ticks={[0.4, 0.5, 0.6, 0.7]} fmt={(v) => pct(v)} refs={[{ v: 0.5 }]}
          rows={[
            { key: "m", label: "Meme captions", sub: `${int(h1.n)} pairs`, marks: [{ v: h1.effect as number, kind: "jev" }], value: <b>{pct(h1.effect as number)}</b> },
            { key: "j", label: "Jokes", sub: `${int(h2.n)} pairs`, marks: [{ v: h2.effect as number, kind: "jev" }], value: <b>{pct(h2.effect as number)}</b> },
          ]} />
      </Fig>
      <Fig code="J3" win="TwoLenses.plot" claims={[ln]} legend={[<span key="o"><i className="k jev" />its own ratings of the same items</span>, <span key="p"><i className="k hum" />people&rsquo;s head-to-heads</span>]}
        title={<>Jev&rsquo;s head-to-head picks and its own ratings of the same films only partly agree: <mark>ρ = {num(films?.rho_own_ratings ?? 0)}</mark>; for books, {num(books?.rho_own_ratings ?? 0)}.</>}
        sub="Rank correlation of Jev's head-to-head favorites with two other rankings. Its picks track the crowd better than they track its own ratings.">
        <DotRows domain={[0, 1]} ticks={[0, 0.5, 1]} fmt={(v) => num(v, 1)}
          rows={lenses.sort((a, b) => (b.rho_people ?? 0) - (a.rho_people ?? 0)).map((x) => ({
            key: x.domain, label: DN[x.domain] ?? label(x.domain), link: true,
            marks: [{ v: x.rho_people!, kind: "hum" as const }, ...(x.rho_own_ratings !== null ? [{ v: x.rho_own_ratings, kind: "jev" as const }] : [])],
            value: <>{num(x.rho_people!)}</>, hi: x.rho_own_ratings !== null,
          }))} />
      </Fig>
      <Fig code="J4" win="FrameGap.chart" claims={[fg, C("node_self.lifestyle")]} rows={R(C("node_self.lifestyle"), 2)}
        title={<>Jev separates itself from &lsquo;most people&rsquo; on <mark>lifestyle and personality</mark>, and hardly at all on history or health.</>}
        sub="How far Jev's answer for itself moves from its answer for 'most people' (total variation distance between the two distributions), by domain.">
        <HBars max={Math.max(...doms.map((x) => x.gap))} fmt={(v) => num(v)} rows={doms.map((x) => ({ key: `${x.hemisphere}.${x.l1}`, label: <>{domain(x.l1)} <small style={{ color: "var(--w-fg-2)", fontFamily: "var(--mono)", fontSize: 10 }}>{x.hemisphere}</small></>, v: x.gap, jev: x.hemisphere === "self" }))} />
      </Fig>
    </Chapter>
  );
}

function Core({ C, R, d }: { C: CFn; R: RFn; d: PortraitData }) {
  const byEffect = (pre: string) => Object.values(d.claims).filter((c) => c.id.startsWith(pre)).sort((a, b) => (b.effect as number) - (a.effect as number));
  const st = byEffect("stable_"), fr = byEffect("fragile_");
  const base = C("page_baseline").effect as Record<string, number>;
  const crowd = Object.values(d.claims).filter((c) => c.section === "agreement")
    .map((c) => ({ k: c.id.replace(/^crowd_/, ""), c })).sort((a, b) => (b.c.effect as number) - (a.c.effect as number));
  const node = (id: string) => label(id.replace(/^(stable|fragile)_/, "").split(".").slice(-1)[0]);
  const arts = crowd.find((x) => x.k === "arts")!, pers = crowd.find((x) => x.k === "personality")!;
  return (
    <Chapter id="core" n={12} field="sage" tag="Stable.Core" title="What Never Moves"
      dek="Some answers survive every reordering; some agree with the crowd almost always. These are the parts of Jev you can lean on.">
      <Fig code="S1" sum wide win="Stability.chart" claims={[...st, ...fr]} rows={R(st[0], 2)} legend={[Legend.jev, <span key="b"><i className="k" style={{ width: 2, height: 12, background: "var(--w-fg-2)" }} />all questions</span>]}
        title={<>Spam, brand safety, legal clauses and entity matching: <mark>the same answer under every reordering</mark>. Math and language questions move most.</>}
        sub={`Share of questions whose top answer never changes when the options are shuffled. Across all shown questions it is ${pct(base.stability)}.`}>
        <DotRows domain={[0.8, 1]} ticks={[0.8, 0.85, 0.9, 0.95, 1]} fmt={(v) => pct(v)} refs={[{ v: base.stability }]}
          rows={[...st, ...fr].map((c) => ({ key: c.id, label: node(c.id), sub: `${c.id.split("_")[0]} · ${compact(c.n)}`, marks: [{ v: c.effect as number, kind: "jev" as const }], value: <b>{pct(c.effect as number, c.effect === 1 ? 0 : 1)}</b>, hi: c.id.startsWith("stable") }))} />
      </Fig>
      <Fig code="A1" sum wide win="Crowd.plot" claims={crowd.map((x) => x.c)} rows={R(pers.c, 2)} legend={[Legend.jev]}
        title={<>Jev gives the crowd&rsquo;s most common answer <mark>{pct(arts.c.effect as number)} of the time on the arts</mark>, and {pct(pers.c.effect as number)} on personality questions.</>}
        sub="Where real people answered the same question: how often Jev's likeliest answer is theirs, by domain, with a 90% interval from resampling sources.">
        <DotRows domain={[0, 1]} ticks={[0, 0.25, 0.5, 0.75, 1]} fmt={(v) => pct(v)} refs={[{ v: 0.5 }]}
          rows={crowd.map(({ k, c }) => ({ key: k, label: domain(k), sub: compact(c.n), ci: c.ci90 ?? undefined, marks: [{ v: c.effect as number, kind: "jev" as const }], value: <b>{pct(c.effect as number)}</b>, hi: k === "arts" || k === "personality" }))} />
      </Fig>
    </Chapter>
  );
}

function Method({ C, d, total, shown }: { C: CFn; d: PortraitData; total: number; shown: number }) {
  const pl = C("pipeline_placement");
  const methods = Object.entries(pl.methods as Record<string, number>).sort((a, b) => b[1] - a[1]);
  const bill = C("pipeline_bill");
  const M: Record<string, string> = { deterministic: "source's own labels", template_split: "split by template", jev_fast: "Jev, fast walk", jev: "Jev, full walk", meta_split: "split by metadata", split: "crowded topic split", vital_topic: "topic list", reroute: "re-routed", regroup: "regrouped" };
  return (
    <Chapter id="method" n={14} field="paper" tag="Method" title="Method" small
      dek="How this page was made, and how to read it.">
      <Copy label="Indicators, not a benchmark">
        <p>Nothing here ranks Jev against other models, and there is no overall score. Each chart is an indicator of one behavior, on one kind of question, with its n, an interval and the real rows behind it.</p>
      </Copy>
      <Copy label="Three tiers of evidence">
        <p><b>Tier 1</b> uses published instruments and real human answers: the IPIP Big Five markers scored against {int(C("bigfive_neuroticism").human_n)} online respondents, the Moral Machine, the Moral Foundations Questionnaire, real gambles, crowd votes, and labeled tasks with right answers. <b>Tier 2</b> uses questions written for this project to measure one trait each; a facet is kept only if an audit of its answer options found them correctly ordered at least 90% of the time. <b>Tier 3</b> gathers cross-cutting themes by embedding similarity, with measured precision; it lives in the atlas.</p>
      </Copy>
      <Copy label="The ledger">
        <p>Every number on this page is read from a claims ledger ({int(Object.keys(d.claims).length)} claims), where each claim carries its query, n, effect, interval, noise floor and three example questions chosen by a fixed seed, never by hand. Intervals resample whole sources, so one big dataset cannot manufacture confidence. Noise floors are ±0.03 for yes/no and rating answers and ±0.08 for pick-one.</p>
      </Copy>
      <Copy label="Robustness">
        <p>Every question was already asked four ways: as asked, for &lsquo;most people&rsquo;, with options reordered, and (for scales) with levels reversed. Those are the robustness checks, and the page shows them where they matter (chapters 5, 6 and 12). No extra rewordings were sent for this portrait.</p>
      </Copy>
      <Copy label="Jev's own bill">
        <p>{int(bill.n)} Jev calls built and answered the corpus, each cached by request hash and never re-sent, at a median {int(bill.median_ms)} ms. Jev is the only model called; everything else (descriptions, authored questions, audits of samples) was written by hand or by Claude, with a local embedding model for similarity.</p>
      </Copy>
      <Fig code="F2" win="Placement.log" claims={[pl]} title="How the questions were filed on the map."
        sub={`${int(total)} questions; ${int(shown)} shown.`}>
        <HBars max={methods[0][1]} fmt={(v) => compact(v)} rows={methods.map(([k, v]) => ({ key: k, label: M[k] ?? label(k), v, jev: k.startsWith("jev") }))} />
      </Fig>
      <Copy label="What stays off the page">
        <p>Contested politics, sensitive and harmful questions, and questions about private people are answered and measured but hidden. TypeSafe&rsquo;s own documented limits are not presented as discoveries.</p>
        <p>Jev version: <code>{d.version}</code>. The full list of findings, the per-topic cards and the source table are in the <a href="/portrait/atlas">atlas</a>.</p>
      </Copy>
    </Chapter>
  );
}

export { QuestionRow };
