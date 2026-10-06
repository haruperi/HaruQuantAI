import type { XY } from '../types';
import type { Primitive } from './types';
export const path = (points: XY[], closed = false, fill = false): Primitive => ({
  kind: 'path',
  points,
  closed,
  fill,
});
export const label = (at: XY, text: string): Primitive => ({ kind: 'text', at, text });
export function line(
  a: XY,
  b: XY,
  left = false,
  right = false,
  width = 1000,
  height = 1000,
): Primitive {
  const dx = b.x - a.x,
    dy = b.y - a.y,
    length = Math.hypot(dx, dy) || 1,
    factor = ((width + height) * 4) / length;
  return path([
    left ? { x: a.x - dx * factor, y: a.y - dy * factor } : a,
    right ? { x: b.x + dx * factor, y: b.y + dy * factor } : b,
  ]);
}
export function segmentDistance(p: XY, a: XY, b: XY): number {
  const dx = b.x - a.x,
    dy = b.y - a.y,
    t = Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / (dx * dx + dy * dy || 1)));
  return Math.hypot(p.x - a.x - t * dx, p.y - a.y - t * dy);
}
export function primitiveHit(shape: Primitive, p: XY): boolean {
  if (shape.kind === 'text')
    return (
      p.x >= shape.at.x - 4 &&
      p.x <= shape.at.x + Math.max(30, shape.text.length * 7) &&
      Math.abs(p.y - shape.at.y) < 18
    );
  if (shape.kind === 'ellipse') {
    const r = Math.hypot(
      (p.x - shape.center.x) / (shape.rx || 1),
      (p.y - shape.center.y) / (shape.ry || 1),
    );
    return r <= 1.15;
  }
  const points = shape.closed ? [...shape.points, shape.points[0]] : shape.points;
  if (shape.closed && shape.fill) {
    let inside = false;
    for (let i = 0, j = shape.points.length - 1; i < shape.points.length; j = i++) {
      const a = shape.points[i],
        b = shape.points[j];
      if (a.y > p.y !== b.y > p.y && p.x < ((b.x - a.x) * (p.y - a.y)) / (b.y - a.y) + a.x)
        inside = !inside;
    }
    if (inside) return true;
  }
  return points.some((b, i) => i > 0 && segmentDistance(p, points[i - 1], b) < 7);
}
export function paint(ctx: CanvasRenderingContext2D, shapes: Primitive[]): void {
  for (const shape of shapes) {
    ctx.beginPath();
    if (shape.kind === 'text') {
      ctx.fillText(shape.text, shape.at.x, shape.at.y);
      continue;
    }
    if (shape.kind === 'ellipse')
      ctx.ellipse(
        shape.center.x,
        shape.center.y,
        Math.max(0.1, shape.rx),
        Math.max(0.1, shape.ry),
        0,
        0,
        Math.PI * 2,
      );
    else {
      shape.points.forEach((p, i) => (i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)));
      if (shape.closed) ctx.closePath();
    }
    if (shape.kind === 'ellipse' || shape.fill) {
      ctx.save();
      ctx.globalAlpha *= 0.12;
      ctx.fill();
      ctx.restore();
    }
    ctx.stroke();
  }
}
