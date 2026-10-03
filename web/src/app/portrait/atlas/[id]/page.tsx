import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Nav } from "@/components/portrait/ui";
import Chart from "@/components/experiments/Chart";
import ExMeme from "@/components/experiments/ExMeme";
import Md from "@/components/experiments/Md";
import Rows from "@/components/experiments/Rows";
import { loadExperiments } from "@/components/experiments/data";
import type { Experiment } from "@/components/experiments/types";
import "@/components/experiments/experiments.css";

// One experiment as a case study (docs/17, "Page structure"): the finding first (result and chart, in short, what the
// data shows, what it means), then the caveats beside Jev's own answers about it, then why it was asked and how it was
// done, where its questions live on the map, and every question behind it.
// Every case study is built once per deploy, so it comes from the CDN; publish.py redeploys with new data.
export async function generateStaticParams() {
  return ((await loadExperiments())?.experiments ?? []).map((e) => ({ id: e.id }));
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const e = (await loadExperiments())?.experiments.find((x) => x.id === id);
  return { title: e ? `${e.title} · Atlas · askjev` : "Case study · Atlas · askjev" };
}

type SectionKey = "why" | "data" | "asked" | "measured" | "found" | "means";
const TITLE: Record<SectionKey, string> = {
  found: "What the data shows", means: "What it means, and what it doesn't", why: "Why ask this",
  data: "The people and the data", asked: "What Jev was asked", measured: "How it was measured",
};

// Before a case study exists, the spec's fields stand in for its sections.
function sectionsOf(e: Experiment): Partial<Record<SectionKey, string>> {
  if (e.case) return e.case.sections;
  return { why: `${e.question}\n\n${e.why}`, data: `${e.sourcing}\n\nCompared with: ${e.compared_with}`, measured: e.scoring };
}

