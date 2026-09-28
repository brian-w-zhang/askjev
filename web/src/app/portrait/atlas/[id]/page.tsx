import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Nav } from "@/components/portrait/ui";
import Chart from "@/components/experiments/Chart";
import ExMeme from "@/components/experiments/ExMeme";
import Md from "@/components/experiments/Md";
import Rows from "@/components/experiments/Rows";
import { loadExperiments } from "@/components/experiments/data";
import { OUTCOME, VERDICT } from "@/components/experiments/labels";
import type { Experiment } from "@/components/experiments/types";
import "@/components/experiments/experiments.css";

// One experiment as a case study (docs/17): the result and its chart, the write-up, Jev's own take, the caveats,
// where its questions live on the map, and every question behind it.
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const e = (await loadExperiments())?.experiments.find((x) => x.id === id);
  return { title: e ? `${e.title} · Atlas · askjev` : "Case study · Atlas · askjev" };
}

type SectionKey = "why" | "data" | "asked" | "measured" | "found" | "means";
const SECTIONS: [SectionKey, string][] = [
  ["why", "Why ask this"], ["data", "The people and the data"], ["asked", "What Jev was asked"],
  ["measured", "How we measured it"], ["found", "What we found"], ["means", "What it means, and what it doesn't"],
];

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

function Take({ e, rank, of }: { e: Experiment; rank: number; of: number }) {
  const ev = e.evaluation;
  return (
    <aside className="ex-take" aria-labelledby="ex-take">
      <h2 id="ex-take">Jev&rsquo;s take</h2>
      {e.take ? <blockquote className="ex-takeq"><Md text={e.take.text} /></blockquote>
        : <p className="dim">Jev hasn&rsquo;t weighed in on this one yet.</p>}
      {e.take && e.take.answers.length > 0 && (
        <details className="ex-takea">
          <summary>what Jev actually answered</summary>
          <ul>{e.take.answers.map((a, i) => <li key={i}><span>{a.q}</span> <b>{a.a}</b>{a.p !== null ? <em> {Math.round(a.p * 100)}%</em> : null}</li>)}</ul>
        </details>
      )}
      {ev && (
        <dl className="ex-verdict-dl">
          <dt>its verdict</dt><dd><span className={`ex-verdict ${ev.outcome}`}>{OUTCOME[ev.outcome] ?? ev.outcome}</span>{ev.top ? ` · ${VERDICT[ev.top] ?? ev.top}` : ""}</dd>
          <dt>how interesting</dt><dd>{typeof ev.interest === "number" ? `${ev.interest.toFixed(1)} of 10` : "–"}</dd>
          <dt>rank</dt><dd>{rank} of {of}, from Jev&rsquo;s head-to-heads between experiments</dd>
        </dl>
      )}
    </aside>
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
          {e.meme && <div className="ex-meme"><ExMeme m={e.meme} /></div>}
        </header>

        <div className="ex-window">
          <div className="ex-wbar"><span>result</span><span>{e.n.toLocaleString("en-US")} {e.n === 1 ? "item" : "items"}</span></div>
          <div className="ex-wbody">
            <p className="ex-result">{e.result}</p>
            <Chart chart={e.chart} />
            {e.case?.chart_note && <p className="ex-note"><b>How to read this:</b> {e.case.chart_note}</p>}
            <p className="ex-evidence">{[e.evidence, e.robustness].filter(Boolean).map((t) => String(t).trim().replace(/[.;]?$/, ".")).join(" ")}</p>
          </div>
        </div>

        <div className="ex-cols">
          <article className="ex-study">
            {SECTIONS.filter(([k]) => s[k]).map(([k, t]) => (
              <section key={k} className={`ex-sec s-${k}`}>
                <h2>{t}</h2>
                <Md text={s[k] as string} />
              </section>
            ))}
          </article>
          <div className="ex-side">
            <Take e={e} rank={i + 1} of={all.length} />
            {caveats.length > 0 && (
              <aside className="ex-caveats" aria-labelledby="ex-cav">
                <h2 id="ex-cav">Caveats</h2>
                <ul>{caveats.map((c, j) => <li key={j}><b>{c.label}.</b> {c.text}</li>)}</ul>
              </aside>
            )}
          </div>
        </div>

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
