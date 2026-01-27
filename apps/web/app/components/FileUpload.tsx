"use client";

import React, { useState } from 'react';
import { Upload, FileCode, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

import { API_BASE_URL } from '../lib/config';

interface UploadProps {
    onSuccess: (data: any) => void;
}

export default function FileUpload({ onSuccess }: UploadProps) {
    const [status, setStatus] = useState<string>('idle'); // idle, uploading, processing, success
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setStatus('uploading');
        setError(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            // First phase: Uploading
            setStatus('uploading');
            const response = await fetch(`${API_BASE_URL}/ingest/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) throw new Error('Failed to process package.');

            // Second phase: Analyzing (the backend does mapping etc after upload)
            setStatus('processing');
            const data = await response.json();

            setStatus('success');
            setTimeout(() => {
                onSuccess(data);
                setStatus('idle');
            }, 1000);
        } catch (err: any) {
            setError(err.message || 'An error occurred during ingestion.');
            setStatus('idle');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="card-premium h-full flex flex-col justify-center items-center text-center space-y-4 relative overflow-hidden">
            {isUploading && (
                <div className="absolute top-0 left-0 w-full h-[2px] bg-cyan-500/20">
                    <div className="h-full bg-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.5)] animate-shimmer w-1/3" />
                </div>
            )}

            <div className={`w-16 h-16 rounded-3xl transition-all duration-500 flex items-center justify-center mb-2 ${isUploading ? 'bg-cyan-500/10 rotate-12 scale-110' : 'bg-primary/5'
                }`}>
                {isUploading ? (
                    <Loader2 className="w-8 h-8 text-cyan-500 animate-spin" />
                ) : status === 'success' ? (
                    <CheckCircle className="w-8 h-8 text-emerald-500 animate-bounce" />
                ) : (
                    <Upload className="w-8 h-8 text-primary group-hover:-translate-y-1 transition-transform" />
                )}
            </div>

            <div>
                <h3 className="font-black text-xs uppercase tracking-[0.2em] text-white">
                    {isUploading ? (status === 'uploading' ? 'Uploading Asset...' : 'Agent A Analyzing...') : 'Ingest Source Asset'}
                </h3>
                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-2 max-w-[200px] leading-relaxed">
                    {isUploading ? 'The Detective is mapping technical lineage' : 'Upload your source package to start the discovery mesh.'}
                </p>
            </div>

            <label className="cursor-pointer group">
                <span className="bg-primary group-hover:bg-secondary text-white px-6 py-2 rounded-lg text-sm font-bold transition-all inline-block">
                    Select File
                </span>
                <input
                    type="file"
                    className="hidden"
                    // accept=".dtsx" // Allow all files for generic ingestion
                    onChange={handleFileUpload}
                    disabled={isUploading}
                />
            </label>

            {error && (
                <div className="flex items-center gap-2 text-error text-xs font-medium animate-in slide-in-from-top-2">
                    <AlertCircle className="w-4 h-4" />
                    {error}
                </div>
            )}
        </div>
    );
}
