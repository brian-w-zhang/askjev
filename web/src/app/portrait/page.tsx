import Portrait from "@/components/portrait/Portrait";
import { loadPortrait } from "@/components/portrait/data";

// Built once per deploy (publish.py redeploys with the data), so the page comes from the CDN and a nav link can
// fetch it ahead. ?ids shows each card's id, to find its words in components/portrait/copy.ts (the pre-paint script
// in app/layout.tsx marks the page; portrait.css shows the ids).
export const dynamic = "force-static";

export default async function PortraitPage() {
  const d = await loadPortrait();
  if (!d) {
    return (
      <main style={{ padding: 32, fontFamily: "var(--mono)", fontSize: 13 }}>
        No portrait data. Run <code>uv run python scripts/portrait/export_page.py</code> to write data/analysis/portrait.json.
      </main>
    );
  }
  return <main><Portrait d={d} /></main>;
}
