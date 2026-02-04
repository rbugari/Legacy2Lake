"use client";

import React, { useState } from 'react';
import { Download, Loader2, FileText } from 'lucide-react';
import { API_BASE_URL } from '../lib/config';
import { fetchWithAuth } from '../lib/auth-client';

interface DownloadReportButtonProps {
    projectId: string;
    reportType: 'triage' | 'final';
    label?: string;
    variant?: 'primary' | 'secondary' | 'outline' | 'ghost'; // To match existing usage if needed
    className?: string;
    icon?: React.ReactNode;
}

export default function DownloadReportButton({
    projectId,
    reportType,
    label,
    variant = 'secondary',
    className = "",
    icon
}: DownloadReportButtonProps) {
    const [isDownloading, setIsDownloading] = useState(false);

    const handleDownload = async () => {
        setIsDownloading(true);
        try {
            // Determine endpoint based on report type
            const endpoint = `/projects/${projectId}/reports/${reportType}`;

            // Use fetchWithAuth to handle authentication headers automatically
            // Note: We need to handle the blob response manually since fetchWithAuth usually returns response object
            // but we need to verify if it throws on error or how it handles non-JSON.
            // Assuming fetchWithAuth behaves like fetch but adds headers.

            const response = await fetchWithAuth(endpoint, {
                method: 'POST', // Report generation is a POST action
            });

            if (!response.ok) {
                // Try to parse error message
                let errorMsg = 'Failed to generate report';
                try {
                    const errorData = await response.json();
                    errorMsg = errorData.detail || errorData.message || errorMsg;
                } catch (e) {
                    // Ignore JSON parse error
                }
                throw new Error(errorMsg);
            }

            // Get filename from Content-Disposition header if available
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = `${reportType}_report.pdf`;
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1];
                }
            }

            // Convert to blob and download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

        } catch (error) {
            console.error("Report download failed:", error);
            alert(`Failed to download report: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            setIsDownloading(false);
        }
    };

    // Base styles tailored to the dark theme UI
    const baseStyles = "flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed";

    // Variant styles
    const variants = {
        primary: "bg-cyan-500 text-white hover:bg-cyan-400 shadow-lg shadow-cyan-500/20",
        secondary: "bg-white/5 text-white border border-white/10 hover:bg-white/10 hover:border-white/20",
        outline: "bg-transparent text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/10",
        ghost: "bg-transparent text-gray-400 hover:text-white hover:bg-white/5"
    };

    const appliedStyle = `${baseStyles} ${variants[variant]} ${className}`;

    // Default label if not provided
    const displayLabel = label || (reportType === 'triage' ? 'Download Discovery Report' : 'Download Final Report');

    return (
        <button
            onClick={handleDownload}
            disabled={isDownloading}
            className={appliedStyle}
            title={displayLabel}
        >
            {isDownloading ? (
                <Loader2 size={16} className="animate-spin" />
            ) : (
                icon || <FileText size={16} />
            )}
            <span>{isDownloading ? 'Generating...' : displayLabel}</span>
        </button>
    );
}
