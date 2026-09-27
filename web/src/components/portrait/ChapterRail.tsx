"use client";

import { useEffect, useState } from "react";

// A fixed chapter index on wide screens: numbered ticks, the current chapter named.
export default function ChapterRail({ chapters }: { chapters: { id: string; name: string }[] }) {
  const [on, setOn] = useState<string | null>(null);
  useEffect(() => {
    const root = document.querySelector(".pt");
    const els = chapters.map((c) => document.getElementById(c.id)).filter((e): e is HTMLElement => !!e);
    const io = new IntersectionObserver((es) => {
      for (const e of es) if (e.isIntersecting) setOn(e.target.id);
    }, { root, rootMargin: "-45% 0px -50% 0px" });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
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
