"use client";
import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { videosApi, matchesApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import { formatFileSize, formatDuration } from "@/lib/utils";
import {
  Upload, Link as LinkIcon, Youtube, Wifi, CheckCircle,
  AlertCircle, Loader2, Film, X, Play, Eye,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useInterval } from "@/hooks/useInterval";

type UploadMode = "file" | "url" | "stream";
type UploadStatus = "idle" | "uploading" | "processing" | "ready" | "error";

interface UploadItem {
  id: string;
  name: string;
  size?: number;
  status: UploadStatus;
  progress: number;
  videoId?: string;
  error?: string;
  duration?: number;
}

export default function UploadPage() {
  const router = useRouter();
  const qc = useQueryClient();
  const [mode, setMode] = useState<UploadMode>("file");
  const [items, setItems] = useState<UploadItem[]>([]);
  const [urlInput, setUrlInput] = useState("");
  const [selectedMatch, setSelectedMatch] = useState("");
  const [title, setTitle] = useState("");

  const { data: matchesData } = useQuery({
    queryKey: ["matches"],
    queryFn: () => matchesApi.list({ limit: 50 }).then(r => r.data),
  });
  const matches: any[] = matchesData || [];

  // Poll status for in-progress items
  useInterval(() => {
    items.forEach(async (item) => {
      if (item.videoId && ["processing", "analyzing", "transcoding", "generating_hls"].includes(item.status)) {
        try {
          const res = await videosApi.getStatus(item.videoId);
          const s = res.data;
          setItems(prev => prev.map(i =>
            i.id === item.id
              ? { ...i, status: s.status === "ready" ? "ready" : s.status, progress: Math.round(s.progress * 100) }
              : i
          ));
        } catch {}
      }
    });
  }, 3000);

  const uploadFile = useCallback(async (file: File) => {
    const itemId = Math.random().toString(36).slice(2);
    const item: UploadItem = {
      id: itemId,
      name: file.name,
      size: file.size,
      status: "uploading",
      progress: 0,
    };
    setItems(prev => [item, ...prev]);

    try {
      const form = new FormData();
      form.append("file", file);
      form.append("title", title || file.name.replace(/\.[^.]+$/, ""));
      if (selectedMatch) form.append("match_id", selectedMatch);

      const res = await videosApi.upload(form, (pct) => {
        setItems(prev => prev.map(i => i.id === itemId ? { ...i, progress: pct } : i));
      });

      setItems(prev => prev.map(i =>
        i.id === itemId
          ? { ...i, status: "processing", progress: 0, videoId: res.data.id }
          : i
      ));
      qc.invalidateQueries({ queryKey: ["videos-recent"] });
    } catch (e: any) {
      setItems(prev => prev.map(i =>
        i.id === itemId
          ? { ...i, status: "error", error: e.response?.data?.detail || "Error al subir" }
          : i
      ));
    }
  }, [title, selectedMatch, qc]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { "video/*": [".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"] },
    onDrop: (files) => files.forEach(uploadFile),
    multiple: true,
  });

  const handleUrlIngest = async () => {
    if (!urlInput.trim()) return;
    const itemId = Math.random().toString(36).slice(2);
    setItems(prev => [{ id: itemId, name: urlInput, status: "uploading", progress: 0 }, ...prev]);
    try {
      const res = await videosApi.ingestUrl({
        url: urlInput,
        title: title || "Video desde URL",
        match_id: selectedMatch || undefined,
      });
      setItems(prev => prev.map(i =>
        i.id === itemId ? { ...i, status: "processing", videoId: res.data.id } : i
      ));
      setUrlInput("");
    } catch (e: any) {
      setItems(prev => prev.map(i =>
        i.id === itemId ? { ...i, status: "error", error: "No se pudo descargar" } : i
      ));
    }
  };

  return (
    <AppShell>
      <div className="p-6 max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">Subir Video</h1>
          <p className="text-gray-400 text-sm mt-1">Sube desde tu dispositivo, YouTube, o conecta una transmisión en vivo</p>
        </div>

        {/* Options */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          {([
            { id: "file",   icon: Upload,  label: "Archivo",  desc: "MP4, MOV, AVI…" },
            { id: "url",    icon: LinkIcon, label: "URL / YouTube", desc: "Link directo" },
            { id: "stream", icon: Wifi,    label: "Stream",   desc: "RTMP / RTSP" },
          ] as const).map(opt => (
            <button
              key={opt.id}
              onClick={() => setMode(opt.id)}
              className={`p-4 rounded-xl border text-left transition-all ${
                mode === opt.id
                  ? "border-pool-500 bg-pool-950/50 shadow-lg shadow-pool-900/30"
                  : "border-gray-800 bg-gray-900 hover:border-gray-600"
              }`}
            >
              <opt.icon className={`w-5 h-5 mb-2 ${mode === opt.id ? "text-pool-400" : "text-gray-400"}`} />
              <p className="font-medium text-white text-sm">{opt.label}</p>
              <p className="text-xs text-gray-500 mt-0.5">{opt.desc}</p>
            </button>
          ))}
        </div>

        {/* Match selector + title */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Partido (opcional)</label>
            <select
              value={selectedMatch}
              onChange={e => setSelectedMatch(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-pool-500"
            >
              <option value="">Sin partido</option>
              {matches.map((m: any) => (
                <option key={m.id} value={m.id}>
                  Partido {m.home_score}–{m.away_score} ({m.status})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Título</label>
            <input
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Ej. Final Liga 2024"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-pool-500 placeholder-gray-500"
            />
          </div>
        </div>

        {/* Upload zone */}
        {mode === "file" && (
          <div
            {...getRootProps()}
            className={`upload-zone rounded-2xl p-12 text-center cursor-pointer transition-all ${isDragActive ? "drag-active" : ""}`}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-gray-800 flex items-center justify-center">
                <Upload className={`w-8 h-8 ${isDragActive ? "text-pool-400" : "text-gray-400"}`} />
              </div>
              <div>
                <p className="text-white font-medium">
                  {isDragActive ? "Suelta los archivos aquí" : "Arrastra tus videos aquí"}
                </p>
                <p className="text-gray-500 text-sm mt-1">o haz clic para seleccionar</p>
                <p className="text-gray-600 text-xs mt-3">MP4 · MOV · AVI · MKV · WebM — hasta 10 GB</p>
              </div>
            </div>
          </div>
        )}

        {mode === "url" && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <label className="block text-sm text-gray-400 mb-2">URL del video</label>
            <div className="flex gap-3">
              <div className="relative flex-1">
                <Youtube className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-red-500" />
                <input
                  value={urlInput}
                  onChange={e => setUrlInput(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleUrlIngest()}
                  placeholder="https://youtube.com/watch?v=... o enlace directo"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 pl-10 text-white text-sm focus:outline-none focus:ring-2 focus:ring-pool-500 placeholder-gray-500"
                />
              </div>
              <button
                onClick={handleUrlIngest}
                disabled={!urlInput.trim()}
                className="px-5 py-2.5 bg-pool-600 hover:bg-pool-500 disabled:opacity-40 text-white text-sm font-medium rounded-lg transition"
              >
                Descargar
              </button>
            </div>
            <p className="text-gray-600 text-xs mt-3">Compatible con YouTube, Vimeo, y enlaces directos MP4</p>
          </div>
        )}

        {mode === "stream" && (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-6">
            <p className="text-gray-400 text-sm mb-4">Conecta tu cámara o codificador RTMP:</p>
            <div className="bg-gray-800 rounded-lg p-4 font-mono text-sm">
              <p className="text-gray-400">URL RTMP:</p>
              <p className="text-pool-400">rtmp://localhost:1935/live</p>
              <p className="text-gray-400 mt-2">Stream Key:</p>
              <p className="text-white">aquavision-{Math.random().toString(36).slice(2, 10)}</p>
            </div>
            <Link href="/livestream" className="mt-4 inline-flex items-center gap-2 text-pool-400 text-sm hover:text-pool-300">
              Ir al panel de transmisión →
            </Link>
          </div>
        )}

        {/* Upload queue */}
        {items.length > 0 && (
          <div className="mt-6 space-y-3">
            <h3 className="text-sm font-medium text-gray-300">Cola de subida</h3>
            {items.map(item => (
              <UploadQueueItem key={item.id} item={item} onRemove={() => setItems(prev => prev.filter(i => i.id !== item.id))} />
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}

function UploadQueueItem({ item, onRemove }: { item: UploadItem; onRemove: () => void }) {
  const icons = {
    idle:       <Film className="w-5 h-5 text-gray-500" />,
    uploading:  <Loader2 className="w-5 h-5 text-pool-400 animate-spin" />,
    processing: <Loader2 className="w-5 h-5 text-yellow-400 animate-spin" />,
    ready:      <CheckCircle className="w-5 h-5 text-green-400" />,
    error:      <AlertCircle className="w-5 h-5 text-red-400" />,
  };
  const labels = {
    idle: "", uploading: `Subiendo ${item.progress}%`,
    processing: `Procesando ${item.progress}%`,
    ready: "Listo", error: item.error || "Error",
  };

  return (
    <div className="flex items-center gap-3 p-4 bg-gray-900 border border-gray-800 rounded-xl">
      {icons[item.status]}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{item.name}</p>
        <div className="flex items-center gap-3 mt-1">
          <span className={`text-xs ${item.status === "error" ? "text-red-400" : item.status === "ready" ? "text-green-400" : "text-gray-400"}`}>
            {labels[item.status]}
          </span>
          {item.size && <span className="text-xs text-gray-500">{formatFileSize(item.size)}</span>}
        </div>
        {["uploading", "processing"].includes(item.status) && (
          <div className="mt-2 h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-pool-600 to-pool-400 rounded-full transition-all duration-300"
              style={{ width: `${item.progress}%` }}
            />
          </div>
        )}
      </div>
      {item.status === "ready" && item.videoId && (
        <Link href={`/editor/${item.videoId}`}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-pool-700 hover:bg-pool-600 text-white text-xs rounded-lg transition"
        >
          <Eye className="w-3.5 h-3.5" /> Ver
        </Link>
      )}
      {(item.status === "error" || item.status === "idle") && (
        <button onClick={onRemove} className="text-gray-600 hover:text-gray-400">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
