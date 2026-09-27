"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useStore } from "@/lib/store";
import { openQuestion, selectNode, travel } from "@/lib/actions";
import "./SiteNav.css";

// The map's links to the portrait and atlas: small white chips at the top, like typesafe.ai's nav (at the bottom on
// phones, where the search window fills the top). Also the map's deep links: /?node=<id> opens a topic and
// /?q=<id> a question, and the address bar follows whatever panel is open so the page can be shared.
export default function SiteNav() {
  useEffect(() => {
    const sp = new URLSearchParams(location.search);
    const node = sp.get("node"), q = sp.get("q");
    let unsub = () => {};
    const go = () => {
      if (q) openQuestion(q);
      else if (node) {
        const parts = node.split(".");
        travel(["root", ...parts.map((_, i) => parts.slice(0, i + 1).join("."))]).then(() => selectNode(node));
      }
      unsub = useStore.subscribe((st, prev) => {
        if (st.panel === prev.panel) return;
        const u = new URL(location.href);
        u.searchParams.delete("node");
        u.searchParams.delete("q");
        if (st.panel.kind === "node") u.searchParams.set("node", st.panel.id);
        else if (st.panel.kind === "question") u.searchParams.set("q", st.panel.id);
        history.replaceState(history.state, "", u.pathname + u.search);
      });
    };
    // wait for the tree's first load before following a link
    if (Object.keys(useStore.getState().nodes).length) go();
    else {
      const wait = useStore.subscribe((st) => {
        if (Object.keys(st.nodes).length) { wait(); go(); }
      });
      return () => { wait(); unsub(); };
    }
    return () => unsub();
  }, []);
  return (
    <nav className="sitenav" aria-label="Site">
      <span className="snav here" aria-current="page">Map</span>
      <Link className="snav" href="/portrait">Portrait</Link>
      <Link className="snav" href="/portrait/atlas">Atlas</Link>
    </nav>
  );
}
