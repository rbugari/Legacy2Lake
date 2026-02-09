import { X, CheckCircle, Clock, AlertCircle, Loader2 } from 'lucide-react';
import { useEffect, useState } from 'react';

interface AgentStep {
    id: string;
    name: string;
    status: 'pending' | 'running' | 'completed' | 'error';
    duration?: number;
}

interface ProcessExecutionModalProps {
    isOpen: boolean;
    onClose: () => void;
    processName: string;
    stages: AgentStep[];
    logs: string[];
    progress: number;
    isRunning: boolean;
    onCancel?: () => void;
}

export default function ProcessExecutionModal({
    isOpen,
    onClose,
    processName,
    stages,
    logs,
    progress,
    isRunning,
    onCancel
}: ProcessExecutionModalProps) {
    const [elapsedTime, setElapsedTime] = useState(0);

    useEffect(() => {
        if (!isRunning) {
            setElapsedTime(0);
            return;
        }

        const startTime = Date.now();
        const interval = setInterval(() => {
            setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
        }, 1000);

        return () => clearInterval(interval);
    }, [isRunning]);

    if (!isOpen) return null;

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const currentStage = stages.find(s => s.status === 'running');
    const completedStages = stages.filter(s => s.status === 'completed').length;

    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-md flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-4xl w-full border border-gray-200 dark:border-gray-700 overflow-hidden max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-purple-500/10 dark:from-cyan-500/20 dark:via-blue-500/20 dark:to-purple-500/20 border-b border-gray-200 dark:border-gray-700 p-6">
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                                <div className={`p-2 rounded-lg ${
                                    isRunning 
                                        ? 'bg-blue-500/20 dark:bg-blue-500/30' 
                                        : progress === 100 
                                            ? 'bg-green-500/20 dark:bg-green-500/30'
                                            : 'bg-gray-500/20 dark:bg-gray-500/30'
                                }`}>
                                    {isRunning ? (
                                        <Loader2 className="text-blue-600 dark:text-blue-400 animate-spin" size={24} />
                                    ) : progress === 100 ? (
                                        <CheckCircle className="text-green-600 dark:text-green-400" size={24} />
                                    ) : (
                                        <Clock className="text-gray-600 dark:text-gray-400" size={24} />
                                    )}
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                                        {processName}
                                    </h3>
                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                        {isRunning 
                                            ? `Processing: ${currentStage?.name || 'Starting...'}` 
                                            : progress === 100 
                                                ? 'Completed Successfully' 
                                                : 'Ready to start'}
                                    </p>
                                </div>
                            </div>

                            {/* Status Indicators */}
                            <div className="flex items-center gap-6 text-sm">
                                <div className="flex items-center gap-2">
                                    <span className="text-gray-500 dark:text-gray-400">Progress:</span>
                                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                                        {completedStages} / {stages.length} stages
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-gray-500 dark:text-gray-400">Time:</span>
                                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                                        {formatTime(elapsedTime)}
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        <button
                            onClick={onClose}
                            disabled={isRunning}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <X size={24} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {/* Progress Bar */}
                    <div>
                        <div className="flex justify-between text-sm mb-2">
                            <span className="text-gray-600 dark:text-gray-400 font-medium">Overall Progress</span>
                            <span className="font-bold text-gray-900 dark:text-gray-100">{Math.round(progress)}%</span>
                        </div>
                        <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 transition-all duration-500 ease-out"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                    </div>

                    {/* Agent Flow Visualization */}
                    <div>
                        <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-3 uppercase tracking-wider">
                            Agent Pipeline
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                            {stages.map((stage, index) => (
                                <div
                                    key={stage.id}
                                    className={`p-4 rounded-xl border-2 transition-all ${
                                        stage.status === 'completed'
                                            ? 'bg-green-50 dark:bg-green-950/30 border-green-300 dark:border-green-700'
                                            : stage.status === 'running'
                                                ? 'bg-blue-50 dark:bg-blue-950/30 border-blue-400 dark:border-blue-600 shadow-lg'
                                                : stage.status === 'error'
                                                    ? 'bg-red-50 dark:bg-red-950/30 border-red-300 dark:border-red-700'
                                                    : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                                    }`}
                                >
                                    <div className="flex items-start justify-between">
                                        <div className="flex-1">
                                            <div className="text-xs font-bold text-gray-500 dark:text-gray-400 mb-1">
                                                STEP {index + 1}
                                            </div>
                                            <div className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                                                {stage.name}
                                            </div>
                                        </div>
                                        <div>
                                            {stage.status === 'completed' && (
                                                <CheckCircle className="text-green-600 dark:text-green-400" size={20} />
                                            )}
                                            {stage.status === 'running' && (
                                                <Loader2 className="text-blue-600 dark:text-blue-400 animate-spin" size={20} />
                                            )}
                                            {stage.status === 'error' && (
                                                <AlertCircle className="text-red-600 dark:text-red-400" size={20} />
                                            )}
                                            {stage.status === 'pending' && (
                                                <Clock className="text-gray-400" size={20} />
                                            )}
                                        </div>
                                    </div>
                                    {stage.duration && (
                                        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                                            {stage.duration}s
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Live Logs */}
                    <div>
                        <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 mb-3 uppercase tracking-wider">
                            Execution Log
                        </h4>
                        <div className="bg-gray-900 dark:bg-black rounded-xl p-4 h-64 overflow-y-auto font-mono text-xs">
                            {logs.length === 0 ? (
                                <div className="text-gray-500">No logs yet...</div>
                            ) : (
                                logs.map((log, i) => (
                                    <div
                                        key={i}
                                        className={`mb-1 ${
                                            log.includes('[ERROR]') || log.includes('error')
                                                ? 'text-red-400'
                                                : log.includes('[SUCCESS]') || log.includes('✅')
                                                    ? 'text-green-400'
                                                    : log.includes('[WARN]')
                                                        ? 'text-yellow-400'
                                                        : 'text-gray-300'
                                        }`}
                                    >
                                        {log}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center gap-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                        {isRunning ? (
                            <span>Process is running... Please wait.</span>
                        ) : progress === 100 ? (
                            <span className="text-green-600 dark:text-green-400 font-semibold">✓ Process completed successfully!</span>
                        ) : (
                            <span>Process ready to execute.</span>
                        )}
                    </div>
                    <div className="flex gap-3">
                        {isRunning && onCancel && (
                            <button
                                onClick={onCancel}
                                className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-lg font-medium transition-colors"
                            >
                                Cancel Process
                            </button>
                        )}
                        <button
                            onClick={onClose}
                            disabled={isRunning}
                            className="px-6 py-2.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isRunning ? 'Processing...' : 'Close'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