function Topics({ e }: { e: Experiment }) {
  const topics = e.topics ?? [];
  if (!topics.length) return null;
  const groups = new Map<string, { label: string; items: typeof topics }>();
  for (const t of topics) {
    const g = groups.get(t.parent) ?? { label: t.parent_label, items: [] };
    g.items.push(t);
    groups.set(t.parent, g);
  }
  const nTopics = e.n_topics ?? topics.length;
  return (
    <section className="ex-where" aria-labelledby="ex-where">
      <h2 id="ex-where">Where these questions live</h2>
      <p className="dim">
        {(e.n_rows ?? 0).toLocaleString("en-US")} questions across {nTopics.toLocaleString("en-US")} {nTopics === 1 ? "topic" : "topics"} of the map
        {nTopics > topics.length ? `; the ${topics.length} biggest are shown` : ""}. Each opens on the map with every question in it.
      </p>
      <div className="ex-tree">
        {[...groups.entries()].map(([p, g]) => (
          <div className="ex-branch" key={p}>
            <a className="ex-parent" href={`/?node=${encodeURIComponent(p)}`}>{g.label}</a>
            <div className="ex-chips">
              {g.items.map((t) => (
                <a key={t.node} className="ex-chip" href={`/?node=${encodeURIComponent(t.node)}`}>
                  {t.label}<em>{t.n.toLocaleString("en-US")}</em>
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// Jev's take (docs/17 item 4): its own answers to questions about this experiment, asked after reading the result
// and the caveats, shown as answers
function Take({ e }: { e: Experiment }) {
  const answers = e.take?.answers ?? [];
  return (
    <section className="ex-take" aria-labelledby="ex-take">
      <h2 id="ex-take">Jev on this experiment</h2>
      <dl className="ex-answers">
        {answers.map((a, i) => (
          <div key={i}>
            <dt>{a.q}</dt>
            <dd>
              <b>{a.a.charAt(0).toUpperCase() + a.a.slice(1)}</b>
              {a.level !== undefined ? (
                <span className="meter" aria-label={`${a.level.toFixed(1)} on a 0 to 4 scale, from ${a.scale?.[0]} to ${a.scale?.[1]}`}>
                  {[0, 1, 2, 3, 4].map((k) => <i key={k} className={Math.round(a.level ?? 0) === k ? "on" : ""} />)}
                </span>
              ) : a.p !== null ? <em>{Math.round(a.p * 100)}%</em> : null}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

export default async function ExperimentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const data = await loadExperiments();
  const all = data?.experiments ?? [];
  const i = all.findIndex((x) => x.id === id);
  if (i < 0) notFound();
  const e = all[i];
  const s = sectionsOf(e);
  const caveats = e.case?.caveats ?? (e.limits ? [{ label: "Limits", text: e.limits }] : []);
  const prev = all[i - 1], next = all[i + 1];
  return (
    <main>
      <Nav here="atlas" />
      <section className="pt-field ex-page" data-f="sage">
        <p className="ex-crumb"><Link href="/portrait/atlas" prefetch={false}>Atlas</Link> › {e.family_label}</p>

        <header className={`ex-head${e.meme ? " with-meme" : ""}`}>
          <div>
            <span className="pt-tag">Case study {i + 1} of {all.length}</span>
            <h1>{e.title}</h1>
            <p className="ex-sub">{e.question}</p>
          </div>
        </header>

        <div className="ex-window">
          <div className="ex-wbar"><span>result</span><span>{(e.n_rows ?? 0).toLocaleString("en-US")} {e.n_rows === 1 ? "question" : "questions"}</span></div>
          <div className="ex-wbody">
            <p className="ex-result">{e.result}</p>
            <Chart chart={e.chart} />
            {e.case?.chart_note && <p className="ex-note"><b>How to read this:</b> {e.case.chart_note}</p>}
            <p className="ex-evidence">{[e.evidence, e.robustness].filter(Boolean).map((t) => String(t).trim().replace(/[.;]?$/, ".")).join(" ")}</p>
          </div>
        </div>

        {(e.case?.takeaways?.length ?? 0) > 0 && (
          <section className="ex-short" aria-labelledby="ex-short">
            <h2 id="ex-short">In short</h2>
            <ul>{e.case!.takeaways!.map((t, j) => <li key={j}>{t}</li>)}</ul>
          </section>
        )}

        <article className="ex-study">
          {(["found", "means"] as SectionKey[]).filter((k) => s[k]).map((k) => (
            <section key={k} className={`ex-sec s-${k}`}>
              <h2>{TITLE[k]}</h2>
              {/* the meme is a joke about the finding, so it sits beside it, the text wrapping round it; its width
                  follows the template's shape so wide and tall memes take up about the same room */}
              {k === "found" && e.meme && (
                <div className="ex-meme-slot" style={{ "--ar": (e.meme.w / e.meme.h).toFixed(3) } as React.CSSProperties}>
                  <ExMeme m={e.meme} />
                </div>
              )}
              <Md text={s[k] as string} />
            </section>
          ))}
        </article>

        <div className="ex-judge">
          {caveats.length > 0 && (
            <section className="ex-caveats" aria-labelledby="ex-cav">
              <h2 id="ex-cav">Caveats</h2>
              <ul>{caveats.map((c, j) => <li key={j}><b>{c.label}.</b> {c.text}</li>)}</ul>
            </section>
          )}
          <Take e={e} />
        </div>

        <article className="ex-study">
          {s.why && <section className="ex-sec s-why"><h2>{TITLE.why}</h2><Md text={s.why} /></section>}
          {(s.data || s.asked || s.measured) && (
            <section className="ex-sec s-how">
              <h2>How this was done</h2>
              {(["data", "asked", "measured"] as SectionKey[]).filter((k) => s[k]).map((k) => (
                <div key={k} className="ex-how"><h3>{TITLE[k]}</h3><Md text={s[k] as string} /></div>
              ))}
            </section>
          )}
        </article>

        <Topics e={e} />

        <section className="ex-rows-sec" aria-labelledby="ex-every">
          <h2 id="ex-every">Every question</h2>
          <p className="dim">All {(e.n_rows ?? 0).toLocaleString("en-US")} questions behind this result, the telling ones first: the examples the analysis points to, then the ones where Jev misses, biggest gap first.</p>
          <Rows id={e.id} total={e.n_rows ?? 0} flagged={e.n_flagged ?? { wrong: 0, differs: 0 }} />
        </section>

        <nav className="ex-pager" aria-label="More case studies">
          {prev ? <Link href={`/portrait/atlas/${prev.id}`} prefetch={false}>← {prev.title}</Link> : <span />}
          {next ? <Link href={`/portrait/atlas/${next.id}`} prefetch={false}>{next.title} →</Link> : <span />}
        </nav>
      </section>
    </main>
  );
}
