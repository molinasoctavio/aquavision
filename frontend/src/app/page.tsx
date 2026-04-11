import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-b from-blue-900 to-slate-900 text-white p-8">
      <div className="max-w-2xl text-center space-y-6">
        <h1 className="text-5xl font-bold">AquaVision Analytics</h1>
        <p className="text-xl text-blue-200">
          Water polo video analysis platform
        </p>
        <div className="flex gap-4 justify-center pt-4">
          <Link
            href="/dashboard"
            className="px-6 py-3 bg-blue-500 hover:bg-blue-400 rounded-lg font-semibold transition"
          >
            Go to Dashboard
          </Link>
          <Link
            href="/auth/login"
            className="px-6 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg font-semibold transition"
          >
            Sign in
          </Link>
        </div>
      </div>
    </main>
  );
}
