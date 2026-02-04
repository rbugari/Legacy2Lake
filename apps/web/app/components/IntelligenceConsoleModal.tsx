"use client";
import { X, Cpu, Code, ArrowRight } from "lucide-react";
import PromptsExplorer from "./PromptsExplorer";
import { useState, useEffect } from "react";

interface IntelligenceConsoleModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId?: string;
    stage?: 'triage' | 'drafting' | 'refinement' | 'all';
    originTech?: string;
    destTech?: string;
}

export default function IntelligenceConsoleModal({
    isOpen,
    onClose,
    projectId,
    stage = 'all',
    originTech,
    destTech
}: IntelligenceConsoleModalProps) {
    const [animate, setAnimate] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setAnimate(true);
        } else {
            setAnimate(false);
        }
    }, [isOpen]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 sm:p-6 lg:p-8">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/90 backdrop-blur-md animate-in fade-in duration-300"
                onClick={onClose}
            />

            {/* Modal Container */}
            <div className={`relative w-full h-full bg-[#0a0a0a] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden transition-all duration-500 ease-out ${animate ? 'scale-100 opacity-100' : 'scale-95 opacity-0'}`}>

                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-black/40">
                    <div className="flex items-center gap-4">
                        <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                            <Cpu size={20} />
                        </div>
                        <div>
                            <h2 className="text-sm font-black uppercase tracking-[0.2em] text-white">
                                Intelligence Console
                            </h2>
                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-0.5 flex items-center gap-2">
                                {originTech?.toUpperCase() || 'UNKNOWN'} <ArrowRight size={10} /> {destTech?.toUpperCase() || 'UNKNOWN'}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-white/10 rounded-xl transition-colors text-gray-400 hover:text-white"
                        title="Close Console"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden p-6 bg-[#050505]">
                    <PromptsExplorer
                        className="h-full"
                        projectId={projectId}
                        stage={stage}
                        originTech={originTech}
                        destTech={destTech}
                    />
                </div>

                {/* Footer Status */}
                <div className="px-6 py-2 bg-black/60 border-t border-white/5 text-[10px] text-gray-600 font-mono flex justify-between uppercase tracking-widest">
                    <span>Session ID: {projectId || 'GLOBAL_AUDIT'}</span>
                    <span>System Status: ONLINE</span>
                </div>
            </div>
        </div>
    );
}
