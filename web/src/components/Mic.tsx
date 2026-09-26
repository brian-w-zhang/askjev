"use client";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";

// Speak a search (docs/07-ui.md, Search): the browser's own speech recognition (Web Speech API), free and
// keyless; words stream into the box as they're heard. Chrome, Edge and Safari have it (they run it on
// their own speech service); where it's missing (Firefox), the button doesn't appear.

interface Recognition {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}
type RecognitionCtor = new () => Recognition;

const ctor = (): RecognitionCtor | undefined => {
  const w = window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
};

const noSubscribe = () => () => {};

export function Mic({ onText }: { onText: (text: string) => void }) {
  // the server can't know, so it renders nothing and the browser fills the button in after hydrating
  const supported = useSyncExternalStore(noSubscribe, () => !!ctor(), () => false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const rec = useRef<Recognition | null>(null);

  useEffect(() => () => rec.current?.stop(), []);

  const toggle = () => {
    if (listening) return rec.current?.stop();
    const Ctor = ctor();
    if (!Ctor) return;
    const r = new Ctor();
    r.lang = navigator.language || "en-US";
    r.interimResults = true;
    r.continuous = false; // stop at the first pause, like a search box
    r.onresult = (e) => onText(Array.from(e.results, (res) => res[0]?.transcript ?? "").join("").trim());
    r.onerror = (e) => setError(e.error === "not-allowed" ? "Microphone access is blocked" : e.error === "no-speech" ? null : `Speech input failed (${e.error})`);
    r.onend = () => setListening(false);
    rec.current = r;
    setError(null);
    setListening(true);
    r.start();
  };

  if (!supported) return null;
  return (
    <button
      type="button"
      className="mic"
      data-on={listening}
      onClick={toggle}
      aria-pressed={listening}
      aria-label={listening ? "Stop listening" : "Search by voice"}
      title={error ?? (listening ? "Listening… click to stop" : "Search by voice")}
    >
      <svg viewBox="0 0 16 16" aria-hidden shapeRendering="crispEdges">
        <path d="M6 2h4v7H6z M4 7v2a4 4 0 0 0 8 0V7 M8 13v2 M5.5 15h5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    </button>
  );
}
