import type { Metadata } from "next";
import "@/components/portrait/portrait.css";

export const metadata: Metadata = {
  title: "A self-portrait of Jev · askjev",
  description: "What 1.09 million closed questions say about Jev: indicators, not a benchmark.",
};

// The map's body never scrolls (it holds a full-screen canvas), so the portrait scrolls inside its own container.
export default function PortraitLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <div className="pt">{children}</div>;
}
