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
    const stages = [
        { id: 0, label: "Discovery", icon: Map },
        { id: 1, label: "Triaje", icon: FileEdit },
        { id: 2, label: "Drafting", icon: Code },
        { id: 3, label: "Refinamiento", icon: CheckCircle },
        { id: 4, label: "Auditoría", icon: ShieldCheck }, // Renamed Output to Auditoría for flow
        { id: 5, label: "Handover", icon: Package },
    ];

    return (
        <div className="w-full max-w-3xl mx-auto my-6 select-none flex items-center justify-center">
            <div className="flex items-center justify-between bg-white/80 dark:bg-gray-900/80 backdrop-blur-md rounded-full border border-gray-200 dark:border-gray-800 p-2 shadow-lg ring-1 ring-black/5 dark:ring-white/5">
                {stages.map((stage, idx) => {
                    const isViewing = activeView === stage.id;
                    const isLocked = stage.id > currentStage;
                    const isCompleted = currentStage > stage.id;
                    const Icon = stage.icon;

                    return (
                        <div key={stage.id} className="flex items-center">
                            <button
                                onClick={() => {
                                    if (!isLocked) onSetView(stage.id);
                                }}
                                title={isLocked ? "Approve the current stage to proceed" : ""}
                                className={`
                                    flex items-center gap-2.5 px-6 py-3 rounded-full text-sm font-black transition-all relative
                                    ${isViewing
                                        ? "bg-cyan-600 text-white shadow-[0_4px_20px_rgba(6,182,212,0.3)] cursor-default scale-105 z-10"
                                        : isLocked
                                            ? "text-gray-400 dark:text-gray-600 cursor-not-allowed grayscale"
                                            : "text-cyan-600 dark:text-cyan-400 hover:bg-cyan-500/10 cursor-pointer hover:scale-102"
                                    }
                                `}
                            >
                                <Icon size={18} className={isViewing ? "animate-pulse" : ""} />
                                <span className="hidden md:inline uppercase tracking-widest">{stage.label}</span>
                                {isLocked && (
                                    <div className="absolute top-1 right-1 bg-gray-100 dark:bg-gray-800 rounded-full p-0.5 border border-gray-200 dark:border-gray-700 w-4 h-4 flex items-center justify-center">
                                        <Lock size={10} className="text-gray-400" />
                                    </div>
                                )}
                            </button>

                            {/* Connector Line (except for last item) */}
                            {idx < stages.length - 1 && (
                                <div className={`mx-2 ${isLocked ? "text-gray-100 dark:text-gray-800" : "text-cyan-500/30 dark:text-cyan-500/20"} opacity-50`}>
                                    <div className="h-px w-6 bg-current" />
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default WorkflowToolbar;
