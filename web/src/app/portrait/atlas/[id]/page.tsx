import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Nav } from "@/components/portrait/ui";
import { QuestionRow } from "@/components/portrait/rows";
import Chart from "@/components/experiments/Chart";
import { loadExperiments } from "@/components/experiments/data";
import { OUTCOME, VERDICT } from "@/components/experiments/labels";
import "@/components/experiments/experiments.css";

// One experiment's page (docs/16 pass 4): the six steps in order, the result and its chart first, then how it was
// made, Jev's verdict on it, the fine print, real rows, and links to where its questions sit on the map.
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const e = (await loadExperiments())?.experiments.find((x) => x.id === id);
  return { title: e ? `${e.title} · Atlas · askjev` : "Experiment · Atlas · askjev" };
}

export default async function ExperimentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const data = await loadExperiments();
  const all = data?.experiments ?? [];
  const i = all.findIndex((x) => x.id === id);
  if (i < 0) notFound();
  const e = all[i];
  const ev = e.evaluation;
  const nodes = [...new Map(e.sources.flatMap((s) => s.nodes).map((n) => [n.node, n])).values()].slice(0, 8);
  const prev = all[i - 1], next = all[i + 1];
  return (
    <main>
      <Nav here="atlas" />
      <section className="pt-field ex-page" data-f="sage">
        <p className="ex-crumb"><Link href="/portrait/atlas" prefetch={false}>Atlas</Link> › {e.family_label} › <code>{e.id}</code></p>
        <header className="ex-head">
          <span className="pt-tag">Experiment #{i + 1} of {all.length}</span>
          <h1>{e.title}</h1>
          <p className="ex-q">{e.question}</p>
        </header>

        <div className="ex-window">
          <div className="ex-wbar"><span>result</span><span>{e.n.toLocaleString("en-US")} {e.n === 1 ? "item" : "items"}</span></div>
          <div className="ex-wbody">
            <p className="ex-result">{e.result}</p>
            <Chart chart={e.chart} />
            <p className="ex-evidence">{e.evidence}</p>
            {e.robustness && <p className="ex-evidence"><b>Robustness.</b> {e.robustness}</p>}
          </div>
        </div>

        <div className="ex-cols">
          <article className="ex-steps">
            <h2>1. Question</h2>
            <p>{e.question}</p>
            <p className="dim">{e.why}</p>
            <h2>2. Sourcing and coverage</h2>
            <p>{e.sourcing}</p>
            {e.sources.length > 0 && (
              <ul className="ex-sources">
                {e.sources.map((s) => (
                  <li key={s.name}><code>{s.name}</code> · {s.shown.toLocaleString("en-US")} shown questions</li>
                ))}
              </ul>
            )}
            <h2>3. Questions asked</h2>
            <p>{e.collection}{e.new_questions ? ` (${e.new_questions.toLocaleString("en-US")} new questions for this experiment.)` : ""}</p>
            <h2>4. Scoring</h2>
            <p>{e.scoring}</p>
            <h2>5. Chart</h2>
            <p>{e.chart_desc}</p>
            <h2>Compared with</h2>
            <p>{e.compared_with}</p>
          </article>

          <aside className="ex-side">
            <div className="ex-verdictbox">
              <h2>6. Jev&rsquo;s verdict</h2>
              {ev ? (
                <>
                  <p className="ex-big2"><span className={`ex-verdict ${ev.outcome}`}>{OUTCOME[ev.outcome] ?? ev.outcome}</span></p>
                  <dl>
                    <dt>its own label</dt><dd>{ev.top ? VERDICT[ev.top] ?? ev.top : "–"}</dd>
                    <dt>interest</dt><dd>{typeof ev.interest === "number" ? `${ev.interest.toFixed(1)} / 10` : "–"}</dd>
                    <dt>head-to-head strength</dt><dd>{typeof ev.strength === "number" ? ev.strength.toFixed(2) : "–"}</dd>
                    <dt>rank</dt><dd>{i + 1} of {all.length}</dd>
                  </dl>
                  <p className="dim">Jev judged this card against every other experiment and a gold set (docs/experiments/evaluator.md). Its word labels run bolder than its numbers; the head-to-heads decide.</p>
                </>
              ) : <p className="dim">Not evaluated yet.</p>}
            </div>
            {e.limits && (
              <div className="ex-fine">
                <h2>Fine print</h2>
                <p>{e.limits}</p>
              </div>
            )}
            {nodes.length > 0 && (
              <div className="ex-fine">
                <h2>On the map</h2>
                <ul className="ex-nodes">
                  {nodes.map((n) => (
                    <li key={n.node}><a href={`/?node=${encodeURIComponent(n.node)}`}>{n.label ?? n.node.split(".").slice(-1)[0].replaceAll("_", " ")}</a> <span className="dim">{n.n.toLocaleString("en-US")}</span></li>
                  ))}
                </ul>
              </div>
            )}
          </aside>
        </div>

        {e.rows.length > 0 && (
          <div className="ex-rows">
            <h2>Real rows</h2>
            <p className="dim">Questions behind the result, each with Jev&rsquo;s answer next to the people&rsquo;s (or Jev&rsquo;s guess for &lsquo;most people&rsquo;). Picked by the experiment&rsquo;s script, not by hand unless it says so.</p>
            <ol className="rc-rows">{e.rows.map((r) => <QuestionRow key={r.id} row={r} />)}</ol>
          </div>
        )}

        <nav className="ex-pager" aria-label="More experiments">
          {prev ? <Link href={`/portrait/atlas/${prev.id}`} prefetch={false}>← {prev.title}</Link> : <span />}
          {next ? <Link href={`/portrait/atlas/${next.id}`} prefetch={false}>{next.title} →</Link> : <span />}
        </nav>
      </section>
    </main>
  );
}
