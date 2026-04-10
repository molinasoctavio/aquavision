"use client";
import { useRef, useEffect } from "react";

interface Props { data?: number[][]; label?: string; }

export default function HeatmapViz({ data, label }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;
    const ctx = canvas.getContext("2d")!;
    const W = canvas.width, H = canvas.height;
    const rows = data.length, cols = data[0]?.length || 30;
    const cellW = W / cols, cellH = H / rows;

    // Pool background
    ctx.fillStyle = "#0277bd";
    ctx.fillRect(0, 0, W, H);

    // Heatmap cells
    data.forEach((row, ri) => {
      row.forEach((val, ci) => {
        if (val <= 0) return;
        const alpha = Math.min(val, 1);
        const r = Math.round(255 * val);
        const g = Math.round(100 * (1 - val));
        const b = Math.round(50 * (1 - val));
        ctx.fillStyle = `rgba(${r},${g},${b},${alpha * 0.8})`;
        ctx.fillRect(ci * cellW, ri * cellH, cellW, cellH);
      });
    });

    // Grid lines subtle
    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= cols; i++) {
      ctx.beginPath(); ctx.moveTo(i * cellW, 0); ctx.lineTo(i * cellW, H); ctx.stroke();
    }
    for (let j = 0; j <= rows; j++) {
      ctx.beginPath(); ctx.moveTo(0, j * cellH); ctx.lineTo(W, j * cellH); ctx.stroke();
    }

    // Pool center line
    ctx.strokeStyle = "rgba(255,255,255,0.3)";
    ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(W/2, 0); ctx.lineTo(W/2, H); ctx.stroke();
  }, [data]);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      {label && <p className="text-xs text-gray-400 p-2 text-center">{label}</p>}
      <canvas
        ref={canvasRef}
        width={300}
        height={100}
        className="w-full"
      />
    </div>
  );
}
