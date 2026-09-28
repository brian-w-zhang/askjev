"use client";

import { useEffect, useRef, useState } from "react";
import ExMeme from "./ExMeme";
import type { ExperimentMeme } from "./types";

// The atlas index's hover memes (docs/17 item 9): while the pointer is over a card, that card's meme floats next to
// the cursor and eases after it. The position is written straight to the element in an animation frame, so moving the
// mouse never re-renders React; only entering or leaving a card does. Off on touch screens and with reduced motion.
export function useMemeFollower() {
  const box = useRef<HTMLDivElement>(null);
  const target = useRef({ x: 0, y: 0 });
  const pos = useRef({ x: 0, y: 0 });
  const raf = useRef(0);
  const [meme, setMeme] = useState<ExperimentMeme | null>(null);
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(hover: hover) and (pointer: fine) and (prefers-reduced-motion: no-preference)");
    const on = () => setEnabled(mq.matches);
    on();
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);

  useEffect(() => {
    if (!meme || !enabled) return;
    const tick = () => {
      const el = box.current;
      if (el) {
        pos.current.x += (target.current.x - pos.current.x) * 0.22;
        pos.current.y += (target.current.y - pos.current.y) * 0.22;
        // keep it on screen: flip to the cursor's left or above it near the edges
        const w = el.offsetWidth, h = el.offsetHeight;
        const x = pos.current.x + 24 + w > window.innerWidth ? pos.current.x - w - 24 : pos.current.x + 24;
        const y = Math.min(Math.max(8, pos.current.y - h / 2), window.innerHeight - h - 8);
        el.style.transform = `translate3d(${x}px, ${y}px, 0)`;
      }
      raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf.current);
  }, [meme, enabled]);

  const handlers = (m: ExperimentMeme | undefined) => enabled && m ? {
    onPointerEnter: (e: React.PointerEvent) => { target.current = { x: e.clientX, y: e.clientY }; pos.current = { x: e.clientX, y: e.clientY }; setMeme(m); },
    onPointerMove: (e: React.PointerEvent) => { target.current = { x: e.clientX, y: e.clientY }; },
    onPointerLeave: () => setMeme(null),
  } : {};

  const layer = enabled && meme ? (
    <div ref={box} className="ex-follow" aria-hidden><ExMeme m={meme} size="float" /></div>
  ) : null;
  return { handlers, layer };
}
