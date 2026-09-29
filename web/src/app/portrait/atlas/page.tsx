import type { Metadata } from "next";
import Link from "next/link";
import Atlas from "@/components/portrait/Atlas";
import { loadPortrait } from "@/components/portrait/data";
import { Nav } from "@/components/portrait/ui";
import { loadExperiments } from "@/components/experiments/data";
import type { Chart, ExperimentCard } from "@/components/experiments/types";
import { jevOf } from "@/components/experiments/labels";
import "@/components/experiments/experiments.css";

export const metadata: Metadata = { title: "Atlas · A self-portrait of Jev · askjev" };

// "self.lifestyle: frame gap..." reads better as "Lifestyle & Taste: frame gap...": swap topic ids for their names
const TOPIC = /\b(?:world|self|machine)(?:\.[a-z0-9_]+)+/g;

// A thumbnail needs a few rows or a few hundred points, not the whole chart: trim before it reaches the browser.
function thumb(c: Chart): Chart {
  const t: Chart = { ...c };
  for (const k of ["rows", "items", "labels", "a", "b", "cells", "ranked", "best", "values"]) {
    if (Array.isArray(t[k])) t[k] = (t[k] as unknown[]).slice(0, k === "cells" ? 60 : 8);
  }
  if (Array.isArray(t.points)) {
    const p = t.points as unknown[];
    t.points = p.filter((_, i) => i % Math.ceil(p.length / 300) === 0);
  }
  for (const k of ["bottom", "strip", "dots", "decide", "labels_all"]) delete t[k];
  return t;
}

export default async function AtlasPage() {
  const [d, x] = await Promise.all([loadPortrait(), loadExperiments()]);
  const labels = new Map((d?.nodes ?? []).map((n) => [n.node_id, n.label as string | null]));
  // the reference tab lists the old claims; it doesn't need their chart data, so only the fields it shows are sent
  const claims = d ? Object.values(d.claims).filter((c) => c.section !== "page")
    .map(({ id, section, sentence, tier, n, ci90, effect, script }) => ({
      id, section, tier, n, ci90, effect: typeof effect === "number" ? effect : null, examples: [], script,
      sentence: String(sentence).replace(TOPIC, (m) => labels.get(m) ?? m),
    })) : [];
  const cards: ExperimentCard[] = (x?.experiments ?? []).map((e) => ({
    id: e.id, family: e.family, family_label: e.family_label, title: e.title, result: e.result, n: e.n,
    new_questions: e.new_questions, n_rows: e.n_rows ?? 0, evaluation: e.evaluation, portrait_rank: e.portrait_rank ?? null, chart: thumb(e.chart), jev: jevOf(e),
    line: e.case?.takeaways?.[0] ?? e.result, // the first takeaway: one whole sentence, not a clipped paragraph
  }));
  return (
    <main>
      <Nav here="atlas" />
      <section className="pt-field atlas-page" data-f="sage">
        <header className="at-head">
          <span className="pt-tag">Jev.Atlas</span>
          <h1>Experiments</h1>
          <dl className="at-stats">
            <div><dt>experiments</dt><dd>{cards.length}</dd></div>
            <div><dt>families</dt><dd>{new Set(cards.map((c) => c.family)).size}</dd></div>
            {d && <div><dt>questions on the map</dt><dd>{((d.claims.landscape_families?.n ?? 0) - (d.claims.landscape_hidden?.n ?? 0)).toLocaleString("en-US")}</dd></div>}
          </dl>
          <p>
            Each experiment gathers many of Jev&rsquo;s answers into one thing you can learn about it in a minute, compared with
            real people or a right answer where one exists. The <Link href="/portrait" prefetch={false}>portrait</Link> picks a
            few; here are all {cards.length}, ranked by Jev: it read the case studies two at a time and picked the one that teaches a curious reader more, and that order is adjusted by how much it would rely on each result and how fair it finds the comparison. Indicators, not a benchmark.
          </p>
        </header>
        {d || cards.length ? <Atlas claims={claims} nNodes={d?.nodes.length ?? 0} nSources={d?.sources.length ?? 0} experiments={cards} />
          : <p className="at-empty">No data. Run scripts/experiments/export.py and scripts/portrait/export_page.py.</p>}
      </section>
    </main>
  );
}
