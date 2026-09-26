"use client";
import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { useStore } from "@/lib/store";
import { goBack, goForward } from "@/lib/actions";
import { Search } from "./Search";
import { Legend } from "./Tools";
import type { Theme } from "@/lib/theme";
import { Panel } from "./panel/Panel";

// the vertical caption, as on typesafe.ai: base64 of "askjev: every closed question, answered by Jev"
const B64 = "YXNramV2OiBldmVyeSBjbG9zZWQgcXVlc3Rpb24sIGFuc3dlcmVkIGJ5IEpldg==";

const Scene = dynamic(() => import("./scene/Scene"), { ssr: false });

export default function App() {
  const open = useStore((s) => s.panel.kind !== "none");
  const count = useStore((s) => Object.keys(s.nodes).length);
  const theme = useStore((s) => s.theme);
  useEffect(() => {
    document.body.classList.toggle("panel-open", open);
  }, [open]);
  // theme: whatever the pre-paint script in layout.tsx picked (saved choice, else the system's), then kept in sync
  useEffect(() => {
    const t = document.documentElement.dataset.theme as Theme | undefined;
    if (t === "dark" || t === "light") useStore.getState().set({ theme: t });
  }, []);
  useEffect(() => {
    // the first run sees the store's default before the effect above has read the page's theme: skip it
    if (!themeTouched.current) { themeTouched.current = true; return; }
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem("askjev.theme", theme); } catch {}
  }, [theme]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement;
      if (typing) return;
      if (e.key === "Escape") useStore.getState().set({ panel: { kind: "none" }, tool: null });
      else if ((e.key === "Backspace" || (e.altKey && e.key === "ArrowLeft")) && useStore.getState().canBack) { e.preventDefault(); goBack(); }
      else if (e.altKey && e.key === "ArrowRight" && useStore.getState().canForward) { e.preventDefault(); goForward(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  // the hint shows once, then gets out of the way
  const themeTouched = useRef(false);
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
        <Search />
      </div>
      <Legend />
      <Panel />
      <i className="crop tl" /><i className="crop tr" /><i className="crop bl" /><i className="crop br" />
      <span className="b64" aria-hidden>{B64}</span>
      <p className="intro" data-hidden={hintGone}>Every dot is a question · drag to orbit · scroll into a cloud to read · click a dot or its text to open</p>
    </main>
  );
}
