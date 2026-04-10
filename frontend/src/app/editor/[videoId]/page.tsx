"use client";
import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import { videosApi, clipsApi, matchesApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import VideoPlayer from "@/components/video/VideoPlayer";
import EventFeed from "@/components/editor/EventFeed";
import ClipPanel from "@/components/editor/ClipPanel";
import DrawingCanvas from "@/components/editor/DrawingCanvas";
import {
  Play, Pause, SkipBack, SkipForward, Scissors,
  Pencil, ChevronDown, Clock, List, Film,
} from "lucide-react";
import { formatMs, EVENT_COLORS, EVENT_LABELS } from "@/lib/utils";

type Panel = "events" | "clips" | "draw";

export default function EditorPage() {
  const { videoId } = useParams<{ videoId: string }>();
  const [currentMs, setCurrentMs] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activePanel, setActivePanel] = useState<Panel>("events");
  const [clipStart, setClipStart] = useState<number | null>(null);
  const [clipEnd, setClipEnd] = useState<number | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const playerRef = useRef<any>(null);

  const { data: video } = useQuery({
    queryKey: ["video", videoId],
    queryFn: () => videosApi.get(videoId).then(r => r.data),
    enabled: !!videoId,
  });

  const { data: streamData } = useQuery({
    queryKey: ["stream-url", videoId],
    queryFn: () => videosApi.getStreamUrl(videoId).then(r => r.data),
    enabled: !!videoId && video?.status === "ready",
  });

  const { data: events = [] } = useQuery({
    queryKey: ["events", video?.match_id],
    queryFn: () => matchesApi.listEvents(video.match_id).then(r => r.data),
    enabled: !!video?.match_id,
  });

  const { data: clips = [] } = useQuery({
    queryKey: ["clips", video?.match_id],
    queryFn: () => clipsApi.list({ match_id: video.match_id }).then(r => r.data),
    enabled: !!video?.match_id,
  });

  const createClipMutation = useMutation({
    mutationFn: (data: any) => clipsApi.create(data),
  });

  const seekTo = (ms: number) => {
    if (playerRef.current) playerRef.current.currentTime(ms / 1000);
  };

  const handleMarkIn = () => setClipStart(currentMs);
  const handleMarkOut = () => setClipEnd(currentMs);

  const handleSaveClip = async () => {
    if (clipStart === null || clipEnd === null || !video) return;
    await createClipMutation.mutateAsync({
      match_id: video.match_id,
      video_id: videoId,
      title: `Clip ${formatMs(clipStart)} – ${formatMs(clipEnd)}`,
      start_ms: clipStart,
      end_ms: clipEnd,
    });
    setClipStart(null);
    setClipEnd(null);
  };

  const duration = video?.duration_seconds ? video.duration_seconds * 1000 : 0;

  return (
    <AppShell>
      <div className="flex flex-col h-screen bg-gray-950">
        {/* Top bar */}
        <div className="flex items-center justify-between px-4 py-2 bg-gray-900 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <span className="text-white font-medium text-sm truncate max-w-xs">{video?.title || "Editor"}</span>
            {video?.match_id && (
              <span className="text-xs bg-pool-900 text-pool-300 px-2 py-0.5 rounded-full">Partido vinculado</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {clipStart !== null && (
              <div className="flex items-center gap-2 text-xs text-gray-300">
                <Clock className="w-3.5 h-3.5 text-green-400" />
                <span>IN: {formatMs(clipStart)}</span>
                {clipEnd !== null && (
                  <>
                    <Clock className="w-3.5 h-3.5 text-red-400" />
                    <span>OUT: {formatMs(clipEnd)}</span>
                    <button
                      onClick={handleSaveClip}
                      className="px-3 py-1 bg-pool-600 hover:bg-pool-500 text-white rounded-lg text-xs font-medium transition"
                    >
                      Guardar Clip
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* Main video area */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Video player */}
            <div className="relative flex-1 bg-black flex items-center justify-center">
              {streamData?.stream_url ? (
                <VideoPlayer
                  src={streamData.stream_url}
                  hlsPath={streamData.hls_path}
                  onTimeUpdate={setCurrentMs}
                  onPlayPause={setIsPlaying}
                  playerRef={playerRef}
                />
              ) : (
                <div className="text-center text-gray-500">
                  <Play className="w-12 h-12 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">
                    {video?.status === "ready" ? "Cargando reproductor…" : `Estado: ${video?.status || "cargando"}`}
                  </p>
                  {video?.processing_progress != null && video.status !== "ready" && (
                    <div className="mt-3 w-48 mx-auto">
                      <div className="h-1.5 bg-gray-800 rounded-full">
                        <div
                          className="h-full bg-pool-500 rounded-full transition-all"
                          style={{ width: `${Math.round(video.processing_progress * 100)}%` }}
                        />
                      </div>
                      <p className="text-xs mt-1">{Math.round(video.processing_progress * 100)}%</p>
                    </div>
                  )}
                </div>
              )}

              {/* Drawing overlay */}
              {isDrawing && (
                <DrawingCanvas
                  width={playerRef.current?.el()?.offsetWidth || 1280}
                  height={playerRef.current?.el()?.offsetHeight || 720}
                  onSave={(annotationData) => {
                    if (video?.match_id) {/* save annotation */}
                    setIsDrawing(false);
                  }}
                />
              )}
            </div>

            {/* Controls */}
            <div className="bg-gray-900 border-t border-gray-800 px-4 py-2">
              <div className="flex items-center gap-3">
                <button onClick={() => seekTo(currentMs - 5000)} className="text-gray-400 hover:text-white"><SkipBack className="w-4 h-4" /></button>
                <button
                  onClick={() => playerRef.current?.[isPlaying ? "pause" : "play"]()}
                  className="w-8 h-8 bg-pool-600 hover:bg-pool-500 rounded-full flex items-center justify-center transition"
                >
                  {isPlaying ? <Pause className="w-4 h-4 text-white" /> : <Play className="w-4 h-4 text-white ml-0.5" />}
                </button>
                <button onClick={() => seekTo(currentMs + 5000)} className="text-gray-400 hover:text-white"><SkipForward className="w-4 h-4" /></button>

                {/* Timeline */}
                <div className="flex-1 relative h-6 flex items-center">
                  <div className="w-full h-1.5 bg-gray-800 rounded-full relative">
                    {/* Progress */}
                    <div
                      className="absolute h-full bg-pool-600 rounded-full"
                      style={{ width: duration > 0 ? `${(currentMs / duration) * 100}%` : "0%" }}
                    />
                    {/* Event markers */}
                    {events.map((e: any) => (
                      <button
                        key={e.id}
                        onClick={() => seekTo(e.timestamp_ms)}
                        className="event-marker"
                        style={{
                          left: `${(e.timestamp_ms / duration) * 100}%`,
                          background: EVENT_COLORS[e.event_type] || "#888",
                        }}
                        title={EVENT_LABELS[e.event_type] || e.event_type}
                      />
                    ))}
                    {/* Clip region */}
                    {clipStart !== null && clipEnd !== null && (
                      <div
                        className="absolute h-full bg-yellow-400/30 border-l-2 border-r-2 border-yellow-400"
                        style={{
                          left: `${(clipStart / duration) * 100}%`,
                          width: `${((clipEnd - clipStart) / duration) * 100}%`,
                        }}
                      />
                    )}
                  </div>
                </div>

                <span className="text-xs text-gray-400 font-mono">
                  {formatMs(currentMs)} / {formatMs(duration)}
                </span>

                {/* Clip tools */}
                <div className="flex items-center gap-1 ml-2">
                  <button onClick={handleMarkIn} title="Marcar inicio" className="p-1.5 text-green-400 hover:bg-green-950 rounded">
                    <Scissors className="w-3.5 h-3.5" />
                  </button>
                  <button onClick={handleMarkOut} title="Marcar fin" className="p-1.5 text-red-400 hover:bg-red-950 rounded">
                    <Scissors className="w-3.5 h-3.5 scale-x-[-1]" />
                  </button>
                  <button
                    onClick={() => setIsDrawing(!isDrawing)}
                    className={`p-1.5 rounded transition ${isDrawing ? "bg-yellow-900 text-yellow-400" : "text-gray-400 hover:bg-gray-800"}`}
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right panel */}
          <div className="w-80 border-l border-gray-800 bg-gray-900 flex flex-col">
            {/* Panel tabs */}
            <div className="flex border-b border-gray-800">
              {([
                { id: "events", icon: List,   label: "Eventos" },
                { id: "clips",  icon: Film,   label: "Clips"   },
                { id: "draw",   icon: Pencil, label: "Dibujo"  },
              ] as const).map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActivePanel(tab.id)}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-medium transition border-b-2 ${
                    activePanel === tab.id
                      ? "border-pool-500 text-pool-400"
                      : "border-transparent text-gray-500 hover:text-gray-300"
                  }`}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Panel content */}
            <div className="flex-1 overflow-y-auto">
              {activePanel === "events" && (
                <EventFeed events={events} currentMs={currentMs} onSeek={seekTo} />
              )}
              {activePanel === "clips" && (
                <ClipPanel clips={clips} onSeek={seekTo} />
              )}
              {activePanel === "draw" && (
                <div className="p-4 text-center text-gray-500 text-sm">
                  <Pencil className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p>Activa el modo dibujo con el lápiz en la barra de controles</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
