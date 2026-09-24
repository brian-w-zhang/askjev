"use client";
import dynamic from "next/dynamic";
import { useEffect } from "react";
import { useStore } from "@/lib/store";
import { Search } from "./Search";
import { Controls } from "./Controls";
import { Panel } from "./panel/Panel";
import { WorthALook } from "./WorthALook";

const Scene = dynamic(() => import("./scene/Scene"), { ssr: false });

export default function App() {
  const open = useStore((s) => s.panel.kind !== "none");
  const count = useStore((s) => Object.keys(s.nodes).length);
  useEffect(() => {
    document.body.classList.toggle("panel-open", open);
  }, [open]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement))
        useStore.getState().set({ panel: { kind: "none" } });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  return (
    <main>
      <div className="stage" data-testid="stage" data-nodes={count}>
        <Scene />
      </div>
      <div className="topleft">
        <div className="wordmark">
          <h1>askjev</h1>
          <p>Every closed question on one tree, answered by Jev</p>
        </div>
        <Search />
      </div>
      <button className="askbtn" onClick={() => useStore.getState().set({ panel: { kind: "ask" } })}>
        Ask Jev a question
      </button>
      <Controls />
      <WorthALook />
      <Panel />
      <p className="intro">Every dot is a question. Drag to orbit, scroll into a cloud to read it, click a star to open it</p>
    </main>
  );
}
