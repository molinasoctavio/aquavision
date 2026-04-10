"use client";
import { useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { analyticsApi, matchesApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import PoolShotMap from "@/components/analytics/PoolShotMap";
import HeatmapViz from "@/components/analytics/HeatmapViz";
import MomentumChart from "@/components/analytics/MomentumChart";
import PassNetwork from "@/components/analytics/PassNetwork";
import CoachAssistPanel from "@/components/analytics/CoachAssistPanel";
import { BarChart2, Map, Activity, Users, MessageSquare, Loader2 } from "lucide-react";

type Tab = "overview" | "shots" | "heatmap" | "momentum" | "coach";

export default function AnalyticsPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const [tab, setTab] = useState<Tab>("overview");

  const { data: analytics, isLoading } = useQuery({
    queryKey: ["analytics", matchId],
    queryFn: () => analyticsApi.getMatchAnalytics(matchId).then(r => r.data),
  });
  const { data: shotMap } = useQuery({
    queryKey: ["shots", matchId],
    queryFn: () => analyticsApi.getShotMap(matchId).then(r => r.data),
    enabled: !!matchId,
  });
  const { data: playerStats = [] } = useQuery({
    queryKey: ["player-stats", matchId],
    queryFn: () => analyticsApi.getPlayerStats(matchId).then(r => r.data),
    enabled: !!matchId,
  });
  const { data: match } = useQuery({
    queryKey: ["match", matchId],
    queryFn: () => matchesApi.get(matchId).then(r => r.data),
  });

  const TABS = [
    { id: "overview", icon: BarChart2,      label: "Resumen"     },
    { id: "shots",    icon: Map,            label: "Lanzamientos"},
    { id: "heatmap",  icon: Activity,       label: "Heatmap"     },
    { id: "momentum", icon: Activity,       label: "Momentum"    },
    { id: "coach",    icon: MessageSquare,  label: "Coach AI"    },
  ] as const;

  if (isLoading) return (
    <AppShell>
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 text-pool-400 animate-spin" />
      </div>
    </AppShell>
  );

  if (!analytics) return (
    <AppShell>
      <div className="p-6 text-center text-gray-500">
        <BarChart2 className="w-10 h-10 mx-auto mb-2 opacity-30" />
        <p>Analytics no disponibles. El video aún se está procesando.</p>
      </div>
    </AppShell>
  );

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">Análisis del Partido</h1>
            <span className="text-xs bg-green-900 text-green-300 px-2 py-1 rounded-full">IA Completado</span>
          </div>
          {match && (
            <p className="text-gray-400 text-sm mt-1">
              {match.venue || "Sin sede"} · {match.home_score}–{match.away_score}
            </p>
          )}
        </div>

        {/* Scoreboard */}
        <div className="grid grid-cols-3 gap-4 mb-6 bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-1">Local</p>
            <p className="text-5xl font-black text-white">{match?.home_score ?? "–"}</p>
            <div className="mt-3 w-32 mx-auto h-2 bg-gray-800 rounded-full">
              <div className="h-full bg-pool-500 rounded-full" style={{ width: `${analytics.home_possession_pct}%` }} />
            </div>
            <p className="text-xs text-pool-400 mt-1">{analytics.home_possession_pct}% posesión</p>
          </div>
          <div className="flex flex-col items-center justify-center gap-2">
            <span className="text-2xl font-bold text-gray-500">VS</span>
            <div className="text-xs text-center space-y-1">
              {[
                ["Lanzam.", `${analytics.home_shots} – ${analytics.away_shots}`],
                ["Power Play", `${analytics.home_power_play_goals}/${analytics.home_power_play_attempts} – ${analytics.away_power_play_goals}/${analytics.away_power_play_attempts}`],
                ["Exclusiones", `${analytics.home_exclusions} – ${analytics.away_exclusions}`],
              ].map(([label, val]) => (
                <div key={label} className="text-gray-400">{label}: <span className="text-white">{val}</span></div>
              ))}
            </div>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-1">Visitante</p>
            <p className="text-5xl font-black text-white">{match?.away_score ?? "–"}</p>
            <div className="mt-3 w-32 mx-auto h-2 bg-gray-800 rounded-full">
              <div className="h-full bg-orange-500 rounded-full" style={{ width: `${analytics.away_possession_pct}%` }} />
            </div>
            <p className="text-xs text-orange-400 mt-1">{analytics.away_possession_pct}% posesión</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-900 border border-gray-800 rounded-xl p-1 mb-6">
          {TABS.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-medium transition ${
                tab === id ? "bg-pool-700 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              <Icon className="w-4 h-4" /> {label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {tab === "overview" && (
          <div className="space-y-6">
            {/* Quarter breakdown */}
            {analytics.quarter_stats && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <h3 className="font-semibold text-white mb-4">Por Período</h3>
                <div className="grid grid-cols-4 gap-3">
                  {Object.entries(analytics.quarter_stats).map(([period, stats]: [string, any]) => (
                    <div key={period} className="bg-gray-800 rounded-lg p-3 text-center">
                      <p className="text-xs text-gray-400 mb-2">{period}</p>
                      <p className="text-2xl font-bold text-white">{stats.home_goals}–{stats.away_goals}</p>
                      <p className="text-xs text-gray-500 mt-1">{stats.home_shots + stats.away_shots} tiros</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Player stats table */}
            {playerStats.length > 0 && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <h3 className="font-semibold text-white mb-4">Estadísticas por Jugador</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-gray-400 text-xs">
                        {["Jugador", "Goles", "Asist.", "Tiros", "Paradas", "Excl.", "Robos"].map(h => (
                          <th key={h} className="text-left pb-2 pr-4">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800">
                      {playerStats.map((ps: any) => (
                        <tr key={ps.id} className="text-gray-300">
                          <td className="py-2 pr-4 font-medium">{ps.player_id.slice(0, 8)}</td>
                          <td className="py-2 pr-4">{ps.goals}</td>
                          <td className="py-2 pr-4">{ps.assists}</td>
                          <td className="py-2 pr-4">{ps.shots}</td>
                          <td className="py-2 pr-4">{ps.saves}</td>
                          <td className="py-2 pr-4">{ps.exclusions_committed}</td>
                          <td className="py-2 pr-4">{ps.steals}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* AI Summary */}
            {analytics.ai_summary && (
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <MessageSquare className="w-4 h-4 text-pool-400" />
                  <h3 className="font-semibold text-white">Resumen IA</h3>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed">{analytics.ai_summary}</p>
              </div>
            )}
          </div>
        )}

        {tab === "shots" && <PoolShotMap shotData={shotMap} />}
        {tab === "heatmap" && (
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-400 mb-2 text-center">Local</p>
              <HeatmapViz data={analytics.heatmaps?.home} label="Local" />
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-2 text-center">Visitante</p>
              <HeatmapViz data={analytics.heatmaps?.away} label="Visitante" />
            </div>
          </div>
        )}
        {tab === "momentum" && (
          <MomentumChart data={analytics.momentum_timeline || []} />
        )}
        {tab === "coach" && (
          <CoachAssistPanel matchId={matchId} />
        )}
      </div>
    </AppShell>
  );
}
