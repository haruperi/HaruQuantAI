import { test, expect } from '@playwright/test';
import { appendFile } from 'node:fs/promises';
import path from 'node:path';
test('5000 visible candles pan and zoom frame budget', async ({ page }, testInfo) => {
  test.setTimeout(90000);
  await page.goto('/chart');
  const host = page.getByTestId('chart-canvas-host');
  await expect(host).toHaveAttribute('data-loading', 'false');
  await page.getByRole('button', { name: '5D', exact: true }).click();
  await page.getByLabel('Interval', { exact: true }).selectOption('1m');
  await expect(host).toHaveAttribute('data-loading', 'false');
  const canvas = page.getByTestId('chart-input'),
    rect = (await canvas.boundingBox())!;
  await page.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2);
  for (let i = 0; i < 4; i++) {
    const count = Number(await host.getAttribute('data-visible-bars'));
    if (count >= 4950 && count <= 5050) break;
    await page.mouse.wheel(0, -Math.log(count / 5000) / 0.0015);
    await page.waitForTimeout(120);
  }
  const count = Number(await host.getAttribute('data-visible-bars'));
  expect(count).toBeGreaterThanOrEqual(4900);
  expect(count).toBeLessThanOrEqual(5100);
  await page.mouse.move(rect.x + rect.width / 2, rect.y + rect.height / 2);
  await page.mouse.down();
  const result = await page.evaluate(async () => {
    const host = document.querySelector<HTMLElement>('[data-testid="chart-canvas-host"]')!,
      canvas = document.querySelector<HTMLCanvasElement>('[data-testid="chart-input"]')!,
      r = canvas.getBoundingClientRect();
    const frames: number[] = [],
      renders: number[] = [];
    let last = performance.now();
    const start = last;
    await new Promise<void>((resolve) => {
      function frame(now: number) {
        const elapsed = now - start;
        if (elapsed > 1000) {
          frames.push(now - last);
          renders.push(Number(host.dataset.renderMs));
        }
        last = now;
        canvas.dispatchEvent(
          new PointerEvent('pointermove', {
            bubbles: true,
            pointerId: 1,
            buttons: 1,
            clientX: r.left + r.width / 2 + Math.sin(elapsed / 300) * 60,
            clientY: r.top + r.height / 2,
          }),
        );
        if (elapsed > 11000) resolve();
        else requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    });
    frames.sort((a, b) => a - b);
    renders.sort((a, b) => a - b);
    return {
      frames: frames.length,
      medianMs: frames[Math.floor(frames.length * 0.5)],
      p95Ms: frames[Math.floor(frames.length * 0.95)],
      renderP95Ms: renders[Math.floor(renders.length * 0.95)],
      over25ms: frames.filter((v) => v > 25).length,
      viewport: [innerWidth, innerHeight],
      dpr: devicePixelRatio,
      userAgent: navigator.userAgent,
      candles: Number(host.dataset.visibleBars),
    };
  });
  await page.mouse.up();
  await testInfo.attach('frame-metrics', {
    body: JSON.stringify(result, null, 2),
    contentType: 'application/json',
  });
  await appendFile(
    path.resolve('../../.agents/logs/2026-09-25T180609_chart-platform/verification.md'),
    '\n## 5000-candle performance\n\n' + JSON.stringify(result, null, 2) + '\n',
  );
  expect(result.medianMs).toBeLessThanOrEqual(18);
  expect(result.p95Ms).toBeLessThanOrEqual(22);
});
