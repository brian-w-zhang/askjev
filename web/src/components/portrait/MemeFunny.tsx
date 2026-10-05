// How funny Jev finds a meme (scripts/experiments/meme_funny.py): it can't see images, so it read the meme described in
// words and gave a probability to each of five levels. Shown as the small window stuck over the meme card's corner
// (typesafe.ai's "fun fact" note), with its pick; the full spread is in the label and the tooltip.
export type Funny = { dist: number[]; level: number; labels: string[] };

export default function MemeFunny({ f }: { f: Funny }) {
  const peak = Math.max(...f.dist);
  const top = f.dist.indexOf(peak);
  const spread = f.dist.map((p, k) => `${k + 1} ${f.labels[k].toLowerCase()}: ${Math.round(p * 100)}%`).join(", ");
  return (
    <div className="meme-funny" role="note" aria-label={`How funny Jev finds this meme: ${top + 1} of 5, ${f.labels[top].toLowerCase()} (${spread})`}
      title={`Jev can't see images, so it read this meme described in words. ${spread}`}>
      <span className="mf-bar">Jev&rsquo;s rating</span>
      <span className="mf-body"><b>{top + 1}/5</b> {f.labels[top].toLowerCase()}</span>
    </div>
  );
}
