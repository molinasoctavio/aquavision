import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function formatMs(ms: number): string {
  return formatDuration(ms / 1000);
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

export const EVENT_COLORS: Record<string, string> = {
  goal:             "#FF6B35",
  shot_on_target:   "#29B6F6",
  shot_blocked:     "#78909C",
  exclusion:        "#FF9800",
  power_play_start: "#9C27B0",
  counterattack:    "#4CAF50",
  save:             "#26C6DA",
  penalty_5m:       "#E91E63",
  period_start:     "#607D8B",
};

export const EVENT_LABELS: Record<string, string> = {
  goal:             "Gol",
  shot_on_target:   "Lanzamiento",
  shot_blocked:     "Bloqueado",
  exclusion:        "Exclusión",
  power_play_start: "Power Play",
  counterattack:    "Contraataque",
  save:             "Parada",
  penalty_5m:       "Penalti 5m",
  period_start:     "Inicio Período",
};

export const PERIOD_LABELS: Record<string, string> = {
  Q1: "1er Período", Q2: "2do Período",
  Q3: "3er Período", Q4: "4to Período",
  OT1: "Prórroga 1", OT2: "Prórroga 2",
  PS: "Penaltis",
};
