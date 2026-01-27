"use client";

import React from 'react';
import { Activity, Cpu, ShieldCheck, Zap } from 'lucide-react';

export default function WorkspaceShield({ status = "Initializing Workspace..." }: { status?: string }) {
    return (
        <div className="fixed inset-0 z-[200] bg-[#050505] flex flex-col items-center justify-center p-6 text-center animate-in fade-in duration-700">
            {/* Ambient Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] animate-pulse" />

            {/* Central Hexagon Shield Logo */}
            <div className="relative mb-12">
                <div className="absolute inset-0 bg-cyan-500/20 rounded-full blur-2xl animate-pulse" />
                <div className="relative w-32 h-32 flex items-center justify-center bg-black/40 border border-white/5 rounded-3xl backdrop-blur-xl shadow-2xl">
                    <Activity className="text-cyan-500 w-12 h-12" />

                    {/* Orbiting Elements */}
                    <div className="absolute inset-0 border border-cyan-500/20 rounded-3xl animate-[spin_10s_linear_infinite]" />
                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-cyan-500 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.8)]" />
                </div>
            </div>

            {/* Status Text Block */}
            <div className="relative space-y-4">
                <h2 className="text-xs font-black uppercase tracking-[0.5em] text-white/90">
                    <span className="inline-block animate-pulse">UTM ENGINE</span>
                </h2>

                <div className="flex items-center gap-4 justify-center">
                    <div className="h-[1px] w-8 bg-gradient-to-r from-transparent to-white/10" />
                    <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-500/80 min-w-[200px]">
                        {status}
                    </p>
                    <div className="h-[1px] w-8 bg-gradient-to-l from-transparent to-white/10" />
                </div>
            </div>

            {/* Progress Micro-elements */}
            <div className="mt-12 flex gap-8">
                <LoadingStep icon={<Cpu size={14} />} label="Agent Matrix" active={true} />
                <LoadingStep icon={<Zap size={14} />} label="Context Sync" active={true} delay="200ms" />
                <LoadingStep icon={<ShieldCheck size={14} />} label="Security Token" active={true} delay="400ms" />
            </div>

            <style jsx>{`
                @keyframes progress-shimmer {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(100%); }
                }
                .animate-shimmer {
                    animation: progress-shimmer 2s infinite linear;
                }
            `}</style>
        </div>
    );
}

function LoadingStep({ icon, label, active, delay = "0ms" }: any) {
    return (
        <div
            className="flex flex-col items-center gap-2 transition-all duration-700 opacity-0 slide-in-from-bottom-2 flex-1"
            style={{
                animation: `fade-in 0.5s forwards ${delay}`,
                animationFillMode: 'forwards'
            }}
        >
            <div className={`p-2 rounded-lg border ${active ? 'bg-white/5 border-white/10 text-cyan-500 shadow-lg' : 'bg-transparent border-white/5 text-gray-700'}`}>
                {icon}
            </div>
            <span className="text-[8px] font-black uppercase tracking-widest text-gray-500">
                {label}
            </span>
        </div>
    );
}
