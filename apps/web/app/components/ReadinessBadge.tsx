"use client";

import React, { useEffect, useState, useCallback } from "react";
import { fetchWithAuth } from "@/app/lib/auth-client";
import {
    AlertTriangle,
    CheckCircle,
    Circle,
    Clock,
    RefreshCw,
    ShieldAlert,
    ShieldCheck,
    XCircle,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ReadinessStatus =
    | "READY"
    | "BASELINE_READY"
    | "REQUIRES_CONTEXT"
    | "NOT_RECOMMENDED_FOR_AUTOMATION";

interface ReadinessSummary {
    status: ReadinessStatus;
    confidence_score: number;
    top_reasons: string[];
    blockers: string[];
    recommended_next_action: string;
    source_signals: {
        quick_assessment_present: boolean;
        triage_complete: boolean;
        source_tech_set: boolean;
        target_tech_set: boolean;
        project_stage: number;
    };
    computed_at: string;
}

interface Props {
    projectId: string;
    /** "badge" = compact inline indicator, "card" = full panel */
    variant?: "badge" | "card";
    /** Force re-fetch when this changes (e.g. after running assessment) */
    refreshKey?: number;
    className?: string;
}

// ---------------------------------------------------------------------------
// Status config
// ---------------------------------------------------------------------------

const STATUS_CONFIG: Record<
    ReadinessStatus,
    { label: string; color: string; bg: string; border: string; icon: React.ReactNode }
> = {
    READY: {
        label: "Ready",
        color: "text-emerald-400",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/30",
        icon: <ShieldCheck size={14} className="text-emerald-400" />,
    },
    BASELINE_READY: {
        label: "Baseline Ready",
        color: "text-sky-400",
        bg: "bg-sky-500/10",
        border: "border-sky-500/30",
        icon: <CheckCircle size={14} className="text-sky-400" />,
    },
    REQUIRES_CONTEXT: {
        label: "Requires Context",
        color: "text-amber-400",
        bg: "bg-amber-500/10",
        border: "border-amber-500/30",
        icon: <AlertTriangle size={14} className="text-amber-400" />,
    },
    NOT_RECOMMENDED_FOR_AUTOMATION: {
        label: "Not Recommended",
        color: "text-red-400",
        bg: "bg-red-500/10",
        border: "border-red-500/30",
        icon: <ShieldAlert size={14} className="text-red-400" />,
    },
};

// ---------------------------------------------------------------------------
// Compact confidence bar
// ---------------------------------------------------------------------------

function ConfidenceBar({ score }: { score: number }) {
    const color =
        score >= 70
            ? "bg-emerald-500"
            : score >= 45
            ? "bg-sky-500"
            : score >= 25
            ? "bg-amber-500"
            : "bg-red-500";

    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 rounded-full bg-white/10 overflow-hidden">
                <div
                    className={`h-full rounded-full transition-all duration-500 ${color}`}
                    style={{ width: `${score}%` }}
                />
            </div>
            <span className="text-xs font-mono text-white/60 min-w-[2.5rem] text-right">
                {score}%
            </span>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function ReadinessBadge({
    projectId,
    variant = "badge",
    refreshKey = 0,
    className = "",
}: Props) {
    const [data, setData] = useState<ReadinessSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [recomputing, setRecomputing] = useState(false);
    const [expanded, setExpanded] = useState(false);

    const fetchReadiness = useCallback(async () => {
        if (!projectId) return;
        setLoading(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/readiness`);
            if (res.ok) {
                const json = await res.json();
                setData(json);
            }
        } catch {
            // silently ignore — readiness is non-blocking
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    useEffect(() => {
        fetchReadiness();
    }, [fetchReadiness, refreshKey]);

    const handleRecompute = async () => {
        setRecomputing(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/readiness/recompute`, {
                method: "POST",
            });
            if (res.ok) {
                const json = await res.json();
                setData(json);
            }
        } finally {
            setRecomputing(false);
        }
    };

    // ── Loading skeleton ──
    if (loading) {
        return (
            <div className={`flex items-center gap-1.5 opacity-40 ${className}`}>
                <Circle size={12} className="text-white/30 animate-pulse" />
                <span className="text-[11px] text-white/40">Readiness…</span>
            </div>
        );
    }

    if (!data) return null;

    const cfg = STATUS_CONFIG[data.status] ?? STATUS_CONFIG["REQUIRES_CONTEXT"];

    // ── Badge variant ──────────────────────────────────────────────────────
    if (variant === "badge") {
        return (
            <button
                onClick={() => setExpanded((v) => !v)}
                className={`inline-flex items-center gap-1.5 px-2 py-1 rounded border text-[11px] font-semibold uppercase tracking-wider transition-all ${cfg.bg} ${cfg.border} ${cfg.color} hover:opacity-80 ${className}`}
                title={data.recommended_next_action}
            >
                {cfg.icon}
                {cfg.label}
                <span className="font-mono opacity-70">{data.confidence_score}%</span>
            </button>
        );
    }

    // ── Card variant ───────────────────────────────────────────────────────
    return (
        <div className={`rounded-lg border ${cfg.border} ${cfg.bg} p-4 space-y-3 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {cfg.icon}
                    <span className={`text-sm font-bold uppercase tracking-widest ${cfg.color}`}>
                        {cfg.label}
                    </span>
                </div>
                <button
                    onClick={handleRecompute}
                    disabled={recomputing}
                    className="p-1 rounded hover:bg-white/10 transition-colors text-white/40 hover:text-white/80"
                    title="Recompute readiness"
                >
                    <RefreshCw size={12} className={recomputing ? "animate-spin" : ""} />
                </button>
            </div>

            {/* Confidence bar */}
            <ConfidenceBar score={data.confidence_score} />

            {/* Recommended next action */}
            <p className="text-xs text-white/70 leading-relaxed">
                {data.recommended_next_action}
            </p>

            {/* Blockers */}
            {data.blockers.length > 0 && (
                <div className="space-y-1">
                    {data.blockers.map((b, i) => (
                        <div key={i} className="flex items-start gap-1.5">
                            <XCircle size={11} className="text-red-400 mt-0.5 flex-shrink-0" />
                            <span className="text-[11px] text-red-300">{b}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Expandable reasons */}
            {data.top_reasons.length > 0 && (
                <button
                    onClick={() => setExpanded((v) => !v)}
                    className="text-[11px] text-white/40 hover:text-white/70 transition-colors underline underline-offset-2"
                >
                    {expanded ? "Hide reasons" : `Show ${data.top_reasons.length} signal(s)`}
                </button>
            )}

            {expanded && (
                <ul className="space-y-1 pl-1">
                    {data.top_reasons.map((r, i) => (
                        <li key={i} className="flex items-start gap-1.5">
                            <Clock size={10} className="text-white/30 mt-0.5 flex-shrink-0" />
                            <span className="text-[11px] text-white/60">{r}</span>
                        </li>
                    ))}
                </ul>
            )}

            {/* Footer timestamp */}
            <p className="text-[10px] text-white/25 pt-1">
                Computed {new Date(data.computed_at).toLocaleString()}
            </p>
        </div>
    );
}
