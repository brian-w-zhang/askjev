import { simulate, type SimInput } from "./forceSim";

// Runs the Web layout's simulation off the main thread, so the page keeps animating while it settles.
self.onmessage = (e: MessageEvent<SimInput>) => {
  self.postMessage(simulate(e.data));
};
