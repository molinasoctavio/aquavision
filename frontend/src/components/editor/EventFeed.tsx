"use client";
import { EVENT_COLORS, EVENT_LABELS, PERIOD_LABELS, formatMs } from "@/lib/utils";

interface Event { id: string; event_type: string; period: string; timestamp_ms: number; player_id?: string; }
interface Props { events: Event[]; currentMs: number; onSeek: (ms: number) => void; }

export default function EventFeed({ events, currentMs, onSeek }: Props) {
  if (!events.length) return (
    <div className="p-4 text-center text-gray-500 text-sm">No hay eventos detectados</div>
  );

  return (
    <div className="divide-y divide-gray-800">
      {events.map(e => {
        const isActive = Math.abs(e.timestamp_ms - currentMs) < 3000;
        const isPast   = e.timestamp_ms < currentMs;
        return (
          <button
            key={e.id}
            onClick={() => onSeek(e.timestamp_ms)}
            className={`w-full flex items-center gap-3 p-3 text-left transition-all hover:bg-gray-800 ${
              isActive ? "bg-gray-800" : ""
            }`}
          >
            <span
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ background: EVENT_COLORS[e.event_type] || "#666" }}
            />
            <div className="flex-1 min-w-0">
              <p className={`text-xs font-medium ${isActive ? "text-white" : isPast ? "text-gray-400" : "text-gray-200"}`}>
                {EVENT_LABELS[e.event_type] || e.event_type}
              </p>
              <p className="text-xs text-gray-600">{PERIOD_LABELS[e.period] || e.period}</p>
            </div>
            <span className="text-xs text-gray-500 font-mono flex-shrink-0">
              {formatMs(e.timestamp_ms)}
            </span>
          </button>
        );
      })}
    </div>
  );
}
