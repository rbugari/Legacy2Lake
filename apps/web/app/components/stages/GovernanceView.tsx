"use client";
import React, { useEffect, useState, useRef, useCallback } from 'react';
import {
    ArrowRight,
    Shield,
    ShieldCheck,
    Zap,
    Download,
    CheckCircle,
    FileText,
    TrendingUp,
    AlertCircle,
    ScrollText,
    Code,
    Database,
    Loader2,
} from 'lucide-react';
import StageHeader from '../StageHeader';
import { fetchWithAuth } from '../../lib/auth-client';
import QualityDashboard from '../visualization/QualityDashboard';
import UnifiedLogViewer from '../UnifiedLogViewer';
import { useConfirm } from '@/app/hooks/useConfirm';

const GOVERNANCE_AGENTS = [
    { id: 'F', name: 'Agent F (Critic)', role: 'Compliance & code quality audit' },
    { id: 'G', name: 'Agent G (Governor)', role: 'Documentation, lineage & certification' },
];

interface GovernanceViewProps {
    projectId: string;
    onStageChange: (stage: number) => void;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onReset?: () => void;
    onBackToCurrent?: () => void;
    activeSection?: string;
    onSectionChange?: (section: string) => void;
    activeTenantId?: string;
}

export default function GovernanceView({
    projectId,
    onStageChange,
    isFullscreen,
    onToggleFullscreen,
    onReset,
    onBackToCurrent,
    activeSection,
    onSectionChange,
    activeTenantId,
}: GovernanceViewProps) {
    const { confirm, ConfirmDialog } = useConfirm();
    const [isGovernanceRunning, setIsGovernanceRunning] = useState(false);
    const isGovernanceRunningRef = useRef(false);
    const [isGovernanceComplete, setIsGovernanceComplete] = useState(false);
    const [isApproving, setIsApproving] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);
    const [report, setReport] = useState<any>(null);
    const [project, setProject] = useState<any>(null);

    // Keep ref in sync with state (no stale closures in callbacks)
    useEffect(() => { isGovernanceRunningRef.current = isGovernanceRunning; }, [isGovernanceRunning]);

    const headers = activeTenantId ? { 'X-Tenant-ID': activeTenantId } : {};

    // â”€â”€ Fetch report from backend (uses cached result if available) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    const fetchReport = useCallback(async () => {
        try {
            const res = await fetchWithAuth(`projects/${projectId}/governance`, { headers });
            const data = await res.json();
            setReport(data);
        } catch (e) {
            console.error('[GovernanceView] Report fetch failed', e);
        }
    }, [projectId, activeTenantId]);

    // â”€â”€ Poll logs + detect completion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    const fetchGovernanceLogs = useCallback(async () => {
        try {
            const res = await fetchWithAuth(`projects/${projectId}/execution-logs?type=governance`, { headers });
            const data = await res.json();
            if (data.logs) {
                const lines = data.logs.split('\n').filter((l: string) => l.trim() !== '');
                if (lines.length > 0) setLogs(lines);
            }
            const statusRes = await fetchWithAuth(`discovery/status/${projectId}`, { headers });
            const statusData = await statusRes.json();
            if (statusData.status === 'CERTIFIED' && isGovernanceRunningRef.current) {
                console.log('[GovernanceView] Certification complete, stopping polling');
                setIsGovernanceRunning(false);
                setIsGovernanceComplete(true);
                fetchReport();
            }
        } catch (e) {
            console.error('[GovernanceView] Log fetch failed', e);
        }
    }, [projectId, activeTenantId]);   // stable ref â€” no isGovernanceRunning dep

    // â”€â”€ Polling effect â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    useEffect(() => {
        let interval: NodeJS.Timeout;
        let timeout: NodeJS.Timeout;
        if (isGovernanceRunning) {
            timeout = setTimeout(() => {
                fetchGovernanceLogs();
                interval = setInterval(fetchGovernanceLogs, 3000);
            }, 1500);
        }
        return () => { clearTimeout(timeout); clearInterval(interval); };
    }, [isGovernanceRunning]);   // fetchGovernanceLogs is stable

    // â”€â”€ On mount: restore state if already CERTIFIED â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    useEffect(() => {
        const init = async () => {
            try {
                const [statusRes, projectRes] = await Promise.all([
                    fetchWithAuth(`discovery/status/${projectId}`, { headers }),
                    fetchWithAuth(`projects/${projectId}`, { headers }),
                ]);
                const { status } = await statusRes.json();
                const projectData = await projectRes.json();
                setProject(projectData);
                if (status === 'CERTIFIED') {
                    setIsGovernanceComplete(true);
                    fetchReport();
                }
            } catch (e) {
                console.error('[GovernanceView] Init failed', e);
            }
        };
        init();
    }, [projectId]);

    // â”€â”€ Run governance â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    const handleRunGovernance = async () => {
        const ok = await confirm({
            variant: 'execute',
            title: 'Run Governance & Certification?',
            description: 'Agents F and G will audit all generated code for compliance, security patterns and Medallion architecture adherence, then generate the certification report and COP score.',
            agents: GOVERNANCE_AGENTS,
            confirmLabel: 'Run Governance',
        });
        if (!ok) return;

        if (onSectionChange) onSectionChange('logs');
        setIsGovernanceRunning(true);
        setIsGovernanceComplete(false);
        setReport(null);
        setLogs(['[SYSTEM] Governance pipeline starting...']);

        try {
            const res = await fetchWithAuth(`projects/${projectId}/governance/run`, {
                method: 'POST',
                headers: { ...headers },
            });
            if (res.status === 423) {
                const data = await res.json();
                setIsGovernanceRunning(false);
                setLogs(prev => [...prev, `[ERROR] Process locked: ${data.detail?.message || 'Already running'}`]);
                return;
            }
            const data = await res.json();
            if (data.status !== 'RUNNING') {
                // Unexpected â€” treat as error
                setIsGovernanceRunning(false);
                setLogs(prev => [...prev, `[ERROR] Unexpected response: ${JSON.stringify(data)}`]);
            }
        } catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            setIsGovernanceRunning(false);
            setLogs(prev => [...prev, `[ERROR] ${msg}`]);
        }
    };

    // â”€â”€ Advance to Handover â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    const handleApprove = async () => {
        setIsApproving(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/stage`, {
                method: 'POST',
                headers: { ...headers, 'Content-Type': 'application/json' },
                body: JSON.stringify({ stage: '5' }),
            });
            const data = await res.json();
            if (data.success) onStageChange(5);
        } catch (e) {
            console.error('[GovernanceView] Stage advance failed', e);
        } finally {
            setIsApproving(false);
        }
    };

    const score = report?.score ?? 0;
    const stats = report?.stats ?? { bronze_count: 0, silver_count: 0, gold_count: 0, total_files: 0, total_lines: 0 };

    return (
        <div className="flex flex-col h-full bg-[var(--background)]">
            {ConfirmDialog}
            <StageHeader
                title="Stage 4: Governance & Certification"
                subtitle="Review the generated solution, capture findings, and produce auditable delivery evidence"
                icon={<ShieldCheck className="text-amber-500" />}
                helpText="Use Governance to understand certification results, remaining findings, and the operational evidence that will accompany delivery."
                onApprove={handleApprove}
                approveLabel="Next Phase: Handover"
                isApproveDisabled={isGovernanceRunning || !isGovernanceComplete}
                isExecuting={isApproving}
                isFullscreen={isFullscreen}
                onToggleFullscreen={onToggleFullscreen}
                onReset={onReset}
                onBackToCurrent={onBackToCurrent}
            />

            <div className="flex-1 overflow-hidden p-6">

                {/* â”€â”€ LOGS / PROGRESS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
                {(activeSection === 'logs' || activeSection === 'progress') && (
                    <div className="h-full max-w-7xl mx-auto flex flex-col gap-4">
                        {isGovernanceComplete && !isGovernanceRunning && (
                            <div className="flex items-center gap-3 px-6 py-4 bg-amber-500/10 border border-amber-500/30 rounded-2xl shrink-0 animate-in fade-in slide-in-from-top-2 duration-300">
                                <CheckCircle size={18} className="text-amber-400 shrink-0" />
                                <div>
                                    <p className="text-sm font-black text-amber-400 uppercase tracking-wide">
                                        Governance Complete â€” COP Score: {score}/100
                                    </p>
                                    <p className="text-xs text-gray-500 mt-0.5">
                                        Certification report ready. Use the <strong className="text-gray-400">Next Phase</strong> button above to proceed to Handover.
                                    </p>
                                </div>
                            </div>
                        )}
                        <div className="flex-1 min-h-0">
                            <UnifiedLogViewer
                                mode="realtime"
                                projectId={projectId}
                                isRunning={isGovernanceRunning}
                                logs={logs}
                                processName="Governance Pipeline"
                                variant="panel"
                            />
                        </div>
                    </div>
                )}

                {/* â”€â”€ CERTIFICATION REPORT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
                {(activeSection === 'overview' || activeSection === 'report' || activeSection === 'completion') && (
                    <div className="h-full overflow-auto custom-scrollbar">
                        {!isGovernanceComplete && !isGovernanceRunning && !report && (
                            <div className="flex flex-col items-center justify-center py-24 max-w-2xl mx-auto text-center">
                                <div className="w-20 h-20 bg-amber-500/10 border border-amber-500/20 rounded-full flex items-center justify-center mb-6">
                                    <ShieldCheck size={40} className="text-amber-400" />
                                </div>
                                <h2 className="text-2xl font-black mb-3 text-white">Governance & Certification</h2>
                                <p className="text-gray-400 mb-8 leading-relaxed max-w-md">
                                    Agents F and G will audit your generated artifacts for compliance, security patterns and Medallion architecture adherence, then issue the certification report.
                                </p>
                                <button
                                    onClick={handleRunGovernance}
                                    className="flex items-center gap-2 px-7 py-3.5 bg-amber-500 hover:bg-amber-400 text-white font-black text-sm uppercase tracking-widest rounded-xl transition-all active:scale-95 shadow-xl shadow-amber-500/20"
                                >
                                    <Zap size={16} /> Run Governance & Certification
                                </button>
                            </div>
                        )}

                        {isGovernanceRunning && !report && (
                            <div className="flex flex-col items-center justify-center py-24 gap-4">
                                <Loader2 size={40} className="animate-spin text-amber-400" />
                                <p className="font-bold text-white">Governance pipeline running...</p>
                                <p className="text-xs text-gray-500">Switch to the <strong className="text-amber-400">Logs</strong> section to monitor progress.</p>
                            </div>
                        )}

                        {report && (
                            <div className="max-w-7xl mx-auto space-y-6">
                                {/* Hero */}
                                <div className="relative overflow-hidden bg-gradient-to-br from-amber-700 via-amber-600 to-orange-600 rounded-2xl p-8 text-white shadow-2xl">
                                    <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-6">
                                        <div className="space-y-3">
                                            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 rounded-full text-[10px] font-black uppercase tracking-widest">
                                                <ShieldCheck size={12} /> Certified
                                            </div>
                                            <h2 className="text-3xl font-black tracking-tight">Migration Certified.</h2>
                                            <p className="text-amber-100 max-w-md leading-relaxed">
                                                {project?.origin || 'Legacy'} logic modernized to {project?.destination || 'Cloud'}-native architecture.
                                            </p>
                                            <button
                                                onClick={handleRunGovernance}
                                                className="mt-1 inline-flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-xs font-bold transition-all"
                                            >
                                                <Zap size={12} /> Re-run Governance
                                            </button>
                                        </div>
                                        {/* COP Score donut */}
                                        <div className="relative w-40 h-40 shrink-0">
                                            <svg className="w-full h-full -rotate-90" viewBox="0 0 160 160">
                                                <circle cx="80" cy="80" r="70" stroke="rgba(255,255,255,0.15)" strokeWidth="10" fill="transparent" />
                                                <circle cx="80" cy="80" r="70" stroke="white" strokeWidth="10" fill="transparent"
                                                    strokeDasharray={440}
                                                    strokeDashoffset={440 - (440 * score) / 100}
                                                    className="transition-all duration-1000 ease-out"
                                                />
                                            </svg>
                                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                                <span className="text-4xl font-black">{score}</span>
                                                <span className="text-[10px] font-bold uppercase opacity-70 tracking-widest">COP Score</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="absolute -top-10 -right-10 w-60 h-60 bg-white/10 rounded-full blur-3xl pointer-events-none" />
                                </div>

                                {/* Stat cards */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <StatCard label="Refined Files" value={stats.total_files} icon={<ScrollText className="text-blue-400" />} />
                                    <StatCard label="Lines Generated" value={(stats.total_lines ?? 0).toLocaleString()} icon={<Code className="text-purple-400" />} />
                                    <StatCard label="Bronze Layer" value={`${stats.bronze_count} files`} icon={<Database className="text-orange-400" />} />
                                    <StatCard label="Silver + Gold" value={`${(stats.silver_count ?? 0) + (stats.gold_count ?? 0)} files`} icon={<ShieldCheck className="text-emerald-400" />} />
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* â”€â”€ AUDIT CHECKS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
                {activeSection === 'audit' && (
                    <div className="max-w-4xl mx-auto h-full overflow-auto custom-scrollbar">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-black text-white flex items-center gap-2">
                                <Shield className="text-amber-400" size={20} /> Compliance Audit Checks
                            </h3>
                            {!isGovernanceRunning && (
                                <button
                                    onClick={handleRunGovernance}
                                    className="flex items-center gap-2 px-4 py-2 bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/30 text-amber-300 text-xs font-black uppercase tracking-widest rounded-xl transition-all"
                                >
                                    <Zap size={13} /> {report ? 'Re-run' : 'Run Audit'}
                                </button>
                            )}
                        </div>

                        {!report && !isGovernanceRunning && (
                            <div className="flex flex-col items-center justify-center py-20 bg-white/[0.02] border border-white/8 rounded-2xl text-gray-500">
                                <Shield size={40} className="mb-4 opacity-20" />
                                <p className="text-sm">No audit data yet. Run Governance & Certification to generate compliance checks.</p>
                            </div>
                        )}

                        {isGovernanceRunning && (
                            <div className="flex items-center justify-center py-20 gap-3 text-gray-400">
                                <Loader2 size={20} className="animate-spin text-amber-400" />
                                <span className="text-sm">Audit running â€” switch to Logs to monitor progress...</span>
                            </div>
                        )}

                        {report?.audit_details?.checks?.length > 0 && (
                            <div className="space-y-3">
                                {report.audit_details.checks.map((check: any, i: number) => (
                                    <div key={i} className="flex items-start gap-4 p-4 bg-white/[0.03] border border-white/8 rounded-xl hover:border-white/15 transition-colors">
                                        <div className={`p-2 rounded-lg shrink-0 ${check.status === 'PASSED' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-orange-500/15 text-orange-400'}`}>
                                            {check.status === 'PASSED' ? <ShieldCheck size={16} /> : <AlertCircle size={16} />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap mb-1">
                                                <span className="text-sm font-bold text-white">{check.check_name}</span>
                                                <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${check.status === 'PASSED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-orange-500/20 text-orange-400'}`}>
                                                    {check.status}
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-400 leading-relaxed">{check.detail}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Fallback: compliance logs when no structured checks */}
                        {report?.compliance_logs?.length > 0 && !report?.audit_details?.checks?.length && (
                            <div className="space-y-2">
                                {report.compliance_logs.map((log: any, i: number) => (
                                    <div key={i} className="flex items-start gap-3 p-3 bg-white/[0.02] border border-white/5 rounded-lg">
                                        <span className={`text-[10px] font-black px-2 py-0.5 rounded-full shrink-0 mt-0.5 ${log.status === 'PASSED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-blue-500/20 text-blue-400'}`}>{log.status}</span>
                                        <p className="text-xs text-gray-300 font-mono">{log.message}</p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* â”€â”€ QUALITY â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
                {activeSection === 'quality' && (
                    <div className="h-full">
                        <QualityDashboard projectId={projectId} />
                    </div>
                )}

                {/* â”€â”€ DOCUMENTATION: LINEAGE + RUNBOOK â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
                {activeSection === 'documentation' && (
                    <div className="max-w-7xl mx-auto h-full overflow-auto custom-scrollbar space-y-8">
                        {/* Lineage */}
                        {report?.lineage?.length > 0 ? (
                            <div className="bg-white/[0.03] border border-white/8 rounded-2xl p-6">
                                <h3 className="text-lg font-black text-white flex items-center gap-2 mb-6">
                                    <TrendingUp size={18} className="text-indigo-400" /> Medallion Lineage Mapping
                                </h3>
                                <div className="space-y-4 pr-1">
                                    {report.lineage.map((item: any, i: number) => (
                                        <LineageRow key={i} item={item} />
                                    ))}
                                </div>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center py-20 bg-white/[0.02] border border-white/8 rounded-2xl text-gray-500">
                                <FileText size={40} className="mb-4 opacity-20" />
                                <p className="text-sm">{report ? 'No lineage data available in this report.' : 'Run Governance to generate lineage mapping.'}</p>
                            </div>
                        )}

                        {/* Runbook */}
                        {report?.runbook && (
                            <div className="bg-white/[0.03] border border-white/8 rounded-2xl p-6">
                                <h3 className="text-lg font-black text-white flex items-center gap-2 mb-4">
                                    <ScrollText size={18} className="text-amber-400" /> Modernization Runbook
                                </h3>
                                <pre className="font-mono text-xs leading-relaxed text-gray-300 whitespace-pre-wrap max-h-[500px] overflow-y-auto custom-scrollbar bg-black/40 rounded-xl p-6 border border-white/5">
                                    {report.runbook}
                                </pre>
                            </div>
                        )}
                    </div>
                )}

            </div>
        </div>
    );
}

// â”€â”€ Sub-components â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

function StatCard({ label, value, icon }: { label: string; value: any; icon: React.ReactNode }) {
    return (
        <div className="bg-white/[0.03] border border-white/8 p-5 rounded-2xl flex flex-col items-center text-center gap-2">
            <div className="p-2 bg-white/5 rounded-xl">{icon}</div>
            <span className="text-xl font-black text-white leading-none">{value}</span>
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">{label}</span>
        </div>
    );
}

function LineageRow({ item }: { item: any }) {
    const nodes = [
        { label: 'Source', name: item.source, color: 'bg-gray-600' },
        { label: 'Bronze', name: item.targets?.bronze, color: 'bg-orange-600' },
        { label: 'Silver', name: item.targets?.silver, color: 'bg-indigo-600' },
        { label: 'Gold', name: item.targets?.gold, color: 'bg-emerald-600' },
    ];
    return (
        <div className="flex flex-col md:flex-row items-stretch md:items-center gap-2">
            {nodes.map((n, i) => (
                <React.Fragment key={i}>
                    <div className="flex-1 flex flex-col items-center gap-1 min-w-0">
                        <span className="text-[9px] font-black text-gray-500 uppercase tracking-widest">{n.label}</span>
                        <div className={`${n.color} rounded-lg px-3 py-2 w-full text-center`}>
                            <span className="text-[11px] font-bold text-white truncate block">{n.name?.split('.').pop() ?? 'â€”'}</span>
                            <span className="text-[9px] text-white/50 truncate block font-mono">{n.name ?? ''}</span>
                        </div>
                    </div>
                    {i < nodes.length - 1 && (
                        <ArrowRight size={14} className="text-gray-600 shrink-0 hidden md:block" />
                    )}
                </React.Fragment>
            ))}
        </div>
    );
}
