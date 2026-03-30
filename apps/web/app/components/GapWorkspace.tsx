"use client";

import React, { useEffect, useState, useCallback } from "react";
import { fetchWithAuth } from "@/app/lib/auth-client";
import {
    AlertTriangle,
    CheckCircle,
    ChevronDown,
    ChevronRight,
    Download,
    Filter,
    Plus,
    RefreshCw,
    RotateCcw,
    ShieldAlert,
    Sparkles,
    X,
    XCircle,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type ResolutionStatus = "OPEN" | "IN_REVIEW" | "RESOLVED" | "WONT_FIX";
type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

interface GapItem {
    gap_id: string;
    category: string;
    severity: Severity;
    title: string;
    description?: string;
    why_it_matters?: string;
    recommended_owner?: string;
    resolution_status: ResolutionStatus;
    decision_note?: string;
    source_stage: string;
    asset_name?: string;
    created_at: string;
    updated_at: string;
}

interface Props {
    projectId: string;
    className?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const SEVERITY_COLORS: Record<Severity, string> = {
    CRITICAL: "text-red-400 bg-red-500/10 border-red-500/30",
    HIGH:     "text-orange-400 bg-orange-500/10 border-orange-500/30",
    MEDIUM:   "text-amber-400 bg-amber-500/10 border-amber-500/30",
    LOW:      "text-gray-400 bg-gray-500/10 border-gray-500/20",
};

const STATUS_COLORS: Record<ResolutionStatus, string> = {
    OPEN:       "text-amber-400 bg-amber-500/10 border-amber-500/30",
    IN_REVIEW:  "text-sky-400 bg-sky-500/10 border-sky-500/30",
    RESOLVED:   "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
    WONT_FIX:   "text-gray-500 bg-gray-500/5 border-gray-500/20",
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
    manual:              "Manual",
};

function Badge({ label, className }: { label: string; className: string }) {
    return (
        <span className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${className}`}>
            {label}
        </span>
    );
}

// ---------------------------------------------------------------------------
// Create gap form (inline)
// ---------------------------------------------------------------------------

function CreateGapForm({
    projectId,
    onCreated,
    onCancel,
}: {
    projectId: string;
    onCreated: (gap: GapItem) => void;
    onCancel: () => void;
}) {
    const [title, setTitle] = useState("");
    const [category, setCategory] = useState("other");
    const [severity, setSeverity] = useState("MEDIUM");
    const [description, setDescription] = useState("");
    const [whyItMatters, setWhyItMatters] = useState("");
    const [saving, setSaving] = useState(false);

    const handleSubmit = async () => {
        if (!title.trim()) return;
        setSaving(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/gaps`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title,
                    category,
                    severity,
                    description,
                    why_it_matters: whyItMatters,
                    source_stage: "manual",
                }),
            });
            if (res.ok) {
                const created = await res.json();
                onCreated(created);
            }
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 space-y-3">
            <div className="flex items-center justify-between">
                <span className="text-xs font-black uppercase tracking-widest text-amber-400">New Gap</span>
                <button onClick={onCancel} className="text-white/30 hover:text-white/70"><X size={14} /></button>
            </div>

            <input
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="Gap title *"
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30 outline-none focus:border-amber-500/50"
            />

            <div className="grid grid-cols-2 gap-2">
                <select
                    value={category}
                    onChange={e => setCategory(e.target.value)}
                    className="bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 outline-none"
                >
                    {Object.entries(CATEGORY_LABELS).map(([val, label]) => (
                        <option key={val} value={val}>{label}</option>
                    ))}
                </select>
                <select
                    value={severity}
                    onChange={e => setSeverity(e.target.value)}
                    className="bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 outline-none"
                >
                    {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map(s => (
                        <option key={s} value={s}>{s}</option>
                    ))}
                </select>
            </div>

            <textarea
                value={description}
                onChange={e => setDescription(e.target.value)}
                placeholder="Description (optional)"
                rows={2}
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 placeholder:text-white/30 outline-none resize-none"
            />

            <textarea
                value={whyItMatters}
                onChange={e => setWhyItMatters(e.target.value)}
                placeholder="Why it matters (optional)"
                rows={2}
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 placeholder:text-white/30 outline-none resize-none"
            />

            <button
                onClick={handleSubmit}
                disabled={saving || !title.trim()}
                className="w-full py-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 rounded-lg text-xs font-black text-white uppercase tracking-widest"
            >
                {saving ? "Saving…" : "Create Gap"}
            </button>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Gap detail / resolve panel
// ---------------------------------------------------------------------------

