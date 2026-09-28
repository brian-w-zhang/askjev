// How funny Jev finds a meme (scripts/experiments/meme_funny.py): it can't see images, so it read the meme described in
// words and gave a probability to each of five levels. Its pick is in pink.
export type Funny = { dist: number[]; level: number; labels: string[] };

export default function MemeFunny({ f }: { f: Funny }) {
  const peak = Math.max(...f.dist);
  const top = f.dist.indexOf(peak);
  return (
    <div className="meme-funny" title="Jev can't see images, so it read this meme described in words">
      <span className="q">How funny is this meme? <b>Jev: {top + 1}/5, {f.labels[top].toLowerCase()}</b></span>
      <span className="opts" role="img" aria-label={f.dist.map((p, k) => `${k + 1}, ${f.labels[k]}: ${Math.round(p * 100)}%`).join("; ")}>
        {f.dist.map((p, k) => (
          <span key={k} className={k === top ? "on" : ""}>
            <i style={{ height: `${Math.max(2, (p / (peak || 1)) * 100)}%` }} />
            <em>{k + 1}</em>
            <small>{Math.round(p * 100)}%</small>
          </span>
        ))}
      </span>
    </div>
  );
}
