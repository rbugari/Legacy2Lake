"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Clock, CheckCircle, AlertCircle, Loader2, X, RefreshCw, ChevronDown, ChevronRight } from 'lucide-react';
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
    const [expandedLogs, setExpandedLogs] = useState(false);
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

        // Completion keywords (always 100%)
        if (logStr.includes('pipeline complete') || logStr.includes('refinement complete') || 
            logStr.includes('governance complete') || logStr.includes('all tasks completed')) {
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

    // === EMBEDDED / PANEL VARIANTS ===
    return (
        <div className={`bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg ${
            variant === 'panel' ? 'p-6' : 'p-4'
        }`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    {mode === 'realtime' && (
                        <>
                            {isRunning && !isComplete && !isError && (
                                <Loader2 size={24} className="text-blue-500 animate-spin" />
                            )}
                            {isComplete && (
                                <CheckCircle size={24} className="text-green-500" />
                            )}
                            {isError && (
                                <AlertCircle size={24} className="text-red-500" />
                            )}
                        </>
                    )}
                    {mode === 'history' && (
                        <Terminal size={24} className="text-cyan-500" />
                    )}
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100">
                                {mode === 'realtime' ? processName : 'Execution History'}
                            </h3>
                            <span className="px-2 py-0.5 text-[9px] font-black uppercase tracking-wider bg-gradient-to-r from-cyan-500 to-blue-500 text-white rounded-md shadow-sm">
                                Enhanced
                            </span>
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            {mode === 'realtime' 
                                ? (isRunning && !isComplete ? 'Processing...' : isComplete ? 'Completed' : 'Ready')
                                : `${logs.length} log entries`
                            }
                        </p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {mode === 'history' && (
                        <button
                            onClick={fetchLogs}
                            disabled={isRefreshing}
                            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors text-gray-600 dark:text-gray-400 disabled:opacity-50"
                            title="Refresh Logs"
                        >
                            <RefreshCw size={18} className={isRefreshing ? 'animate-spin' : ''} />
                        </button>
                    )}
                    {mode === 'realtime' && isRunning && onCancel && (
                        <button
                            onClick={onCancel}
                            className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-bold rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                    )}
                </div>
            </div>

            {/* Progress Bar (Realtime) */}
            {mode === 'realtime' && showProgress && isRunning && (
                <div className="mb-4">
                    <div className="flex justify-between items-center mb-2">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                            Progress: {progress}%
                        </span>
                        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                            <Clock size={14} />
                            <span>Last activity: {timeSince}</span>
                        </div>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                        <div
                            className={`h-full rounded-full transition-all duration-500 ${
                                isError ? 'bg-red-500' :
                                isComplete ? 'bg-green-500' :
                                'bg-blue-500 animate-pulse'
                            }`}
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Latest Log Preview (for embedded with few logs) */}
            {logs.length <= 3 && (
                <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                    <div className="flex items-start gap-3">
                        <Terminal size={16} className="text-gray-400 mt-1 shrink-0" />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-mono text-gray-700 dark:text-gray-300 break-words">
                                {latestLog}
                            </p>
                            {logs.length > 1 && (
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                    {logs.length} log entries · Last: {lastLogTime.toLocaleTimeString()}
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Full Logs (Always visible for history mode or many logs) */}
            {(mode === 'history' || logs.length > 3) && (
                <div className="mt-4">
                    {logs.length > 5 && (
                        <button
                            onClick={() => setExpandedLogs(!expandedLogs)}
                            className="mb-2 text-sm text-blue-500 hover:text-blue-600 font-medium flex items-center gap-1"
                        >
                            {expandedLogs ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                            {expandedLogs ? 'Collapse' : `View all ${logs.length} logs`}
                        </button>
                    )}
                    
                    {(expandedLogs || logs.length <= 5 || mode === 'history') && (
                        <div 
                            ref={scrollRef}
                            className="bg-black dark:bg-gray-950 rounded-lg p-4 max-h-96 overflow-y-auto custom-scrollbar"
                        >
                            {logs.length === 0 ? (
                                <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                                    <Terminal size={32} className="mb-3 opacity-20" />
                                    <p className="text-sm font-mono">{getEmptyMessage()}</p>
                                    {mode === 'realtime' && !isRunning && (
                                        <p className="text-xs mt-2 opacity-60">Click "Run Triage" to start execution</p>
                                    )}
                                </div>
                            ) : (
                                logs.map((log, idx) => (
                                    <div
                                        key={idx}
                                        className={`text-xs font-mono mb-1 ${getLogColor(log)}`}
                                    >
                                        <span className="text-gray-600 mr-2">{String(idx + 1).padStart(3, '0')}</span>
                                        {log}
                                    </div>
                                ))
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
