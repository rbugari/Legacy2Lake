"use client";

import React, { useState, useEffect } from 'react';
import { Terminal, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface ProcessProgressProps {
    isRunning: boolean;
    logs: string[];
    processName: string;
    onCancel?: () => void;
}

export default function ProcessProgress({
    isRunning,
    logs,
    processName,
    onCancel
}: ProcessProgressProps) {
    const [lastLogTime, setLastLogTime] = useState<Date>(new Date());
    const [progress, setProgress] = useState(0);

    // Update last log time when new logs arrive
    useEffect(() => {
        if (logs.length > 0) {
            setLastLogTime(new Date());
        }
    }, [logs.length]);

    // Estimate progress based on logs (improved heuristic)
    useEffect(() => {
        if (logs.length === 0) {
            setProgress(5);
            return;
        }

        const logStr = logs.join('\n').toLowerCase();

        // Completion keywords
        if (logStr.includes('complete') || logStr.includes('success') || logStr.includes('finished') || logStr.includes('pipeline complete')) {
            setProgress(100);
            return;
        }

        // Failure keywords
        if (logStr.includes('failed') || logStr.includes('error') || logStr.includes('cancelled')) {
            // Keep current progress but maybe cap it or show it differently? 
            // For now just let it be, but these usually stop the process.
            return;
        }

        // Stage-based heuristics
        let estimatedProgress = 10;

        if (logStr.includes('agent o') || logStr.includes('orchestrat')) estimatedProgress = 90;
        else if (logStr.includes('agent r') || logStr.includes('reasoning') || logStr.includes('refining')) estimatedProgress = 75;
        else if (logStr.includes('agent a') || logStr.includes('architect')) estimatedProgress = 60;
        else if (logStr.includes('agent c') || logStr.includes('coder') || logStr.includes('generating')) estimatedProgress = 45;
        else if (logStr.includes('agent f') || logStr.includes('critic') || logStr.includes('validating')) estimatedProgress = 30;
        else if (logStr.includes('starting') || logStr.includes('initializ') || logStr.includes('loading')) estimatedProgress = 15;

        // Add a small increment based on number of logs to show "movement" 
        // within a stage, capped to not jump to next stage prematurely
        const logBonus = Math.min(logs.length * 0.5, 10);
        const finalProgress = Math.min(estimatedProgress + logBonus, 98);

        // Only update if progress increased to prevent jumping back
        setProgress(prev => Math.max(prev, Math.round(finalProgress)));

    }, [logs]);

    const getTimeSinceLastLog = () => {
        const seconds = Math.floor((new Date().getTime() - lastLogTime.getTime()) / 1000);
        if (seconds < 60) return `${seconds}s ago`;
        const minutes = Math.floor(seconds / 60);
        return `${minutes}m ago`;
    };

    const [timeSince, setTimeSince] = useState(getTimeSinceLastLog());

    // Update time since every second
    useEffect(() => {
        if (!isRunning) return;
        const interval = setInterval(() => {
            setTimeSince(getTimeSinceLastLog());
        }, 1000);
        return () => clearInterval(interval);
    }, [isRunning, lastLogTime]);

    if (!isRunning && logs.length === 0) {
        return null;
    }

    const latestLog = logs[logs.length - 1] || 'Waiting for logs...';
    const isError = latestLog.toLowerCase().includes('error');
    const isComplete = latestLog.toLowerCase().includes('complete') || latestLog.toLowerCase().includes('success');

    return (
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-6 shadow-lg">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    {isRunning && !isComplete && !isError && (
                        <Loader2 size={24} className="text-blue-500 animate-spin" />
                    )}
                    {isComplete && (
                        <CheckCircle size={24} className="text-green-500" />
                    )}
                    {isError && (
                        <AlertCircle size={24} className="text-red-500" />
                    )}
                    <div>
                        <h3 className="font-bold text-lg text-gray-900 dark:text-gray-100">
                            {processName}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                            {isRunning && !isComplete ? 'Processing...' : isComplete ? 'Completed' : 'Ready'}
                        </p>
                    </div>
                </div>

                {isRunning && onCancel && (
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-bold rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                )}
            </div>

            {/* Progress Bar */}
            {isRunning && (
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
                            className={`h-full rounded-full transition-all duration-500 ${isError ? 'bg-red-500' :
                                    isComplete ? 'bg-green-500' :
                                        'bg-blue-500 animate-pulse'
                                }`}
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                </div>
            )}

            {/* Latest Log */}
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

            {/* Full Logs (Collapsible) */}
            {logs.length > 3 && (
                <details className="mt-4">
                    <summary className="cursor-pointer text-sm text-blue-500 hover:text-blue-600 font-medium">
                        View all {logs.length} logs
                    </summary>
                    <div className="mt-3 bg-black rounded-lg p-4 max-h-64 overflow-y-auto custom-scrollbar">
                        {logs.map((log, idx) => (
                            <div
                                key={idx}
                                className={`text-xs font-mono mb-1 ${log.toLowerCase().includes('error') ? 'text-red-400' :
                                        log.toLowerCase().includes('success') || log.toLowerCase().includes('complete') ? 'text-green-400' :
                                            log.toLowerCase().includes('warning') ? 'text-yellow-400' :
                                                'text-gray-300'
                                    }`}
                            >
                                <span className="text-gray-500 mr-2">{String(idx + 1).padStart(3, '0')}</span>
                                {log}
                            </div>
                        ))}
                    </div>
                </details>
            )}
        </div>
    );
}
