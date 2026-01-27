"use client";

import { Map, FileEdit, Code, CheckCircle, ArrowRight, Lock, Package, ShieldCheck } from "lucide-react";

interface WorkflowToolbarProps {
    currentStage: number; // The stage the project is officially in
    activeView: number;   // The stage currently being viewed
    onSetView: (stage: number) => void;
}

const WorkflowToolbar: React.FC<WorkflowToolbarProps> = ({
    currentStage,
    activeView,
    onSetView
}) => {
    const stageGroups = [
        {
            name: "Orígenes",
            color: "bg-cyan-500/5 dark:bg-cyan-500/10",
            shadow: "shadow-[0_0_30px_rgba(6,182,212,0.1)]",
            stages: [
                { id: 1, label: "Discovery", icon: Map },
                { id: 2, label: "Triage", icon: FileEdit },
            ]
        },
        {
            name: "Core Logic",
            color: "bg-emerald-500/5 dark:bg-emerald-500/10",
            shadow: "shadow-[0_0_30px_rgba(16,185,129,0.1)]",
            stages: [
                { id: 3, label: "Drafting", icon: Code },
                { id: 4, label: "Refinement", icon: CheckCircle },
            ]
        },
        {
            name: "Salida",
            color: "bg-indigo-500/5 dark:bg-indigo-500/10",
            shadow: "shadow-[0_0_30px_rgba(99,102,241,0.1)]",
            stages: [
                { id: 5, label: "Audit", icon: ShieldCheck },
                { id: 6, label: "Handover", icon: Package },
            ]
        }
    ];

    return (
        <div className="w-full flex flex-col items-center select-none py-2">
            <div className="flex bg-white/40 dark:bg-gray-900/40 backdrop-blur-xl rounded-[2.5rem] border border-gray-200 dark:border-gray-800 p-1.5 shadow-2xl ring-1 ring-black/5 dark:ring-white/5 relative">
                {stageGroups.map((group, groupIdx) => (
                    <div key={group.name} className="flex items-center relative group/cluster">
                        {/* Group Label */}
                        <div className="absolute -top-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
                            <span className="text-[9px] font-black uppercase tracking-[0.3em] text-gray-500 opacity-0 group-hover/cluster:opacity-100 transition-opacity duration-300">
                                {group.name}
                            </span>
                        </div>

                        {/* Group Container with Shadow/Color */}
                        <div className={`flex items-center p-1 rounded-[2rem] transition-all duration-500 ${group.color} ${group.shadow} mx-0.5`}>
                            {group.stages.map((stage, idx) => {
                                const isViewing = activeView === stage.id;
                                const isLocked = stage.id > currentStage;
                                const Icon = stage.icon;

                                return (
                                    <div key={stage.id} className="flex items-center">
                                        <button
                                            onClick={() => {
                                                if (!isLocked) onSetView(stage.id);
                                            }}
                                            title={isLocked ? "Approve the current stage to proceed" : ""}
                                            className={`
                                                flex items-center gap-2.5 px-6 py-3 rounded-full text-[11px] font-black tracking-widest transition-all relative
                                                ${isViewing
                                                    ? "bg-cyan-600 text-white shadow-[0_4px_20px_rgba(6,182,212,0.3)] cursor-default scale-105 z-10"
                                                    : isLocked
                                                        ? "text-gray-400 dark:text-gray-600 cursor-not-allowed grayscale"
                                                        : "text-cyan-600 dark:text-cyan-400 hover:bg-cyan-500/10 cursor-pointer"
                                                }
                                            `}
                                        >
                                            <Icon size={16} className={isViewing ? "animate-pulse" : ""} />
                                            <span className="hidden lg:inline uppercase">{stage.label}</span>
                                            {isLocked && (
                                                <div className="absolute top-1 right-1 bg-gray-100 dark:bg-gray-800 rounded-full p-0.5 border border-gray-200 dark:border-gray-700 w-4 h-4 flex items-center justify-center">
                                                    <Lock size={10} className="text-gray-400" />
                                                </div>
                                            )}
                                        </button>

                                        {/* Inner Group Connector */}
                                        {idx < group.stages.length - 1 && (
                                            <div className="mx-1 h-0.5 w-4 bg-gray-200 dark:bg-gray-800 rounded-full opacity-30" />
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Inter-Group Connector */}
                        {groupIdx < stageGroups.length - 1 && (
                            <div className="mx-2 flex items-center justify-center">
                                <ArrowRight size={14} className="text-gray-300 dark:text-gray-700" />
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default WorkflowToolbar;
