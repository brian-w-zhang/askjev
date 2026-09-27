"use client";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useStore, type PanelView } from "@/lib/store";
import { load, peek, prefetch } from "@/lib/cache";
import { nodeUrl, viewUrl } from "@/lib/panelData";
import { deselect, goBack, goForward } from "@/lib/actions";
import { NodeView } from "./NodeView";
import { QuestionCard } from "./QuestionCard";
import { AskBox } from "./AskBox";

export function Panel() {
  const panel = useStore((s) => s.panel);
  const url = viewUrl(panel);
  const ready = !url || peek(url) !== undefined;
  // Stale-while-revalidate: the current view stays on screen until the next one's data is in (instantly
  // when it's cached), so the panel never flashes a loading state or jumps in height between pages.
  const [shown, setShown] = useState<PanelView>(panel);
  if (ready && shown !== panel) setShown(panel);
  // while sliding shut, keep drawing what was there
  const [content, setContent] = useState<PanelView>(panel);
  if (shown.kind !== "none" && shown !== content) setContent(shown);
  const [, arrived] = useState(0);
  useEffect(() => {
    if (!url || ready) return;
    let live = true;
    load(url).then(() => live && arrived((x) => x + 1), () => live && setShown(panel)); // errors show in the view
    return () => { live = false; };
  }, [url, ready, panel]);

  const close = deselect;
  const v = content;
  return (
    <aside className="panel" data-open={shown.kind !== "none"} data-pending={shown !== panel && panel.kind !== "none"} data-testid="panel" aria-label="Details">
      {v.kind === "node" && <NodeView key={v.id} id={v.id} onClose={close} />}
      {v.kind === "question" && <QuestionCard key={v.id} id={v.id} note={v.note} onClose={close} />}
      {v.kind === "ask" && <AskBox key={v.text ?? ""} onClose={close} initial={v.text} />}
    </aside>
  );
}

/** The panel's chrome, like a small browser: title bar with close, then Back / Forward and the path as an address. */
export function Crumbs({ items, onClose }: { items: { id: string; label: string }[]; onClose: () => void }) {
  const canBack = useStore((s) => s.canBack);
  const canForward = useStore((s) => s.canForward);
  const kind = useStore((s) => s.panel.kind);
  return (
    <>
      <div className="panel-head">
        <span className="panel-title">{kind === "question" ? "Question.View 1.1" : "Topic.View 1.1"}</span>
        <button className="iconbtn" onClick={onClose} aria-label="Close panel" title="Close (Esc)">
          ✕
        </button>
      </div>
      <div className="panel-nav">
        <button className="navbtn" onClick={goBack} disabled={!canBack} aria-label="Back" title="Back (Backspace or Alt+←)">
          ‹
        </button>
        <button className="navbtn" onClick={goForward} disabled={!canForward} aria-label="Forward" title="Forward (Alt+→)">
          ›
        </button>
        <Path items={items} />
      </div>
    </>
  );
}

/**
 * The address: the path from the root, one line. When it doesn't fit, the leading steps fold into a "…" step
 * (clicking it goes up to the last folded one), as file browsers do, so every step shown is whole. A hidden copy
 * of the full path is measured to decide how many to fold, again whenever the panel changes width.
 */
function Path({ items }: { items: { id: string; label: string }[] }) {
  const nav = useRef<HTMLElement>(null);
  const ruler = useRef<HTMLSpanElement>(null);
  const [fold, setFold] = useState(0);
  useLayoutEffect(() => {
    const el = nav.current, r = ruler.current;
    if (!el || !r) return;
    const fit = () => {
      const pad = 16, ell = 30; // the address's side padding; the "…" step and its separator
      const w = [...r.children].map((c) => c.getBoundingClientRect().width);
      let total = w.reduce((s, x) => s + x, 0);
      let k = 0;
      while (k < w.length - 1 && total + (k ? ell : 0) > el.clientWidth - pad) total -= w[k++];
      setFold(k);
    };
    const ro = new ResizeObserver(fit);
    ro.observe(el);
    return () => ro.disconnect();
  }, [items]);
  const step = (a: { id: string; label: string }, i: number) => (
    <span key={a.id} className="step">
      {i > 0 && <span className="sep">/</span>}
      <CrumbLink id={a.id} label={i === 0 ? "All" : a.label} />
    </span>
  );
  return (
    <nav className="crumbs" aria-label="Location in the tree" ref={nav}>
      <span className="ruler" aria-hidden ref={ruler}>{items.map(step)}</span>
      {fold > 0 && (
        <span className="step">
          <CrumbLink id={items[fold - 1].id} label="…" title={items.slice(0, fold).map((a, i) => (i === 0 ? "All" : a.label)).join(" / ")} />
        </span>
      )}
      {items.map((a, i) => (i < fold ? null : step(a, i)))}
    </nav>
  );
}

function CrumbLink({ id, label, title }: { id: string; label: string; title?: string }) {
  return (
    <button
      title={title}
      onPointerEnter={() => prefetch(nodeUrl(id))}
      onClick={async () => {
        const { selectNode } = await import("@/lib/actions");
        selectNode(id);
      }}
    >
      {label}
    </button>
  );
}

export const pct = (x: number | null | undefined, d = 0) => (x === null || x === undefined ? "n/a" : `${(x * 100).toFixed(d)}%`);
