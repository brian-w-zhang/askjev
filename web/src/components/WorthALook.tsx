"use client";
import { useEffect, useMemo, useState } from "react";
import { useStore } from "@/lib/store";
import { attention, INDICATORS } from "@/lib/color";
import { selectNode } from "@/lib/actions";
import { starData } from "@/lib/stars";
import { HEMI_COLOR } from "@/lib/layout";
import type { Indicator } from "@/lib/types";
import { home } from "./scene/CameraRig";

const TOP = 8;
const MIN_STARS = 15; // enough questions for the node's indicator to mean something
const TOUR_MS = 7000;

// "Worth a look" (docs/07-ui.md): the topics that stand out on the current indicator, one click to fly there.
export function WorthALook() {
  const nodes = useStore((s) => s.nodes);
  const indicator = useStore((s) => s.indicator);
  const ready = useStore((s) => s.starsReady);
  const tour = useStore((s) => s.tour);
  const selected = useStore((s) => s.selected);
  const set = useStore((s) => s.set);
  const [open, setOpen] = useState(true);
  const ind: Indicator = indicator === "hemisphere" ? "stability" : indicator;
  const label = INDICATORS.find((i) => i.id === ind)?.label ?? ind;

  const top = useMemo(() => {
    const d = starData();
    if (!ready || !d) return [];
    return Object.values(nodes)
      .filter((n) => (d.offsets.get(n.id)?.[1] ?? 0) >= MIN_STARS)
      .map((n) => ({ n, a: attention(n, ind) }))
      .filter((x): x is { n: typeof x.n; a: number } => x.a !== null)
      .sort((a, b) => b.a - a.a)
      .slice(0, TOP);
  }, [nodes, ind, ready]);

  useEffect(() => {
    if (!tour || !top.length) return;
    let k = Math.max(0, top.findIndex((x) => x.n.id === selected) + 1) % top.length;
    selectNode(top[k].n.id);
    const h = setInterval(() => {
      k = (k + 1) % top.length;
      selectNode(top[k].n.id);
    }, TOUR_MS);
    return () => clearInterval(h);
    // restart only when the tour or the list changes, not on every selection
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tour, top]);

  if (!top.length) return null;
  return (
    <div className="worth" data-open={open} data-title="Worth.A.Look 1.0">
      <div className="worth-head">
        <button className="worth-title" onClick={() => setOpen(!open)} aria-expanded={open}>
          Worth a look <span>by {label.toLowerCase()}</span>
        </button>
        <button className="worth-tour" aria-pressed={tour} onClick={() => set({ tour: !tour })}>
          {tour ? "Stop tour" : "Tour"}
        </button>
      </div>
      {open && (
        <ol>
          {top.map(({ n, a }) => (
            <li key={n.id}>
              <button aria-current={selected === n.id} onClick={() => { set({ tour: false }); selectNode(n.id); }}>
                <i style={{ background: HEMI_COLOR[n.hemisphere] }} />
                <span className="worth-label">{n.label}</span>
                <span className="worth-meter"><b style={{ ["--a" as string]: `${Math.round(a * 100)}%` }} /></span>
              </button>
            </li>
          ))}
        </ol>
      )}
      {open && (
        <button className="worth-home" onClick={() => { set({ tour: false, selected: null, panel: { kind: "none" } }); home(); }}>
          Back to the whole sky
        </button>
      )}
    </div>
  );
}
