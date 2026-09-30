import type { Metadata } from "next";
import Atlas from "@/components/portrait/Atlas";
import { TABS, type Tab } from "@/components/portrait/atlasTabs";
import { loadPortrait } from "@/components/portrait/data";
import { Nav } from "@/components/portrait/ui";
import { loadExperiments } from "@/components/experiments/data";
import type { Chart, ExperimentCard } from "@/components/experiments/types";
import { jevOf } from "@/components/experiments/labels";
import "@/components/experiments/experiments.css";

export const metadata: Metadata = { title: "Atlas · A self-portrait of Jev · askjev" };

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

export default async function AtlasPage({ searchParams }: { searchParams: Promise<{ tab?: string | string[] }> }) {
  const [d, x, sp] = await Promise.all([loadPortrait(), loadExperiments(), searchParams]);
  const want = typeof sp.tab === "string" ? sp.tab : "";
  const initial: Tab = (TABS as string[]).includes(want) ? (want as Tab) : "experiments";
  const cards: ExperimentCard[] = (x?.experiments ?? []).map((e) => ({
    id: e.id, family: e.family, family_label: e.family_label, title: e.title, result: e.result, n: e.n,
    new_questions: e.new_questions, n_rows: e.n_rows ?? 0, evaluation: e.evaluation, portrait_rank: e.portrait_rank ?? null, chart: thumb(e.chart), jev: jevOf(e),
    line: e.case?.takeaways?.[0] ?? e.result, // the first takeaway: one whole sentence, not a clipped paragraph
  }));
  const nQuestions = d ? (d.claims.landscape_families?.n ?? 0) - (d.claims.landscape_hidden?.n ?? 0) : 0;
  return (
    <main>
      <Nav here="atlas" />
      <section className="pt-field atlas-page" data-f="sage">
        {d || cards.length ? (
          <Atlas initial={initial} nNodes={d?.nodes.length ?? 0} nSources={d?.sources.length ?? 0} nQuestions={nQuestions}
            experiments={cards} coverage={x?.coverage ?? null} />
        ) : <p className="at-empty">No data. Run scripts/experiments/export.py and scripts/portrait/export_page.py.</p>}
      </section>
    </main>
  );
}
