"use client";

import React from 'react';
import { X, AlertTriangle, Zap, Bot, ChevronRight } from 'lucide-react';

export type ConfirmModalVariant = 'execute' | 'rollback' | 'danger' | 'default';

export interface ConfirmModalAgent {
    id: string;
    name: string;
    role: string;
}

export interface ConfirmModalOptions {
    variant?: ConfirmModalVariant;
    title: string;
    description?: string;
    /** For execute variant: list of agents that will run */
    agents?: ConfirmModalAgent[];
    /** For rollback variant: list of phases that will be lost */
    lostPhases?: string[];
    /** Label for the confirm button */
    confirmLabel?: string;
    /** Label for the cancel button */
    cancelLabel?: string;
}

interface ConfirmModalProps extends ConfirmModalOptions {
    isOpen: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}

export default function ConfirmModal({
    isOpen,
    onConfirm,
    onCancel,
    variant = 'default',
    title,
    description,
    agents = [],
    lostPhases = [],
    confirmLabel,
    cancelLabel = 'Cancel',
}: ConfirmModalProps) {
    if (!isOpen) return null;

    const isExecute = variant === 'execute';
    const isRollback = variant === 'rollback';
    const isDanger = variant === 'danger' || isRollback;

    const defaultConfirmLabel = isExecute ? 'Run Now' : isDanger ? 'Yes, proceed' : 'Confirm';
    const finalConfirmLabel = confirmLabel ?? defaultConfirmLabel;

    const confirmBtnStyle = isExecute
        ? { background: '#2563eb' }
        : isDanger
            ? { background: '#dc2626' }
            : { background: '#2563eb' };

    return (
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
            style={{ backgroundColor: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)' }}
            onClick={onCancel}
        >
            <div
                className="relative w-full max-w-lg rounded-2xl shadow-2xl overflow-hidden"
                style={{
                    background: '#0f1117',
                    border: `1px solid ${isDanger ? 'rgba(220,38,38,0.3)' : 'rgba(255,255,255,0.08)'}`,
                }}
                onClick={e => e.stopPropagation()}
            >
                {/* Header stripe */}
                <div style={{
                    height: '3px',
                    background: isDanger
                        ? 'linear-gradient(90deg, #dc2626, #f97316)'
                        : 'linear-gradient(90deg, #2563eb, #06b6d4)'
                }} />

                <div className="p-6">
                    {/* Icon + Title */}
                    <div className="flex items-start gap-4 mb-5">
                        <div style={{
                            background: isDanger ? 'rgba(220,38,38,0.12)' : 'rgba(37,99,235,0.12)',
                            borderRadius: '12px',
                            padding: '10px',
                            flexShrink: 0,
                        }}>
                            {isDanger
                                ? <AlertTriangle size={22} style={{ color: '#f87171' }} />
                                : <Zap size={22} style={{ color: '#60a5fa' }} />
                            }
                        </div>
                        <div>
                            <h2 style={{ color: '#f1f5f9', fontSize: '18px', fontWeight: 700, marginBottom: '4px' }}>
                                {title}
                            </h2>
                            {description && (
                                <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
                                    {description}
                                </p>
                            )}
                        </div>
                        <button
                            onClick={onCancel}
                            style={{ color: '#475569', marginLeft: 'auto', flexShrink: 0 }}
                            className="hover:text-white transition-colors"
                        >
                            <X size={18} />
                        </button>
                    </div>

                    {/* Agents list (execute variant) */}
                    {isExecute && agents.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                            <p style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#475569', marginBottom: '8px' }}>
                                Agents that will run
                            </p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                                {agents.map(agent => (
                                    <div key={agent.id} style={{
                                        display: 'flex', alignItems: 'center', gap: '10px',
                                        background: 'rgba(255,255,255,0.03)',
                                        border: '1px solid rgba(255,255,255,0.07)',
                                        borderRadius: '8px',
                                        padding: '8px 12px',
                                    }}>
                                        <Bot size={14} style={{ color: '#60a5fa', flexShrink: 0 }} />
                                        <span style={{ color: '#e2e8f0', fontWeight: 600, fontSize: '13px' }}>{agent.name}</span>
                                        <ChevronRight size={12} style={{ color: '#334155', margin: '0 2px' }} />
                                        <span style={{ color: '#64748b', fontSize: '12px' }}>{agent.role}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Lost phases list (rollback variant) */}
                    {isRollback && lostPhases.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                            <p style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#475569', marginBottom: '8px' }}>
                                Progress that will be lost
                            </p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                                {lostPhases.map(phase => (
                                    <div key={phase} style={{
                                        display: 'flex', alignItems: 'center', gap: '8px',
                                        padding: '6px 10px',
                                        background: 'rgba(220,38,38,0.06)',
                                        border: '1px solid rgba(220,38,38,0.15)',
                                        borderRadius: '6px',
                                    }}>
                                        <span style={{ color: '#f87171', fontSize: '12px' }}>✕</span>
                                        <span style={{ color: '#fca5a5', fontSize: '13px', fontWeight: 500 }}>{phase}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Cost disclaimer (execute variant) */}
                    {isExecute && (
                        <div style={{
                            display: 'flex', gap: '10px',
                            background: 'rgba(234,179,8,0.06)',
                            border: '1px solid rgba(234,179,8,0.2)',
                            borderRadius: '8px',
                            padding: '10px 12px',
                            marginBottom: '20px',
                        }}>
                            <span style={{ flexShrink: 0 }}>⚠️</span>
                            <p style={{ color: '#fde68a', fontSize: '12px', lineHeight: '1.6', margin: 0 }}>
                                This operation uses AI processing and incurs <strong style={{ color: '#fcd34d' }}>token and compute costs</strong>. Execution time varies based on the number of assets in your project.
                            </p>
                        </div>
                    )}

                    {/* Rollback disclaimer */}
                    {isRollback && (
                        <div style={{
                            display: 'flex', gap: '10px',
                            background: 'rgba(220,38,38,0.06)',
                            border: '1px solid rgba(220,38,38,0.2)',
                            borderRadius: '8px',
                            padding: '10px 12px',
                            marginBottom: '20px',
                        }}>
                            <span style={{ flexShrink: 0 }}>❗</span>
                            <p style={{ color: '#fca5a5', fontSize: '12px', lineHeight: '1.6', margin: 0 }}>
                                This action <strong style={{ color: '#f87171' }}>cannot be undone</strong>. All progress listed above will be permanently removed. Discovery-phase data will be preserved.
                            </p>
                        </div>
                    )}

                    {/* Buttons */}
                    <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                        <button
                            onClick={onCancel}
                            style={{
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid rgba(255,255,255,0.1)',
                                color: '#94a3b8',
                                padding: '9px 20px',
                                borderRadius: '8px',
                                fontSize: '14px',
                                fontWeight: 500,
                                cursor: 'pointer',
                            }}
                            className="hover:bg-white/10 transition-colors"
                        >
                            {cancelLabel}
                        </button>
                        <button
                            onClick={onConfirm}
                            style={{
                                ...confirmBtnStyle,
                                color: '#fff',
                                padding: '9px 24px',
                                borderRadius: '8px',
                                fontSize: '14px',
                                fontWeight: 600,
                                cursor: 'pointer',
                                border: 'none',
                            }}
                            className="hover:opacity-90 transition-opacity"
                        >
                            {finalConfirmLabel}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
