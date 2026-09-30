"use client";

import { useMemo, useRef, useState } from "react";
import type { Methods, Source } from "./types";

// The data landscape as a treemap: every source a tile sized by its questions, grouped by family. Color by family, or
// by how much of each source has a right answer or real people's answers. A tooltip follows the pointer; on touch a
// tap shows the source below the map. Picking a family zooms into it (tiles glide to their new place).

type Rect = { x: number; y: number; w: number; h: number };
type Tile<T> = Rect & { item: T };

// squarified treemap (Bruls, Huizing, van Wijk): rows that keep tiles close to square
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

// one clear hue per family, kept soft enough to carry dark labels
const FAMILY_COLOR: Record<string, string> = {
  "machine task datasets": "#8fb3d9", "authored banks": "#e6a57e", "crowd judgments": "#9fcf9a", "knowledge & exams": "#d9b45f",
  "real asked questions": "#c7a3d9", "polls & surveys": "#e68ba2", "taste pairs & ratings": "#7fcbc0", "instruments & norms": "#b8b0a0",
  "internet culture": "#f0d27a", "experiment designs": "#a3a9e0", "records & statistics": "#d49a9a",
};
type Mode = "family" | "truth" | "humans";
const MODES: [Mode, string][] = [["family", "family"], ["truth", "has a right answer"], ["humans", "has real people’s answers"]];
// a single-hue ramp for the shares: pale (none) to Jev magenta (all)
const ramp = (v: number) => `color-mix(in oklab, #d0419f ${Math.round(12 + v * 80)}%, #f4eef2)`;
const pc = (v: number) => `${Math.round(v * 100)}%`;
const n0 = (v: number) => v.toLocaleString("en-US");
const name = (s: string) => s.replace(/_/g, " ");

