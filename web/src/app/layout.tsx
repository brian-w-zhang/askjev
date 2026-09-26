import type { Metadata, Viewport } from "next";
import { Inter_Tight, JetBrains_Mono, VT323 } from "next/font/google";
import "./globals.css";

// Free stand-ins for TypeSafe's type (docs/07-ui.md, Look): Die Grotesk C -> Inter Tight,
// LisaTerminal Paper -> VT323; JetBrains Mono is the real thing.
const sans = Inter_Tight({ subsets: ["latin"], variable: "--font-sans", weight: ["400", "500", "600"] });
const pixel = VT323({ subsets: ["latin"], variable: "--font-pixel", weight: "400" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", weight: ["300", "400"] });

export const metadata: Metadata = {
  title: "askjev",
  description: "A map of the closed questions people and programs ask, answered by Jev.",
};

export const viewport: Viewport = {
  themeColor: [{ media: "(prefers-color-scheme: dark)", color: "#1E1E1E" }, { color: "#DBF0FF" }],
  width: "device-width",
  initialScale: 1,
};

// Picks the theme before first paint (saved choice, else the system's), so dark mode never flashes light.
const THEME_SCRIPT = `try{var t=localStorage.getItem("askjev.theme");if(t!=="light"&&t!=="dark")t=matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";document.documentElement.dataset.theme=t}catch(e){document.documentElement.dataset.theme="light"}`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${sans.variable} ${pixel.variable} ${mono.variable}`} suppressHydrationWarning>
      <body>
        {/* first thing in <body>: browser extensions inject scripts into <head>, which would shift what
            React matches this against; its content is static, so skip comparing it on hydration */}
        <script dangerouslySetInnerHTML={{ __html: THEME_SCRIPT }} suppressHydrationWarning />
        {children}
      </body>
    </html>
  );
}
