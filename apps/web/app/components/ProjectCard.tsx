"use client";
import Link from "next/link";
import { Github, FolderPlus, Settings, Trash2, RefreshCw, AlertCircle, FileText, Package, Archive, Database } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface ProjectCardProps {
    project: {
        id: string;
        name: string;
        progress: number;
        stage: number | string;
        origin: string;
        assets_count?: number;
        alerts?: number;
        updated_at?: string;
        source_tech?: string;
        target_tech?: string;
    };
    onDelete: (e: React.MouseEvent, id: string) => void;
    onReset: (e: React.MouseEvent, id: string) => void;
}

export default function ProjectCard({ project, onDelete, onReset }: ProjectCardProps) {
    const stageMap: { [key: string]: { label: string; color: string; emoji: string } } = {
        "1": { label: "DISCOVERY", color: "from-slate-500 to-slate-600", emoji: "🔭" },
        "2": { label: "TRIAGE", color: "from-cyan-500 to-teal-500", emoji: "🔍" },
        "3": { label: "DRAFTING", color: "from-blue-500 to-indigo-500", emoji: "📐" },
        "4": { label: "REFINEMENT", color: "from-emerald-500 to-green-500", emoji: "⚡" },
        "5": { label: "GOVERNANCE", color: "from-teal-500 to-emerald-600", emoji: "🛡️" },
        "6": { label: "HANDOVER", color: "from-blue-600 to-cyan-600", emoji: "🚀" }
    };
    const currentStage = stageMap[project.stage.toString()] || { label: "INITIATED", color: "from-slate-500 to-slate-600", emoji: "🏁" };

    const getOriginConfig = (origin: string) => {
        switch (origin.toLowerCase()) {
            case "github":
                return { label: "GitHub Repository", icon: <Github size={14} className="text-cyan-500" /> };
            case "zip":
            case "local_zip":
                return { label: "Local Archive", icon: <Archive size={14} className="text-emerald-500" /> };
            case "manual":
            case "upload":
                return { label: "Manual Upload", icon: <Package size={14} className="text-blue-500" /> };
            default:
                return { label: "Legacy Source", icon: <Database size={14} className="text-gray-500" /> };
        }
    };

    const originConfig = getOriginConfig(project.origin);

    return (
        <div className="group relative">
            {/* Glow effect on hover */}
            <div className={cn(
                "absolute -inset-0.5 bg-gradient-to-r rounded-2xl blur opacity-0 group-hover:opacity-75 transition duration-700",
                currentStage.color
            )} />

            {/* Main Card */}
            <div className="relative bg-[var(--surface)] backdrop-blur-xl border border-[var(--border)] rounded-2xl p-6 flex flex-col h-full hover:border-[var(--accent)]/50 transition-all duration-300 shadow-lg dark:shadow-[0_0_30px_rgba(0,0,0,0.4)] hover:shadow-2xl">

                {/* Header Row */}
                <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-2 text-[var(--text-tertiary)] text-[10px] font-bold tracking-widest uppercase">
                        {originConfig.icon}
                        {originConfig.label}
                    </div>

                    <div className={cn(
                        "px-3 py-1 rounded-full text-[10px] font-black tracking-wider uppercase text-white shadow-lg flex items-center gap-1.5 bg-gradient-to-r",
                        currentStage.color
                    )}>
                        <span>{currentStage.emoji}</span>
                        {currentStage.label}
                    </div>
                </div>

                {/* Project Title */}
                <Link href={`/workspace?id=${project.id}`} className="block group/title">
                    <h3 className="text-xl font-bold mb-1 text-[var(--text-primary)] group-hover/title:text-cyan-500 transition-colors line-clamp-1">
                        {project.name}
                    </h3>
                    <p className="text-xs text-[var(--text-tertiary)] mb-4 font-mono">
                        {project.source_tech && project.target_tech ? (
                            <>
                                <span className="text-cyan-500 font-bold">{project.source_tech}</span>
                                <span className="mx-2 opacity-40">→</span>
                                <span className="text-blue-500 font-bold">{project.target_tech}</span>
                            </>
                        ) : (
                            <span className="opacity-40 italic">Tech stack not defined yet</span>
                        )}
                    </p>
                </Link>

                {/* Progress Bar */}
                <div className="mb-6">
                    <div className="flex justify-between items-end mb-2 px-0.5">
                        <span className="text-[10px] font-bold text-[var(--text-tertiary)] uppercase tracking-tight">Progress</span>
                        <span className="text-sm font-black text-cyan-500">{project.progress}%</span>
                    </div>
                    <div className="h-2.5 w-full bg-[var(--background-secondary)] rounded-full overflow-hidden shadow-inner">
                        <div
                            className={cn(
                                "h-full rounded-full transition-all duration-1000 ease-out relative bg-gradient-to-r shadow-lg",
                                currentStage.color
                            )}
                            style={{ width: `${project.progress}%` }}
                        >
                            {/* Shimmer effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"
                                style={{ backgroundSize: '200% 100%' }} />
                        </div>
                    </div>
                </div>

                {/* Metrics Row */}
                <div className="flex items-center gap-4 mb-6 mt-auto">
                    <div className="flex items-center gap-2 text-xs font-medium text-[var(--text-secondary)]">
                        <FileText size={14} className="text-cyan-400" />
                        <span className="font-bold">{project.assets_count || 0}</span>
                        <span className="opacity-60">assets</span>
                    </div>

                    {project.alerts && project.alerts > 0 ? (
                        <div className="flex items-center gap-2 text-xs font-medium text-orange-400">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                            </span>
                            <span className="font-bold">{project.alerts} alerts</span>
                        </div>
                    ) : (
                        <div className="flex items-center gap-2 text-xs font-medium text-emerald-400">
                            <AlertCircle size={14} />
                            <span className="font-bold">Healthy</span>
                        </div>
                    )}
                </div>

                {/* Footer / Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
                    <Link
                        href={`/workspace?id=${project.id}`}
                        className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-cyan-600/30 active:scale-95 relative overflow-hidden group/btn"
                    >
                        <span className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-700"></span>
                        <span className="relative">Open Project</span>
                    </Link>

                    <div className="flex items-center gap-1">
                        {parseInt(project.stage.toString()) > 1 && (
                            <button
                                onClick={(e) => onReset(e, project.id)}
                                className="p-2 text-[var(--text-tertiary)] hover:text-cyan-500 hover:bg-cyan-500/10 rounded-lg transition-all"
                                title="Reset to Triage"
                            >
                                <RefreshCw size={18} />
                            </button>
                        )}
                        <Link
                            href={`/workspace/settings?id=${project.id}`}
                            className="p-2 text-[var(--text-tertiary)] hover:text-white hover:bg-white/5 rounded-lg transition-all"
                            title="Settings"
                        >
                            <Settings size={18} />
                        </Link>
                        <button
                            onClick={(e) => onDelete(e, project.id)}
                            className="p-2 text-[var(--text-tertiary)] hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                            title="Delete"
                        >
                            <Trash2 size={18} />
                        </button>
                    </div>
                </div>
            </div>

            <style jsx>{`
                @keyframes shimmer {
                    0% { background-position: -200% 0; }
                    100% { background-position: 200% 0; }
                }
                .animate-shimmer {
                    animation: shimmer 3s infinite linear;
                }
            `}</style>
        </div>
    );
}
