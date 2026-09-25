"use client";
import { useEffect, useState } from "react";
import { useStore } from "@/lib/store";
import { cards, nodeSlots, starSlots, useOverlay } from "@/lib/overlay";
import { selectNode } from "@/lib/actions";
import { loadTexts, starData, starText } from "@/lib/stars";

// HTML over the canvas (docs/07-ui.md, Look): node labels, question labels, and hover cards.
// Text and classes come from React; positions and fades are written by the scene each frame via refs
// (never through state), so 60 moving labels cost no React renders.
export function SkyOverlay() {
  const nodes = useOverlay((s) => s.nodes);
  const stars = useOverlay((s) => s.stars);
  return (
    <div className="skylabels" aria-hidden>
      {nodes.map((l, i) => (
        <div
          key={`n${i}`}
          ref={(el) => { nodeSlots[i].el = el; }}
          className={`skylabel ${l.cls}`}
          style={{ opacity: 0 }}
          onClick={() => { const id = nodeSlots[i].key; if (id) selectNode(id); }}
        >
          {l.text}
        </div>
      ))}
      {stars.map((l, i) => (
        <div key={`s${i}`} ref={(el) => { starSlots[i].el = el; }} className={`skylabel ${l.cls}`} style={{ opacity: 0 }}>
          {l.text}
        </div>
      ))}
      <NodeCard />
      <StarCard />
      <Walker />
      <Destination />
    </div>
  );
}

/** The journey's walker: a glowing dot with a chip saying who is walking, where, and how sure Jev was. */
function Walker() {
  const w = useOverlay((s) => s.walker);
  return (
    <div ref={(el) => { cards.walker = el; }} className="walker skycard" data-who={w?.who ?? "jev"} style={{ visibility: "hidden" }}>
      <i className="walker-dot" />
      {w && (
        <span className="walker-chip">
          <b>{w.who === "jev" ? "JEV" : "PATH"}</b> ▸ {w.label}
          {w.p !== null && <span className="num"> · {Math.round(w.p * 100)}%</span>}
        </span>
      )}
    </div>
  );
}

/** Where the journey ends: a lit ring on the question's dot, with its text. */
function Destination() {
  const i = useStore((s) => s.focusStar);
  const [, loaded] = useState(0);
  useEffect(() => {
    const d = starData();
    if (i < 0 || !d || starText(i)) return;
    let live = true;
    loadTexts(d.nodeIds[d.node[i]]).then(() => live && loaded((x) => x + 1));
    return () => { live = false; };
  }, [i]);
  const q = i >= 0 ? starText(i) : undefined;
  return (
    <div ref={(el) => { cards.dest = el; }} className="dest skycard" style={{ visibility: "hidden" }}>
      <i className="dest-ring" />
      {q && <div className="dest-callout">{q.label}</div>}
    </div>
  );
}

function NodeCard() {
  const id = useStore((s) => s.hovered);
  const n = useStore((s) => (id ? s.nodes[id] : undefined));
  return (
    <div ref={(el) => { cards.node = el; }} className="hovercard skycard" style={{ visibility: "hidden" }}>
      {n && (
        <>
          <div className="hovercard-label">{n.label}</div>
          <div className="hovercard-meta">
            {n.n_questions} question{n.n_questions === 1 ? "" : "s"}
            {n.n_children ? `, ${n.n_desc} topics below` : ""}
          </div>
        </>
      )}
    </div>
  );
}

function StarCard() {
  const hoverStar = useStore((s) => s.hoverStar);
  const [, loaded] = useState(0);
  // the text cache lives outside React; this only makes sure the hovered star's node is loading
  useEffect(() => {
    const d = starData();
    if (hoverStar < 0 || !d || starText(hoverStar)) return;
    let live = true;
    loadTexts(d.nodeIds[d.node[hoverStar]]).then(() => live && loaded((x) => x + 1));
    return () => { live = false; };
  }, [hoverStar]);
  const q = hoverStar >= 0 ? starText(hoverStar) : undefined;
  return (
    <div ref={(el) => { cards.star = el; }} className="hovercard star-card skycard" style={{ visibility: "hidden" }}>
      {q && (
        <>
          <div className="hovercard-label">Question</div>
          <div className="body">{q.text}</div>
          {q.label !== q.text && <div className="hovercard-meta">{q.label}</div>}
        </>
      )}
    </div>
  );
}
