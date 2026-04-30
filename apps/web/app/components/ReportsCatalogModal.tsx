"use client";

import React, { useMemo, useState } from 'react';
import { X, FileText, Download, Search, Archive, AlertCircle, CheckCircle2, Clock, ShieldCheck, Package } from 'lucide-react';
import { fetchWithAuth } from '../lib/auth-client';

interface ReportsCatalogModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: string;
    projectName: string;
    currentStage: number;
    activeTenantId?: string;
}

type ReportCategory = 'analysis' | 'governance' | 'handover' | 'certification';

interface CatalogItem {
    id: string;
    name: string;
    description: string;
    category: ReportCategory;
    format: 'PDF' | 'ZIP';
    availableAfterStage: number;
    method: 'GET' | 'POST';
    endpoint: string;
    defaultFilename: string;
}

const STAGE_LABELS: Record<number, string> = {
    0: 'Discovery',
    1: 'Triage',
    2: 'Drafting',
    3: 'Refinement',
    4: 'Governance',
    5: 'Handover'
};

const CATEGORY_META: Record<ReportCategory, {
    label: string;
    icon: typeof FileText;
    accent: string;
    badge: string;
    iconWrap: string;
    iconColor: string;
    action: string;
}> = {
    analysis: {
        label: 'Analysis',
        icon: FileText,
        accent: 'border-cyan-200 dark:border-cyan-800',
        badge: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-300',
        iconWrap: 'bg-cyan-500/10 border-cyan-500/20',
        iconColor: 'text-cyan-600 dark:text-cyan-400',
        action: 'bg-cyan-600 hover:bg-cyan-500'
    },
    governance: {
        label: 'Governance',
        icon: ShieldCheck,
        accent: 'border-violet-200 dark:border-violet-800',
        badge: 'bg-violet-50 text-violet-700 dark:bg-violet-950/30 dark:text-violet-300',
        iconWrap: 'bg-violet-500/10 border-violet-500/20',
        iconColor: 'text-violet-600 dark:text-violet-400',
        action: 'bg-violet-600 hover:bg-violet-500'
    },
    handover: {
        label: 'Handover',
        icon: Package,
        accent: 'border-emerald-200 dark:border-emerald-800',
        badge: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300',
        iconWrap: 'bg-emerald-500/10 border-emerald-500/20',
        iconColor: 'text-emerald-600 dark:text-emerald-400',
        action: 'bg-emerald-600 hover:bg-emerald-500'
    },
    certification: {
        label: 'Certification',
        icon: CheckCircle2,
        accent: 'border-amber-200 dark:border-amber-800',
        badge: 'bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:text-amber-300',
        iconWrap: 'bg-amber-500/10 border-amber-500/20',
        iconColor: 'text-amber-600 dark:text-amber-400',
        action: 'bg-amber-600 hover:bg-amber-500'
    }
};

const CATALOG_ITEMS: CatalogItem[] = [
    {
        id: 'triage-analysis-pdf',
        name: 'Discovery Analysis Report',
        description: 'PDF summary of discovered assets, complexity signals, technology detection, and migration recommendations.',
        category: 'analysis',
        format: 'PDF',
        availableAfterStage: 1,
        method: 'POST',
        endpoint: 'reports/triage',
        defaultFilename: 'discovery_analysis_report.pdf'
    },
    {
        id: 'certification-delivery-pdf',
        name: 'Certification & Delivery Report',
        description: 'PDF report combining governance outcomes, certification score, delivery timeline, and generated artifact inventory.',
        category: 'certification',
        format: 'PDF',
        availableAfterStage: 4,
        method: 'POST',
        endpoint: 'reports/final',
        defaultFilename: 'certification_delivery_report.pdf'
    },
    {
        id: 'governance-solution-zip',
        name: 'Governance Solution Bundle',
        description: 'ZIP bundle with governance-ready solution artifacts and supporting documentation exported from the project state.',
        category: 'governance',
        format: 'ZIP',
        availableAfterStage: 4,
        method: 'GET',
        endpoint: 'export/governance',
        defaultFilename: 'governance_solution_bundle.zip'
    },
    {
        id: 'handover-delivery-zip',
        name: 'Delivery Package Bundle',
        description: 'ZIP package for handover with deployable outputs, packaging structure, and final delivery assets.',
        category: 'handover',
        format: 'ZIP',
        availableAfterStage: 5,
        method: 'GET',
        endpoint: 'export/delivery',
        defaultFilename: 'delivery_package_bundle.zip'
    }
];

