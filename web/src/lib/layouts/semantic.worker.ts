import { semantic } from "./semantic";
import type { LayoutInput } from "./common";

// Runs the Meaning layout (its overlap pass is ~0.5 s) off the main thread, so switching to it never freezes the page.
self.onmessage = (e: MessageEvent<LayoutInput>) => {
  self.postMessage(semantic(e.data));
};
