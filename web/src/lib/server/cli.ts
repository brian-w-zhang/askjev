import "server-only";
import { spawn } from "node:child_process";
import { REPO_ROOT } from "./env";

/** Run `uv run askjev <args>` at the repo root and parse the last JSON object on stdout. */
export function askjev(args: string[], timeoutMs = 120_000): Promise<unknown> {
  return new Promise((resolve, reject) => {
    const p = spawn("uv", ["run", "--quiet", "askjev", ...args], { cwd: REPO_ROOT, env: process.env });
    let out = "";
    let err = "";
    const timer = setTimeout(() => {
      p.kill("SIGTERM");
      reject(new Error(`askjev ${args[0]} timed out after ${timeoutMs} ms`));
    }, timeoutMs);
    p.stdout.on("data", (d) => (out += d));
    p.stderr.on("data", (d) => (err += d));
    p.on("error", (e) => { clearTimeout(timer); reject(e); });
    p.on("close", (code) => {
      clearTimeout(timer);
      if (code !== 0) return reject(new Error(`askjev ${args[0]} exited ${code}: ${err.trim().split("\n").slice(-3).join(" | ")}`));
      const start = out.indexOf("{");
      const end = out.lastIndexOf("}");
      if (start < 0 || end < start) return reject(new Error(`askjev ${args[0]} printed no JSON: ${out.slice(0, 200)}`));
      try {
        resolve(JSON.parse(out.slice(start, end + 1)));
      } catch (e) {
        reject(new Error(`askjev ${args[0]} JSON parse failed: ${(e as Error).message}`));
      }
    });
  });
}
