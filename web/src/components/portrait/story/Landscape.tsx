"use client";

import { useMemo, useState } from "react";
import type { Methods, Source } from "./types";

// The data landscape as a treemap: every source a tile sized by its questions, grouped by family. Hover or tap a tile
// to read what the source is; pick a family to zoom into it.

type Rect = { x: number; y: number; w: number; h: number };
type Tile<T> = Rect & { item: T };

// squarified treemap (Bruls, Huizing, van Wijk): lay items out in rows that keep tiles close to square
function squarify<T>(items: T[], value: (t: T) => number, box: Rect): Tile<T>[] {
  const total = items.reduce((a, t) => a + value(t), 0) || 1;
  const scale = (box.w * box.h) / total;
  const queue = [...items].sort((a, b) => value(b) - value(a)).map((item) => ({ item, a: value(item) * scale }));
  const out: Tile<T>[] = [];
  let r = { ...box };
  const worst = (row: { a: number }[], side: number) => {
    const s = row.reduce((x, t) => x + t.a, 0);
    const mx = Math.max(...row.map((t) => t.a)), mn = Math.min(...row.map((t) => t.a));
    return Math.max((side * side * mx) / (s * s), (s * s) / (side * side * mn));
  };
  while (queue.length) {
    const side = Math.min(r.w, r.h);
    const row = [queue.shift()!];
    while (queue.length && worst([...row, queue[0]], side) <= worst(row, side)) row.push(queue.shift()!);
    const s = row.reduce((x, t) => x + t.a, 0);
    if (r.w >= r.h) {
      const w = s / r.h;
      let y = r.y;
      for (const t of row) { const h = t.a / w; out.push({ x: r.x, y, w, h, item: t.item }); y += h; }
      r = { x: r.x + w, y: r.y, w: r.w - w, h: r.h };
    } else {
      const h = s / r.w;
      let x = r.x;
      for (const t of row) { const w = t.a / h; out.push({ x, y: r.y, w, h, item: t.item }); x += w; }
      r = { x: r.x, y: r.y + h, w: r.w, h: r.h - h };
    }
  }
  return out;
}

// the portrait's field colors, one per family (the treemap's only color, so each family reads as a block)
const COLORS = ["#e68ba2", "#56ada3", "#abbab9", "#c462b0", "#f3b3c3", "#8fd3c7", "#d5dcdb", "#e2a3d6", "#f7d4dd", "#b9e3dc", "#9aa7a6"];
const pc = (v: number) => `${Math.round(v * 100)}%`;
const n0 = (v: number) => v.toLocaleString("en-US");
const name = (s: string) => s.replace(/_/g, " ");

export default function Landscape({ m }: { m: Methods }) {
  const [focus, setFocus] = useState<string | null>(null);
  const [hover, setHover] = useState<{ src: Source; fam: string } | null>(null);
  const color = useMemo(() => Object.fromEntries(m.families.map((f, i) => [f.family, COLORS[i % COLORS.length]])), [m.families]);
  const W = 1000, H = 560;
  const tiles = useMemo(() => {
    const fams = focus ? m.families.filter((f) => f.family === focus) : m.families;
    const outer = squarify(fams, (f) => f.n, { x: 0, y: 0, w: W, h: H });
    return outer.flatMap((ft) => {
      const pad = focus ? 0 : 3;
      const inner = squarify(ft.item.sources, (s) => s.n, { x: ft.x + pad, y: ft.y + pad + (focus ? 0 : 18), w: ft.w - 2 * pad, h: ft.h - 2 * pad - (focus ? 0 : 18) });
      return [{ kind: "fam" as const, ...ft }, ...inner.map((t) => ({ kind: "src" as const, fam: ft.item.family, ...t }))];
    });
  }, [focus, m.families]);
  const sel = hover ?? (focus ? { src: m.families.find((f) => f.family === focus)!.sources[0], fam: focus } : null);
  const fam = focus ? m.families.find((f) => f.family === focus) : null;
  return (
    <div className="ls">
      <div className="ls-top">
        {focus ? <button type="button" className="ls-back" onClick={() => { setFocus(null); setHover(null); }}>← all families</button>
          : <span className="ls-hint">{m.families.length} families · {m.families.reduce((a, f) => a + f.sources.length, 0)} sources · tap a family to zoom</span>}
        {fam && <span className="ls-fam"><i style={{ background: color[fam.family] }} />{fam.family} · {n0(fam.n)} questions · {fam.sources.length} sources</span>}
      </div>
      <div className="ls-map" style={{ aspectRatio: `${W} / ${H}` }} onMouseLeave={() => setHover(null)}>
        {tiles.map((t, i) => {
          const style = { left: `${(t.x / W) * 100}%`, top: `${(t.y / H) * 100}%`, width: `${(t.w / W) * 100}%`, height: `${(t.h / H) * 100}%` };
          if (t.kind === "fam") {
            if (focus) return null;
            return (
              <button key={`f${i}`} type="button" className="ls-f" style={{ ...style, background: color[t.item.family] }}
                onClick={() => setFocus(t.item.family)} aria-label={`${t.item.family}: ${n0(t.item.n)} questions. Zoom in`}>
                {t.w > 70 && <span>{t.item.family} <em>{n0(t.item.n)}</em></span>}
              </button>
            );
          }
          const s = t.item as Source;
          const on = hover?.src.source === s.source;
          const big = (t.w / W) * 1000 > (focus ? 70 : 90) && (t.h / H) * 560 > 26;
          return (
            <div key={`s${i}`} className={`ls-s${on ? " on" : ""}`} style={{ ...style, background: color[t.fam] }} tabIndex={0}
              onMouseEnter={() => setHover({ src: s, fam: t.fam })} onFocus={() => setHover({ src: s, fam: t.fam })}
              onClick={(e) => { e.stopPropagation(); if (!focus) setFocus(t.fam); setHover({ src: s, fam: t.fam }); }}>
              {big && <span>{name(s.source)}<em>{n0(s.n)}</em></span>}
            </div>
          );
        })}
      </div>
      <div className="ls-info" aria-live="polite">
        {sel ? (
          <>
            <p className="ls-k"><i style={{ background: color[sel.fam] }} />{sel.fam}</p>
            <p className="ls-n"><b>{name(sel.src.source)}</b> · {n0(sel.src.n)} questions</p>
            {sel.src.line && <p className="ls-l">{sel.src.line}</p>}
            <p className="ls-meta">
              {sel.src.truth > 0 && <span>{pc(sel.src.truth)} have a right answer</span>}
              {sel.src.humans > 0 && <span>{pc(sel.src.humans)} have real people&rsquo;s answers</span>}
              {sel.src.license && <span>license: {sel.src.license}</span>}
            </p>
          </>
        ) : (
          <p className="ls-l">Hover or tap a tile to see where its questions came from.</p>
        )}
        {fam && <p className="ls-what">{fam.what}</p>}
      </div>
      {!focus && (
        <ul className="ls-key">
          {m.families.map((f) => (
            <li key={f.family}>
              <button type="button" onClick={() => setFocus(f.family)}>
                <i style={{ background: color[f.family] }} /><b>{f.family}</b> <em>{n0(f.n)}</em>
                <span>{f.what}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
