"use client";

import { useEffect } from "react";

// The portrait and atlas pages are dark only (the map alone offers both themes). Arriving from the map in light mode,
// this switches the page to dark while it's open and puts the map's theme back on the way out.
export default function ThemeToggle() {
  useEffect(() => {
    const el = document.documentElement;
    const prev = el.dataset.theme;
    el.dataset.theme = "dark";
    return () => { if (prev) el.dataset.theme = prev; };
  }, []);
  return null;
}
