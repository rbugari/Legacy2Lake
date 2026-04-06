"use client";

import React, { useEffect, useState, useCallback } from "react";
import { fetchWithAuth } from "@/app/lib/auth-client";
import {
    AlertTriangle,
    BookOpen,
    CheckCircle,
    ChevronDown,
    ChevronRight,
    Cpu,
    GitBranch,
    HelpCircle,
    Layers,
    Lightbulb,
    RefreshCw,
    Shield,
    Workflow,
    Zap,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FunctionalCapability {
    name: string;
    asset_ref: string;
    source_tech: string;
    datasets: string[];
    reads_from: string[];
    evidence_refs: string[];
    confidence: number;
    uncertainty: string[];
}

interface FunctionalDomain {
    name: string;
    capabilities: FunctionalCapability[];
}

interface FunctionalMap {
    version: string;
    generated_at: string;
    domains: FunctionalDomain[];
    total_assets: number;
    total_domains: number;
}

interface Process {
    id: string;
    name: string;
    asset_ref: string;
    source_tech: string;
    trigger: string;
    schedule_hint: string;
    depends_on: string[];
    depends_on_names: string[];
    inputs: string[];
    outputs: string[];
    fragility_signals: string[];
    evidence_refs: string[];
    confidence: number;
    uncertainty: string[];
}

interface OperationalMap {
    version: string;
    generated_at: string;
    processes: Process[];
    execution_levels: string[][];
    total_processes: number;
}

interface Recommendation {
    id: string;
    category: string;
    statement: string;
    rationale: string;
    based_on: string[];
    impact: string;
    effort: string;
    confidence: number;
    uncertainty: string[];
}

interface RecommendationSet {
    version: string;
    generated_at: string;
    items: Recommendation[];
    total: number;
}

interface RuleCandidate {
    id: string;
    pattern: string;
    sample_expression: string;
    observed_in_assets: string[];
    asset_refs: string[];
    occurrence_count: number;
    reuse_scope: string;
    evidence_refs: string[];
    confidence: number;
    uncertainty: string[];
}

interface RuleCandidateSummary {
    version: string;
    generated_at: string;
    candidates: RuleCandidate[];
    total: number;
    project_scope_count: number;
}

interface Props {
    projectId: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function ConfidenceBadge({ value }: { value: number }) {
    const pct = Math.round(value * 100);
    const color =
        pct >= 80
            ? "bg-emerald-500/15 text-emerald-400"
            : pct >= 60
            ? "bg-amber-500/15 text-amber-400"
            : "bg-red-500/15 text-red-400";
    return (
        <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded ${color}`}>
            {pct}% conf.
        </span>
    );
}

function UncertaintyHints({ items }: { items: string[] }) {
    if (!items.length) return null;
    return (
        <div className="flex flex-wrap gap-1 mt-1">
            {items.map((u) => (
                <span
                    key={u}
                    className="inline-flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded bg-yellow-500/10 text-yellow-400"
                >
                    <HelpCircle size={8} />
                    {u.replaceAll("_", " ")}
                </span>
            ))}
        </div>
    );
}

function ImpactBadge({ value }: { value: string }) {
    const color =
        value === "high"
            ? "bg-red-500/15 text-red-400"
            : value === "medium"
            ? "bg-amber-500/15 text-amber-400"
            : "bg-blue-500/15 text-blue-400";
    return (
        <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${color}`}>
            {value}
        </span>
    );
}

function FragilityBadge({ signal }: { signal: string }) {
    return (
        <span className="inline-flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400">
            <AlertTriangle size={8} />
            {signal.replaceAll("_", " ")}
        </span>
    );
}

function SectionHeader({
    icon,
    title,
    subtitle,
    count,
}: {
    icon: React.ReactNode;
    title: string;
    subtitle?: string;
    count?: number;
}) {
    return (
        <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-2">
                <span className="text-[var(--accent)]">{icon}</span>
                <div>
                    <h3 className="text-sm font-semibold text-[var(--text-primary)]">{title}</h3>
                    {subtitle && (
                        <p className="text-[11px] text-[var(--text-tertiary)] mt-0.5">{subtitle}</p>
                    )}
                </div>
            </div>
            {count !== undefined && (
                <span className="text-xs text-[var(--text-tertiary)] bg-[var(--surface-secondary)] px-2 py-0.5 rounded-full">
                    {count}
                </span>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Sub-panels
// ---------------------------------------------------------------------------

function FunctionalMapPanel({ data }: { data: FunctionalMap }) {
    const [expanded, setExpanded] = useState<Set<string>>(new Set());

    const toggle = (name: string) =>
        setExpanded((prev) => {
            const next = new Set(prev);
            next.has(name) ? next.delete(name) : next.add(name);
            return next;
        });

    return (
        <div>
            <SectionHeader
                icon={<Workflow size={15} />}
                title="Functional Map"
                subtitle="Business domains and the assets that support each capability"
                count={data.total_domains}
            />
            {data.domains.length === 0 ? (
                <p className="text-xs text-[var(--text-tertiary)] italic">
                    No domains inferred. Run triage to populate impact data.
                </p>
            ) : (
                <div className="space-y-2">
                    {data.domains.map((domain) => {
                        const isOpen = expanded.has(domain.name);
                        return (
                            <div
                                key={domain.name}
                                className="border border-[var(--border)] rounded-lg overflow-hidden"
                            >
                                <button
                                    onClick={() => toggle(domain.name)}
                                    className="w-full flex items-center justify-between px-3 py-2.5 bg-[var(--surface-secondary)] hover:bg-[var(--surface-hover)] transition-colors text-left"
                                >
                                    <span className="text-xs font-semibold capitalize text-[var(--text-primary)]">
                                        {domain.name}
                                    </span>
                                    <div className="flex items-center gap-2">
                                        <span className="text-[10px] text-[var(--text-tertiary)]">
                                            {domain.capabilities.length} asset{domain.capabilities.length !== 1 ? "s" : ""}
                                        </span>
                                        {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                    </div>
                                </button>
                                {isOpen && (
                                    <div className="divide-y divide-[var(--border)]">
                                        {domain.capabilities.map((cap) => (
                                            <div key={cap.asset_ref} className="px-3 py-2.5">
                                                <div className="flex items-start justify-between gap-2">
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-xs font-medium text-[var(--text-primary)] truncate">
                                                            {cap.name}
                                                        </p>
                                                        <p className="text-[10px] text-[var(--text-tertiary)] mt-0.5">
                                                            {cap.source_tech}
                                                        </p>
                                                    </div>
                                                    <ConfidenceBadge value={cap.confidence} />
                                                </div>
                                                {cap.datasets.length > 0 && (
                                                    <div className="mt-1.5 flex flex-wrap gap-1">
                                                        <span className="text-[9px] text-[var(--text-tertiary)] mr-1">
                                                            writes:
                                                        </span>
                                                        {cap.datasets.map((d) => (
                                                            <span
                                                                key={d}
                                                                className="text-[9px] font-mono px-1 py-0.5 rounded bg-emerald-500/10 text-emerald-400"
                                                            >
                                                                {d}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                                {cap.reads_from.length > 0 && (
                                                    <div className="mt-1 flex flex-wrap gap-1">
                                                        <span className="text-[9px] text-[var(--text-tertiary)] mr-1">
                                                            reads:
                                                        </span>
                                                        {cap.reads_from.map((r) => (
                                                            <span
                                                                key={r}
                                                                className="text-[9px] font-mono px-1 py-0.5 rounded bg-blue-500/10 text-blue-400"
                                                            >
                                                                {r}
                                                            </span>
                                                        ))}
                                                    </div>
                                                )}
                                                <UncertaintyHints items={cap.uncertainty} />
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

function OperationalMapPanel({ data }: { data: OperationalMap }) {
    const [expanded, setExpanded] = useState<Set<string>>(new Set());
    const toggle = (id: string) =>
        setExpanded((prev) => {
            const next = new Set(prev);
            next.has(id) ? next.delete(id) : next.add(id);
            return next;
        });

    return (
        <div>
            <SectionHeader
                icon={<GitBranch size={15} />}
                title="Operational Map"
                subtitle="Process execution order, dependencies, and fragility signals"
                count={data.total_processes}
            />
            {data.execution_levels.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-1 items-center">
                    <span className="text-[10px] text-[var(--text-tertiary)] mr-1">Execution levels:</span>
                    {data.execution_levels.map((level, idx) => (
                        <span
                            key={idx}
                            className="text-[9px] px-1.5 py-0.5 rounded bg-[var(--surface-secondary)] text-[var(--text-secondary)]"
                        >
                            L{idx}: {level.length} proc.
                        </span>
                    ))}
                </div>
            )}
            {data.processes.length === 0 ? (
                <p className="text-xs text-[var(--text-tertiary)] italic">
                    No processes mapped. Run triage to populate impact data.
                </p>
            ) : (
                <div className="space-y-2">
                    {data.processes.map((proc) => {
                        const isOpen = expanded.has(proc.id);
                        const hasFragility = proc.fragility_signals.length > 0;
                        return (
                            <div
                                key={proc.id}
                                className={`border rounded-lg overflow-hidden ${
                                    hasFragility
                                        ? "border-orange-500/30"
                                        : "border-[var(--border)]"
                                }`}
                            >
                                <button
                                    onClick={() => toggle(proc.id)}
                                    className="w-full flex items-center justify-between px-3 py-2.5 bg-[var(--surface-secondary)] hover:bg-[var(--surface-hover)] transition-colors text-left"
                                >
                                    <div className="flex items-center gap-2 min-w-0">
                                        {hasFragility && (
                                            <AlertTriangle size={11} className="text-orange-400 shrink-0" />
                                        )}
                                        <span className="text-xs font-medium text-[var(--text-primary)] truncate">
                                            {proc.name}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 shrink-0">
                                        <ConfidenceBadge value={proc.confidence} />
                                        {isOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                                    </div>
                                </button>
                                {isOpen && (
                                    <div className="px-3 py-2.5 space-y-2 text-xs">
                                        <div className="flex flex-wrap gap-2">
                                            <span className="text-[var(--text-tertiary)]">Tech:</span>
                                            <span className="text-[var(--text-secondary)]">{proc.source_tech}</span>
                                            <span className="text-[var(--text-tertiary)]">Trigger:</span>
                                            <span className="text-[var(--text-secondary)]">{proc.trigger}</span>
                                            {proc.schedule_hint !== "not_configured" && (
                                                <>
                                                    <span className="text-[var(--text-tertiary)]">Schedule:</span>
                                                    <span className="font-mono text-[var(--text-secondary)]">
                                                        {proc.schedule_hint}
                                                    </span>
                                                </>
                                            )}
                                        </div>
                                        {proc.depends_on_names.length > 0 && (
                                            <div className="flex flex-wrap gap-1 items-center">
                                                <span className="text-[var(--text-tertiary)]">Depends on:</span>
                                                {proc.depends_on_names.map((d) => (
                                                    <span
                                                        key={d}
                                                        className="text-[9px] font-mono px-1 py-0.5 rounded bg-purple-500/10 text-purple-400"
                                                    >
                                                        {d}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                        {proc.inputs.length > 0 && (
                                            <div className="flex flex-wrap gap-1 items-center">
                                                <span className="text-[var(--text-tertiary)]">Reads:</span>
                                                {proc.inputs.map((t) => (
                                                    <span
                                                        key={t}
                                                        className="text-[9px] font-mono px-1 py-0.5 rounded bg-blue-500/10 text-blue-400"
                                                    >
                                                        {t}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                        {proc.outputs.length > 0 && (
                                            <div className="flex flex-wrap gap-1 items-center">
                                                <span className="text-[var(--text-tertiary)]">Writes:</span>
                                                {proc.outputs.map((t) => (
                                                    <span
                                                        key={t}
                                                        className="text-[9px] font-mono px-1 py-0.5 rounded bg-emerald-500/10 text-emerald-400"
                                                    >
                                                        {t}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                        {proc.fragility_signals.length > 0 && (
                                            <div className="flex flex-wrap gap-1 items-center">
                                                <span className="text-[var(--text-tertiary)]">Fragility:</span>
                                                {proc.fragility_signals.map((s) => (
                                                    <FragilityBadge key={s} signal={s} />
                                                ))}
                                            </div>
                                        )}
                                        <UncertaintyHints items={proc.uncertainty} />
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

function RecommendationsPanel({ data }: { data: RecommendationSet }) {
    const CATEGORY_ICONS: Record<string, React.ReactNode> = {
        compliance: <Shield size={12} />,
        human_review: <BookOpen size={12} />,
        discovery: <Cpu size={12} />,
        migration_strategy: <Layers size={12} />,
        architecture: <GitBranch size={12} />,
        documentation: <CheckCircle size={12} />,
    };

    return (
        <div>
            <SectionHeader
                icon={<Lightbulb size={15} />}
                title="Recommendations"
                subtitle="Prioritized actions grounded in project evidence"
                count={data.total}
            />
            {data.items.length === 0 ? (
                <p className="text-xs text-[var(--text-tertiary)] italic">
                    No recommendations generated. More project data needed.
                </p>
            ) : (
                <div className="space-y-2">
                    {data.items.map((rec) => (
                        <div
                            key={rec.id}
                            className="border border-[var(--border)] rounded-lg p-3 space-y-2"
                        >
                            <div className="flex items-start justify-between gap-2">
                                <div className="flex items-start gap-2 flex-1 min-w-0">
                                    <span className="text-[var(--accent)] mt-0.5 shrink-0">
                                        {CATEGORY_ICONS[rec.category] ?? <Lightbulb size={12} />}
                                    </span>
                                    <p className="text-xs font-medium text-[var(--text-primary)]">
                                        {rec.statement}
                                    </p>
                                </div>
                                <div className="flex items-center gap-1 shrink-0">
                                    <ImpactBadge value={rec.impact} />
                                    <ConfidenceBadge value={rec.confidence} />
                                </div>
                            </div>
                            <p className="text-[11px] text-[var(--text-tertiary)] leading-relaxed">
                                {rec.rationale}
                            </p>
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] text-[var(--text-tertiary)]">Effort:</span>
                                <span className="text-[10px] text-[var(--text-secondary)]">{rec.effort}</span>
                                <span className="text-[10px] text-[var(--text-tertiary)] ml-2">Category:</span>
                                <span className="text-[10px] text-[var(--text-secondary)] capitalize">
                                    {rec.category.replaceAll("_", " ")}
                                </span>
                            </div>
                            <UncertaintyHints items={rec.uncertainty} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function RuleCandidatesPanel({ data }: { data: RuleCandidateSummary }) {
    return (
        <div>
            <SectionHeader
                icon={<Zap size={15} />}
                title="Rule Candidates"
                subtitle={`Reusable transformation patterns — ${data.project_scope_count} project-scope`}
                count={data.total}
            />
            {data.candidates.length === 0 ? (
                <p className="text-xs text-[var(--text-tertiary)] italic">
                    No rule candidates detected. Column mapping data needed.
                </p>
            ) : (
                <div className="space-y-2">
                    {data.candidates.map((c) => (
                        <div
                            key={c.id}
                            className="border border-[var(--border)] rounded-lg p-3 space-y-2"
                        >
                            <div className="flex items-start justify-between gap-2">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-medium text-[var(--text-primary)] capitalize">
                                            {c.pattern.replaceAll("_", " ")}
                                        </span>
                                        <span
                                            className={`text-[9px] px-1.5 py-0.5 rounded font-semibold ${
                                                c.reuse_scope === "project"
                                                    ? "bg-emerald-500/15 text-emerald-400"
                                                    : "bg-gray-500/15 text-gray-400"
                                            }`}
                                        >
                                            {c.reuse_scope.toUpperCase()}
                                        </span>
                                    </div>
                                    <code className="text-[10px] font-mono text-[var(--text-secondary)] block mt-1 truncate">
                                        {c.sample_expression}
                                    </code>
                                </div>
                                <ConfidenceBadge value={c.confidence} />
                            </div>
                            <div className="flex flex-wrap gap-1 items-center">
                                <span className="text-[10px] text-[var(--text-tertiary)]">
                                    Found in {c.occurrence_count}x across:
                                </span>
                                {c.observed_in_assets.map((a) => (
                                    <span
                                        key={a}
                                        className="text-[9px] px-1 py-0.5 rounded bg-[var(--surface-secondary)] text-[var(--text-tertiary)]"
                                    >
                                        {a}
                                    </span>
                                ))}
                            </div>
                            <UncertaintyHints items={c.uncertainty} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------

type UnderstandingTab = "functional" | "operational" | "recommendations" | "rules";

const PANEL_TABS: { id: UnderstandingTab; label: string; icon: React.ReactNode }[] = [
    { id: "functional", label: "Functional Map", icon: <Workflow size={12} /> },
    { id: "operational", label: "Operational Map", icon: <GitBranch size={12} /> },
    { id: "recommendations", label: "Recommendations", icon: <Lightbulb size={12} /> },
    { id: "rules", label: "Rule Candidates", icon: <Zap size={12} /> },
];

export default function UnderstandingPanel({ projectId }: Props) {
    const [activeTab, setActiveTab] = useState<UnderstandingTab>("functional");
    const [loading, setLoading] = useState(false);
    const [rebuilding, setRebuilding] = useState(false);
    const [generatedAt, setGeneratedAt] = useState<string | null>(null);

    const [functionalMap, setFunctionalMap] = useState<FunctionalMap | null>(null);
    const [operationalMap, setOperationalMap] = useState<OperationalMap | null>(null);
    const [recommendations, setRecommendations] = useState<RecommendationSet | null>(null);
    const [ruleCandidates, setRuleCandidates] = useState<RuleCandidateSummary | null>(null);

    const fetchTab = useCallback(
        async (tab: UnderstandingTab) => {
            setLoading(true);
            try {
                const endpoint =
                    tab === "functional"
                        ? "functional-map"
                        : tab === "operational"
                        ? "operational-map"
                        : tab === "recommendations"
                        ? "recommendations"
                        : "rule-candidates";
                const res = await fetchWithAuth(`/projects/${projectId}/understanding/${endpoint}`);
                const data = await res.json();
                if (tab === "functional") setFunctionalMap(data);
                else if (tab === "operational") setOperationalMap(data);
                else if (tab === "recommendations") setRecommendations(data);
                else setRuleCandidates(data);
                if (data.generated_at) setGeneratedAt(data.generated_at);
            } catch (e) {
                console.error("[UnderstandingPanel] fetch error:", e);
            } finally {
                setLoading(false);
            }
        },
        [projectId]
    );

    useEffect(() => {
        if (
            (activeTab === "functional" && !functionalMap) ||
            (activeTab === "operational" && !operationalMap) ||
            (activeTab === "recommendations" && !recommendations) ||
            (activeTab === "rules" && !ruleCandidates)
        ) {
            fetchTab(activeTab);
        }
    }, [activeTab, functionalMap, operationalMap, recommendations, ruleCandidates, fetchTab]);

    const handleRebuild = async () => {
        setRebuilding(true);
        try {
            await fetchWithAuth(`/projects/${projectId}/understanding/rebuild`, { method: "POST" });
            // Reset cached data so next tab switch re-fetches
            setFunctionalMap(null);
            setOperationalMap(null);
            setRecommendations(null);
            setRuleCandidates(null);
            setGeneratedAt(null);
            // Reload current tab
            fetchTab(activeTab);
        } catch (e) {
            console.error("[UnderstandingPanel] rebuild error:", e);
        } finally {
            setRebuilding(false);
        }
    };

    const formatDate = (iso: string | null) => {
        if (!iso) return null;
        try {
            return new Date(iso).toLocaleString();
        } catch {
            return iso;
        }
    };

    return (
        <div className="h-full w-full flex flex-col overflow-hidden bg-[var(--background)]">
            {/* Panel header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] bg-[var(--surface-secondary)] shrink-0">
                <div className="flex items-center gap-2">
                    <BookOpen size={14} className="text-[var(--accent)]" />
                    <span className="text-xs font-semibold text-[var(--text-primary)]">
                        Project Understanding
                    </span>
                    {generatedAt && (
                        <span className="text-[10px] text-[var(--text-tertiary)]">
                            — generated {formatDate(generatedAt)}
                        </span>
                    )}
                </div>
                <button
                    onClick={handleRebuild}
                    disabled={rebuilding}
                    className="flex items-center gap-1.5 text-[10px] text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors disabled:opacity-50"
                    title="Rebuild all understanding artifacts"
                >
                    <RefreshCw size={11} className={rebuilding ? "animate-spin" : ""} />
                    {rebuilding ? "Rebuilding…" : "Rebuild"}
                </button>
            </div>

            {/* Tab bar */}
            <div className="flex gap-0.5 px-2 pt-2 pb-0 border-b border-[var(--border)] bg-[var(--surface-secondary)] shrink-0">
                {PANEL_TABS.map((t) => (
                    <button
                        key={t.id}
                        onClick={() => setActiveTab(t.id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-t-md transition-colors ${
                            activeTab === t.id
                                ? "bg-[var(--background)] text-[var(--text-primary)] border border-b-0 border-[var(--border)]"
                                : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                        }`}
                    >
                        {t.icon}
                        {t.label}
                    </button>
                ))}
            </div>

            {/* Content area */}
            <div className="flex-1 overflow-y-auto p-4">
                {loading ? (
                    <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
                        <RefreshCw size={13} className="animate-spin" />
                        Loading…
                    </div>
                ) : (
                    <>
                        {activeTab === "functional" && functionalMap && (
                            <FunctionalMapPanel data={functionalMap} />
                        )}
                        {activeTab === "operational" && operationalMap && (
                            <OperationalMapPanel data={operationalMap} />
                        )}
                        {activeTab === "recommendations" && recommendations && (
                            <RecommendationsPanel data={recommendations} />
                        )}
                        {activeTab === "rules" && ruleCandidates && (
                            <RuleCandidatesPanel data={ruleCandidates} />
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
