import type { ChartEngine } from './ChartEngine';
import type { ChartStore } from '../store/chartStore';
export async function fullscreen(root: HTMLElement | null, store: ChartStore) {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else if (root) await root.requestFullscreen();
  } catch {
    store
      .getState()
      .setUI({ toast: 'Fullscreen was blocked by this browser. Try its fullscreen command.' });
  }
}
export async function exportChart(
  root: HTMLElement | null,
  engine: ChartEngine | null,
  store: ChartStore,
) {
  if (!root || !engine) return;
  try {
    await document.fonts.ready;
    const bounds = root.getBoundingClientRect(),
      scale = window.devicePixelRatio || 1;
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(bounds.width * scale);
    canvas.height = Math.round(bounds.height * scale);
    const ctx = canvas.getContext('2d')!;
    ctx.scale(scale, scale);
    async function draw(element: Element): Promise<void> {
      const style = getComputedStyle(element),
        rect = element.getBoundingClientRect();
      if (
        style.display === 'none' ||
        style.visibility === 'hidden' ||
        Number(style.opacity) === 0 ||
        !rect.width ||
        !rect.height
      )
        return;
      const x = rect.left - bounds.left,
        y = rect.top - bounds.top;
      if (x > bounds.width || y > bounds.height || x + rect.width < 0 || y + rect.height < 0)
        return;
      ctx.save();
      ctx.globalAlpha = Number(style.opacity);
      ctx.fillStyle = style.backgroundColor;
      ctx.fillRect(x, y, rect.width, rect.height);
      if (parseFloat(style.borderTopWidth)) {
        ctx.strokeStyle = style.borderTopColor;
        ctx.lineWidth = parseFloat(style.borderTopWidth);
        ctx.strokeRect(x, y, rect.width, rect.height);
      }
      if (element instanceof HTMLCanvasElement) {
        ctx.drawImage(element, x, y, rect.width, rect.height);
        ctx.restore();
        return;
      }
      if (element instanceof SVGElement) {
        const copy = element.cloneNode(true) as SVGElement;
        copy.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
        copy.setAttribute('color', style.color);
        const blob = new Blob([new XMLSerializer().serializeToString(copy)], {
            type: 'image/svg+xml',
          }),
          url = URL.createObjectURL(blob);
        try {
          const image = new Image();
          image.src = url;
          await image.decode();
          ctx.drawImage(image, x, y, rect.width, rect.height);
        } finally {
          URL.revokeObjectURL(url);
        }
        ctx.restore();
        return;
      }
      ctx.fillStyle = style.color;
      ctx.font = style.font || style.fontSize + ' ' + style.fontFamily;
      ctx.textBaseline = 'middle';
      if (element instanceof HTMLInputElement || element instanceof HTMLSelectElement) {
        const value =
          element instanceof HTMLSelectElement ? element.selectedOptions[0]?.text : element.value;
        ctx.fillText(
          value ?? '',
          x + parseFloat(style.paddingLeft || '4'),
          y + rect.height / 2,
          rect.width - 8,
        );
      } else
        for (const node of element.childNodes) {
          if (node.nodeType === Node.TEXT_NODE && node.textContent?.trim()) {
            const range = document.createRange();
            range.selectNodeContents(node);
            const r = range.getBoundingClientRect();
            ctx.fillText(
              node.textContent.trim(),
              r.left - bounds.left,
              r.top - bounds.top + r.height / 2,
            );
          } else if (node instanceof Element) await draw(node);
        }
      ctx.restore();
    }
    await draw(root);
    const blob = await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob(
        (b) => (b ? resolve(b) : reject(new Error('PNG encoding failed'))),
        'image/png',
      ),
    );
    const url = URL.createObjectURL(blob),
      link = document.createElement('a');
    link.download = store.getState().chart.symbol + '-chart.png';
    link.href = url;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    store.getState().setUI({ toast: 'Chart image exported as PNG.' });
  } catch (error) {
    store
      .getState()
      .setUI({ toast: error instanceof Error ? error.message : 'Image export failed.' });
  }
}
