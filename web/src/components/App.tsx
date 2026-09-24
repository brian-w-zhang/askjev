"use client";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { useStore } from "@/lib/store";
import { Search } from "./Search";
import { Controls } from "./Controls";
import { Panel } from "./panel/Panel";

// the vertical caption, as on typesafe.ai: base64 of "askjev: every closed question, answered by Jev"
const B64 = "YXNramV2OiBldmVyeSBjbG9zZWQgcXVlc3Rpb24sIGFuc3dlcmVkIGJ5IEpldg==";

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
  // the hint shows once, then gets out of the way
  const [hintGone, setHintGone] = useState(false);
  useEffect(() => {
    const h = setTimeout(() => setHintGone(true), 9000);
    return () => clearTimeout(h);
  }, []);
  return (
    <main>
      <div className="stage" data-testid="stage" data-nodes={count}>
        <Scene />
      </div>
      <div className="topleft">
        <div className="wordmark">
          <h1>askjev</h1>
          <p>Every closed question, answered by Jev</p>
        </div>
        <Search />
      </div>
      <Controls />
      <Panel />
      <i className="crop tl" /><i className="crop tr" /><i className="crop bl" /><i className="crop br" />
      <span className="b64" aria-hidden>{B64}</span>
      <p className="intro" data-hidden={hintGone}>Every dot is a question · drag to orbit · scroll into a cloud to read · click a dot to open</p>
    </main>
  );
}
