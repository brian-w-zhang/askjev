import type { Metadata } from "next";
import Link from "next/link";
import Atlas from "@/components/portrait/Atlas";
import { loadPortrait } from "@/components/portrait/data";
import { Nav } from "@/components/portrait/ui";

export const metadata: Metadata = { title: "Atlas · A self-portrait of Jev · askjev" };

// "self.lifestyle: frame gap..." reads better as "Lifestyle & Taste: frame gap...": swap topic ids for their names
const TOPIC = /\b(?:world|self|machine)(?:\.[a-z0-9_]+)+/g;

export default async function AtlasPage() {
  const d = await loadPortrait();
  const labels = new Map((d?.nodes ?? []).map((n) => [n.node_id, n.label as string | null]));
  // the atlas lists claims; it doesn't need their chart data, so only the fields it shows are sent to the browser
  const claims = d ? Object.values(d.claims).filter((c) => c.section !== "page")
    .map(({ id, section, sentence, tier, n, ci90, effect, script }) => ({
      id, section, tier, n, ci90, effect: typeof effect === "number" ? effect : null, examples: [], script,
      sentence: String(sentence).replace(TOPIC, (m) => labels.get(m) ?? m),
    })) : [];
  return (
    <main>
      <Nav here="atlas" />
      <section className="pt-field atlas-page" data-f="sage">
        <header className="at-head">
          <span className="pt-tag">Jev.Atlas</span>
          <h1>Everything else</h1>
          <p>The <Link href="/portrait" prefetch={false}>portrait</Link> picks a few dozen findings. Here are all {claims.length}, what a human self-portrait would cover and how much of that this does, every topic&rsquo;s numbers, and every source.</p>
        </header>
        {d ? <Atlas claims={claims} nNodes={d.nodes.length} nSources={d.sources.length} />
          : <p className="at-empty">No portrait data. Run scripts/portrait/export_page.py.</p>}
      </section>
    </main>
  );
}
