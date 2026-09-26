import { add, ballOf, basis, finish, hash01, kidsFn, len, mul, norm, relax, type Body, type LayoutInput, type Placed, type V3 } from "./common";

// Spiral galaxies: World, Self and Machine are three tilted disks. Each top-level topic (L1) is one
// logarithmic spiral arm, and each of its subtopics is a knot along that arm (its own subtree packed
// around it like a sunflower head), in reading order outward. The hemisphere's own questions are the
// bulge at the center.

const PITCH = (28 * Math.PI) / 180; // arm pitch angle: bigger winds less
const KNOT = 0.62; // sunflower spacing inside a knot, × the mean ball diameter
const GOLDEN = Math.PI * (3 - Math.sqrt(5));
const GALAXY_GAP = 10;

export function galaxy(inp: LayoutInput): Map<string, Placed> {
  const kids = kidsFn(inp);
  const hemis = kids(inp.rootId);
  const pos = new Map<string, V3>();
  const normalOf = new Map<string, V3>();
  const disks = hemis.map((h, hi) => {
    const a = hi * 2.1 + 0.4;
    const n = norm([0.35 * Math.cos(a), 0.8, 0.55 + 0.25 * Math.sin(a)]);
    const [e1, e2] = basis(n, hash01(h, 31) * Math.PI * 2);
    // disk coordinates (x, y in the plane, z along the normal), centered on the hemisphere
    const local = new Map<string, V3>();
    const core = ballOf(inp, h) * 1.3 + 2.5;
    local.set(h, [0, 0, 0]);
    const arms = kids(h);
    const tanP = Math.tan(PITCH), sinP = Math.sin(PITCH);
    arms.forEach((arm, ai) => {
      const phi = (ai / arms.length) * Math.PI * 2 + hash01(arm, 33) * 0.3;
      // position along the arm (distance s) → disk coordinates, plus the arm's in-plane "across" direction
      const onArm = (s: number): [V3, V3, V3] => {
        const r = core + s * sinP;
        const th = phi + Math.log(r / core) / tanP;
        const radial: V3 = [Math.cos(th), Math.sin(th), 0];
        const tangent: V3 = [-Math.sin(th), Math.cos(th), 0];
        return [mul(radial, r), norm(add(mul(radial, Math.cos(PITCH)), mul(tangent, -Math.sin(PITCH)))), norm(add(mul(radial, Math.sin(PITCH)), mul(tangent, Math.cos(PITCH))))];
      };
      const lift = (id: string, b: number, r: number) => (hash01(id, 37) - 0.5) * (0.8 + b) * Math.max(0.35, 1.4 - r / 60);
      local.set(arm, onArm(0)[0]);
      // each second-level topic is a knot on the arm: it sits on the spine and its whole subtree
      // spirals around it like a sunflower head, in reading order
      let s = ballOf(inp, arm) + 1.5;
      for (const knot of kids(arm)) {
        const members: string[] = [];
        const walk = (id: string) => kids(id).forEach((k) => { members.push(k); walk(k); });
        walk(knot);
        const kb = ballOf(inp, knot);
        const step = members.length ? (2 * members.reduce((t, m) => t + ballOf(inp, m), 0)) / members.length + 0.5 : 0;
        const rg = Math.max(kb, KNOT * step * Math.sqrt(members.length + 1));
        s += rg;
        const [c, across, along] = onArm(s);
        local.set(knot, add(c, [0, 0, lift(knot, kb, len(c))]));
        members.forEach((m, j) => {
          const rr = kb + KNOT * step * Math.sqrt(j + 1);
          const a = j * GOLDEN + hash01(knot, 39) * 6.283;
          const p = add(c, add(mul(across, rr * Math.cos(a)), mul(along, rr * Math.sin(a))));
          local.set(m, add(p, [0, 0, lift(m, ballOf(inp, m), len(c))]));
        });
        s += rg + 1;
      }
    });
    // resolve collisions, keeping everything close to the disk
    const ids = [...local.keys()];
    const bodies: Body[] = ids.map((id) => ({ p: local.get(id)!, r: ballOf(inp, id) * 1.1, fixed: id === h }));
    const maxH = (p: V3) => 1.2 + 3.5 * Math.exp(-len([p[0], p[1], 0]) / 25);
    relax(bodies, 60, 0.3, (_, p) => [p[0], p[1], Math.max(-maxH(p), Math.min(maxH(p), p[2]))]);
    let R = 0;
    ids.forEach((id, i) => {
      local.set(id, bodies[i].p);
      R = Math.max(R, len(bodies[i].p) + ballOf(inp, id) * 1.3);
    });
    return { h, n, e1, e2, local, R };
  });

  // Place the three galaxies on a slightly tilted triangle around the root, clear of each other.
  const tri = hemis.map((_, i) => norm([Math.cos(-Math.PI / 2 + (i * 2 * Math.PI) / 3), 0.12 * (i - 1), Math.sin(-Math.PI / 2 + (i * 2 * Math.PI) / 3)]) as V3);
  let D = 0;
  for (let i = 0; i < disks.length; i++) for (let j = i + 1; j < disks.length; j++)
    D = Math.max(D, (disks[i].R + disks[j].R + GALAXY_GAP) / Math.sqrt(3));
  D = Math.max(D, ballOf(inp, inp.rootId) * 2 + 10);
  pos.set(inp.rootId, [0, 0, 0]);
  disks.forEach((dk, i) => {
    const c = mul(tri[i], D);
    for (const [id, l] of dk.local) {
      pos.set(id, add(c, add(add(mul(dk.e1, l[0]), mul(dk.e2, l[1])), mul(dk.n, l[2]))));
      normalOf.set(id, dk.n);
    }
  });
  return finish(inp, pos, { halo: true, squash: 0.45, flatAxis: (id) => normalOf.get(id) });
}