function GapDetail({
    projectId,
    gap,
    onResolved,
    onReopened,
    onClose,
}: {
    projectId: string;
    gap: GapItem;
    onResolved: (updated: GapItem) => void;
    onReopened: (updated: GapItem) => void;
    onClose: () => void;
}){
    const [decisionNote, setDecisionNote] = useState(gap.decision_note || "");
    const [saving, setSaving] = useState(false);

    const handleResolve = async () => {
        setSaving(true);
        try {
            const res = await fetchWithAuth(
                `projects/${projectId}/gaps/${gap.gap_id}/resolve`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ decision_note: decisionNote }),
                }
            );
            if (res.ok) onResolved({ ...gap, resolution_status: "RESOLVED", decision_note: decisionNote });
        } finally {
            setSaving(false);
        }
    };

    const handleReopen = async () => {
        setSaving(true);
        try {
            const res = await fetchWithAuth(
                `projects/${projectId}/gaps/${gap.gap_id}/reopen`,
                { method: "POST" }
            );
            if (res.ok) onReopened({ ...gap, resolution_status: "OPEN", decision_note: decisionNote });
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="rounded-xl border border-white/10 bg-black/40 p-4 space-y-3">
            <div className="flex items-start justify-between gap-2">
                <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                        <Badge label={gap.severity} className={SEVERITY_COLORS[gap.severity]} />
                        <Badge label={gap.resolution_status} className={STATUS_COLORS[gap.resolution_status]} />
                        <span className="text-[10px] text-white/30">{CATEGORY_LABELS[gap.category] ?? gap.category}</span>
                    </div>
                    <p className="text-sm font-bold text-white">{gap.title}</p>
                </div>
                <button onClick={onClose} className="text-white/30 hover:text-white/70 flex-shrink-0"><X size={14} /></button>
            </div>

            {gap.description && (
                <p className="text-xs text-white/60">{gap.description}</p>
            )}

            {gap.why_it_matters && (
                <div className="rounded-lg bg-white/5 border border-white/10 p-3">
                    <p className="text-[10px] font-black uppercase tracking-wider text-white/40 mb-1">Why It Matters</p>
                    <p className="text-xs text-white/60 italic">{gap.why_it_matters}</p>
                </div>
            )}

            {gap.recommended_owner && (
                <p className="text-[11px] text-white/40">Recommended owner: <span className="text-white/60">{gap.recommended_owner}</span></p>
            )}

            {/* Decision note */}
            <div>
                <label className="text-[10px] font-black uppercase tracking-widest text-white/40 block mb-1">Decision Note</label>
                <textarea
                    value={decisionNote}
                    onChange={e => setDecisionNote(e.target.value)}
                    placeholder="Record the decision or reason for resolution…"
                    rows={3}
                    className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-xs text-white/80 placeholder:text-white/30 outline-none resize-none"
                />
            </div>

            {/* Actions */}
            <div className="flex gap-2">
                {gap.resolution_status !== "RESOLVED" ? (
                    <button
                        onClick={handleResolve}
                        disabled={saving}
                        className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 rounded-lg text-xs font-black text-white uppercase tracking-widest flex items-center justify-center gap-1"
                    >
                        <CheckCircle size={12} /> Resolve
                    </button>
                ) : (
                    <button
                        onClick={handleReopen}
                        disabled={saving}
                        className="flex-1 py-2 bg-white/10 hover:bg-white/20 disabled:opacity-50 rounded-lg text-xs font-black text-white uppercase tracking-widest flex items-center justify-center gap-1"
                    >
                        <RotateCcw size={12} /> Reopen
                    </button>
                )}
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main workspace component
// ---------------------------------------------------------------------------

export default function GapWorkspace({ projectId, className = "" }: Props) {
    const [gaps, setGaps] = useState<GapItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [importing, setImporting] = useState(false);
    const [showCreate, setShowCreate] = useState(false);
    const [selectedGap, setSelectedGap] = useState<GapItem | null>(null);
    const [statusFilter, setStatusFilter] = useState<string>("OPEN");
    const [severityFilter, setSeverityFilter] = useState<string>("");

    const loadGaps = useCallback(async () => {
        if (!projectId) return;
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (statusFilter) params.set("status", statusFilter);
            if (severityFilter) params.set("severity", severityFilter);
            const res = await fetchWithAuth(`projects/${projectId}/gaps?${params}`);
            if (res.ok) setGaps(await res.json());
        } finally {
            setLoading(false);
        }
    }, [projectId, statusFilter, severityFilter]);

    useEffect(() => { loadGaps(); }, [loadGaps]);

    const handleImport = async () => {
        setImporting(true);
        try {
            await fetchWithAuth(`projects/${projectId}/gaps/import`, { method: "POST" });
            await loadGaps();
        } finally {
            setImporting(false);
        }
    };

    const handleCreated = (gap: GapItem) => {
        setGaps(prev => [gap, ...prev]);
        setShowCreate(false);
    };

    const handleResolved = (updated: GapItem) => {
        setGaps(prev => prev.map(g => g.gap_id === updated.gap_id ? updated : g));
        setSelectedGap(updated);
    };

    const handleReopened = (updated: GapItem) => {
        setGaps(prev => prev.map(g => g.gap_id === updated.gap_id ? updated : g));
        setSelectedGap(updated);
    };

    const openCount   = gaps.filter(g => g.resolution_status === "OPEN").length;
    const resolvedCount = gaps.filter(g => g.resolution_status === "RESOLVED").length;

    return (
        <div className={`space-y-4 ${className}`}>
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-2">
                <h3 className="text-sm font-black uppercase tracking-widest text-white flex items-center gap-2">
                    <ShieldAlert size={16} className="text-amber-400" />
                    Gap Workspace
                    <span className="text-[11px] text-amber-400 font-mono">{openCount} open</span>
                    {resolvedCount > 0 && (
                        <span className="text-[11px] text-emerald-400 font-mono">{resolvedCount} resolved</span>
                    )}
                </h3>
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleImport}
                        disabled={importing}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[11px] font-bold text-white/70 uppercase tracking-widest transition-colors"
                        title="Auto-import gaps from project signals"
                    >
                        <Sparkles size={11} className={importing ? "animate-spin" : ""} />
                        {importing ? "Importing…" : "Import"}
                    </button>
                    <button
                        onClick={() => setShowCreate(v => !v)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 rounded-lg text-[11px] font-bold text-amber-400 uppercase tracking-widest transition-colors"
                    >
                        <Plus size={11} /> Add Gap
                    </button>
                    <button
                        onClick={loadGaps}
                        className="p-1.5 rounded hover:bg-white/10 transition-colors text-white/30 hover:text-white/60"
                    >
                        <RefreshCw size={12} />
                    </button>
                </div>
            </div>

            {/* Filters */}
            <div className="flex items-center gap-2 flex-wrap">
                {(["", "OPEN", "IN_REVIEW", "RESOLVED", "WONT_FIX"] as const).map(s => (
                    <button
                        key={s}
                        onClick={() => setStatusFilter(s)}
                        className={`px-3 py-1 rounded-lg text-[11px] font-bold uppercase tracking-wider transition-colors border ${
                            statusFilter === s
                                ? "bg-amber-500/20 border-amber-500/40 text-amber-400"
                                : "bg-white/5 border-white/10 text-white/40 hover:text-white/60"
                        }`}
                    >
                        {s || "All"}
                    </button>
                ))}
                <div className="ml-auto">
                    <select
                        value={severityFilter}
                        onChange={e => setSeverityFilter(e.target.value)}
                        className="bg-black/30 border border-white/10 rounded-lg px-2 py-1 text-[11px] text-white/60 outline-none"
                    >
                        <option value="">All Severity</option>
                        {["CRITICAL", "HIGH", "MEDIUM", "LOW"].map(s => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Create form */}
            {showCreate && (
                <CreateGapForm
                    projectId={projectId}
                    onCreated={handleCreated}
                    onCancel={() => setShowCreate(false)}
                />
            )}

            {/* Selected gap detail */}
            {selectedGap && (
                <GapDetail
                    projectId={projectId}
                    gap={selectedGap}
                    onResolved={handleResolved}
                    onReopened={handleReopened}
                    onClose={() => setSelectedGap(null)}
                />
            )}

            {/* Gap list */}
            {loading ? (
                <div className="space-y-2">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="h-14 rounded-lg bg-white/5 animate-pulse" />
                    ))}
                </div>
            ) : gaps.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center opacity-50">
                    <CheckCircle size={32} className="text-emerald-400 mb-3" />
                    <p className="text-sm font-bold text-white/60">No gaps matching current filters.</p>
                    <p className="text-xs text-white/30 mt-1">Use "Import" to auto-detect from project signals.</p>
                </div>
            ) : (
                <div className="space-y-2">
                    {gaps.map(gap => (
                        <button
                            key={gap.gap_id}
                            onClick={() => setSelectedGap(selectedGap?.gap_id === gap.gap_id ? null : gap)}
                            className={`w-full text-left rounded-xl border transition-all p-3 space-y-1 ${
                                selectedGap?.gap_id === gap.gap_id
                                    ? "border-amber-500/40 bg-amber-500/5"
                                    : "border-white/10 bg-white/5 hover:bg-white/10"
                            }`}
                        >
                            <div className="flex items-center justify-between gap-2">
                                <span className="text-[11px] font-bold text-white truncate flex-1">{gap.title}</span>
                                <div className="flex items-center gap-1.5 flex-shrink-0">
                                    <Badge label={gap.severity} className={`${SEVERITY_COLORS[gap.severity]} text-[9px]`} />
                                    <Badge label={gap.resolution_status} className={`${STATUS_COLORS[gap.resolution_status]} text-[9px]`} />
                                </div>
                            </div>
                            {gap.description && (
                                <p className="text-[11px] text-white/50 truncate">{gap.description}</p>
                            )}
                            <p className="text-[10px] text-white/25">
                                {CATEGORY_LABELS[gap.category] ?? gap.category} · {gap.source_stage}
                            </p>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
