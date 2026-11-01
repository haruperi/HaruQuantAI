/** Chart-anchored text and content annotations (prices/time always come from drawing anchors). */
import type { Drawing, ToolId, XY } from '../types';
import type { Primitive, Tool, Projection } from './types';
import { line, path, label } from './geometry';

export const textNoteSections: { title: string; ids: ToolId[] }[] = [
  { title: 'Text and Notes', ids: ['Text', 'Note', 'PriceNote', 'Pin', 'Table', 'Callout', 'Comment', 'PriceLabel', 'Signpost', 'FlagMark'] },
  { title: 'Content', ids: ['Image', 'Post', 'Idea'] },
];

export const textNoteIds = textNoteSections.flatMap(section => section.ids);
export const isTextNote = (id: ToolId): boolean => textNoteIds.includes(id);

const point = (drawing: Drawing, projection: Projection): XY =>
  projection.point(drawing.points[0] ?? { time: 0, price: 1 });
const caption = (drawing: Drawing, fallback: string): string => drawing.text.trim() || fallback;
const noteText = (drawing: Drawing, fallback: string): string =>
  caption(drawing, fallback).split('\n').slice(0, 12).map(line => line.slice(0, 100)).join('\n');
const edge = (x: number, y: number, w: number, h: number): Primitive =>
  path([{ x, y }, { x: x + w, y }, { x: x + w, y: y + h }, { x, y: y + h }], true, true);
const captionWidth = (value: string, min = 88, max = 290): number =>
  Math.min(max, Math.max(min, ...value.split('\n').map(line => line.length * 7 + 20)));
const card = (at: XY, value: string, minWidth = 112): Primitive[] => {
  const lines = value.split('\n'), w = captionWidth(value, minWidth);
  const h = Math.max(34, lines.length * 16 + 16);
  return [edge(at.x, at.y - 20, w, h), label({ x: at.x + 10, y: at.y }, value)];
};
const priced = (drawing: Drawing): string => drawing.points[0]?.price.toFixed(5) ?? '—';
function tool(labelText: string, build: Tool['build']): Tool {
  return { label: labelText, anchors: 1, group: 'Annotate', build };
}

export const Note = tool('Note', (d, p) => {
  const at = point(d, p), content = noteText(d, 'Note');
  return [line(at, { x: at.x + 20, y: at.y - 22 }), ...card({ x: at.x + 22, y: at.y - 22 }, content)];
});
export const PriceNote = tool('Price note', (d, p) => {
  const at = point(d, p);
  return [line(at, { x: at.x + 20, y: at.y - 25 }), ...card({ x: at.x + 20, y: at.y - 25 }, priced(d) + '\n' + noteText(d, 'Price note'))];
});
export const Pin = tool('Pin', (d, p) => {
  const at = point(d, p), center = { x: at.x, y: at.y - 14 };
  return [
    path([{ x: at.x, y: at.y }, { x: at.x - 9, y: at.y - 17 }]),
    { kind: 'ellipse', center, rx: 10, ry: 10 },
    path([{ x: at.x + 9, y: at.y - 17 }, at]),
    { kind: 'ellipse', center, rx: 3, ry: 3 },
    label({ x: at.x + 15, y: at.y - 15 }, noteText(d, 'Pin')),
  ];
});
export const Table = tool('Table', (d, p) => {
  const at = point(d, p);
  const rows = (d.text.trim() || 'Field | Value\nPrice | 0.00')
    .split('\n').slice(0, 8).map(row => row.split('|').slice(0, 6).map(cell => cell.trim().slice(0, 22)));
  const cols = Math.max(1, ...rows.map(row => row.length)), cellWidth = 90, rowHeight = 23;
  const w = cols * cellWidth, h = rows.length * rowHeight;
  const shapes: Primitive[] = [edge(at.x, at.y, w, h)];
  for (let col = 1; col < cols; col++)
    shapes.push(line({ x: at.x + col * cellWidth, y: at.y }, { x: at.x + col * cellWidth, y: at.y + h }));
  for (let row = 1; row < rows.length; row++)
    shapes.push(line({ x: at.x, y: at.y + row * rowHeight }, { x: at.x + w, y: at.y + row * rowHeight }));
  rows.forEach((row, i) => row.forEach((cell, j) => shapes.push(label({ x: at.x + j * cellWidth + 7, y: at.y + i * rowHeight + 16 }, cell))));
  return shapes;
});
export const Callout = tool('Callout', (d, p) => {
  const at = point(d, p), content = noteText(d, 'Callout');
  const w = captionWidth(content, 120), h = Math.max(34, content.split('\n').length * 16 + 16);
  const x = at.x + 18, y = at.y - h - 10;
  return [line(at, { x, y: y + h - 6 }), edge(x, y, w, h), label({ x: x + 10, y: y + 20 }, content)];
});
export const Comment = tool('Comment', (d, p) => {
  const at = point(d, p), content = noteText(d, 'Comment');
  return [...card(at, content, 115), line({ x: at.x + 13, y: at.y + 14 }, { x: at.x + 4, y: at.y + 26 })];
});
export const PriceLabel = tool('Price label', (d, p) => {
  const at = point(d, p);
  return [line(at, { x: at.x + 12, y: at.y - 22 }), ...card({ x: at.x + 12, y: at.y - 22 }, noteText(d, 'Price') + ' · ' + priced(d))];
});
export const Signpost = tool('Signpost', (d, p) => {
  const at = point(d, p), center = { x: at.x, y: at.y - 23 };
  return [line(at, { x: at.x, y: at.y - 11 }), { kind: 'ellipse', center, rx: 12, ry: 12 },
    label({ x: at.x - 4, y: at.y - 19 }, '★'),
    label({ x: at.x + 18, y: at.y - 20 }, noteText(d, 'Signpost'))];
});
export const FlagMark = tool('Flag mark', (d, p) => {
  const at = point(d, p);
  return [
    line(at, { x: at.x, y: at.y - 43 }),
    path([{ x: at.x, y: at.y - 43 }, { x: at.x + 34, y: at.y - 43 },
      { x: at.x + 27, y: at.y - 32 }, { x: at.x + 34, y: at.y - 21 }, { x: at.x, y: at.y - 21 }], true, true),
    label({ x: at.x + 39, y: at.y - 26 }, noteText(d, 'Flag')),
  ];
});
export const Image = tool('Image', (d, p) => {
  const at = point(d, p);
  const url = d.text.trim();
  if (/^https?:\/\/\S+$/i.test(url))
    return [{ kind: 'image', at, url, width: 184, height: 116 }];
  return [edge(at.x, at.y - 116, 184, 116),
    path([{ x: at.x + 12, y: at.y - 16 }, { x: at.x + 60, y: at.y - 70 },
      { x: at.x + 95, y: at.y - 38 }, { x: at.x + 130, y: at.y - 82 }, { x: at.x + 172, y: at.y - 16 }]),
    label({ x: at.x + 12, y: at.y - 91 }, 'Image · Set URL')];
});
export const Post = tool('Post', (d, p) => {
  const at = point(d, p);
  return [...card(at, '𝕏  Post\n' + noteText(d, 'Write post text…'), 184)];
});
export const Idea = tool('Idea', (d, p) => {
  const at = point(d, p);
  return [...card(at, '✦  Idea\n' + noteText(d, 'Write an idea…'), 176)];
});
