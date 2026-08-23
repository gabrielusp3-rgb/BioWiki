import { Curve, Vector3 } from "three";

/**
 * Procedural single-strand helix curve.
 * Sweeps a point around the Y axis while translating vertically, producing one
 * sugar-phosphate backbone. The second strand is the same curve with `phase = PI`.
 * No imported models — the geometry is generated entirely from these parameters.
 */
export class HelixCurve extends Curve<Vector3> {
  private readonly turns: number;
  private readonly radius: number;
  private readonly height: number;
  private readonly phase: number;

  constructor(turns: number, radius: number, height: number, phase = 0) {
    super();
    this.turns = turns;
    this.radius = radius;
    this.height = height;
    this.phase = phase;
  }

  getPoint(t: number, optionalTarget = new Vector3()): Vector3 {
    const angle = this.phase + t * this.turns * Math.PI * 2;
    const x = Math.cos(angle) * this.radius;
    const z = Math.sin(angle) * this.radius;
    const y = (t - 0.5) * this.height;
    return optionalTarget.set(x, y, z);
  }
}
