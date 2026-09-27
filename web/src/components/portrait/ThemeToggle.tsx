"use client";

import { useSyncExternalStore } from "react";

// Same key and attribute as the map (layout.tsx picks the theme before first paint); this reads the attribute.
const subscribe = (cb: () => void) => {
  const o = new MutationObserver(cb);
  o.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return () => o.disconnect();
};
const read = () => (document.documentElement.dataset.theme === "dark" ? "dark" : "light");

export default function ThemeToggle() {
  const theme = useSyncExternalStore(subscribe, read, () => null);
  const flip = () => {
    const next = read() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("askjev.theme", next); } catch {}
  };
  return (
    <button type="button" className="pt-chipnav dark" onClick={flip} aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}>
      {theme === "dark" ? "☀ Light" : "☾ Dark"}
    </button>
  );
}
