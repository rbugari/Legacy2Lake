import { AlertCircle, Lock, User, Clock, X } from 'lucide-react';

interface ProcessLockModalProps {
    isOpen: boolean;
    onClose: () => void;
    processType: string;
    lockedBy: string;
    message?: string;
}

export default function ProcessLockModal({
    isOpen,
    onClose,
    processType,
    lockedBy,
    message
}: ProcessLockModalProps) {
    if (!isOpen) return null;

    // Map process types to friendly names
    const processNames: Record<string, string> = {
        'triage': 'Triage & Analysis',
        'drafting': 'Code Generation',
        'refinement': 'Code Refinement',
        'certification': 'Quality Certification',
        'governance': 'Governance & Documentation'
    };

    const displayName = processNames[processType] || processType;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-md w-full border border-gray-200 dark:border-gray-700 overflow-hidden">
                {/* Header */}
                <div className="bg-amber-500/10 dark:bg-amber-500/20 border-b border-amber-200 dark:border-amber-800 p-6">
                    <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-amber-500/20 dark:bg-amber-500/30 rounded-lg">
                                <Lock className="text-amber-600 dark:text-amber-400" size={24} />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                                    Process Locked
                                </h3>
                                <p className="text-sm text-amber-700 dark:text-amber-300">
                                    {displayName}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        >
                            <X size={20} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                    {/* Warning Message */}
                    <div className="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
                        <AlertCircle className="text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" size={20} />
                        <p className="text-sm text-gray-700 dark:text-gray-300">
                            {message || 'This process is currently being executed by another user.'}
                        </p>
                    </div>

                    {/* Lock Details */}
                    <div className="space-y-3">
                        <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <User className="text-gray-500 dark:text-gray-400" size={18} />
                            <div>
                                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider">
                                    Locked By
                                </p>
                                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                                    {lockedBy}
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                            <Clock className="text-gray-500 dark:text-gray-400" size={18} />
                            <div>
                                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider">
                                    Status
                                </p>
                                <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                                    In Progress
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Info Box */}
                    <div className="p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
                        <p className="text-sm text-gray-700 dark:text-gray-300">
                            <strong className="font-semibold text-blue-900 dark:text-blue-100">What to do:</strong>
                            <br />
                            • Wait for the current execution to complete
                            <br />
                            • Contact the user if you need immediate access
                            <br />
                            • Contact an administrator to force-release the lock if needed
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
                    <button
                        onClick={onClose}
                        className="w-full px-4 py-2.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
