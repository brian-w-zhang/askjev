/* eslint-disable @next/next/no-img-element -- local templates served by /portrait/memes, no optimizer needed */
import type { ReactNode } from "react";

// Meme templates (imgflip; files in data/portrait/memes, served by /portrait/memes/[file]) and where their labels go,
// in percent of the image. Reaction images get a caption above them, the way they're posted now; panel memes get
// outlined labels on the image.
type Label = { x: number; y: number; w: number; style?: "outline" | "ink" };
type Def = { file: string; w: number; h: number; labels?: Label[] };

export const MEMES = {
  chill: { file: "chill.png", w: 215, h: 234 },
  cinema: { file: "cinema.png", w: 936, h: 725 },
  gigachad: { file: "gigachad.jpg", w: 1068, h: 601 },
  monkey: { file: "monkey.jpg", w: 923, h: 768 },
  spiderman: { file: "spiderman.jpg", w: 800, h: 450, labels: [{ x: 27, y: 12, w: 42 }, { x: 74, y: 12, w: 44 }] },
  anakin: {
    file: "anakin.png", w: 768, h: 768,
    labels: [{ x: 25, y: 41, w: 46 }, { x: 75, y: 41, w: 46 }, { x: 25, y: 91, w: 46 }, { x: 75, y: 91, w: 46 }],
  },
  pooh: { file: "pooh.png", w: 800, h: 582, labels: [{ x: 74, y: 25, w: 48, style: "ink" }, { x: 74, y: 75, w: 48, style: "ink" }] },
  enjoyer: { file: "enjoyer.png", w: 480, h: 263, labels: [{ x: 25, y: 88, w: 46 }, { x: 75, y: 88, w: 46 }] },
  pigeon: { file: "pigeon.jpg", w: 1587, h: 1425, labels: [{ x: 30, y: 60, w: 36 }, { x: 80, y: 30, w: 34 }, { x: 50, y: 90, w: 80 }] },
} satisfies Record<string, Def>;

export type MemeName = keyof typeof MEMES;

export default function Meme({ name, caption, labels = [], size = "m", tilt = 0, alt }: {
  name: MemeName; caption?: ReactNode; labels?: ReactNode[]; size?: "s" | "m" | "l"; tilt?: number; alt: string;
}) {
  const d: Def = MEMES[name];
  return (
    <figure className={`meme ${size}`} style={tilt ? { transform: `rotate(${tilt}deg)` } : undefined}>
      <div className="pt-bar"><span>{name}.{d.file.split(".")[1]}</span><span className="sp" /><span className="dots" aria-hidden>▪▪▪</span></div>
      {caption && <figcaption className="cap">{caption}</figcaption>}
      <div className="img" style={{ aspectRatio: `${d.w} / ${d.h}` }}>
        <img src={`/portrait/memes/${d.file}`} alt={alt} />
        {(d.labels ?? []).map((l, i) => labels[i] ? (
          <span key={i} className={`lab lab-${l.style ?? "outline"}`} style={{ left: `${l.x}%`, top: `${l.y}%`, width: `${l.w}%` }}>{labels[i]}</span>
        ) : null)}
      </div>
    </figure>
  );
}
