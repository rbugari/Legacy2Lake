import { FileText, Download, X, CheckCircle, Clock, AlertCircle, Info } from 'lucide-react';
import { useState } from 'react';
import { fetchWithAuth } from '../lib/auth-client';

interface Report {
    id: string;
    name: string;
    description: string;
    type: 'triage' | 'final';
    availableAfterStage: number;
    icon: React.ReactNode;
    color: string;
}

interface ReportsLibraryModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: string;
    projectName: string;
    currentStage: number;
    activeTenantId?: string;
}

const AVAILABLE_REPORTS: Report[] = [
    {
        id: 'triage',
        name: 'Discovery Analysis Report',
        description: 'Comprehensive analysis of discovered assets including complexity assessment, PII detection, technology stack identification, and migration recommendations. Generated after Triage (Stage 2).',
        type: 'triage',
        availableAfterStage: 2,
        icon: <FileText size={24} />,
        color: 'cyan'
    },
    {
        id: 'final',
        name: 'Migration Delivery Report',
        description: 'Complete migration documentation including generated artifacts catalog, transformation lineage, architecture decisions, quality metrics, and deployment instructions. Generated after Drafting (Stage 3+).',
        type: 'final',
        availableAfterStage: 3,
        icon: <FileText size={24} />,
        color: 'purple'
    }
];

export default function ReportsLibraryModal({
    isOpen,
    onClose,
    projectId,
    projectName,
    currentStage,
    activeTenantId
}: ReportsLibraryModalProps) {
    const [downloadingReports, setDownloadingReports] = useState<Set<string>>(new Set());
    const [errors, setErrors] = useState<Record<string, string>>({});

    if (!isOpen) return null;

    const handleDownloadReport = async (report: Report) => {
        setDownloadingReports(prev => new Set(prev).add(report.id));
        setErrors(prev => ({ ...prev, [report.id]: '' }));

        try {
            const endpoint = `projects/${projectId}/reports/${report.type}`;
            const res = await fetchWithAuth(endpoint, {
                method: 'POST',
                headers: activeTenantId ? { 'X-Tenant-ID': activeTenantId } : {}
            });

            if (!res.ok) {
                let errorMsg = 'Failed to generate report';
                try {
                    const errorData = await res.json();
                    errorMsg = errorData.detail || errorData.error || errorMsg;
                } catch {
                    errorMsg = `Server error: ${res.status} ${res.statusText}`;
                }
                throw new Error(errorMsg);
            }

            // Get filename from headers
            const contentDisposition = res.headers.get('Content-Disposition') || 
                                      res.headers.get('X-Suggested-Filename');
            let filename = `${projectName}_${report.type}_report.pdf`;
            
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="(.+)"/);
                if (match) filename = match[1];
            }

            // Download blob
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

        } catch (error) {
            const errorMsg = error instanceof Error ? error.message : 'Unknown error';
            setErrors(prev => ({ ...prev, [report.id]: errorMsg }));
        } finally {
            setDownloadingReports(prev => {
                const updated = new Set(prev);
                updated.delete(report.id);
                return updated;
            });
        }
    };

    const getReportStatus = (report: Report) => {
        if (currentStage >= report.availableAfterStage) {
            return { available: true, label: 'Available', color: 'text-green-500', icon: CheckCircle };
        }
        return { 
            available: false, 
            label: `Available after Stage ${report.availableAfterStage}`, 
            color: 'text-amber-500', 
            icon: Clock 
        };
    };

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-4xl w-full border border-gray-200 dark:border-gray-700 overflow-hidden max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-blue-500/10 dark:from-cyan-500/20 dark:via-purple-500/20 dark:to-blue-500/20 border-b border-gray-200 dark:border-gray-700 p-6">
                    <div className="flex items-start justify-between">
                        <div>
                            <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                                Reports Library
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                Download comprehensive reports for: <span className="font-semibold text-gray-900 dark:text-gray-100">{projectName}</span>
                            </p>
                            <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 bg-blue-500/10 dark:bg-blue-500/20 rounded-lg border border-blue-200 dark:border-blue-800">
                                <Info size={14} className="text-blue-600 dark:text-blue-400" />
                                <span className="text-xs font-medium text-blue-700 dark:text-blue-300">
                                    Current Stage: {currentStage}
                                </span>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                        >
                            <X size={24} />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    <div className="space-y-4">
                        {AVAILABLE_REPORTS.map((report) => {
                            const status = getReportStatus(report);
                            const isDownloading = downloadingReports.has(report.id);
                            const error = errors[report.id];
                            const StatusIcon = status.icon;

                            return (
                                <div
                                    key={report.id}
                                    className={`p-6 rounded-xl border-2 transition-all ${
                                        status.available
                                            ? 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-cyan-300 dark:hover:border-cyan-700 hover:shadow-lg'
                                            : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 opacity-75'
                                    }`}
                                >
                                    <div className="flex items-start gap-4">
                                        {/* Icon */}
                                        <div className={`p-3 rounded-lg bg-${report.color}-500/10 dark:bg-${report.color}-500/20 border border-${report.color}-200 dark:border-${report.color}-800 flex-shrink-0`}>
                                            <div className={`text-${report.color}-600 dark:text-${report.color}-400`}>
                                                {report.icon}
                                            </div>
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-4 mb-2">
                                                <div>
                                                    <h4 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">
                                                        {report.name}
                                                    </h4>
                                                    <div className="flex items-center gap-2">
                                                        <StatusIcon size={14} className={status.color} />
                                                        <span className={`text-xs font-semibold uppercase tracking-wider ${status.color}`}>
                                                            {status.label}
                                                        </span>
                                                    </div>
                                                </div>

                                                {/* Download Button */}
                                                <button
                                                    onClick={() => handleDownloadReport(report)}
                                                    disabled={!status.available || isDownloading}
                                                    className={`px-4 py-2 rounded-lg font-medium text-sm flex items-center gap-2 transition-all ${
                                                        status.available && !isDownloading
                                                            ? `bg-${report.color}-600 hover:bg-${report.color}-500 text-white shadow-lg`
                                                            : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-500 cursor-not-allowed'
                                                    }`}
                                                >
                                                    {isDownloading ? (
                                                        <>
                                                            <Download size={16} className="animate-bounce" />
                                                            Generating...
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Download size={16} />
                                                            Download PDF
                                                        </>
                                                    )}
                                                </button>
                                            </div>

                                            {/* Description */}
                                            <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                                                {report.description}
                                            </p>

                                            {/* Error Display */}
                                            {error && (
                                                <div className="mt-3 p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-2">
                                                    <AlertCircle size={16} className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                                                    <p className="text-sm text-red-700 dark:text-red-300">
                                                        {error}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {/* Info Box */}
                    <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/30 rounded-xl border border-blue-200 dark:border-blue-800">
                        <div className="flex items-start gap-3">
                            <Info size={20} className="text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                            <div className="text-sm text-gray-700 dark:text-gray-300">
                                <p className="font-semibold text-blue-900 dark:text-blue-100 mb-1">Report Availability</p>
                                <p>Reports become available as you complete different stages of the migration process. Each report contains comprehensive information relevant to that stage.</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex justify-between items-center">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        {AVAILABLE_REPORTS.filter(r => currentStage >= r.availableAfterStage).length} of {AVAILABLE_REPORTS.length} reports available
                    </p>
                    <button
                        onClick={onClose}
                        className="px-6 py-2.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-lg font-medium hover:bg-gray-800 dark:hover:bg-gray-200 transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
