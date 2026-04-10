"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { matchesApi, teamsApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import { format } from "date-fns";
import { es } from "date-fns/locale";
import {
  Plus, Play, BarChart2, Upload, ChevronRight,
  Calendar, MapPin, Loader2
} from "lucide-react";
import Link from "next/link";

const STATUS_BADGE: Record<string, string> = {
  scheduled:  "bg-gray-700 text-gray-300",
  live:       "bg-red-900 text-red-300",
  recording:  "bg-yellow-900 text-yellow-300",
  processing: "bg-blue-900 text-blue-300",
  analyzed:   "bg-green-900 text-green-300",
  completed:  "bg-gray-800 text-gray-400",
};

export default function MatchesPage() {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ home_team_id: "", away_team_id: "", venue: "", scheduled_at: "" });

  const { data: matches = [], isLoading } = useQuery({
    queryKey: ["matches"],
    queryFn: () => matchesApi.list({ limit: 50 }).then(r => r.data),
  });
  const { data: teams = [] } = useQuery({
    queryKey: ["teams"],
    queryFn: () => teamsApi.list().then(r => r.data),
  });

  const createMatch = useMutation({
    mutationFn: () => matchesApi.create({
      home_team_id: form.home_team_id,
      away_team_id: form.away_team_id,
      venue: form.venue || undefined,
      scheduled_at: form.scheduled_at || undefined,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["matches"] }); setShowCreate(false); },
  });

  return (
    <AppShell>
      <div className="p-6 max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white">Partidos</h1>
            <p className="text-gray-400 text-sm mt-1">Gestiona y analiza todos tus partidos</p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 px-4 py-2 bg-pool-600 hover:bg-pool-500 rounded-lg text-white text-sm font-medium transition"
          >
            <Plus className="w-4 h-4" /> Nuevo Partido
          </button>
        </div>

        {/* Create modal */}
        {showCreate && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
              <h2 className="font-semibold text-white mb-4">Nuevo Partido</h2>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Equipo Local</label>
                  <select value={form.home_team_id} onChange={e => setForm({...form, home_team_id: e.target.value})}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-pool-500">
                    <option value="">Seleccionar…</option>
                    {(teams as any[]).map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Equipo Visitante</label>
                  <select value={form.away_team_id} onChange={e => setForm({...form, away_team_id: e.target.value})}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-pool-500">
                    <option value="">Seleccionar…</option>
                    {(teams as any[]).map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Sede</label>
                  <input value={form.venue} onChange={e => setForm({...form, venue: e.target.value})}
                    placeholder="Piscina Municipal…"
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-pool-500 placeholder-gray-500" />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Fecha y hora</label>
                  <input type="datetime-local" value={form.scheduled_at} onChange={e => setForm({...form, scheduled_at: e.target.value})}
                    className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-pool-500" />
                </div>
              </div>
              <div className="flex gap-3 mt-5">
                <button onClick={() => setShowCreate(false)} className="flex-1 py-2 border border-gray-700 rounded-lg text-sm text-gray-400 hover:text-white transition">Cancelar</button>
                <button
                  onClick={() => createMatch.mutate()}
                  disabled={!form.home_team_id || !form.away_team_id || createMatch.isPending}
                  className="flex-1 py-2 bg-pool-600 hover:bg-pool-500 disabled:opacity-40 rounded-lg text-sm text-white font-medium transition flex items-center justify-center gap-2"
                >
                  {createMatch.isPending && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  Crear
                </button>
              </div>
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center py-12"><Loader2 className="w-7 h-7 text-pool-400 animate-spin" /></div>
        ) : (matches as any[]).length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <Calendar className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p>No hay partidos. Crea el primero.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {(matches as any[]).map((m: any) => (
              <div key={m.id} className="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-center min-w-20">
                      <p className="text-3xl font-black text-white">{m.home_score} — {m.away_score}</p>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[m.status] || "bg-gray-700 text-gray-400"}`}>
                          {m.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                        {m.venue && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{m.venue}</span>}
                        {m.scheduled_at && (
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {format(new Date(m.scheduled_at), "d MMM yyyy HH:mm", { locale: es })}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link href={`/upload?match=${m.id}`}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition">
                      <Upload className="w-3.5 h-3.5" /> Video
                    </Link>
                    {m.status === "analyzed" && (
                      <Link href={`/analytics/${m.id}`}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-pool-800 text-pool-300 hover:bg-pool-700 rounded-lg transition">
                        <BarChart2 className="w-3.5 h-3.5" /> Análisis
                      </Link>
                    )}
                    <Link href={`/matches/${m.id}`}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition">
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
