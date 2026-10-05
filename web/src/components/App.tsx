"use client";
import dynamic from "next/dynamic";
import { useEffect, useRef, useState } from "react";
import { loadSubtree, useStore } from "@/lib/store";
import { loadStars } from "@/lib/stars";
import { goBack, goForward, deselect, resetView } from "@/lib/actions";
import { Search } from "./Search";
import { Legend } from "./Tools";
import type { Theme } from "@/lib/theme";
import { Panel } from "./panel/Panel";
import SiteNav from "./SiteNav";

// the vertical caption, as on typesafe.ai: base64 of "I want to join the jevolution" (theirs hides "No comment.")
const B64 = "SSB3YW50IHRvIGpvaW4gdGhlIGpldm9sdXRpb24=";

const Scene = dynamic(() => import("./scene/Scene"), { ssr: false });

export default function App() {
  const open = useStore((s) => s.panel.kind !== "none");
  const count = useStore((s) => Object.keys(s.nodes).length);
  const theme = useStore((s) => s.theme);
  const starsReady = useStore((s) => s.starsReady);
  // the whole tree and every dot, fetched while the 3D scene's code is still downloading, not after it
  useEffect(() => {
    Promise.all([loadSubtree("root", 12), loadStars()]).then(() => useStore.getState().set({ starsReady: true }));
  }, []);
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
      if (e.key === "Escape") {
        // Esc peels one layer at a time: an open tool, then the selection, then everything (search too, fly home)
        const st = useStore.getState();
        if (st.tool) st.set({ tool: null });
        else if (st.panel.kind !== "none" || st.selected) deselect();
        else resetView();
      }
      else if ((e.key === "Backspace" || (e.altKey && e.key === "ArrowLeft")) && useStore.getState().canBack) { e.preventDefault(); goBack(); }
      else if (e.altKey && e.key === "ArrowRight" && useStore.getState().canForward) { e.preventDefault(); goForward(); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  // iOS Safari pinch-zooms the page whatever the viewport says; on the map a pinch belongs to the 3D scene
  useEffect(() => {
    const stop = (e: Event) => e.preventDefault();
    const opts = { passive: false } as AddEventListenerOptions;
    for (const t of ["gesturestart", "gesturechange", "gestureend"]) document.addEventListener(t, stop, opts);
    return () => { for (const t of ["gesturestart", "gesturechange", "gestureend"]) document.removeEventListener(t, stop, opts); };
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
      <div className="stage" data-testid="stage" data-nodes={count} data-stars={starsReady}>
        <Scene />
      </div>
      <div className="topleft">
        <Search />
      </div>
      <Legend />
      <SiteNav />
      <Panel />
      <i className="crop tl" /><i className="crop tr" /><i className="crop bl" /><i className="crop br" />
      <span className="b64" aria-hidden>{B64}</span>
      <p className="intro" data-hidden={hintGone}>Every dot is a question · drag to orbit · scroll into a cloud to read · click a dot or its text to open</p>
    </main>
  );
}
