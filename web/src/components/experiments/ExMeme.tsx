/* eslint-disable @next/next/no-img-element -- private templates served by /portrait/memes, no optimizer needed */
import MemeFunny from "@/components/portrait/MemeFunny";
import type { ExperimentMeme } from "./types";

// An experiment's meme (docs/17 item 8): a template with our words set on it in HTML, so the text stays sharp in both
// themes. Reaction formats carry a caption above the image instead of labels. It's dressed as one of typesafe.ai's team
// cards: a black pixel title bar naming where it sits, the picture in a grey frame, and Jev's funniness rating as the
// "fun fact" window stuck over the corner.
export default function ExMeme({ m, where = "meme" }: { m: ExperimentMeme; where?: string }) {
  return (
    <figure className="ex-memefig">
      <div className="ex-wbar"><span>{where} · meme</span></div>
      {m.caption && <figcaption className="cap">{m.caption}</figcaption>}
      <div className="img" style={{ aspectRatio: `${m.w} / ${m.h}` }}>
        <img src={`/portrait/memes/${m.file}`} alt={m.alt} loading="lazy" draggable={false} />
        {m.boxes.map((b, i) => m.texts[i] ? (
          <span key={i} className={`lab lab-${b.style ?? "outline"}${b.case === "keep" ? " keep-case" : ""}${b.y < 25 ? " at-top" : b.y > 75 ? " at-bottom" : ""}`}
            style={{ left: `${b.x}%`, width: `${b.w}%`, ...(b.size ? { "--s": b.size } : {}),
              // near an edge the text grows away from it, so extra lines never fall off the picture
              ...(b.y < 25 ? { top: `${Math.max(1.5, b.y - 7)}%` } : b.y > 75 ? { bottom: `${Math.max(1.5, 93 - b.y)}%` } : { top: `${b.y}%` }),
            } as React.CSSProperties}>{m.texts[i]}</span>
        ) : null)}
      </div>
      {m.funny && <MemeFunny f={m.funny} />}
    </figure>
  );
}
