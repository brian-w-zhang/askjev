"use client";
// Sky overlay (docs/07-ui.md, Look): labels and hover cards are HTML rendered by <SkyOverlay> next to the
// canvas, so the dither pass never touches text. React owns the elements, their text and classes
// (re-rendered only when a label slot is reassigned); the 3D frame loop only moves them, through refs.
import { create } from "zustand";

export const NODE_LABELS = 60;
export const STAR_LABELS = 24;

export interface Slot<K> { el: HTMLDivElement | null; key: K | null; o: number; want: boolean }
export interface LabelView { text: string; cls: string }

const slots = <K,>(n: number): Slot<K>[] => Array.from({ length: n }, () => ({ el: null, key: null, o: 0, want: false }));

/** Filled by <SkyOverlay> refs, moved by the scene every frame. */
export const nodeSlots = slots<string>(NODE_LABELS);
export const starSlots = slots<number>(STAR_LABELS);
export const cards = { star: null as HTMLDivElement | null, node: null as HTMLDivElement | null };

const EMPTY: LabelView = { text: "", cls: "" };
export const useOverlay = create<{ nodes: LabelView[]; stars: LabelView[] }>(() => ({
  nodes: Array(NODE_LABELS).fill(EMPTY),
  stars: Array(STAR_LABELS).fill(EMPTY),
}));

/** Hand the overlay new label text/classes; a no-op (no React render) when nothing changed. */
export function publish(which: "nodes" | "stars", views: LabelView[]) {
  const cur = useOverlay.getState()[which];
  if (views.every((v, i) => v.text === cur[i].text && v.cls === cur[i].cls)) return;
  useOverlay.setState({ [which]: views });
}

/** Keep slots whose key is still wanted; hand faded-out slots to new keys. */
export function assign<K>(pool: Slot<K>[], wanted: K[]) {
  const want = new Set(wanted);
  for (const s of pool) s.want = s.key !== null && want.has(s.key);
  for (const s of pool) if (s.want) want.delete(s.key!);
  const fresh = [...want];
  for (const s of pool) {
    if (s.want || s.o > 0.05 || !fresh.length) continue;
    s.key = fresh.shift()!;
    s.want = true;
  }
}

/** Fade toward wanted/unwanted and put the label's bottom-center at (x, y); x = null hides it. */
export function place<K>(s: Slot<K>, x: number | null, y: number, k: number) {
  const el = s.el;
  s.o += ((s.want && x !== null ? 1 : 0) - s.o) * k;
  if (s.o < 0.02 && !s.want) s.key = null;
  if (!el) return;
  if (s.o < 0.02 || x === null) {
    if (el.style.opacity !== "0") el.style.opacity = "0";
    return;
  }
  el.style.opacity = s.o.toFixed(3);
  el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(-50%, -100%)`;
}

/** Show a hover card beside a screen point, or hide it (x = null). */
export function moveCard(el: HTMLDivElement | null, x: number | null, y: number) {
  if (!el) return;
  if (x === null) {
    if (el.style.visibility !== "hidden") el.style.visibility = "hidden";
    return;
  }
  el.style.visibility = "visible";
  el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) translate(14px, -50%)`;
}
