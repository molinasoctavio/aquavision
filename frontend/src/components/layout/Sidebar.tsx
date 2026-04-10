"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, Upload, Play, BarChart2, Users,
  Radio, Settings, LogOut, Waves, ChevronRight,
} from "lucide-react";
import { useAuthStore } from "@/store/auth";

const nav = [
  { href: "/dashboard",        icon: LayoutDashboard, label: "Dashboard"    },
  { href: "/upload",           icon: Upload,          label: "Subir Video"  },
  { href: "/matches",          icon: Play,            label: "Partidos"     },
  { href: "/analytics",        icon: BarChart2,       label: "Estadísticas" },
  { href: "/players",          icon: Users,           label: "Jugadores"    },
  { href: "/livestream",       icon: Radio,           label: "En Vivo"      },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  return (
    <aside className="w-64 min-h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pool-500 to-pool-800 flex items-center justify-center">
            <Waves className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-white leading-tight">AquaVision</h1>
            <p className="text-xs text-gray-400">Water Polo Analytics</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {nav.map(({ href, icon: Icon, label }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
                active
                  ? "bg-pool-600 text-white shadow-lg shadow-pool-900/50"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              )}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              <span className="flex-1">{label}</span>
              {active && <ChevronRight className="w-4 h-4 opacity-60" />}
            </Link>
          );
        })}
      </nav>

      {/* User */}
      <div className="p-4 border-t border-gray-800 space-y-2">
        <Link href="/settings" className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-white hover:bg-gray-800">
          <Settings className="w-5 h-5" />
          <span>Configuración</span>
        </Link>
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-pool-600 flex items-center justify-center text-sm font-bold">
            {user?.full_name?.[0] ?? "?"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
            <p className="text-xs text-gray-400 capitalize">{user?.role}</p>
          </div>
          <button onClick={logout} className="text-gray-500 hover:text-red-400">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
