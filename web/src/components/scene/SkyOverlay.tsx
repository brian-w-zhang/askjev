"use client";
import { useEffect, useState } from "react";
import { useStore } from "@/lib/store";
import { cards, nodeSlots, starSlots, useOverlay } from "@/lib/overlay";
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
        <div key={`n${i}`} ref={(el) => { nodeSlots[i].el = el; }} className={`skylabel ${l.cls}`} style={{ opacity: 0 }}>
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
