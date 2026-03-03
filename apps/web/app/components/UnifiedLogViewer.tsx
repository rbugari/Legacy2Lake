"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Clock, CheckCircle, AlertCircle, Loader2, X, RefreshCw } from 'lucide-react';
import { fetchWithAuth } from '../lib/auth-client';

interface UnifiedLogViewerProps {
    mode: 'realtime' | 'history';
    projectId: string;
    
    // For realtime mode
    logs?: string[];
    isRunning?: boolean;
    processName?: string;
    onCancel?: () => void;
    
    // For history mode
    autoRefresh?: boolean;
    refreshInterval?: number; // milliseconds, default 5000
    
    // Common
    showProgress?: boolean; // Show progress bar (default true for realtime)
    variant?: 'panel' | 'embedded' | 'side'; // Layout variant
    onClose?: () => void; // For side panel / dialog variants
}

export default function UnifiedLogViewer({
    mode,
    projectId,
    logs: realtimeLogs = [],
    isRunning = false,
    processName = 'Process',
    onCancel,
    autoRefresh = true,
    refreshInterval = 5000,
    showProgress: showProgressProp,
    variant = 'embedded',
    onClose
}: UnifiedLogViewerProps) {
    const [historyLogs, setHistoryLogs] = useState<string[]>([]);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [autoScroll, setAutoScroll] = useState(true);
    const [lastLogTime, setLastLogTime] = useState<Date>(new Date());
    const [progress, setProgress] = useState(0);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Determine which logs to use
    const logs = mode === 'realtime' ? realtimeLogs : historyLogs;
    const showProgress = showProgressProp ?? (mode === 'realtime');

    // Fetch logs for history mode
    const fetchLogs = async () => {
        if (mode !== 'history' || !projectId) return;
        setIsRefreshing(true);
        try {
            const res = await fetchWithAuth(`projects/${projectId}/logs`);
            const data = await res.json();
            if (data.logs) {
                const logLines = data.logs.split("\n").filter((l: string) => l.trim() !== "");
                setHistoryLogs(logLines);
            }
        } catch (e) {
            console.error("[UnifiedLogViewer] Failed to load logs", e);
        } finally {
            setIsRefreshing(false);
        }
    };

    // Auto-refresh for history mode
    useEffect(() => {
        if (mode === 'history' && autoRefresh) {
            fetchLogs();
            const interval = setInterval(fetchLogs, refreshInterval);
            return () => clearInterval(interval);
        }
    }, [mode, autoRefresh, refreshInterval, projectId]);

    // Update last log time when new logs arrive
    useEffect(() => {
        if (logs.length > 0) {
            setLastLogTime(new Date());
        }
    }, [logs.length]);

    // Auto-scroll
    useEffect(() => {
        if (autoScroll && scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, autoScroll]);

    // Estimate progress based on logs (for realtime mode)
    useEffect(() => {
        if (mode !== 'realtime' || !showProgress) return;

        if (logs.length === 0) {
            setProgress(5);
            return;
        }

        const logStr = logs.join('\n').toLowerCase();
        const logRaw = logs.join('\n');

        // === Priority 1: Explicit [PROGRESS: X/Y] markers (asset-level, most accurate) ===
        const progressMatches = logRaw.match(/\[PROGRESS:\s*(\d+)\/(\d+)\]/g);
        if (progressMatches && progressMatches.length > 0) {
            const last = progressMatches[progressMatches.length - 1];
            const parts = last.match(/\[PROGRESS:\s*(\d+)\/(\d+)\]/);
            if (parts) {
                const current = parseInt(parts[1]);
                const total = parseInt(parts[2]);
                if (total > 0) {
                    // Scale to 15–95%: init (0–15%) → execution (15–95%) → finalization (95–100%)
                    const scaled = Math.round(15 + (current / total) * 80);
                    setProgress(prev => Math.max(prev, Math.min(scaled, 95)));
                    return;
                }
            }
        }

        // === Priority 2: [PHASE PROGRESS: X/Y] markers (refinement 4-phase pipeline) ===
        const phaseMatches = logRaw.match(/\[PHASE PROGRESS:\s*(\d+)\/(\d+)\]/g);
        if (phaseMatches && phaseMatches.length > 0) {
            const last = phaseMatches[phaseMatches.length - 1];
            const parts = last.match(/\[PHASE PROGRESS:\s*(\d+)\/(\d+)\]/);
            if (parts) {
                const current = parseInt(parts[1]);
                const total = parseInt(parts[2]);
                if (total > 0) {
                    const scaled = Math.round(10 + (current / total) * 80);
                    setProgress(prev => Math.max(prev, Math.min(scaled, 90)));
                    return;
                }
            }
        }

        // Completion keywords (always 100%)
        if (logStr.includes('pipeline complete') || logStr.includes('refinement complete') ||
            logStr.includes('governance complete') || logStr.includes('all tasks completed') ||
            logStr.includes('pipeline complete —')) {
            setProgress(100);
            return;
        }

        // Failure keywords (freeze progress)
        if (logStr.includes('failed') || logStr.includes('cancelled')) {
            return; // Don't update progress on error
        }

        // Refinement-specific stage detection (P -> A -> R -> O)
        let estimatedProgress = 10;

        // Agent O (Ops) - Final packaging [90-98%]
        if (logStr.includes('agent o') || logStr.includes('ops agent') || 
            logStr.includes('packaging') || logStr.includes('deployment')) {
            estimatedProgress = 90;
        }
        // Agent R (Refactor) - Code optimization [60-75%]
        else if (logStr.includes('agent r') || logStr.includes('refactor') || 
                 logStr.includes('reasoning') || logStr.includes('optimizing')) {
            estimatedProgress = 70;
        }
        // Agent A (Architect) - Design patterns [40-55%]
        else if (logStr.includes('agent a') || logStr.includes('architect') || 
                 logStr.includes('medallion') || logStr.includes('designing')) {
            estimatedProgress = 50;
        }
        // Agent P (Profiler) - Analysis [20-35%]
        else if (logStr.includes('agent p') || logStr.includes('profiler') || 
                 logStr.includes('analyzing') || logStr.includes('scanning')) {
            estimatedProgress = 30;
        }
        // General execution keywords
        else if (logStr.includes('executing') || logStr.includes('processing')) {
            estimatedProgress = 40;
        }
        // Agent C (Coder) - Generation [25-40%]
        else if (logStr.includes('agent c') || logStr.includes('coder') || 
                 logStr.includes('generating')) {
            estimatedProgress = 35;
        }
        // Agent F (Critic) - Validation [15-25%]
        else if (logStr.includes('agent f') || logStr.includes('critic') || 
                 logStr.includes('validating') || logStr.includes('reviewing')) {
            estimatedProgress = 20;
        }
        // Initialization
        else if (logStr.includes('starting') || logStr.includes('initializ') || 
                 logStr.includes('loading') || logStr.includes('clearing logs')) {
            estimatedProgress = 15;
        }

        // Add small increment based on log count (shows activity)
        const logBonus = Math.min(logs.length * 0.3, 8);
        const finalProgress = Math.min(estimatedProgress + logBonus, 98);

        // Only move progress forward (never backwards)
        setProgress(prev => Math.max(prev, Math.round(finalProgress)));

    }, [logs, mode, showProgress]);

    const getTimeSinceLastLog = () => {
        const seconds = Math.floor((new Date().getTime() - lastLogTime.getTime()) / 1000);
        if (seconds < 60) return `${seconds}s ago`;
        const minutes = Math.floor(seconds / 60);
        return `${minutes}m ago`;
    };

    const [timeSince, setTimeSince] = useState(getTimeSinceLastLog());

    // Update time since every second (realtime only)
    useEffect(() => {
        if (mode !== 'realtime' || !isRunning) return;
        const interval = setInterval(() => {
            setTimeSince(getTimeSinceLastLog());
        }, 1000);
        return () => clearInterval(interval);
    }, [mode, isRunning, lastLogTime]);

    // Determine log status
    const getEmptyMessage = () => {
        if (mode === 'realtime') {
            if (isRunning) return 'Initializing process...';
            return 'No execution in progress. Start a process to see logs here.';
        }
        return 'No historical logs available. Execute the process at least once.';
    };
    
    const latestLog = logs[logs.length - 1] || getEmptyMessage();
    const isError = latestLog.toLowerCase().includes('error');
    const isComplete = latestLog.toLowerCase().includes('complete') || latestLog.toLowerCase().includes('success');

    // Get log line color
    const getLogColor = (line: string) => {
        const lower = line.toLowerCase();
        if (lower.includes('[error]') || lower.includes('error')) return 'text-red-400';
        if (lower.includes('[warn]') || lower.includes('warning')) return 'text-yellow-400';
        if (lower.includes('success') || lower.includes('complete')) return 'text-emerald-400';
        if (lower.includes('starting') || lower.includes('executing')) return 'text-cyan-400';
        return 'text-gray-400';
    };

    // === SIDE PANEL VARIANT ===
    if (variant === 'side') {
        return (
            <div className="fixed top-0 right-0 h-full w-[450px] bg-[#0a0a0a] border-l border-white/5 z-[100] shadow-2xl flex flex-col font-mono animate-in slide-in-from-right duration-300">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-black/40 backdrop-blur-xl shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-cyan-500/10 rounded-lg">
                            <Terminal size={18} className="text-cyan-500" />
                        </div>
                        <div>
                            <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-white">
                                {mode === 'realtime' ? processName : 'Console Output'}
                            </h3>
                            <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-0.5">
                                {mode === 'realtime' ? 'Live Processing' : 'History Logs'}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {mode === 'history' && (
                            <button
                                onClick={fetchLogs}
                                className={`p-2 hover:bg-white/5 rounded-lg transition-colors ${isRefreshing ? 'animate-spin text-cyan-500' : 'text-gray-400'}`}
                                title="Manual Refresh"
                            >
                                <RefreshCw size={16} />
                            </button>
                        )}
                        {onClose && (
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-red-500/10 hover:text-red-500 rounded-lg transition-colors text-gray-400"
                            >
                                <X size={18} />
                            </button>
                        )}
                    </div>
                </div>

                {/* Progress Bar (Realtime) */}
                {mode === 'realtime' && showProgress && isRunning && (
                    <div className="px-6 py-3 border-b border-white/5 bg-black/20">
                        <div className="flex justify-between items-center mb-2">
                            <span className="text-[10px] font-bold text-gray-300 uppercase tracking-wider">
                                Progress: {progress}%
                            </span>
                            <div className="flex items-center gap-2 text-[9px] text-gray-500 uppercase tracking-wider">
                                <Clock size={12} />
                                <span>{timeSince}</span>
                            </div>
                        </div>
                        <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all duration-500 ${
                                    isError ? 'bg-red-500' :
                                    isComplete ? 'bg-green-500' :
                                    'bg-cyan-500 animate-pulse'
                                }`}
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                    </div>
                )}

                {/* Scroll Control */}
                <div className="px-6 py-2 bg-white/5 border-b border-white/5 flex justify-between items-center shrink-0">
                    <label className="flex items-center gap-2 cursor-pointer group">
                        <input
                            type="checkbox"
                            checked={autoScroll}
                            onChange={(e) => setAutoScroll(e.target.checked)}
                            className="w-3 h-3 rounded bg-black border-white/10 text-cyan-500 focus:ring-0"
                        />
                        <span className="text-[9px] font-bold text-gray-400 group-hover:text-white transition-colors uppercase tracking-widest">Auto-Scroll</span>
                    </label>
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
                            <div className="text-center">
                                <p className="text-[10px] uppercase font-black tracking-widest opacity-30 mb-2">
                                    {mode === 'realtime' && isRunning ? 'Initializing...' : 'No Logs Available'}
                                </p>
                                <p className="text-[9px] text-gray-700 opacity-50">
                                    {mode === 'realtime' 
                                        ? (isRunning ? 'Waiting for process output...' : 'Start a process to see logs')
                                        : 'No historical execution logs found'
                                    }
                                </p>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-1.5">
                            {logs.map((line, i) => (
                                <div key={i} className="flex gap-4 group">
                                    <span className="text-[9px] text-gray-700 select-none w-8 text-right shrink-0 group-hover:text-gray-500">
                                        {i + 1}
                                    </span>
                                    <div className={`text-[11px] leading-relaxed whitespace-pre-wrap break-all ${getLogColor(line)}`}>
                                        <span className="text-white/20 mr-2 opacity-0 group-hover:opacity-100 transition-opacity">›</span>
                                        {line}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/5 bg-black/40 text-[9px] font-bold text-gray-500 uppercase tracking-widest flex justify-between items-center shrink-0">
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        <span>{mode === 'realtime' && isRunning ? 'Processing' : 'Ready'}</span>
                    </div>
                    <div>PROJECT: {projectId.substring(0, 8)}</div>
                </div>
            </div>
        );
    }

    // === EMBEDDED / PANEL VARIANTS — dark terminal (uniform across all phases) ===
    return (
        <div className="flex flex-col h-full min-h-[320px] bg-[#0a0a0a] border border-white/5 rounded-2xl overflow-hidden font-mono">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-3 border-b border-white/5 bg-black/40 backdrop-blur shrink-0">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-cyan-500/10 rounded-lg">
                        {
                            mode === 'realtime' && isRunning && !isComplete && !isError
                                ? <Loader2 size={15} className="text-cyan-400 animate-spin" />
                                : isComplete
                                    ? <CheckCircle size={15} className="text-emerald-400" />
                                    : isError
                                        ? <AlertCircle size={15} className="text-red-400" />
                                        : <Terminal size={15} className="text-cyan-400" />
                        }
                    </div>
                    <div>
                        <p className="text-[10px] font-black uppercase tracking-[0.18em] text-white">
                            {mode === 'realtime' ? processName : 'Console Output'}
                        </p>
                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-0.5">
                            {mode === 'realtime'
                                ? (isRunning && !isComplete ? 'Live · Processing' : isComplete ? 'Complete' : 'Idle')
                                : `${logs.length} entries`}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {mode === 'history' && (
                        <button
                            onClick={fetchLogs}
                            disabled={isRefreshing}
                            className={`p-1.5 hover:bg-white/5 rounded-lg transition-colors ${
                                isRefreshing ? 'animate-spin text-cyan-400' : 'text-gray-500 hover:text-gray-300'
                            }`}
                            title="Refresh"
                        >
                            <RefreshCw size={14} />
                        </button>
                    )}
                    {mode === 'realtime' && isRunning && onCancel && (
                        <button
                            onClick={onCancel}
                            className="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-400 text-[10px] font-black uppercase tracking-widest rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                    )}
                </div>
            </div>

            {/* Progress Bar */}
            {mode === 'realtime' && showProgress && isRunning && (
                <div className="px-5 py-2.5 border-b border-white/5 bg-black/20 shrink-0">
                    <div className="flex justify-between items-center mb-1.5">
                        <span className="text-[9px] font-bold text-gray-400 uppercase tracking-wider">
                            Progress: {progress}%
                        </span>
                        <div className="flex items-center gap-1.5 text-[9px] text-gray-600 uppercase tracking-wider">
                            <Clock size={10} />
                            <span>{timeSince}</span>
                        </div>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                        <div
                            className={`h-full rounded-full transition-all duration-500 ${
                                isError ? 'bg-red-500' :
                                isComplete ? 'bg-emerald-500' :
                                'bg-cyan-500 animate-pulse'
                            }`}
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Scroll control */}
            <div className="px-5 py-1.5 bg-white/[0.02] border-b border-white/5 flex justify-between items-center shrink-0">
                <label className="flex items-center gap-1.5 cursor-pointer group">
                    <input
                        type="checkbox"
                        checked={autoScroll}
                        onChange={(e) => setAutoScroll(e.target.checked)}
                        className="w-3 h-3 rounded bg-black border-white/10 text-cyan-500 focus:ring-0"
                    />
                    <span className="text-[9px] font-bold text-gray-500 group-hover:text-gray-300 transition-colors uppercase tracking-widest">
                        Auto-scroll
                    </span>
                </label>
                <span className="text-[9px] font-bold text-gray-600 uppercase tracking-widest">{logs.length} lines</span>
            </div>

            {/* Logs area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-5 scroll-smooth custom-scrollbar bg-black/20"
            >
                {logs.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-3">
                        <Terminal size={28} className="opacity-10" />
                        <p className="text-[10px] uppercase font-black tracking-widest opacity-30">
                            {mode === 'realtime' && isRunning ? 'Initializing...' : 'No Logs Available'}
                        </p>
                        <p className="text-[9px] text-gray-700 opacity-50">
                            {mode === 'realtime'
                                ? (isRunning ? 'Waiting for output...' : 'Start a process to see logs')
                                : 'No historical execution logs found'}
                        </p>
                    </div>
                ) : (
                    <div className="space-y-1">
                        {logs.map((line, i) => (
                            <div key={i} className="flex gap-3 group">
                                <span className="text-[9px] text-gray-700 select-none w-8 text-right shrink-0 group-hover:text-gray-500">
                                    {i + 1}
                                </span>
                                <div className={`text-[11px] leading-relaxed whitespace-pre-wrap break-all ${getLogColor(line)}`}>
                                    <span className="text-white/20 mr-1.5 opacity-0 group-hover:opacity-100 transition-opacity">›</span>
                                    {line}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="px-5 py-2.5 border-t border-white/5 bg-black/40 text-[9px] font-bold text-gray-600 uppercase tracking-widest flex justify-between items-center shrink-0">
                <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${
                        isError ? 'bg-red-500' :
                        isComplete ? 'bg-emerald-500' :
                        isRunning ? 'bg-cyan-500 animate-pulse' :
                        'bg-gray-600'
                    }`} />
                    <span>{isError ? 'Error' : isComplete ? 'Done' : isRunning ? 'Running' : 'Ready'}</span>
                </div>
                <div>Project: {projectId.substring(0, 8)}</div>
            </div>
        </div>
    );
}
