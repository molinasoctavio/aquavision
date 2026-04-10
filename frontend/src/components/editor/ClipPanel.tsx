"use client";
import { formatMs } from "@/lib/utils";
import { Film, Clock, Share2, Download } from "lucide-react";

interface Clip {
  id: string; title: string; start_ms: number; end_ms: number;
  duration_ms: number; is_auto_generated: boolean;
  ability_labels?: string[]; share_token?: string;
}
interface Props { clips: Clip[]; onSeek: (ms: number) => void; }

export default function ClipPanel({ clips, onSeek }: Props) {
  if (!clips.length) return (
    <div className="p-4 text-center text-gray-500 text-sm">
      <Film className="w-7 h-7 mx-auto mb-2 opacity-30" />
      Los clips detectados automáticamente aparecerán aquí
    </div>
  );

  return (
    <div className="divide-y divide-gray-800">
      {clips.map(clip => (
        <div key={clip.id} className="p-3 hover:bg-gray-800 transition">
          <button onClick={() => onSeek(clip.start_ms)} className="w-full text-left">
            <div className="flex items-start gap-2">
              <div className="w-8 h-8 rounded bg-gray-800 flex items-center justify-center flex-shrink-0">
                <Film className="w-4 h-4 text-gray-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white truncate">{clip.title}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <Clock className="w-3 h-3 text-gray-500" />
                  <span className="text-xs text-gray-500 font-mono">
                    {formatMs(clip.start_ms)} → {formatMs(clip.end_ms)}
                  </span>
                </div>
                {clip.ability_labels && clip.ability_labels.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {clip.ability_labels.map((l: string) => (
                      <span key={l} className="text-xs bg-pool-950 text-pool-400 px-1.5 py-0.5 rounded">
                        {l}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </button>
          <div className="flex gap-2 mt-2">
            {clip.share_token && (
              <button className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition">
                <Share2 className="w-3 h-3" /> Compartir
              </button>
            )}
            <button className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition">
              <Download className="w-3 h-3" /> Exportar
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
