import Portrait from "@/components/portrait/Portrait";
import { loadPortrait } from "@/components/portrait/data";

// ?ids shows each card's id, to find its words in components/portrait/copy.ts
export default async function PortraitPage({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const d = loadPortrait();
  const showIds = (await searchParams).ids !== undefined;
  if (!d) {
    return (
      <main style={{ padding: 32, fontFamily: "var(--mono)", fontSize: 13 }}>
        No portrait data. Run <code>uv run python scripts/portrait/export_page.py</code> to write data/analysis/portrait.json.
      </main>
    );
  }
  return <main><Portrait d={d} showIds={showIds} /></main>;
}
