"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, type ComponentProps } from "react";

// The site's nav links (map, portrait, atlas): the next page is fetched ahead, so switching is instant. Not as soon
// as the link is on screen (the portrait and atlas are half a megabyte or more each, too much to fetch unasked on a
// phone), but when the visitor shows intent (hover, touch, keyboard focus) and, with `idle`, once the page has
// settled on a fast connection that isn't saving data.
type Conn = { saveData?: boolean; effectiveType?: string };

export default function NavLink({ href, idle = false, ...rest }: ComponentProps<typeof Link> & { href: string; idle?: boolean }) {
  const router = useRouter();
  const warm = () => router.prefetch(href);
  useEffect(() => {
    if (!idle) return;
    const c = (navigator as Navigator & { connection?: Conn }).connection;
    if (c?.saveData || (c?.effectiveType && c.effectiveType !== "4g")) return;
    const ric = window.requestIdleCallback ?? ((f: () => void) => window.setTimeout(f, 1));
    const t = window.setTimeout(() => ric(() => router.prefetch(href)), 2500);
    return () => window.clearTimeout(t);
  }, [idle, href, router]);
  return <Link href={href} prefetch={false} onPointerEnter={warm} onTouchStart={warm} onFocus={warm} {...rest} />;
}
