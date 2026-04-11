"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Waves, Eye, EyeOff, Loader2 } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import Link from "next/link";

const schema = z.object({
  full_name: z.string().min(2, "Nombre requerido"),
  email:     z.string().email("Email inválido"),
  password:  z.string().min(6, "Mínimo 6 caracteres"),
});

export default function RegisterPage() {
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = async (data: any) => {
    setError("");
    try {
      await authApi.register(data);
      const res = await authApi.login(data.email, data.password);
      const { access_token, refresh_token } = res.data;
      const me = await fetch("/api/v1/auth/me", {
        headers: { Authorization: `Bearer ${access_token}` },
      }).then(r => r.json());
      setAuth(me, access_token, refresh_token);
      router.push("/dashboard");
    } catch (e: any) {
      setError(e.response?.data?.detail || "No se pudo crear la cuenta");
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-pool-900/30 via-gray-950 to-gray-950" />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-96 h-96 bg-pool-600/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-pool-500 to-pool-800 mb-4 shadow-xl shadow-pool-900/50">
            <Waves className="w-9 h-9 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">AquaVision Analytics</h1>
          <p className="text-gray-400 text-sm mt-1">Plataforma de Análisis Waterpolo</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl">
          <h2 className="text-lg font-semibold text-white mb-6">Crear Cuenta</h2>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-950 border border-red-800 text-red-300 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Nombre completo</label>
              <input
                type="text"
                {...register("full_name")}
                placeholder="Juan Pérez"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-pool-500 focus:border-transparent transition"
              />
              {errors.full_name && <p className="text-red-400 text-xs mt-1">{String(errors.full_name.message)}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
              <input
                type="email"
                {...register("email")}
                placeholder="entrenador@club.com"
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-pool-500 focus:border-transparent transition"
              />
              {errors.email && <p className="text-red-400 text-xs mt-1">{String(errors.email.message)}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Contraseña</label>
              <div className="relative">
                <input
                  type={showPw ? "text" : "password"}
                  {...register("password")}
                  placeholder="••••••••"
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-pool-500 focus:border-transparent transition pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {errors.password && <p className="text-red-400 text-xs mt-1">{String(errors.password.message)}</p>}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-pool-600 hover:bg-pool-500 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition-all flex items-center justify-center gap-2"
            >
              {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {isSubmitting ? "Creando..." : "Crear cuenta"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            ¿Ya tienes cuenta?{" "}
            <Link href="/auth/login" className="text-pool-400 hover:text-pool-300 font-medium">
              Iniciar sesión
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
