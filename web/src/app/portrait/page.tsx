import Portrait from "@/components/portrait/Portrait";
import { loadPortrait } from "@/components/portrait/data";

export default function PortraitPage() {
  const d = loadPortrait();
  if (!d) {
    return (
      <main style={{ padding: 32, fontFamily: "var(--mono)", fontSize: 13 }}>
        No portrait data. Run <code>uv run python scripts/portrait/export_page.py</code> to write data/analysis/portrait.json.
      </main>
    );
  }
  return <main><Portrait d={d} /></main>;
}
