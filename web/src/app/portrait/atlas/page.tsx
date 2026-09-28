import type { Metadata } from "next";
import Link from "next/link";
import Atlas from "@/components/portrait/Atlas";
import { loadPortrait } from "@/components/portrait/data";
import { Nav } from "@/components/portrait/ui";
import { loadExperiments } from "@/components/experiments/data";
import type { Chart, ExperimentCard } from "@/components/experiments/types";
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
    new_questions: e.new_questions, evaluation: e.evaluation, portrait_rank: e.portrait_rank ?? null, chart: thumb(e.chart),
  }));
  return (
    <main>
      <Nav here="atlas" />
      <section className="pt-field atlas-page" data-f="sage">
        <header className="at-head">
          <span className="pt-tag">Jev.Atlas</span>
          <h1>Experiments</h1>
          <p>
            Each experiment gathers many of Jev&rsquo;s answers into one thing you can learn about it in a minute, compared with
            real people or a right answer where one exists. The <Link href="/portrait" prefetch={false}>portrait</Link> picks a
            few; here are all {cards.length}, ranked by Jev&rsquo;s own verdict on them. Indicators, not a benchmark.
          </p>
        </header>
        {d || cards.length ? <Atlas claims={claims} nNodes={d?.nodes.length ?? 0} nSources={d?.sources.length ?? 0} experiments={cards} />
          : <p className="at-empty">No data. Run scripts/experiments/export.py and scripts/portrait/export_page.py.</p>}
      </section>
    </main>
  );
}
