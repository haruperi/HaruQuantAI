import { useEffect, useRef } from 'react';
import { useChart } from '../../hooks/useChartEngine';
export function Minimap() {
  const { engine } = useChart(),
    ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const timer = setInterval(() => {
      const c = ref.current,
        e = engine.current;
      if (!c || !e?.visible.length) return;
      c.width = c.clientWidth * devicePixelRatio;
      c.height = 36 * devicePixelRatio;
      const ctx = c.getContext('2d')!;
      ctx.scale(devicePixelRatio, devicePixelRatio);
      const bars = e.visible,
        step = Math.max(1, Math.floor(bars.length / c.clientWidth)),
        sample = bars.filter((_, i) => i % step === 0),
        low = Math.min(...sample.map((b) => b.close)),
        high = Math.max(...sample.map((b) => b.close));
      ctx.strokeStyle = '#787b86';
      ctx.beginPath();
      sample.forEach((b, i) => {
        const x = (i / (sample.length - 1)) * c.clientWidth,
          y = 32 - ((b.close - low) / (high - low || 1)) * 28;
        if (i) ctx.lineTo(x, y);
        else ctx.moveTo(x, y);
      });
      ctx.stroke();
      const left = Math.max(0, (-e.offset / e.spacing / bars.length) * c.clientWidth),
        width = (e.plotWidth / e.spacing / bars.length) * c.clientWidth;
      ctx.fillStyle = '#2962ff33';
      ctx.fillRect(left, 0, width, 36);
      ctx.strokeStyle = '#2962ff';
      ctx.strokeRect(left, 0, width, 36);
    }, 300);
    return () => clearInterval(timer);
  }, [engine]);
  return (
    <canvas
      className="cq-minimap"
      aria-label="History minimap"
      ref={ref}
      onPointerDown={(e) => {
        e.currentTarget.setPointerCapture(e.pointerId);
        const r = e.currentTarget.getBoundingClientRect();
        engine.current?.setWindow((e.clientX - r.left) / r.width);
      }}
      onPointerMove={(e) => {
        if (e.buttons) {
          const r = e.currentTarget.getBoundingClientRect();
          engine.current?.setWindow((e.clientX - r.left) / r.width);
        }
      }}
    />
  );
}
