/**
 * Geometry + selection helpers for the morphing-polygon loader.
 * All functions are pure (no DOM, no global state) so they are unit-testable.
 */

export interface PolygonMorphKeyframes {
  values: string;
  keyTimes: string;
  durationMs: number;
}

/**
 * Radius of a regular n-gon's edge at angle `theta` (apothem-based), supporting
 * a fractional number of sides. The apothem of a unit-circumradius polygon is
 * `cos(pi / n)`; the edge distance at an angle measured from a vertex follows the
 * sawtooth `apothem / cos(angle mod sector - sector/2)`.
 */
export function polygonRadiusAt(theta: number, sides: number, radius: number): number {
  const n = Math.max(3, sides);
  const sector = (2 * Math.PI) / n;
  const apothem = Math.cos(Math.PI / n);
  // Fold theta into a single sector, centered on the sector midpoint.
  const a = ((theta % sector) + sector) % sector;
  const edgeAngle = a - sector / 2;
  return (radius * apothem) / Math.cos(edgeAngle);
}

/**
 * Build a closed SVG path `d` for a regular polygon with a (possibly fractional)
 * side count, sampled at a fixed resolution so morphing between vertex counts is
 * smooth (the command count never changes → no popping).
 */
export function polygonPath(
  sides: number,
  radius: number,
  rotation: number,
  cx: number,
  cy: number,
  samples = 120,
): string {
  const n = Math.max(3, sides);
  const count = Math.max(3, Math.floor(samples));
  let d = '';
  for (let i = 0; i < count; i++) {
    const theta = (i / count) * 2 * Math.PI;
    const r = polygonRadiusAt(theta, n, radius);
    const x = cx + r * Math.cos(theta + rotation);
    const y = cy + r * Math.sin(theta + rotation);
    d += `${i === 0 ? 'M' : 'L'}${x.toFixed(3)} ${y.toFixed(3)}`;
    if (i < count - 1) d += ' ';
  }
  return `${d} Z`;
}

/**
 * Build SVG animation keyframes for a dwell-then-morph polygon sequence.
 * Repeating identical paths across dwell boundaries lets SVG interpolation hold
 * a shape without any JS-driven frame updates.
 */
export function polygonMorphKeyframes(
  sideSequence: readonly number[],
  dwellMs: number,
  morphMs: number,
  radius: number,
  rotation: number,
  cx: number,
  cy: number,
  samples = 120,
): PolygonMorphKeyframes {
  const sequence = sideSequence.length > 0 ? sideSequence : [3];
  const stepMs = dwellMs + morphMs;
  const durationMs = sequence.length * stepMs;
  const values: string[] = [];
  const keyTimes: string[] = [];

  values.push(polygonPath(sequence[0], radius, rotation, cx, cy, samples));
  keyTimes.push('0');

  for (let i = 0; i < sequence.length; i++) {
    const from = sequence[i];
    const to = sequence[(i + 1) % sequence.length];
    const stepOffsetMs = i * stepMs;
    const dwellEnd = (stepOffsetMs + dwellMs) / durationMs;
    const morphEnd = (stepOffsetMs + stepMs) / durationMs;

    values.push(polygonPath(from, radius, rotation, cx, cy, samples));
    keyTimes.push(dwellEnd.toFixed(4));

    values.push(polygonPath(to, radius, rotation, cx, cy, samples));
    keyTimes.push(morphEnd.toFixed(4));
  }

  return {
    values: values.join(';'),
    keyTimes: keyTimes.join(';'),
    durationMs,
  };
}

/**
 * Pick a random index in [0, length) that is not `prev`.
 * Returns 0 when `length <= 1`. `rand` is injectable for deterministic tests.
 */
export function pickNextIndex(length: number, prev: number, rand: () => number = Math.random): number {
  if (length <= 1) return 0;
  let next = Math.floor(rand() * length);
  if (next >= length) next = length - 1;
  if (next === prev) next = (next + 1) % length;
  return next;
}
