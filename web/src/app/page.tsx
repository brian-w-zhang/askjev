import type { Viewport } from "next";
import App from "@/components/App";
import { starVersion } from "@/lib/server/stars";

// The map is a full-screen 3D scene: a pinch zooms the scene, never the page (the portrait and atlas keep page zoom).
// Chrome honors this; iOS Safari ignores it, so App also cancels Safari's own pinch events on this page.
export const viewport: Viewport = {
  themeColor: "#1E1E1E",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

// The map's three data files start downloading with the HTML, before any bundle loads: an inline script fetches them
// and the app picks those requests up (lib/boot.ts). The dots are named by the snapshot's version (production: fixed
// per deploy), the same request the app would make.
export default async function Page() {
  const v = await starVersion().catch(() => undefined);
  const urls = ["/api/tree?root=root&depth=12", "/api/stars", ...(v ? [`/api/stars?bin=1&v=${encodeURIComponent(v)}`] : [])];
  const boot = `try{window.__boot={};for(const u of ${JSON.stringify(urls)})window.__boot[u]=fetch(u)}catch(e){}`;
  return (
    <>
      <script dangerouslySetInnerHTML={{ __html: boot }} />
      <App starsVersion={v} />
    </>
  );
}