export default function Landscape({ m }: { m: Methods }) {
  const [focus, setFocus] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("family");
  const [hover, setHover] = useState<{ src: Source; fam: string; x: number; y: number; w: number } | null>(null);
  const [picked, setPicked] = useState<{ src: Source; fam: string } | null>(null);
  const box = useRef<HTMLDivElement>(null);
  const W = 1000, H = 600, HEAD = 22;
  const tiles = useMemo(() => {
    const fams = focus ? m.families.filter((f) => f.family === focus) : m.families;
    const outer = squarify(fams, (f) => f.n, { x: 0, y: 0, w: W, h: H });
    const out: ({ kind: "fam"; key: string } & Tile<Methods["families"][number]> | { kind: "src"; key: string; fam: string } & Tile<Source>)[] = [];
    for (const ft of outer) {
      const head = !focus && ft.h > 60 && ft.w > 80 ? HEAD : 0;
      out.push({ kind: "fam", key: `f:${ft.item.family}`, ...ft });
      for (const t of squarify(ft.item.sources, (s) => s.n, { x: ft.x + 2, y: ft.y + 2 + head, w: ft.w - 4, h: ft.h - 4 - head }))
        out.push({ kind: "src", key: `s:${ft.item.family}:${t.item.source}`, fam: ft.item.family, ...t });
    }
    return out;
  }, [focus, m.families]);
  const fill = (s: Source, fam: string) => (mode === "family" ? FAMILY_COLOR[fam] ?? "#bbb" : ramp(mode === "truth" ? s.truth : s.humans));
  const pos = (e: React.PointerEvent) => {
    const r = box.current!.getBoundingClientRect();
    return { x: e.clientX - r.left, y: e.clientY - r.top, w: r.width };
  };
  const fam = focus ? m.families.find((f) => f.family === focus) : null;
  const info = picked ?? null;
  return (
    <div className="ls">
      <div className="ls-top">
        <div className="ls-crumb">
          <button type="button" onClick={() => { setFocus(null); setPicked(null); }} disabled={!focus}>all {m.families.length} families</button>
          {fam && <><span aria-hidden>›</span><b>{fam.family}</b><em>{n0(fam.n)} questions · {fam.sources.length} sources</em></>}
        </div>
        <div className="ls-mode" role="radiogroup" aria-label="Color by">
          <span>color by</span>
          {MODES.map(([k, l]) => <button key={k} type="button" role="radio" aria-checked={mode === k} onClick={() => setMode(k)}>{l}</button>)}
        </div>
      </div>
      <div className="ls-map" ref={box} style={{ aspectRatio: `${W} / ${H}` }} onPointerLeave={() => setHover(null)}>
        {tiles.map((t) => {
          const style = { left: `${(t.x / W) * 100}%`, top: `${(t.y / H) * 100}%`, width: `${(t.w / W) * 100}%`, height: `${(t.h / H) * 100}%` };
          if (t.kind === "fam") {
            const col = FAMILY_COLOR[t.item.family] ?? "#bbb";
            return (
              <div key={t.key} className="ls-f" style={{ ...style, ["--fc" as string]: col }}>
                {!focus && t.h > 60 && t.w > 80 && (
                  <button type="button" className="ls-fh" onClick={() => { setFocus(t.item.family); setPicked(null); }}>
                    {t.item.family} <em>{n0(t.item.n)}</em>
                  </button>
                )}
              </div>
            );
          }
          const s = t.item;
          const on = hover?.src.source === s.source || picked?.src.source === s.source;
          const label = (t.w / W) * 1000 > (focus ? 60 : 88) && (t.h / H) * 600 > 30;
          return (
            <button key={t.key} type="button" className={`ls-s${on ? " on" : ""}`} style={{ ...style, background: fill(s, t.fam) }}
              aria-label={`${name(s.source)}: ${n0(s.n)} questions`}
              onPointerMove={(e) => { if (e.pointerType === "mouse") { const p = pos(e); setHover({ src: s, fam: t.fam, x: p.x, y: p.y, w: p.w }); } }}
              onClick={() => { if (!focus) setFocus(t.fam); setPicked({ src: s, fam: t.fam }); }}>
              {label && <span>{name(s.source)}<em>{n0(s.n)}</em></span>}
            </button>
          );
        })}
        {hover && (() => {
          const w = hover.w;
          const left = hover.x + 16 + 280 > w ? hover.x - 16 - 280 : hover.x + 16;
          return (
            <div className="ls-tip" style={{ left: Math.max(4, left), top: Math.max(4, hover.y - 12) }} role="tooltip">
              <p className="ls-k"><i style={{ background: FAMILY_COLOR[hover.fam] }} />{hover.fam}</p>
              <p className="ls-n"><b>{name(hover.src.source)}</b> {n0(hover.src.n)} questions</p>
              {hover.src.line && <p className="ls-l">{hover.src.line}</p>}
              <p className="ls-meta">{pc(hover.src.truth)} with a right answer · {pc(hover.src.humans)} with people&rsquo;s answers</p>
            </div>
          );
        })()}
      </div>
      {mode !== "family" && (
        <div className="ls-ramp"><span>none</span><i style={{ background: `linear-gradient(90deg, ${ramp(0)}, ${ramp(1)})` }} /><span>all of its questions</span></div>
      )}
      {info && (
        <div className="ls-info" aria-live="polite">
          <p className="ls-k"><i style={{ background: FAMILY_COLOR[info.fam] }} />{info.fam}</p>
          <p className="ls-n"><b>{name(info.src.source)}</b> {n0(info.src.n)} questions</p>
          {info.src.line && <p className="ls-l">{info.src.line}</p>}
          <p className="ls-meta">{pc(info.src.truth)} with a right answer · {pc(info.src.humans)} with people&rsquo;s answers{info.src.license ? ` · ${info.src.license}` : ""}</p>
        </div>
      )}
      {!focus ? (
        <ul className="ls-key">
          {m.families.map((f) => (
            <li key={f.family}>
              <button type="button" onClick={() => setFocus(f.family)}>
                <i style={{ background: FAMILY_COLOR[f.family] }} /><b>{f.family}</b> <em>{n0(f.n)}</em>
                <span>{f.what}</span>
              </button>
            </li>
          ))}
        </ul>
      ) : <p className="ls-what">{fam?.what}</p>}
    </div>
  );
}
