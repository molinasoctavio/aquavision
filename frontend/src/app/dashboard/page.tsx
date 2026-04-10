"use client";
import { useQuery } from "@tanstack/react-query";
import { matchesApi, videosApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import { formatDuration, EVENT_COLORS } from "@/lib/utils";
import { Play, Upload, BarChart2, Clock, CheckCircle, Loader2, AlertCircle, Plus, Radio } from "lucide-react";
import Link from "next/link";
import { format } from "date-fns";
import { es } from "date-fns/locale";

const STATUS_CONFIG: Record<string, { color: string; icon: any; label: string }> = {
  ready:       { color: "text-green-400", icon: CheckCircle, label: "Listo"       },
  processing:  { color: "text-yellow-400", icon: Loader2,   label: "Procesando"  },
  analyzing:   { color: "text-blue-400",  icon: BarChart2,  label: "Analizando"  },
  uploading:   { color: "text-gray-400",  icon: Upload,     label: "Subiendo"    },
  error:       { color: "text-red-400",   icon: AlertCircle,label: "Error"       },
};

export default function DashboardPage() {
  const { data: matchesData } = useQuery({
    queryKey: ["matches"],
    queryFn: () => matchesApi.list({ limit: 10 }).then(r => r.data),
  });
  const { data: videosData } = useQuery({
    queryKey: ["videos-recent"],
    queryFn: () => videosApi.list({ limit: 10 }).then(r => r.data),
    refetchInterval: 10_000,
  });

  const matches: any[] = matchesData || [];
  const videos: any[] = videosData || [];

  const stats = [
    { label: "Partidos",  value: matches.length,                   icon: Play,     color: "from-blue-600 to-blue-800"   },
    { label: "Videos",    value: videos.length,                    icon: Upload,   color: "from-pool-600 to-pool-800"   },
    { label: "Analizados",value: videos.filter(v=>v.status==="ready").length, icon: BarChart2, color: "from-green-600 to-green-800" },
    { label: "Procesando",value: videos.filter(v=>["processing","analyzing","transcoding"].includes(v.status)).length, icon: Clock, color: "from-orange-600 to-orange-800" },
  ];

  return (
    <AppShell>
      <div className="p-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Dashboard</h1>
            <p className="text-gray-400 text-sm mt-1">Centro de control AquaVision</p>
          </div>
          <div className="flex gap-3">
            <Link href="/livestream" className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-white text-sm font-medium transition">
              <Radio className="w-4 h-4" /> En Vivo
            </Link>
            <Link href="/upload" className="flex items-center gap-2 px-4 py-2 bg-pool-600 hover:bg-pool-500 rounded-lg text-white text-sm font-medium transition">
              <Plus className="w-4 h-4" /> Subir Video
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {stats.map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center mb-3`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <p className="text-3xl font-bold text-white">{value}</p>
              <p className="text-gray-400 text-sm">{label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Videos */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-white">Videos Recientes</h2>
              <Link href="/upload" className="text-pool-400 text-sm hover:text-pool-300">Ver todos →</Link>
            </div>
            <div className="space-y-3">
              {videos.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Upload className="w-8 h-8 mx-auto mb-2 opacity-40" />
                  <p className="text-sm">Sube tu primer video</p>
                </div>
              )}
              {videos.map((v: any) => {
                const s = STATUS_CONFIG[v.status] ?? STATUS_CONFIG.processing;
                const SIcon = s.icon;
                return (
                  <div key={v.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-800 hover:bg-gray-750 transition">
                    {v.thumbnail_path ? (
                      <img src={`/api/v1/videos/${v.id}/thumbnail`} className="w-14 h-10 rounded object-cover bg-gray-700" alt="" />
                    ) : (
                      <div className="w-14 h-10 rounded bg-gray-700 flex items-center justify-center">
                        <Play className="w-4 h-4 text-gray-500" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{v.title}</p>
                      {v.duration_seconds && (
                        <p className="text-xs text-gray-400">{formatDuration(v.duration_seconds)}</p>
                      )}
                    </div>
                    <div className={`flex items-center gap-1.5 text-xs ${s.color}`}>
                      <SIcon className="w-3.5 h-3.5" />
                      <span>{s.label}</span>
                    </div>
                    {v.status === "ready" && (
                      <Link href={`/editor/${v.id}`} className="ml-2 text-pool-400 hover:text-pool-300">
                        <Play className="w-4 h-4" />
                      </Link>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Recent Matches */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-white">Partidos</h2>
              <Link href="/matches" className="text-pool-400 text-sm hover:text-pool-300">Ver todos →</Link>
            </div>
            <div className="space-y-3">
              {matches.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <BarChart2 className="w-8 h-8 mx-auto mb-2 opacity-40" />
                  <p className="text-sm">No hay partidos registrados</p>
                </div>
              )}
              {matches.map((m: any) => (
                <Link key={m.id} href={`/matches/${m.id}`}
                  className="flex items-center gap-3 p-3 rounded-lg bg-gray-800 hover:bg-gray-750 transition"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-white">
                        {m.home_score} — {m.away_score}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        m.status === "live" ? "bg-red-900 text-red-300" :
                        m.status === "analyzed" ? "bg-green-900 text-green-300" :
                        "bg-gray-700 text-gray-300"
                      }`}>{m.status}</span>
                    </div>
                    {m.venue && <p className="text-xs text-gray-400">{m.venue}</p>}
                  </div>
                  <div className="text-right">
                    {m.created_at && (
                      <p className="text-xs text-gray-400">
                        {format(new Date(m.created_at), "d MMM", { locale: es })}
                      </p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
