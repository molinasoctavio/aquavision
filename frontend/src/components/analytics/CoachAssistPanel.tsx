"use client";
import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api";
import { MessageSquare, Send, Loader2, Waves } from "lucide-react";

interface Message { role: "user" | "assistant"; content: string; }
const QUICK_QUESTIONS = [
  "¿Cuál fue la eficiencia en superioridad numérica?",
  "¿Qué períodos fueron más fuertes para el local?",
  "¿Qué jugadores destacaron más en ataque?",
  "¿Cuántos contraataques ejecutamos y cuántos convirtimos?",
  "¿Qué recomendaciones hay para el próximo partido?",
];

export default function CoachAssistPanel({ matchId }: { matchId: string }) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "¡Hola entrenador! Soy tu asistente de análisis. Puedes preguntarme cualquier cosa sobre el partido. ¿En qué te puedo ayudar?" }
  ]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const mutation = useMutation({
    mutationFn: (question: string) =>
      analyticsApi.coachAssist(matchId, question).then(r => r.data),
    onSuccess: (data) => {
      setMessages(prev => [...prev, { role: "assistant", content: data.answer }]);
    },
    onError: () => {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "Lo siento, no pude procesar esa pregunta en este momento. Por favor verifica que la API de Claude está configurada."
      }]);
    },
  });

  const handleSend = (text: string) => {
    if (!text.trim()) return;
    setMessages(prev => [...prev, { role: "user", content: text }]);
    setInput("");
    mutation.mutate(text);
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl flex flex-col h-96">
      {/* Header */}
      <div className="flex items-center gap-2 p-4 border-b border-gray-800">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pool-500 to-pool-800 flex items-center justify-center">
          <Waves className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-medium text-white">CoachAssist IA</p>
          <p className="text-xs text-gray-400">Powered by Claude</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-7 h-7 rounded-full bg-pool-700 flex items-center justify-center flex-shrink-0">
                <Waves className="w-3.5 h-3.5 text-white" />
              </div>
            )}
            <div className={`max-w-[85%] text-sm p-3 rounded-2xl leading-relaxed ${
              msg.role === "user"
                ? "bg-pool-700 text-white rounded-br-md"
                : "bg-gray-800 text-gray-200 rounded-bl-md"
            }`}>
              {msg.content}
            </div>
          </div>
        ))}
        {mutation.isPending && (
          <div className="flex gap-2">
            <div className="w-7 h-7 rounded-full bg-pool-700 flex items-center justify-center">
              <Waves className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="bg-gray-800 px-4 py-3 rounded-2xl rounded-bl-md">
              <Loader2 className="w-4 h-4 animate-spin text-pool-400" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick questions */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2 flex gap-2 flex-wrap">
          {QUICK_QUESTIONS.slice(0, 3).map(q => (
            <button
              key={q}
              onClick={() => handleSend(q)}
              className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-2.5 py-1.5 rounded-lg transition"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="p-3 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && !e.shiftKey && handleSend(input)}
            placeholder="Pregunta sobre el partido…"
            className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-pool-500"
          />
          <button
            onClick={() => handleSend(input)}
            disabled={!input.trim() || mutation.isPending}
            className="p-2 bg-pool-600 hover:bg-pool-500 disabled:opacity-40 rounded-xl transition"
          >
            <Send className="w-4 h-4 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}
