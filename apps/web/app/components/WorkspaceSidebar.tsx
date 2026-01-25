"use client";

import React, { useState } from 'react';
import {
    LayoutDashboard,
    Database,
    Zap,
    ArrowRight,
    RotateCcw,
    Download,
    ChevronLeft,
    ChevronRight,
    BarChart3,
    Activity,
    Box,
    FileCode,
    Settings2
} from 'lucide-react';

interface SidebarProps {
    projectName: string;
    origin?: string;
    destination?: string;
    activeStage: number;
    stats?: {
        core: number;
        ignored: number;
        pending: number;
    };
    onAction: (action: string) => void;
}

export default function WorkspaceSidebar({
    projectName,
    origin = "Legacy SQL",
    destination = "Databricks",
    activeStage,
    stats = { core: 0, ignored: 0, pending: 0 },
    onAction
}: SidebarProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);

    return (
        <aside
            className={`bg-[#0a0a0a] border-r border-white/5 flex flex-col transition-all duration-300 ease-in-out relative z-30 ${isCollapsed ? 'w-16' : 'w-72'}`}
        >
            {/* Collapse Toggle */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="absolute -right-3 top-20 bg-cyan-600 text-white p-1 rounded-full shadow-lg shadow-cyan-600/20 hover:bg-cyan-500 transition-all z-40"
            >
                {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            </button>

            {/* Project Identity */}
            <div className={`p-6 pb-4 ${isCollapsed ? 'items-center' : ''} flex flex-col gap-4`}>
                {!isCollapsed && (
                    <div className="space-y-1">
                        <p className="text-[9px] font-black text-gray-500 uppercase tracking-[0.3em]">Active Workspace</p>
                        <h2 className="text-sm font-black text-white uppercase tracking-wider truncate" title={projectName}>
                            {projectName}
                        </h2>
                    </div>
                )}

                <div className={`flex items-center gap-3 bg-white/5 p-3 rounded-2xl border border-white/5 ${isCollapsed ? 'justify-center' : ''}`}>
                    <div className="p-2 bg-cyan-500/10 rounded-lg text-cyan-500">
                        <Database size={16} />
                    </div>
                    {!isCollapsed && (
                        <div className="flex-1 flex items-center justify-between overflow-hidden">
                            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest truncate">{origin}</span>
                            <ArrowRight size={12} className="text-gray-600 shrink-0 mx-2" />
                            <span className="text-[10px] font-bold text-cyan-500 uppercase tracking-widest truncate">{destination}</span>
                        </div>
                    )}
                </div>
            </div>

            <div className="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar py-4 px-3 space-y-8">
                {/* Discovery Section (Visual for Triage phase) */}
                <div className="space-y-4">
                    {!isCollapsed && (
                        <div className="px-3 flex items-center justify-between">
                            <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] flex items-center gap-2">
                                <BarChart3 size={12} /> Discovery
                            </h4>
                        </div>
                    )}

                    <div className="space-y-2">
                        <StatItem
                            label="Core Assets"
                            count={stats.core}
                            color="text-emerald-500"
                            bg="bg-emerald-500/10"
                            icon={<Box size={14} />}
                            isCollapsed={isCollapsed}
                        />
                        <StatItem
                            label="Ignored"
                            count={stats.ignored}
                            color="text-gray-500"
                            bg="bg-white/5"
                            icon={<FileCode size={14} />}
                            isCollapsed={isCollapsed}
                        />
                        <StatItem
                            label="Review Needed"
                            count={stats.pending}
                            color="text-amber-500"
                            bg="bg-amber-500/10"
                            icon={<Activity size={14} />}
                            isCollapsed={isCollapsed}
                        />
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="space-y-4 pt-4 border-t border-white/5">
                    {!isCollapsed && (
                        <h4 className="px-3 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] flex items-center gap-2">
                            <Zap size={12} /> Execution
                        </h4>
                    )}

                    <div className="space-y-2">
                        <ActionItem
                            label="Configure Stack"
                            icon={<Settings2 size={16} />}
                            onClick={() => onAction('config')}
                            isCollapsed={isCollapsed}
                        />
                        <ActionItem
                            label="Export Package"
                            icon={<Download size={16} />}
                            onClick={() => onAction('export')}
                            isCollapsed={isCollapsed}
                            primary
                        />
                        <ActionItem
                            label="Reset Phase"
                            icon={<RotateCcw size={16} />}
                            onClick={() => onAction('reset')}
                            isCollapsed={isCollapsed}
                            danger
                        />
                    </div>
                </div>
            </div>

            {/* Footer */}
            {!isCollapsed && (
                <div className="p-6 border-t border-white/5">
                    <div className="bg-gradient-to-br from-cyan-900/20 to-black p-4 rounded-2xl border border-cyan-500/10">
                        <p className="text-[10px] font-black text-cyan-500 uppercase tracking-widest mb-2">Stage Status</p>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            <span className="text-[10px] font-bold text-gray-300 uppercase tracking-widest">Stage {activeStage} Ready</span>
                        </div>
                    </div>
                </div>
            )}
        </aside>
    );
}

function StatItem({ label, count, color, bg, icon, isCollapsed }: any) {
    return (
        <div className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${isCollapsed ? 'justify-center' : 'hover:bg-white/5'}`}>
            <div className={`p-2 rounded-lg ${bg} ${color}`}>
                {icon}
            </div>
            {!isCollapsed && (
                <div className="flex-1 flex items-center justify-between">
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{label}</span>
                    <span className={`text-xs font-black ${color}`}>{count}</span>
                </div>
            )}
        </div>
    );
}

function ActionItem({ label, icon, onClick, isCollapsed, primary, danger }: any) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl transition-all group ${isCollapsed ? 'justify-center' : 'hover:translate-x-1'} ${primary ? 'bg-cyan-600/10 text-cyan-500 hover:bg-cyan-600 hover:text-white' :
                    danger ? 'text-gray-500 hover:text-red-500 hover:bg-red-500/10' :
                        'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
        >
            <div className={`transition-transform group-hover:scale-110 ${isCollapsed ? '' : ''}`}>
                {icon}
            </div>
            {!isCollapsed && (
                <span className="text-[10px] font-black uppercase tracking-widest">{label}</span>
            )}
        </button>
    );
}
