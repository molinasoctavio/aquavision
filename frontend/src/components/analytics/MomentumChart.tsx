"use client";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";
import { formatMs } from "@/lib/utils";

interface Props { data: { timestamp_ms: number; momentum: number }[]; }

export default function MomentumChart({ data }: Props) {
  if (!data.length) return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 text-center text-gray-500">
      Datos de momentum no disponibles
    </div>
  );

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <h3 className="font-semibold text-white mb-4">Momentum del Partido</h3>
      <p className="text-xs text-gray-400 mb-3">Positivo = ventaja local · Negativo = ventaja visitante</p>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="timestamp_ms"
            tickFormatter={(v) => formatMs(v)}
            tick={{ fill: "#6b7280", fontSize: 10 }}
          />
          <YAxis domain={[-100, 100]} tick={{ fill: "#6b7280", fontSize: 10 }} />
          <Tooltip
            formatter={(v: number) => [v > 0 ? `+${v} Local` : `${v} Visitante`, "Momentum"]}
            labelFormatter={(l) => formatMs(Number(l))}
            contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
          />
          <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="4 4" />
          <defs>
            <linearGradient id="momGradPos" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#03a9f4" stopOpacity={0.6} />
              <stop offset="95%" stopColor="#03a9f4" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="momGradNeg" x1="0" y1="1" x2="0" y2="0">
              <stop offset="5%" stopColor="#ff6b35" stopOpacity={0.6} />
              <stop offset="95%" stopColor="#ff6b35" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area type="monotone" dataKey="momentum" stroke="#03a9f4" fill="url(#momGradPos)" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
