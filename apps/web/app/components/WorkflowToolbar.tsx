"use client";

import { Map, FileEdit, Code, CheckCircle, ArrowRight } from "lucide-react";

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
        { id: 1, label: "Triaje", icon: Map },
        { id: 2, label: "Drafting", icon: FileEdit },
        { id: 3, label: "Refinamiento", icon: Code },
        { id: 4, label: "Output", icon: CheckCircle },
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
                                        ? "bg-primary text-white shadow-[0_4px_12px_rgba(59,130,246,0.3)] cursor-default scale-105 z-10"
                                        : isLocked
                                            ? "text-gray-400 dark:text-gray-600 cursor-not-allowed grayscale"
                                            : "text-primary hover:bg-primary/10 cursor-pointer hover:scale-102"
                                    }
                                `}
                            >
                                <Icon size={18} className={isViewing ? "animate-pulse" : ""} />
                                <span className="hidden md:inline uppercase tracking-wider">{stage.label}</span>
                                {isLocked && (
                                    <div className="absolute top-1 right-1 bg-gray-100 dark:bg-gray-800 rounded-full p-0.5 border border-gray-200 dark:border-gray-700 w-4 h-4 flex items-center justify-center">
                                        <ArrowRight size={10} className="text-gray-400 rotate-90" />
                                    </div>
                                )}
                            </button>

                            {/* Connector Line (except for last item) */}
                            {idx < stages.length - 1 && (
                                <div className={`mx-2 ${isLocked ? "text-gray-100 dark:text-gray-800" : "text-gray-300 dark:text-gray-700"} opacity-50`}>
                                    <ArrowRight size={16} />
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
