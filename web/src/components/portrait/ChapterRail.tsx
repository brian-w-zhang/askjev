"use client";

import { useEffect, useState } from "react";

// A fixed chapter index on wide screens: numbered ticks, the current chapter named.
export default function ChapterRail({ chapters }: { chapters: { id: string; name: string }[] }) {
  const [on, setOn] = useState<string | null>(null);
  // the current chapter is the last one whose top has passed the middle of the screen, worked out from positions on
  // each scroll (not from intersections, which a jump from a link or the rail skips past); none past the last chapter
  useEffect(() => {
    const root = document.querySelector<HTMLElement>(".pt");
    if (!root) return;
    const els = chapters.map((c) => document.getElementById(c.id)).filter((e): e is HTMLElement => !!e);
    let frame = 0;
    const update = () => {
      frame = 0;
      const line = root.clientHeight * 0.45;
      let cur: HTMLElement | null = null;
      for (const e of els) if (e.getBoundingClientRect().top <= line) cur = e;
      setOn(cur && cur.getBoundingClientRect().bottom > line ? cur.id : null);
    };
    const onScroll = () => { if (!frame) frame = requestAnimationFrame(update); };
    update();
    root.addEventListener("scroll", onScroll, { passive: true });
    return () => { root.removeEventListener("scroll", onScroll); cancelAnimationFrame(frame); };
  }, [chapters]);
  return (
    <nav className="rail" aria-label="Chapters">
      {chapters.map((c, i) => (
        <a key={c.id} href={`#${c.id}`} aria-current={on === c.id ? "true" : undefined}>
          <span className="n">{String(i + 1).padStart(2, "0")}</span><span className="t">{c.name}</span>
        </a>
      ))}
    </nav>
  );
}
