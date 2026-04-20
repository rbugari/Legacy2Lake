"use client";
import React, { useState, useRef, useEffect, useCallback } from "react";
import { fetchWithAuth } from "../lib/auth-client";
import { X, Send, Bot, Trash2, Loader2 } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  text: string;
  intent?: string;
  confidence?: string;
}

interface Props {
  projectId: string;
  projectName?: string;
  onClose: () => void;
}

export default function ProjectAssistantModal({ projectId, projectName, onClose }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Load history on open
  useEffect(() => {
    if (historyLoaded) return;
    setHistoryLoaded(true);
    fetchWithAuth(`projects/${projectId}/assistant/history`)
      .then((r) => (r.ok ? r.json() : []))
      .then((rows: any[]) => {
        if (!Array.isArray(rows) || rows.length === 0) return;
        const hydrated: Message[] = rows.map((r) => ({
          role: "assistant",
          text: r.answer || "",
          intent: r.intent,
          confidence: r.confidence,
          // prepend question as user message pair
        }));
        // Reconstruct pairs: user question + assistant answer
        const pairs: Message[] = [];
        rows.forEach((r) => {
          if (r.question) pairs.push({ role: "user", text: r.question });
          if (r.answer)   pairs.push({ role: "assistant", text: r.answer, intent: r.intent, confidence: r.confidence });
        });
        if (pairs.length > 0) setMessages(pairs);
      })
      .catch(() => {/* non-blocking */});
  }, [projectId, historyLoaded]);

  useEffect(() => {
    if (!loading) inputRef.current?.focus();
  }, [loading]);

  async function send() {
    const text = input.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetchWithAuth(`projects/${projectId}/assistant/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: data.answer,
          intent: data.intent,
          confidence: data.confidence,
        },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `Error: ${e.message || "Could not reach the assistant."}`,
          confidence: "low",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function clearHistory() {
    if (clearing || loading) return;
    setClearing(true);
    try {
      await fetchWithAuth(`projects/${projectId}/assistant/history`, { method: "DELETE" });
      setMessages([]);
    } catch {
      /* non-blocking */
    } finally {
      setClearing(false);
    }
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  function confidenceColor(c?: string) {
    if (c === "high") return "text-emerald-400";
    if (c === "medium") return "text-yellow-400";
    return "text-gray-500";
  }

  const SAMPLE_QUESTIONS = [
    "Where is table dim_cliente used?",
    "Which assets contain PII data?",
    "What are the main source dependencies?",
    "What is the readiness status and why?",
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-end p-4 pointer-events-none"
      aria-modal="true"
      role="dialog"
      aria-label="Project Assistant"
    >
      <div className="pointer-events-auto flex flex-col bg-[#0f1117] border border-gray-700 rounded-xl shadow-2xl w-full max-w-md h-[560px]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <Bot size={16} className="text-indigo-400" />
            <span className="text-sm font-semibold text-white">Source Assistant</span>
            {projectName && (
              <span className="text-xs text-gray-500 truncate max-w-[140px]">— {projectName}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={clearHistory}
              disabled={clearing || loading || messages.length === 0}
              title="Clear history"
              className="text-gray-500 hover:text-red-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              {clearing ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
            </button>
            <button
              onClick={onClose}
              title="Close"
              className="text-gray-500 hover:text-gray-300 transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 text-sm">
          {messages.length === 0 && !loading && (
            <div className="space-y-3">
              <p className="text-gray-400 text-xs leading-relaxed">
                Ask questions about the <strong className="text-gray-200">legacy source</strong> —
                assets, tables, fields, PII, and dependencies collected during Triage.
              </p>
              <div className="grid gap-1.5">
                {SAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => { setInput(q); inputRef.current?.focus(); }}
                    className="text-left text-xs text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 rounded px-3 py-1.5 border border-indigo-500/20 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div
                className={
                  msg.role === "user"
                    ? "bg-indigo-600 text-white rounded-xl rounded-tr-sm px-3 py-2 max-w-[85%] whitespace-pre-wrap"
                    : "bg-gray-800 text-gray-100 rounded-xl rounded-tl-sm px-3 py-2 max-w-[90%] whitespace-pre-wrap"
                }
              >
                {msg.text}
                {msg.role === "assistant" && msg.confidence && (
                  <div className={`text-[10px] mt-1 ${confidenceColor(msg.confidence)}`}>
                    {msg.intent && msg.intent !== "general" && msg.intent !== "triage_gate" && (
                      <span className="mr-2 capitalize">{msg.intent.replace("_", " ")}</span>
                    )}
                    confidence: {msg.confidence}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-800 rounded-xl rounded-tl-sm px-3 py-2">
                <span className="text-gray-400 text-xs animate-pulse">Thinking…</span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-3 pb-3 pt-2 border-t border-gray-700">
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder="Ask about the source assets… (Enter to send)"
              rows={2}
              className="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-100 placeholder-gray-600 resize-none focus:outline-none focus:border-indigo-500 transition-colors"
              disabled={loading}
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="p-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
              title="Send"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
