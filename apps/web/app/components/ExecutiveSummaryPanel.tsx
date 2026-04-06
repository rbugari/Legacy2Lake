"use client";

import React, { useEffect, useState, useCallback } from "react";
import { fetchWithAuth } from "@/app/lib/auth-client";
import {
    AlertTriangle,
    ArrowRight,
    BarChart3,
    CheckCircle,
    Clock,
    RefreshCw,
    Shield,
    ShieldAlert,
    TrendingUp,
    XCircle,
    Zap,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExecutiveSummary {
    migration_posture: string;
    confidence_score: number;
    source_tech: string;
    target_tech: string;
    detected_techs: string[];
    total_assets: number;
    migrable_assets: number;
    pii_assets: number;
    top_risks: string[];
    manual_effort_areas: string[];
    open_blockers: string[];
    readiness_warnings?: string[];
    readiness_next_steps?: string[];
    recommended_next_action: string;
    readiness_status: string;
    total_gaps: number;
    decision_queue?: {
        title: string;
        severity: string;
        category: string;
        why_it_matters: string;
        source_stage: string;
        asset_name?: string;
    }[];
    decision_focus?: string;
    decision_open_count?: number;
    computed_at: string;
}

interface GapItem {
    category: string;
    severity: string;
    title: string;
    description: string;
    why_it_matters: string;
    source_stage: string;
    asset_name?: string;
}

interface GapsSummary {
    total: number;
    by_severity: { CRITICAL: number; HIGH: number; MEDIUM: number; LOW: number };
    by_category: Record<string, number>;
    grouped: Record<string, GapItem[]>;
    computed_at: string;
}

interface Props {
    projectId: string;
    /** "full" = complete panel, "compact" = key stats + posture only */
    variant?: "full" | "compact";
    onOpenGaps?: () => void;
    className?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const POSTURE_CONFIG: Record<string, { color: string; bg: string; border: string }> = {
    "Strong — Automation Recommended":      { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/30" },
    "Moderate — Proceed with monitoring":   { color: "text-sky-400",     bg: "bg-sky-500/10",     border: "border-sky-500/30" },
    "Caution — Open items require resolution": { color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30" },
    "High Risk — Manual review required":   { color: "text-red-400",     bg: "bg-red-500/10",     border: "border-red-500/30" },
};

const defaultPostureStyle = { color: "text-white/60", bg: "bg-white/5", border: "border-white/10" };

const SEVERITY_COLORS: Record<string, string> = {
    CRITICAL: "text-red-400 bg-red-500/10 border-red-500/30",
    HIGH:     "text-orange-400 bg-orange-500/10 border-orange-500/30",
    MEDIUM:   "text-amber-400 bg-amber-500/10 border-amber-500/30",
    LOW:      "text-gray-400 bg-gray-500/10 border-gray-500/20",
};

const CATEGORY_LABELS: Record<string, string> = {
    schema:              "Schema",
    mappings:            "Mappings",
    business_rules:      "Business Rules",
    orchestration:       "Orchestration",
    data_quality:        "Data Quality",
    compliance:          "Compliance",
    target_architecture: "Target Architecture",
    other:               "Other",
};

function SeverityBadge({ severity }: { severity: string }) {
    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${SEVERITY_COLORS[severity] ?? SEVERITY_COLORS.LOW}`}>
            {severity}
        </span>
    );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function ExecutiveSummaryPanel({
    projectId,
    variant = "full",
    onOpenGaps,
    className = "",
}: Props) {
    const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
    const [gaps, setGaps] = useState<GapsSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [activeGapCategory, setActiveGapCategory] = useState<string | null>(null);

    const load = useCallback(async () => {
        if (!projectId) return;
        try {
            const [sumRes, gapRes] = await Promise.all([
                fetchWithAuth(`projects/${projectId}/executive-summary`),
                fetchWithAuth(`projects/${projectId}/gaps-summary`),
            ]);
            if (sumRes.ok) setSummary(await sumRes.json());
            if (gapRes.ok) setGaps(await gapRes.json());
        } catch {
            // non-blocking
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [projectId]);

    useEffect(() => { load(); }, [load]);

    const handleRefresh = () => {
        setRefreshing(true);
        load();
    };

    if (loading) {
        return (
            <div className={`rounded-xl border border-white/10 bg-white/5 p-6 animate-pulse ${className}`}>
                <div className="h-4 bg-white/10 rounded w-1/3 mb-3" />
                <div className="h-3 bg-white/5 rounded w-2/3 mb-2" />
                <div className="h-3 bg-white/5 rounded w-1/2" />
            </div>
        );
    }

    if (!summary) return null;

    const postureStyle = POSTURE_CONFIG[summary.migration_posture] ?? defaultPostureStyle;
    const coveragePct = summary.total_assets > 0
        ? Math.round((summary.migrable_assets / summary.total_assets) * 100)
        : 0;

    // ── Compact variant ────────────────────────────────────────────────────
    if (variant === "compact") {
        return (
            <div className={`rounded-xl border ${postureStyle.border} ${postureStyle.bg} p-4 space-y-2 ${className}`}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <BarChart3 size={14} className={postureStyle.color} />
                        <span className={`text-xs font-bold uppercase tracking-widest ${postureStyle.color}`}>
                            {summary.migration_posture}
                        </span>
                    </div>
                    <span className="text-[11px] font-mono text-white/50">{summary.confidence_score}% confidence</span>
                </div>
                <p className="text-xs text-white/60">{summary.recommended_next_action}</p>
                {summary.total_gaps > 0 && (
                    <p className="text-[11px] text-amber-400">{summary.total_gaps} open gap(s) identified</p>
                )}
            </div>
        );
    }

    // ── Full variant ───────────────────────────────────────────────────────
    return (
        <div className={`space-y-5 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-black uppercase tracking-widest text-white flex items-center gap-2">
                    <Shield size={16} className="text-amber-400" />
                    Executive Summary
                </h3>
                <button
                    onClick={handleRefresh}
                    className="p-1.5 rounded hover:bg-white/10 transition-colors text-white/40 hover:text-white/70"
                    title="Refresh summary"
                >
                    <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} />
                </button>
            </div>

            {/* Migration posture banner */}
            <div className={`rounded-xl border ${postureStyle.border} ${postureStyle.bg} p-4`}>
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-[10px] font-black uppercase tracking-widest text-white/40 mb-1">Migration Posture</p>
                        <p className={`text-base font-black ${postureStyle.color}`}>{summary.migration_posture}</p>
                    </div>
                    <div className="text-right">
                        <p className="text-[10px] text-white/30 font-semibold uppercase tracking-wider">Confidence</p>
                        <p className={`text-2xl font-black ${postureStyle.color}`}>{summary.confidence_score}%</p>
                    </div>
                </div>

                {/* Tech stack */}
                <div className="mt-3 flex items-center gap-2 text-[11px] text-white/50">
                    <span className="px-2 py-0.5 bg-white/5 rounded border border-white/10 font-mono">
                        {summary.source_tech}
                    </span>
                    <ArrowRight size={10} />
                    <span className="px-2 py-0.5 bg-white/5 rounded border border-white/10 font-mono">
                        {summary.target_tech}
                    </span>
                </div>
            </div>

            {/* Stat row */}
            <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg border border-white/10 bg-white/5 p-3 text-center">
                    <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Total Assets</p>
                    <p className="text-xl font-black text-white">{summary.total_assets}</p>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/5 p-3 text-center">
                    <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Migratable</p>
                    <p className="text-xl font-black text-emerald-400">{summary.migrable_assets}</p>
                    <p className="text-[10px] text-white/30">{coveragePct}% coverage</p>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/5 p-3 text-center">
                    <p className="text-[10px] text-white/40 uppercase tracking-wider mb-1">Open Gaps</p>
                    <p className={`text-xl font-black ${summary.total_gaps > 0 ? "text-amber-400" : "text-emerald-400"}`}>
                        {summary.total_gaps}
                    </p>
                </div>
            </div>

            {/* Top risks */}
            {summary.top_risks.length > 0 && (
                <div className="space-y-2">
                    <p className="text-[10px] font-black uppercase tracking-widest text-white/40">Top Risks</p>
                    {summary.top_risks.map((risk, i) => (
                        <div key={i} className="flex items-start gap-2">
                            <AlertTriangle size={12} className="text-amber-400 mt-0.5 flex-shrink-0" />
                            <span className="text-[11px] text-white/70">{risk}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Manual effort areas */}
            {summary.manual_effort_areas.length > 0 && (
                <div className="space-y-2">
                    <p className="text-[10px] font-black uppercase tracking-widest text-white/40">Manual Effort Areas</p>
                    {summary.manual_effort_areas.map((area, i) => (
                        <div key={i} className="flex items-start gap-2">
                            <Zap size={12} className="text-sky-400 mt-0.5 flex-shrink-0" />
                            <span className="text-[11px] text-white/70">{area}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Open blockers */}
            {summary.open_blockers.length > 0 && (
                <div className="space-y-2">
                    <p className="text-[10px] font-black uppercase tracking-widest text-red-400/70">Open Blockers</p>
                    {summary.open_blockers.map((b, i) => (
                        <div key={i} className="flex items-start gap-2">
                            <XCircle size={12} className="text-red-400 mt-0.5 flex-shrink-0" />
                            <span className="text-[11px] text-red-300">{b}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Readiness warnings */}
            {(summary.readiness_warnings?.length ?? 0) > 0 && (
                <div className="space-y-2">
                    <p className="text-[10px] font-black uppercase tracking-widest text-amber-300/80">Readiness Warnings</p>
                    {summary.readiness_warnings?.map((warning, i) => (
                        <div key={i} className="flex items-start gap-2">
                            <ShieldAlert size={12} className="text-amber-300 mt-0.5 flex-shrink-0" />
                            <span className="text-[11px] text-amber-100/80">{warning}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Recommended next action */}
            <div className="rounded-lg border border-white/10 bg-white/5 p-3 flex items-start gap-3">
                <TrendingUp size={16} className="text-sky-400 mt-0.5 flex-shrink-0" />
                <div>
                    <p className="text-[10px] font-black uppercase tracking-widest text-white/40 mb-1">Next Action</p>
                    <p className="text-xs text-white/70">{summary.recommended_next_action}</p>
                </div>
            </div>

            {/* Readiness next steps */}
            {(summary.readiness_next_steps?.length ?? 0) > 0 && (
                <div className="space-y-2 rounded-lg border border-sky-500/20 bg-sky-500/5 p-3">
                    <p className="text-[10px] font-black uppercase tracking-widest text-sky-300">Execution Checklist</p>
                    {summary.readiness_next_steps?.map((step, i) => (
                        <div key={i} className="flex items-start gap-2">
                            <Clock size={12} className="text-sky-300 mt-0.5 flex-shrink-0" />
                            <span className="text-[11px] text-white/75">{step}</span>
                        </div>
                    ))}
                </div>
            )}

            {/* Gaps breakdown */}
            {gaps && gaps.total > 0 && (
                <div className="space-y-3">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                        <p className="text-[10px] font-black uppercase tracking-widest text-white/40">
                            Gaps by Category ({gaps.total} total)
                        </p>
                        {onOpenGaps && (
                            <button
                                onClick={onOpenGaps}
                                className="text-[10px] font-black uppercase tracking-widest text-amber-400 hover:text-amber-300"
                            >
                                Open Gap Workspace
                            </button>
                        )}
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                        {Object.entries(gaps.by_category).map(([cat, count]) => (
                            <button
                                key={cat}
                                onClick={() => setActiveGapCategory(activeGapCategory === cat ? null : cat)}
                                className={`flex items-center justify-between px-3 py-2 rounded-lg border transition-all text-left ${
                                    activeGapCategory === cat
                                        ? "border-amber-500/50 bg-amber-500/10"
                                        : "border-white/10 bg-white/5 hover:bg-white/10"
                                }`}
                            >
                                <span className="text-[11px] text-white/70">
                                    {CATEGORY_LABELS[cat] ?? cat}
                                </span>
                                <span className="text-[11px] font-bold text-amber-400">{count}</span>
                            </button>
                        ))}
                    </div>

                    {/* Decision queue */}
                    {summary.decision_queue && summary.decision_queue.length > 0 && (
                        <div className="space-y-3 rounded-xl border border-sky-500/20 bg-sky-500/5 p-4">
                            <div className="flex items-center justify-between gap-2 flex-wrap">
                                <p className="text-[10px] font-black uppercase tracking-widest text-sky-300">
                                    Decision Queue ({summary.decision_open_count ?? summary.decision_queue.length})
                                </p>
                                {onOpenGaps && (
                                    <button
                                        onClick={onOpenGaps}
                                        className="text-[10px] font-black uppercase tracking-widest text-sky-300 hover:text-sky-200"
                                    >
                                        Review in Gap Workspace
                                    </button>
                                )}
                            </div>
                            {summary.decision_focus && (
                                <p className="text-xs text-white/65">{summary.decision_focus}</p>
                            )}
                            <div className="space-y-2">
                                {summary.decision_queue.map((item, index) => (
                                    <div key={`${item.title}-${index}`} className="rounded-lg border border-white/10 bg-black/20 p-3 space-y-1">
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-[11px] font-bold text-white">{item.title}</span>
                                            <SeverityBadge severity={item.severity} />
                                        </div>
                                        <p className="text-[10px] text-white/35 uppercase tracking-wider">
                                            {CATEGORY_LABELS[item.category] ?? item.category} · {item.source_stage}
                                        </p>
                                        <p className="text-[11px] text-white/60">{item.why_it_matters}</p>
                                        {item.asset_name && (
                                            <p className="text-[10px] font-mono text-white/30">Asset: {item.asset_name}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Expanded gap detail */}
                    {activeGapCategory && gaps.grouped[activeGapCategory] && (
                        <div className="space-y-2">
                            {gaps.grouped[activeGapCategory].map((gap, i) => (
                                <div key={i} className="rounded-lg border border-white/10 bg-black/20 p-3 space-y-1">
                                    <div className="flex items-center justify-between gap-2">
                                        <span className="text-[11px] font-bold text-white">{gap.title}</span>
                                        <SeverityBadge severity={gap.severity} />
                                    </div>
                                    <p className="text-[11px] text-white/60">{gap.description}</p>
                                    <p className="text-[10px] text-white/40 italic">{gap.why_it_matters}</p>
                                    {gap.asset_name && (
                                        <p className="text-[10px] font-mono text-white/30">Asset: {gap.asset_name}</p>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {gaps && gaps.total === 0 && (
                <div className="flex items-center gap-2 text-[11px] text-emerald-400">
                    <CheckCircle size={12} />
                    No gaps identified from available signals.
                </div>
            )}

            {/* Footer */}
            <p className="text-[10px] text-white/20">
                Computed {new Date(summary.computed_at).toLocaleString()}
            </p>
        </div>
    );
}
