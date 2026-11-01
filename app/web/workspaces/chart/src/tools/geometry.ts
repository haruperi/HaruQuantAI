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
  if (shape.kind === 'image')
    return p.x >= shape.at.x && p.x <= shape.at.x + shape.width &&
      p.y >= shape.at.y - shape.height && p.y <= shape.at.y;
  if (shape.kind === 'badge')
    return Math.abs(p.x - shape.at.x) < 100 && Math.abs(p.y - shape.at.y) < 18;
  if (shape.kind === 'text') {
    const rows = shape.text.split('\n');
    return p.x >= shape.at.x - 4 &&
      p.x <= shape.at.x + Math.max(30, ...rows.map(row => row.length * 7)) &&
      p.y >= shape.at.y - 18 && p.y <= shape.at.y + (rows.length - 1) * 16 + 5;
  }
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
  return points.some(
    (b, i) =>
      i > 0 && segmentDistance(p, points[i - 1], b) < Math.max(7, (shape.strokeWidth ?? 0) / 2 + 2),
  );
}
type CachedImage = { image: HTMLImageElement; state: 'loading' | 'ready' | 'failed'; notify: Set<() => void> };
const images = new Map<string, CachedImage>();
function getImage(url: string, onLoad?: () => void): CachedImage | null {
  if (!/^https?:\/\/\S+$/i.test(url) || typeof Image === 'undefined') return null;
  const cached = images.get(url);
  if (cached) {
    if (onLoad && cached.state === 'loading') cached.notify.add(onLoad);
    return cached;
  }
  // Keep the resource cache bounded. Images are loaded via CORS to avoid tainting the chart canvas.
  if (images.size > 64) {
    const oldest = images.keys().next().value;
    if (oldest) images.delete(oldest);
  }
  const image = new Image();
  const entry: CachedImage = { image, state: 'loading', notify: new Set(onLoad ? [onLoad] : []) };
  images.set(url, entry);
  image.crossOrigin = 'anonymous';
  image.onload = () => {
    entry.state = 'ready';
    for (const listener of entry.notify) listener();
    entry.notify.clear();
  };
  image.onerror = () => {
    entry.state = 'failed';
    for (const listener of entry.notify) listener();
    entry.notify.clear();
  };
  image.src = url;
  return entry;
}
export function paint(ctx: CanvasRenderingContext2D, shapes: Primitive[], onAssetLoad?: () => void): void {
  for (const shape of shapes) {
    ctx.save();
    if (shape.color) {
      ctx.strokeStyle = shape.color;
      ctx.fillStyle = shape.color;
    }
    if (shape.strokeWidth) ctx.lineWidth = shape.strokeWidth;
    if (shape.strokeOpacity !== undefined) ctx.globalAlpha *= shape.strokeOpacity;
    if (shape.lineCap) ctx.lineCap = shape.lineCap;
    if (shape.dash) ctx.setLineDash(shape.dash);
    ctx.beginPath();
    if (shape.kind === 'badge') {
      const lines = shape.text.split('\n');
      const width = Math.max(...lines.map((text) => ctx.measureText(text).width)) + 12;
      const height = lines.length * 15 + 8;
      const x = shape.at.x - width / 2,
        y = shape.at.y - height / 2;
      ctx.setLineDash([]);
      ctx.fillStyle = shape.background;
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1;
      ctx.roundRect(x, y, width, height, 4);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'center';
      lines.forEach((text, i) => ctx.fillText(text, shape.at.x, y + 16 + i * 15));
      ctx.restore();
      continue;
    }
    if (shape.kind === 'image') {
      const entry = getImage(shape.url, onAssetLoad);
      const x = shape.at.x, y = shape.at.y - shape.height;
      ctx.strokeRect(x, y, shape.width, shape.height);
      if (entry?.state === 'ready') ctx.drawImage(entry.image, x, y, shape.width, shape.height);
      else ctx.fillText(entry?.state === 'failed' ? 'Image unavailable' : 'Loading image…', x + 10, y + 23);
      ctx.restore();
      continue;
    }
    if (shape.kind === 'text') {
      shape.text.split('\n').forEach((row, i) => ctx.fillText(row, shape.at.x, shape.at.y + i * 16));
      ctx.restore();
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
      ctx.globalAlpha *= shape.fillOpacity ?? 0.12;
      ctx.fill();
      ctx.restore();
    }
    ctx.stroke();
    ctx.restore();
  }
}
