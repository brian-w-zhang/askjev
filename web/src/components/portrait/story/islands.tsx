"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import Rows from "../../experiments/Rows";

const pc = (v: number) => `${Math.round(v * 100)}%`;

// Marks its box data-in once it scrolls into view, so CSS can play the chapter's entrance (bars fill, dots slide).
// The portrait scrolls inside .pt, not the window.
export function Reveal({ children, className = "", as: Tag = "div" }: { children: ReactNode; className?: string; as?: "div" | "section" }) {
  const ref = useRef<HTMLDivElement>(null);
  const [on, setOn] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (!("IntersectionObserver" in window)) return; // no observer: the rv-on class never goes on, so nothing is hidden
    document.documentElement.classList.add("rv-on");
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setOn(true); io.disconnect(); } },
      { root: document.querySelector(".pt"), threshold: 0.2 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return <Tag ref={ref} className={`rv ${className}`} data-in={on ? "" : undefined}>{children}</Tag>;
}


// A 0-100 ruler of probability words; the toggle slides each word from people's reading to Jev's.
export function ProbRuler({ rows }: { rows: { phrase: string; jev: number; people: number }[] }) {
  const [who, setWho] = useState<"jev" | "people">("jev");
  const sorted = [...rows].sort((a, b) => a.people - b.people);
  return (
    <div className="pr">
      <div className="tf-tabs" role="tablist" aria-label="Whose reading">
        <button role="tab" aria-selected={who === "jev"} onClick={() => setWho("jev")}>Jev</button>
        <button role="tab" aria-selected={who === "people"} onClick={() => setWho("people")}>people</button>
      </div>
      <div className="pr-track">
        {sorted.map((r, i) => {
          const v = who === "jev" ? r.jev : r.people;
          const moved = Math.abs(r.jev - r.people) >= 15;
          return (
            // words near either end grow inward, so none hangs off the ruler; six rows keep neighbors apart
            <span key={r.phrase} className={`pr-w${moved ? " moved" : ""}`}
              style={{ left: `${v}%`, top: `${(i % 6) * (100 / 6)}%`, transform: `translateX(${v < 15 ? -8 : v > 85 ? -92 : -50}%)` }}
              title={`${r.phrase}: Jev ${r.jev}%, people ${r.people}%`}>
              <i />{r.phrase.toLowerCase()} <em>{v}%</em>
            </span>
          );
        })}
      </div>
      <div className="pr-axis"><span>0%</span><span>50%</span><span>100%</span></div>
    </div>
  );
}


// A chat where a user claims a crowd; Jev's probability for the named option climbs when the card comes into view.
export function PressureChat({ shift, label, claim }: { shift: number; label: string; claim: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [on, setOn] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setOn(true); io.disconnect(); } },
      { root: document.querySelector(".pt"), threshold: 0.5 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div className="pc" ref={ref} data-in={on ? "" : undefined}>
      <p className="pc-u">{claim}</p>
      <div className="pc-j">
        <span>{label}</span>
        {/* how far Jev's probability moved toward the claimed side, out of 100 points */}
        <div className="pc-bar"><i style={{ width: on ? pc(shift) : "0%" }} /></div>
        <b>{on ? `+${Math.round(shift * 100)} points` : "…"}</b>
      </div>
    </div>
  );
}

// Every question behind an experiment, loaded only when opened (the same paged list as its case study)
export function QuestionList({ id, total, label }: { id: string; total: number; label: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="ql">
      <button type="button" className="ql-b" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? "▾" : "▸"} {label} <em>{total.toLocaleString("en-US")}</em>
      </button>
      {open && <div className="ql-rows"><Rows id={id} total={total} flagged={{ wrong: 0, differs: 0 }} /></div>}
    </div>
  );
}
