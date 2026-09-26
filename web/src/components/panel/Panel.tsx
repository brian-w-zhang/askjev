"use client";
import { useEffect, useState } from "react";
import { useStore, type PanelView } from "@/lib/store";
import { load, peek, prefetch } from "@/lib/cache";
import { nodeUrl, viewUrl } from "@/lib/panelData";
import { goBack, goForward } from "@/lib/actions";
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

  const close = () => useStore.getState().set({ panel: { kind: "none" } });
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
        <nav className="crumbs" aria-label="Location in the tree">
          {items.map((a, i) => (
            <span key={a.id} style={{ display: "contents" }}>
              {i > 0 && <span className="sep">/</span>}
              <CrumbLink id={a.id} label={i === 0 ? "All" : a.label} />
            </span>
          ))}
        </nav>
      </div>
    </>
  );
}

function CrumbLink({ id, label }: { id: string; label: string }) {
  return (
    <button
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
