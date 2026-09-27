import type { Metadata } from "next";
import Atlas from "@/components/portrait/Atlas";
import { loadPortrait } from "@/components/portrait/data";
import { Nav } from "@/components/portrait/ui";

export const metadata: Metadata = { title: "Atlas · A self-portrait of Jev · askjev" };

export default function AtlasPage() {
  const d = loadPortrait();
  const claims = d ? Object.values(d.claims).filter((c) => c.section !== "page") : [];
  return (
    <main>
      <Nav here="atlas" />
      <section className="pt-field" data-f="sage" style={{ minHeight: "100vh" }}>
        <header className="pt-open" style={{ paddingBottom: 40 }}>
          <i className="pt-crop tl" /><i className="pt-crop tr" /><i className="pt-crop bl" /><i className="pt-crop br" />
          <span className="pt-tag">Jev.Atlas</span>
          <h1 className="pt-h1 sm">Everything Else</h1>
          <p className="pt-dek">The portrait picks a few dozen findings. Here are all {claims.length} of them, what a human self-portrait would cover and how much of it this does, every topic&rsquo;s indicators, and every source.</p>
        </header>
        {d ? <Atlas claims={claims} nodes={d.nodes} sources={d.sources} />
          : <p style={{ textAlign: "center" }}>No portrait data. Run scripts/portrait/export_page.py.</p>}
      </section>
    </main>
  );
}
