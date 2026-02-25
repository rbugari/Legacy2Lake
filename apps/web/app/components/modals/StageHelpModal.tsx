"use client";

import React, { useEffect, useState } from 'react';
import { X, HelpCircle, Loader2 } from 'lucide-react';

interface StageHelpModalProps {
    isOpen: boolean;
    onClose: () => void;
    stageId: number;
}

const STAGE_LABELS: Record<number, string> = {
    0: 'Discovery',
    1: 'Triage',
    2: 'Drafting',
    3: 'Refinement',
    4: 'Governance',
    5: 'Handover'
};

export default function StageHelpModal({ isOpen, onClose, stageId }: StageHelpModalProps) {
    const [htmlContent, setHtmlContent] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!isOpen) return;

        let isMounted = true;

        async function fetchContent() {
            setIsLoading(true);
            setError(null);
            setHtmlContent('');
            try {
                const res = await fetch(`/help/stages/${stageId}.html`);
                if (!res.ok) {
                    throw new Error(res.status === 404
                        ? `Help content for this stage is coming soon.`
                        : 'Failed to load help content.'
                    );
                }
                const text = await res.text();
                if (isMounted) setHtmlContent(text);
            } catch (err: any) {
                if (isMounted) setError(err.message || 'An error occurred.');
            } finally {
                if (isMounted) setIsLoading(false);
            }
        }

        fetchContent();
        return () => { isMounted = false; };
    }, [isOpen, stageId]);

    // Close on Escape key
    useEffect(() => {
        if (!isOpen) return;
        const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    const stageLabel = STAGE_LABELS[stageId] ?? `Stage ${stageId}`;

    return (
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
            style={{ backgroundColor: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)' }}
            onClick={onClose}
        >
            <div
                className="relative w-full max-w-3xl flex flex-col rounded-2xl shadow-2xl overflow-hidden"
                style={{ maxHeight: '88vh', background: '#0f1117', border: '1px solid rgba(255,255,255,0.08)' }}
                onClick={e => e.stopPropagation()}
            >
                {/* Header */}
                <div style={{ borderBottom: '1px solid rgba(255,255,255,0.07)', background: 'rgba(255,255,255,0.03)' }}
                    className="flex items-center justify-between px-6 py-4 shrink-0">
                    <div className="flex items-center gap-3">
                        <div style={{ background: 'rgba(59,130,246,0.15)', borderRadius: '10px' }} className="p-2">
                            <HelpCircle size={22} style={{ color: '#60a5fa' }} />
                        </div>
                        <div>
                            <p style={{ color: '#60a5fa', fontSize: '11px', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                                Stage Guide
                            </p>
                            <h2 style={{ color: '#f1f5f9', fontSize: '18px', fontWeight: 700 }}>{stageLabel} Phase</h2>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        style={{ color: '#94a3b8', borderRadius: '8px', padding: '6px' }}
                        className="hover:bg-white/10 transition-colors"
                        title="Close"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto px-6 py-6" style={{ scrollbarWidth: 'thin', scrollbarColor: '#334155 transparent' }}>
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center py-24" style={{ color: '#64748b' }}>
                            <Loader2 size={32} className="animate-spin mb-4" style={{ color: '#3b82f6' }} />
                            <p style={{ fontSize: '14px' }}>Loading guide...</p>
                        </div>
                    ) : error ? (
                        <div className="flex flex-col items-center justify-center py-24 text-center gap-3">
                            <div style={{ background: 'rgba(59,130,246,0.1)', borderRadius: '50%', padding: '20px' }}>
                                <HelpCircle size={32} style={{ color: '#60a5fa' }} />
                            </div>
                            <p style={{ color: '#94a3b8', fontSize: '14px' }}>{error}</p>
                        </div>
                    ) : (
                        <div
                            className="stage-help-content"
                            dangerouslySetInnerHTML={{ __html: htmlContent }}
                        />
                    )}
                </div>

                {/* Footer */}
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.07)', background: 'rgba(255,255,255,0.02)' }}
                    className="flex items-center justify-between px-6 py-3 shrink-0">
                    <p style={{ color: '#475569', fontSize: '12px' }}>
                        Press <kbd style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', padding: '2px 6px', fontSize: '11px', color: '#94a3b8' }}>Esc</kbd> to close
                    </p>
                    <button
                        onClick={onClose}
                        style={{ background: '#2563eb', color: '#fff', fontSize: '14px', fontWeight: 600, padding: '8px 20px', borderRadius: '8px' }}
                        className="hover:bg-blue-500 transition-colors"
                    >
                        Got it
                    </button>
                </div>
            </div>
        </div>
    );
}
