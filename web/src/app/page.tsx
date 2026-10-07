import type { Viewport } from "next";
import App from "@/components/App";

// The map is a full-screen 3D scene: a pinch zooms the scene, never the page (the portrait and atlas keep page zoom).
// Chrome honors this; iOS Safari ignores it, so App also cancels Safari's own pinch events on this page.
export const viewport: Viewport = {
  themeColor: "#1E1E1E",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function Page() {
  return <App />;
}
