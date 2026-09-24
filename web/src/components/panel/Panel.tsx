"use client";
import { useStore } from "@/lib/store";
import { NodeView } from "./NodeView";
import { QuestionCard } from "./QuestionCard";
import { AskBox } from "./AskBox";

export function Panel() {
  const panel = useStore((s) => s.panel);
  const close = () => useStore.getState().set({ panel: { kind: "none" } });
  return (
    <aside className="panel" data-open={panel.kind !== "none"} data-testid="panel" aria-label="Details">
      {panel.kind === "node" && <NodeView key={panel.id} id={panel.id} onClose={close} />}
      {panel.kind === "question" && <QuestionCard key={panel.id} id={panel.id} note={panel.note} onClose={close} />}
      {panel.kind === "ask" && <AskBox key={panel.text ?? ""} onClose={close} initial={panel.text} />}
    </aside>
  );
}

export function Crumbs({ items, onClose }: { items: { id: string; label: string }[]; onClose: () => void }) {
  return (
    <div className="panel-head">
      <nav className="crumbs" aria-label="Location in the tree">
        {items.map((a, i) => (
          <span key={a.id} style={{ display: "contents" }}>
            {i > 0 && <span className="sep">/</span>}
            <CrumbLink id={a.id} label={i === 0 ? "All" : a.label} />
          </span>
        ))}
      </nav>
      <button className="iconbtn" onClick={onClose} aria-label="Close panel">
        ✕
      </button>
    </div>
  );
}

function CrumbLink({ id, label }: { id: string; label: string }) {
  return (
    <button
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
