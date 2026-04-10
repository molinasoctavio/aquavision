"use client";
import { useRef, useEffect, useState } from "react";

interface Shot { x: number; y: number; outcome: string; period: string; is_power_play?: boolean; }
interface Props { shotData?: { shots: Shot[]; total_shots: number; goals: number; saves: number; misses: number; }; }

const OUTCOME_COLORS: Record<string, string> = {
  goal: "#FF6B35", saved: "#4CAF50", missed: "#9E9E9E", blocked: "#607D8B",
};

export default function PoolShotMap({ shotData }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !shotData?.shots) return;
    const ctx = canvas.getContext("2d")!;
    const W = canvas.width, H = canvas.height;

    // Pool background
    const grad = ctx.createLinearGradient(0, 0, 0, H);
    grad.addColorStop(0, "#0288d1");
    grad.addColorStop(1, "#01579b");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, W, H);

    // Pool lines
    ctx.strokeStyle = "rgba(255,255,255,0.4)";
    ctx.lineWidth = 1.5;

    // Center line
    ctx.beginPath(); ctx.moveTo(W/2, 0); ctx.lineTo(W/2, H); ctx.stroke();

    // 5m lines (16.67% from each end)
    const line5m = W * 0.1667;
    ctx.strokeStyle = "rgba(255,200,0,0.5)";
    ctx.setLineDash([6, 4]);
    ctx.beginPath(); ctx.moveTo(line5m, 0); ctx.lineTo(line5m, H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(W - line5m, 0); ctx.lineTo(W - line5m, H); ctx.stroke();

    // 2m lines (6.67%)
    const line2m = W * 0.0667;
    ctx.strokeStyle = "rgba(255,100,100,0.4)";
    ctx.beginPath(); ctx.moveTo(line2m, 0); ctx.lineTo(line2m, H); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(W - line2m, 0); ctx.lineTo(W - line2m, H); ctx.stroke();
    ctx.setLineDash([]);

    // Goals (at each end, centered vertically)
    ctx.fillStyle = "rgba(255,255,255,0.15)";
    ctx.strokeStyle = "rgba(255,255,255,0.6)";
    ctx.lineWidth = 2;
    const goalH = H * 0.33, goalW = W * 0.03;
    ctx.fillRect(0, (H - goalH)/2, goalW, goalH);
    ctx.strokeRect(0, (H - goalH)/2, goalW, goalH);
    ctx.fillRect(W - goalW, (H - goalH)/2, goalW, goalH);
    ctx.strokeRect(W - goalW, (H - goalH)/2, goalW, goalH);

    // Shots
    const shots = filter === "all" ? shotData.shots : shotData.shots.filter(s => s.outcome === filter);
    shots.forEach(s => {
      const x = s.x * W;
      const y = s.y * H;
      const color = OUTCOME_COLORS[s.outcome] || "#888";

      ctx.beginPath();
      ctx.arc(x, y, 7, 0, Math.PI * 2);
      ctx.fillStyle = color + "cc";
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Power play marker
      if (s.is_power_play) {
        ctx.beginPath();
        ctx.arc(x, y, 11, 0, Math.PI * 2);
        ctx.strokeStyle = "#9C27B0";
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    });
  }, [shotData, filter]);

  if (!shotData) return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
      Mapa de lanzamientos no disponible
    </div>
  );

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-white">Mapa de Lanzamientos</h3>
        <div className="flex gap-2">
          {["all", "goal", "saved", "missed"].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
                filter === f ? "bg-pool-700 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              {f === "all" ? "Todos" : f === "goal" ? "Goles" : f === "saved" ? "Parados" : "Fallados"}
            </button>
          ))}
        </div>
      </div>

      <div className="pool-map rounded-xl overflow-hidden">
        <canvas ref={canvasRef} width={600} height={200} className="w-full" />
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 text-xs">
        {Object.entries(OUTCOME_COLORS).map(([outcome, color]) => (
          <div key={outcome} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ background: color }} />
            <span className="text-gray-400 capitalize">{outcome === "saved" ? "Parado" : outcome === "goal" ? "Gol" : outcome === "missed" ? "Fallado" : "Bloqueado"}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-full border-2 border-purple-500 bg-transparent" />
          <span className="text-gray-400">Power Play</span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3 mt-4">
        {[
          { label: "Total", value: shotData.total_shots, color: "text-white" },
          { label: "Goles", value: shotData.goals, color: "text-orange-400" },
          { label: "Parados", value: shotData.saves, color: "text-green-400" },
          { label: "Fallados", value: shotData.misses, color: "text-gray-400" },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-gray-800 rounded-lg p-3 text-center">
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-gray-500">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
