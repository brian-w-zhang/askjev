"use client";

import { useState, type ReactNode } from "react";
import type { Row } from "./types";
import { QuestionRow } from "./rows";

// A card's receipts: the evidence line and the real rows behind it. The rows render only once opened, so the page
// doesn't carry every card's example questions in its first load.
export default function Receipts({ meta, rows }: { meta: ReactNode; rows?: Row[] }) {
  const [open, setOpen] = useState(false);
  return (
    <details className="receipts" onToggle={(e) => setOpen((e.target as HTMLDetailsElement).open)}>
      <summary>receipts</summary>
      <p className="rc-meta">{meta}</p>
      {open && rows && rows.length > 0 && <ol className="rc-rows">{rows.map((r) => <QuestionRow key={r.id} row={r} />)}</ol>}
    </details>
  );
}
