"use client";
import { useId, useRef, useState, type ReactNode } from "react";

const POP_W = 268;
const POP_H = 230; // room a window needs below the "i" (the longest runs about this tall)

/**
 * A small "i" beside a term on the cards, explaining it in plain words (docs/07-ui.md, Side panel). Hover or
 * focus shows it; a tap toggles it (touch has no hover). Styled as a tiny OS window, like the hover cards.
 */
export function Info({ label, children }: { label: string; children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [shift, setShift] = useState(0);
  const [up, setUp] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const id = useId();
  // keep the window inside the panel: slide it left when the "i" sits far right, open it upward near the bottom
  const fit = () => {
    const el = ref.current;
    const box = el?.closest(".panel")?.getBoundingClientRect();
    if (!el || !box) return;
    const r = el.getBoundingClientRect();
    setShift(Math.min(0, box.right - 14 - (r.left - 4 + POP_W)));
    setUp(r.bottom + POP_H > box.bottom && r.top - POP_H > box.top);
  };
  return (
    <span className="info" data-open={open} data-up={up} ref={ref} onMouseEnter={fit} onFocus={fit} onMouseLeave={() => setOpen(false)}>
      <button
        type="button"
        className="info-i"
        aria-label={`About ${label}`}
        aria-describedby={id}
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        onBlur={() => setOpen(false)}
        onKeyDown={(e) => { if (e.key === "Escape" && open) { e.stopPropagation(); setOpen(false); } }}
      >
        i
      </button>
      <span className="info-pop" role="tooltip" id={id} style={{ width: POP_W, left: -4 + shift }}>
        <span className="info-head">{label}</span>
        <span className="info-body">{children}</span>
      </span>
    </span>
  );
}
