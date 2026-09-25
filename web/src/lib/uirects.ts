"use client";
// Screen rectangles covered by the HTML UI, so labels drawn in the canvas never sit under a panel.
export interface Rect { x0: number; x1: number; y0: number; y1: number }

// panels, plus the journey's destination callout (labels give it room)
const SEL = ".topleft, .controls, .panel[data-open='true'], .dest-callout";
let cache: { t: number; rects: Rect[] } = { t: -1, rects: [] };

export function uiRects(canvas: HTMLElement): Rect[] {
  const t = performance.now();
  if (t - cache.t < 150) return cache.rects;
  const c = canvas.getBoundingClientRect();
  const rects: Rect[] = [];
  document.querySelectorAll<HTMLElement>(SEL).forEach((el) => {
    if (el.checkVisibility && !el.checkVisibility({ visibilityProperty: true })) return;
    const r = el.getBoundingClientRect();
    if (r.width && r.height) rects.push({ x0: r.left - c.left - 6, x1: r.right - c.left + 6, y0: r.top - c.top - 6, y1: r.bottom - c.top + 6 });
  });
  cache = { t, rects };
  return rects;
}

export const overlaps = (a: Rect, list: Rect[]) => list.some((o) => a.x0 < o.x1 && a.x1 > o.x0 && a.y0 < o.y1 && a.y1 > o.y0);
