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
  description: "Every closed question, placed on one tree and answered by Jev.",
};

export const viewport: Viewport = { themeColor: "#D6EAF8", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${sans.variable} ${pixel.variable} ${mono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
