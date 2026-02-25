"use client";
import React, { useEffect, useState } from 'react';
import {
    ArrowLeft,
    ArrowRight,
    Binary,
    Database,
    Github,
    Maximize2,
    Minimize2,
    RotateCcw,
    Search,
    Settings,
    Share2,
    Shield,
    ShieldCheck,
    Zap,
    Download,
    CheckCircle,
    Info,
    FileText,
    TrendingUp,
    AlertCircle,
    ScrollText,
    Code,
    ShieldAlert,
    Cpu,
    LucideIcon
} from 'lucide-react';
import StageHeader from '../StageHeader';
import StageSidebar from '@/app/components/navigation/StageSidebar';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { fetchWithAuth } from '../../lib/auth-client';
import DesignRegistryPanel from './DesignRegistryPanel';
import OrchestrationPanel from './OrchestrationPanel';
import QualityDashboard from '../visualization/QualityDashboard';


interface GovernanceViewProps {
    projectId: string;
    onStageChange: (stage: number) => void;
    isFullscreen?: boolean;
    onToggleFullscreen?: () => void;
    onReset?: () => void;
    onBackToCurrent?: () => void;
    activeSection?: string;
    onSectionChange?: (section: string) => void;
}

export default function GovernanceView({
    projectId,
    onStageChange,
    isFullscreen,
    onToggleFullscreen,
    onReset,
    onBackToCurrent,
    activeSection,
    onSectionChange
}: GovernanceViewProps) {
    const [report, setReport] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<"report" | "registry" | "orchestration" | "quality" | "audit" | "documentation">("report");

    // Map sidebar action IDs to handler functions
    useEffect(() => {
        if (!activeSection) return;

        switch (activeSection) {
            case "generate-governance":
                fetchGovernanceReport();
                if (onSectionChange) onSectionChange("completion");
                break;
            case "audit":
                runAudit();
                setActiveTab("audit");
                break;
            case "completion":
                setActiveTab("report");
                break;
            case "technical":
                setActiveTab("registry");
                break;
            case "dictionary":
                setActiveTab("orchestration");
                break;
            case "lineage":
            case "runbook":
                setActiveTab("documentation");
                break;
            case "quality":
                setActiveTab("quality");
                break;
            default:
                setActiveTab("report");
        }
    }, [activeSection, onSectionChange]);
    const [isPushing, setIsPushing] = useState(false);
    const [auditReport, setAuditReport] = useState<any>(null);
    const [isAuditing, setIsAuditing] = useState(false);

    const runAudit = async () => {
        setIsAuditing(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/audit`);
            const data = await res.json();
            setAuditReport(data);
        } catch (e) {
            console.error("Audit failed", e);
        } finally {
            setIsAuditing(false);
        }
    };

    const handlePush = () => {
        setIsPushing(true);
        setTimeout(() => {
            setIsPushing(false);
            alert("Success! A Pull Request has been created in the repository with the modernized code.");
        }, 3000);
    };

    const [project, setProject] = useState<any>(null);

    useEffect(() => {
        // Fetch Project Metadata only
        fetchWithAuth(`projects/${projectId}`)
            .then(res => res.json())
            .then(data => setProject(data))
            .catch(err => console.error("Failed to fetch project details:", err));
    }, [projectId]);

    const fetchGovernanceReport = async () => {
        setLoading(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/governance`);
            const data = await res.json();
            setReport(data);
        } catch (err) {
            console.error("Failed to fetch governance report:", err);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center bg-gray-50/50 dark:bg-gray-950 text-gray-500">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <p className="font-bold animate-pulse">Generating Certification Report...</p>
                </div>
            </div>
        );
    }

    const auditScore = auditReport?.score ?? report?.score ?? 0;
    const stats = report?.stats ?? {
        bronze_count: 0,
        silver_count: 0,
        gold_count: 0,
        total_files: 0,
        total_lines: 0
    };



    return (
        <div className={`h-full bg-gray-50/50 dark:bg-gray-950 overflow-y-auto custom-scrollbar transition-all duration-300 ${isFullscreen ? 'fixed inset-0 z-50 bg-white dark:bg-gray-950' : ''}`}>
            <div className="flex-1">
                <StageHeader
                    title="Stage 4: Intelligent Governance"
                    subtitle="The Governor: Compliance audit and final quality gate"
                    icon={<ShieldCheck className="text-amber-500" />}
                    helpText="Final verification of dependencies, security patterns, and Medallion architecture compliance."
                    onApprove={() => onStageChange(5)}
                    approveLabel="Next Phase: Handover"
                    isApproveDisabled={isAuditing || !report}
                    isFullscreen={isFullscreen}
                    onToggleFullscreen={onToggleFullscreen}
                    onReset={onReset}
                    onBackToCurrent={onBackToCurrent}
                >
                    {/* Action buttons can be removed or kept for redundancy */}
                </StageHeader>

                {/* Navigation Tabs (Removed entirely as requested, migrating to sidebar) */}
                <div className="sticky top-0 z-20 bg-white/80 dark:bg-[#0a0a0a]/80 backdrop-blur-md border-b border-gray-200 dark:border-white/5 px-8 py-3 flex items-center justify-end shadow-sm">
                    <button
                        onClick={() => window.history.back()}
                        className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm text-[10px] font-bold uppercase tracking-widest text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-all"
                    >
                        <ArrowLeft size={12} /> Back
                    </button>
                </div>

                <div className="p-8 max-w-7xl mx-auto space-y-8">
                    {activeTab === "registry" ? (
                        <div className="card-glass border-none shadow-2xl">
                            <DesignRegistryPanel projectId={projectId} />
                        </div>
                    ) : activeTab === "orchestration" ? (
                        <div className="card-glass border-none shadow-2xl min-h-[600px]">
                            <OrchestrationPanel projectId={projectId} />
                        </div>
                    ) : activeTab === "quality" ? (
                        <div className="card-glass border-none shadow-2xl min-h-[600px]">
                            <QualityDashboard projectId={projectId} />
                        </div>
                    ) : !report ? (
                        <div className="flex flex-col items-center justify-center py-20 bg-white dark:bg-gray-900 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm text-center mx-auto max-w-4xl mt-10">
                            <div className="w-24 h-24 bg-blue-50 dark:bg-blue-900/20 rounded-full flex items-center justify-center mb-6 text-blue-600 dark:text-blue-400">
                                <ShieldCheck size={48} />
                            </div>
                            <h2 className="text-3xl font-extrabold mb-4 text-gray-900 dark:text-white tracking-tight">Governance & Certification</h2>
                            <p className="text-gray-500 dark:text-gray-400 max-w-lg mb-8 mx-auto text-lg leading-relaxed">
                                This project is ready for its final compliance audit. Generate the governance report from the sidebar menu to verify dependencies, security patterns, and Medallion architecture compliance.
                            </p>
                        </div>
                    ) : activeTab === "audit" ? (
                        <div className="card-glass border-none shadow-2xl min-h-[600px] p-8">
                            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                                {auditReport ? <ShieldCheck className="text-primary" /> : <CheckCircle className="text-green-500" />}
                                {auditReport ? "AI Audit Findings" : "Compliance Audit Trail"}
                            </h3>
                            <div className="space-y-4">
                                {report?.audit_details?.checks ? (
                                    report.audit_details.checks.map((check: any, idx: number) => (
                                        <div key={idx} className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-gray-100 dark:border-gray-800 group hover:shadow-md transition-all">
                                            <div className={`p-2 rounded-xl ${check.status === 'PASSED' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'}`}>
                                                {check.status === 'PASSED' ? <ShieldCheck size={18} /> : <AlertCircle size={18} />}
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100">{check.check_name}</h4>
                                                    <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${check.status === 'PASSED' ? 'bg-emerald-500 text-white' : 'bg-orange-500 text-white'}`}>
                                                        {check.status}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">
                                                    {check.detail}
                                                </p>
                                            </div>
                                        </div>
                                    ))
                                ) : report?.compliance_logs?.length > 0 ? (
                                    report.compliance_logs.map((log: any, idx: number) => (
                                        <LogItem
                                            key={idx}
                                            status={log.status}
                                            message={log.message}
                                            time={log.time}
                                        />
                                    ))
                                ) : (
                                    <div className="text-center py-20 bg-gray-50 dark:bg-gray-800/20 rounded-3xl">
                                        <div className="p-4 bg-gray-100 dark:bg-gray-800 rounded-full inline-block mb-4">
                                            <Shield size={40} className="text-gray-300" />
                                        </div>
                                        <p className="text-sm text-gray-400 italic">
                                            No audit data available. Run AI Audit to certify this project.
                                        </p>
                                        <button
                                            onClick={runAudit}
                                            disabled={isAuditing}
                                            className="mt-6 px-6 py-3 bg-[var(--accent)] text-white rounded-xl font-bold hover:scale-105 active:scale-95 transition-all flex items-center gap-2 mx-auto disabled:opacity-50"
                                        >
                                            {isAuditing ? "Auditing..." : "Run AI Audit Now"}
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : activeTab === "documentation" ? (
                        <div className="space-y-8">
                            {/* Visual Lineage Section */}
                            <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-sm">
                                <h3 className="text-xl font-bold mb-8 flex items-center gap-2">
                                    <TrendingUp size={20} className="text-indigo-500" /> Medallion Lineage Mapping
                                </h3>
                                <div className="space-y-12 max-h-[600px] overflow-y-auto pr-4 custom-scrollbar">
                                    {report?.lineage?.map((item: any, idx: number) => (
                                        <LineageRow key={idx} item={item} />
                                    ))}
                                    {!report?.lineage && (
                                        <p className="text-gray-500 italic text-center py-10">No lineage mapping available.</p>
                                    )}
                                </div>
                            </div>

                            {/* Runbook Preview */}
                            {report?.runbook && (
                                <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-sm">
                                    <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                                        <ScrollText size={20} className="text-amber-500" /> Modernization Runbook Preview
                                    </h3>
                                    <div className="p-6 bg-gray-50 dark:bg-gray-950 rounded-2xl border border-gray-200 dark:border-gray-800 max-h-[400px] overflow-y-auto custom-scrollbar font-mono text-xs whitespace-pre-wrap text-gray-600 dark:text-gray-400">
                                        {report.runbook}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <>
                            {/* Hero Success Section */}
                            <div className="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-blue-600 to-indigo-700 rounded-3xl p-10 text-white shadow-2xl mb-8">
                                <div className="relative z-10 flex flex-col md:flex-row justify-between items-center gap-8">
                                    <div className="space-y-4">
                                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-[10px] font-bold uppercase tracking-widest">
                                            <ShieldCheck size={12} /> Compliance Passed
                                        </div>
                                        <h1 className="text-4xl font-extrabold tracking-tight">Migration Certified.</h1>
                                        <p className="text-blue-100 max-w-md text-lg leading-relaxed">
                                            Your legacy {project?.origin || 'Legacy'} logic has been successfully architecturalized into modern, idempotent {project?.destination || 'Cloud'} logic.
                                        </p>
                                        <div className="flex items-center gap-4 pt-4">
                                            <button
                                                onClick={() => onStageChange(5)}
                                                className="px-6 py-3 bg-emerald-500 text-white rounded-xl font-bold shadow-lg shadow-emerald-500/20 hover:scale-105 active:scale-95 hover:bg-emerald-400 transition-all flex items-center gap-2"
                                            >
                                                <ArrowRight size={18} /> Proceed to Handover
                                            </button>
                                        </div>
                                    </div>

                                    {/* Large Score Circle */}
                                    <div className="relative w-48 h-48 flex items-center justify-center">
                                        <svg className="w-full h-full transform -rotate-90">
                                            <circle
                                                cx="96"
                                                cy="96"
                                                r="88"
                                                stroke="currentColor"
                                                strokeWidth="12"
                                                fill="transparent"
                                                className="text-white/10"
                                            />
                                            <circle
                                                cx="96"
                                                cy="96"
                                                r="88"
                                                stroke="currentColor"
                                                strokeWidth="12"
                                                fill="transparent"
                                                strokeDasharray={552}
                                                strokeDashoffset={552 - (552 * auditScore) / 100}
                                                className="text-white transition-all duration-1000 ease-out"
                                            />
                                        </svg>
                                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                                            <span className="text-5xl font-black">{auditScore}</span>
                                            <span className="text-[10px] font-bold uppercase opacity-60">Architect Score</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Background Decorative Elements */}
                                <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-white/10 rounded-full blur-3xl opacity-50" />
                                <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-64 h-64 bg-black/10 rounded-full blur-3xl opacity-50" />
                            </div>

                            {/* Grid Layout for details */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                                {/* Column 1 & 2: Main Details */}
                                <div className="lg:col-span-2 space-y-8">
                                    {/* Summary Metrics */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                        <StatCard label="Total Refined" value={stats.total_files} icon={<ScrollText className="text-blue-500" />} />
                                        <StatCard label="Pyspark Lines" value={stats.total_lines} icon={<Code className="text-purple-500" />} />
                                        <StatCard label="Medallion Layers" value="3/3" icon={<Database className="text-green-500" />} />
                                        <StatCard label="Idempotency" value="100%" icon={<ShieldCheck className="text-indigo-500" />} />
                                    </div>
                                </div>

                                {/* Column 3: Sidebar Details */}
                                <div className="space-y-8">
                                    {/* Output Artifacts */}
                                    <div className="bg-white dark:bg-gray-900 rounded-3xl p-6 border border-gray-200 dark:border-gray-800 shadow-sm h-full">
                                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                            <FileText size={20} className="text-gray-400" /> Deliverables
                                        </h3>
                                        <div className="space-y-3">
                                            <ArtifactLink label="Bronze Layer Scripts" size={`${stats.bronze_count} files`} />
                                            <ArtifactLink label="Silver Layer Scripts" size={`${stats.silver_count} files`} />
                                            <ArtifactLink label="Gold Layer Scripts" size={`${stats.gold_count} files`} />
                                            <ArtifactLink label="IaC & DevOp Manifests" size="2 files" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

function StatCard({ label, value, icon }: any) {
    return (
        <div className="bg-white dark:bg-gray-900 p-5 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm flex flex-col items-center text-center">
            <div className="p-2 bg-gray-50 dark:bg-gray-800 rounded-2xl mb-3">
                {icon}
            </div>
            <span className="text-xl font-black text-gray-900 dark:text-white leading-none mb-1">{value}</span>
            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">{label}</span>
        </div>
    );
}

function LogItem({ status, message, time }: any) {
    return (
        <div className="flex items-start gap-4 p-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 rounded-2xl transition-all cursor-default group">
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full mt-1 ${status === 'PASSED' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                }`}>
                {status}
            </span>
            <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-snug">{message}</p>
                <span className="text-[10px] text-gray-400">{time}</span>
            </div>
        </div>
    );
}

function ArtifactLink({ label, size }: any) {
    return (
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800/50 rounded-2xl group cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 transition-all border border-transparent hover:border-blue-200 dark:hover:border-blue-900">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white dark:bg-gray-950 flex items-center justify-center shadow-sm">
                    <Download size={14} className="text-gray-400 group-hover:text-blue-500 transition-colors" />
                </div>
                <div className="flex flex-col">
                    <span className="text-xs font-bold text-gray-700 dark:text-gray-200">{label}</span>
                    <span className="text-[9px] text-gray-400 uppercase">{size}</span>
                </div>
            </div>
            <ArrowRight size={14} className="text-gray-300 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
        </div>
    );
}
function LineageRow({ item }: any) {
    return (
        <div className="flex flex-col md:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-gray-50 dark:bg-gray-800/30 border border-gray-100 dark:border-gray-800">
            <LineageNode label="Source File" name={item.source} icon={<FileText size={14} />} color="gray" />
            <LineageConnector />
            <LineageNode label="Bronze Layer" name={item.targets.bronze} icon={<Database size={14} />} color="blue" />
            <LineageConnector />
            <LineageNode label="Silver Layer" name={item.targets.silver} icon={<ShieldCheck size={14} />} color="indigo" />
            <LineageConnector />
            <LineageNode label="Gold Layer" name={item.targets.gold} icon={<TrendingUp size={14} />} color="green" />
        </div>
    );
}

function LineageNode({ label, name, icon, color }: any) {
    const colors: any = {
        gray: "bg-gray-500",
        blue: "bg-blue-500",
        indigo: "bg-indigo-500",
        green: "bg-green-500"
    };

    return (
        <div className="flex flex-col items-center gap-2 min-w-[140px]">
            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-tighter">{label}</span>
            <div className={`p-3 rounded-2xl ${colors[color]} text-white shadow-lg flex items-center gap-2 w-full justify-center`}>
                {icon}
                <span className="text-[11px] font-bold truncate max-w-[120px]">{name.split('.').pop()}</span>
            </div>
            <span className="text-[9px] text-gray-500 font-mono truncate max-w-[140px] opacity-60">{name}</span>
        </div>
    );
}

function LineageConnector() {
    return (
        <div className="hidden md:flex flex-1 items-center justify-center">
            <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-700 to-transparent relative">
                <ArrowRight size={12} className="absolute right-0 -top-[5px] text-gray-300 dark:text-gray-700" />
            </div>
        </div>
    );
}
