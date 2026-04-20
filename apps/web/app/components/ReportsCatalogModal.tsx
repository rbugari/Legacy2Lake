"use client";

import React, { useState, useEffect } from 'react';
import { X, FileText, Download, Eye, Filter, Search } from 'lucide-react';

interface ReportsCatalogModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: string;
    projectName: string;
    currentStage: number;
    activeTenantId?: string;
}

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

    if (!isOpen) return null;

    // Mock data - replace with actual API call
    const reportCategories = [
        { id: 'all', label: 'All Reports', count: 0 },
        { id: 'governance', label: 'Governance', count: 0 },
        { id: 'handover', label: 'Handover', count: 0 },
        { id: 'certification', label: 'Certification', count: 0 },
    ];

    const reports: any[] = [];

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
                                No Reports Available
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                                Reports will be generated as the project progresses through the governance and handover stages.
                            </p>
                        </div>
                    ) : (
                        <div className="grid gap-4">
                            {/* Report cards will be rendered here */}
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
