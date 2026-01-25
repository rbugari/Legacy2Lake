"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, X, RefreshCw, Trash2, ChevronRight, Play, Square, Settings } from 'lucide-react';
import { fetchWithAuth } from '../lib/auth-client';

interface LogsSidePanelProps {
    projectId: string;
    isOpen: boolean;
    onClose: () => void;
}

export default function LogsSidePanel({ projectId, isOpen: propOpen, onClose }: LogsSidePanelProps) {
    const [internalOpen, setInternalOpen] = React.useState(false);

    React.useEffect(() => {
        const handleToggle = (e: any) => {
            if (e.detail?.open !== undefined) setInternalOpen(e.detail.open);
        };
        window.addEventListener('toggle-logs', handleToggle);
        return () => window.removeEventListener('toggle-logs', handleToggle);
    }, []);

    const isOpen = propOpen || internalOpen;
    const [logs, setLogs] = React.useState<string[]>([]);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [autoScroll, setAutoScroll] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    const fetchLogs = async () => {
        if (!projectId) return;
        setIsRefreshing(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/logs`);
            const data = await res.json();
            if (data.logs) {
                const logLines = data.logs.split("\n").filter((l: string) => l.trim() !== "");
                setLogs(logLines);
            }
        } catch (e) {
            console.error("Failed to load global logs", e);
        } finally {
            setIsRefreshing(false);
        }
    };

    useEffect(() => {
        if (isOpen) {
            fetchLogs();
            const interval = setInterval(fetchLogs, 5000);
            return () => clearInterval(interval);
        }
    }, [isOpen, projectId]);

    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, autoScroll]);

    if (!isOpen) return null;

    return (
        <div className="fixed top-0 right-0 h-full w-[450px] bg-[#0a0a0a] border-l border-white/5 z-[100] shadow-2xl flex flex-col font-mono animate-in slide-in-from-right duration-500 ease-out">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black/40 backdrop-blur-xl shrink-0">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-cyan-500/10 rounded-lg">
                        <Terminal size={18} className="text-cyan-500" />
                    </div>
                    <div>
                        <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-white">Console Output</h3>
                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-0.5">Live Monitoring</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={fetchLogs}
                        className={`p-2 hover:bg-white/5 rounded-lg transition-colors ${isRefreshing ? 'animate-spin text-cyan-500' : 'text-gray-400'}`}
                        title="Manual Refresh"
                    >
                        <RefreshCw size={16} />
                    </button>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-red-500/10 hover:text-red-500 rounded-lg transition-colors text-gray-400"
                    >
                        <X size={18} />
                    </button>
                </div>
            </div>

            {/* Scroll Control */}
            <div className="px-6 py-2 bg-white/5 border-b border-white/5 flex justify-between items-center shrink-0">
                <div className="flex items-center gap-4">
                    <label className="flex items-center gap-2 cursor-pointer group">
                        <input
                            type="checkbox"
                            checked={autoScroll}
                            onChange={(e) => setAutoScroll(e.target.checked)}
                            className="w-3 h-3 rounded bg-black border-white/10 text-cyan-500 focus:ring-0 focus:ring-offset-0"
                        />
                        <span className="text-[9px] font-bold text-gray-400 group-hover:text-white transition-colors uppercase tracking-widest">Auto-Scroll</span>
                    </label>
                </div>
                <span className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">{logs.length} Lines</span>
            </div>

            {/* Logs Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-6 scroll-smooth custom-scrollbar bg-black/20"
            >
                {logs.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-4">
                        <Terminal size={32} className="opacity-10" />
                        <p className="text-[10px] uppercase font-black tracking-widest opacity-30">Waiting for agent activity...</p>
                    </div>
                ) : (
                    <div className="space-y-1.5">
                        {logs.map((line, i) => (
                            <div key={i} className="flex gap-4 group">
                                <span className="text-[9px] text-gray-700 select-none w-8 text-right shrink-0 group-hover:text-gray-500">{i + 1}</span>
                                <div className={`text-[11px] leading-relaxed whitespace-pre-wrap break-all ${line.includes('[ERROR]') ? 'text-red-400' :
                                    line.includes('[WARN]') ? 'text-yellow-400' :
                                        line.includes('SUCCESS') || line.includes('Complete') ? 'text-emerald-400' :
                                            line.includes('Starting') || line.includes('Executing') ? 'text-cyan-400' : 'text-gray-400'
                                    }`}>
                                    <span className="text-white/20 mr-2 opacity-0 group-hover:opacity-100 transition-opacity">›</span>
                                    {line}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Footer / Stats */}
            <div className="p-4 border-t border-white/5 bg-black/40 text-[9px] font-bold text-gray-500 uppercase tracking-widest flex justify-between items-center shrink-0">
                <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span>System Online</span>
                </div>
                <div>PROJECT ID: {projectId}</div>
            </div>
        </div>
    );
}