export default function ReportsCatalogModal({
    isOpen,
    onClose,
    projectId,
    projectName,
    currentStage,
    activeTenantId
}: ReportsCatalogModalProps) {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
    const [errors, setErrors] = useState<Record<string, string>>({});

    const availableItems = useMemo(
        () => CATALOG_ITEMS.filter((item) => currentStage >= item.availableAfterStage),
        [currentStage]
    );

    const reportCategories = useMemo(() => {
        const counts = CATALOG_ITEMS.reduce<Record<string, number>>((acc, item) => {
            if (currentStage >= item.availableAfterStage) {
                acc[item.category] = (acc[item.category] || 0) + 1;
                acc.all += 1;
            }
            return acc;
        }, { all: 0 });

        return [
            { id: 'all', label: 'All Reports', count: counts.all || 0 },
            { id: 'analysis', label: 'Analysis', count: counts.analysis || 0 },
            { id: 'governance', label: 'Governance', count: counts.governance || 0 },
            { id: 'handover', label: 'Handover', count: counts.handover || 0 },
            { id: 'certification', label: 'Certification', count: counts.certification || 0 },
        ];
    }, [currentStage]);

    const reports = useMemo(() => {
        const normalizedQuery = searchTerm.trim().toLowerCase();

        return CATALOG_ITEMS.filter((item) => {
            if (selectedCategory !== 'all' && item.category !== selectedCategory) {
                return false;
            }

            if (!normalizedQuery) {
                return true;
            }

            const haystack = `${item.name} ${item.description} ${item.category} ${item.format}`.toLowerCase();
            return haystack.includes(normalizedQuery);
        });
    }, [searchTerm, selectedCategory]);

    const handleDownload = async (report: CatalogItem) => {
        setDownloadingIds((prev) => new Set(prev).add(report.id));
        setErrors((prev) => ({ ...prev, [report.id]: '' }));

        try {
            const response = await fetchWithAuth(`/projects/${projectId}/${report.endpoint}`, {
                method: report.method,
                headers: activeTenantId ? { 'X-Tenant-ID': activeTenantId } : undefined,
            });

            if (!response.ok) {
                let errorMessage = 'Failed to download report';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.error || errorMessage;
                } catch {
                    errorMessage = `Server error: ${response.status} ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            const contentDisposition = response.headers.get('Content-Disposition') || response.headers.get('X-Suggested-Filename');
            let filename = report.defaultFilename;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?([^";]+)"?/i);
                if (match?.[1]) {
                    filename = match[1];
                }
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            setErrors((prev) => ({
                ...prev,
                [report.id]: error instanceof Error ? error.message : 'Unknown download error'
            }));
        } finally {
            setDownloadingIds((prev) => {
                const next = new Set(prev);
                next.delete(report.id);
                return next;
            });
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[300] flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-5xl max-h-[90vh] bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-800 flex flex-col animate-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-800">
                    <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                            <FileText className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                                Reports Library
                            </h2>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                                {projectName}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Search and Filters */}
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 space-y-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search reports..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
                        />
                    </div>

                    <div className="flex gap-2">
                        {reportCategories.map((category) => (
                            <button
                                key={category.id}
                                onClick={() => setSelectedCategory(category.id)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                                    selectedCategory === category.id
                                        ? 'bg-cyan-500 text-white'
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                                }`}
                            >
                                {category.label}
                                <span className="ml-2 text-xs opacity-70">({category.count})</span>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    {reports.length === 0 ? (
                        <div className="text-center py-12">
                            <FileText className="w-16 h-16 text-gray-300 dark:text-gray-700 mx-auto mb-4" />
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                                No Matching Reports
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                                {availableItems.length === 0
                                    ? 'Reports will appear here as the project advances through triage, governance, and handover.'
                                    : 'Adjust the search or category filter to see the available exports.'}
                            </p>
                        </div>
                    ) : (
                        <div className="grid gap-4">
                            {reports.map((report) => {
                                const categoryMeta = CATEGORY_META[report.category];
                                const Icon = categoryMeta.icon;
                                const isAvailable = currentStage >= report.availableAfterStage;
                                const isDownloading = downloadingIds.has(report.id);
                                const statusLabel = isAvailable
                                    ? 'Available now'
                                    : `Available after ${STAGE_LABELS[report.availableAfterStage] || `Stage ${report.availableAfterStage}`}`;

                                return (
                                    <div
                                        key={report.id}
                                        className={`rounded-2xl border bg-white dark:bg-gray-950 ${categoryMeta.accent} ${isAvailable ? 'shadow-sm' : 'opacity-75'} p-5`}
                                    >
                                        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                                            <div className="flex gap-4 min-w-0">
                                                <div className={`flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl border ${categoryMeta.iconWrap}`}>
                                                    <Icon className={`w-5 h-5 ${categoryMeta.iconColor}`} />
                                                </div>
                                                <div className="min-w-0">
                                                    <div className="flex flex-wrap items-center gap-2 mb-2">
                                                        <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                                                            {report.name}
                                                        </h3>
                                                        <span className={`px-2 py-1 rounded-md text-[11px] font-semibold uppercase tracking-wide ${categoryMeta.badge}`}>
                                                            {categoryMeta.label}
                                                        </span>
                                                        <span className="px-2 py-1 rounded-md text-[11px] font-semibold uppercase tracking-wide bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                                                            {report.format}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-gray-600 dark:text-gray-400">
                                                        {report.description}
                                                    </p>
                                                    <div className="mt-3 flex items-center gap-2 text-xs font-medium">
                                                        {isAvailable ? (
                                                            <CheckCircle2 className="w-4 h-4 text-green-600 dark:text-green-400" />
                                                        ) : (
                                                            <Clock className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                                                        )}
                                                        <span className={isAvailable ? 'text-green-700 dark:text-green-300' : 'text-amber-700 dark:text-amber-300'}>
                                                            {statusLabel}
                                                        </span>
                                                    </div>
                                                    {errors[report.id] && (
                                                        <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">
                                                            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                                            <span>{errors[report.id]}</span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>

                                            <button
                                                onClick={() => handleDownload(report)}
                                                disabled={!isAvailable || isDownloading}
                                                className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors ${isAvailable && !isDownloading ? categoryMeta.action : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'}`}
                                            >
                                                <Download className={`w-4 h-4 ${isDownloading ? 'animate-bounce' : ''}`} />
                                                {isDownloading ? 'Preparing...' : 'Download'}
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-800 flex justify-end gap-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
}
