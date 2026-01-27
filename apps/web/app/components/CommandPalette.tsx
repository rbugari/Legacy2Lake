"use client";

import React, { useState, useEffect, useRef } from 'react';
import {
    Search,
    Zap,
    ArrowRight,
    Command,
    LayoutDashboard,
    Database,
    Settings2,
    Terminal,
    Box,
    X,
    FolderOpen,
    Download
} from 'lucide-react';
import { useRouter } from 'next/navigation';

interface CommandPaletteProps {
    isOpen: boolean;
    onClose: () => void;
    projects: any[];
    onToggleLogs?: () => void;
}

export default function CommandPalette({ isOpen, onClose, projects, onToggleLogs }: CommandPaletteProps) {
    const [query, setQuery] = useState("");
    const [selectedIndex, setSelectedIndex] = useState(0);
    const router = useRouter();
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isOpen) {
            setQuery("");
            setSelectedIndex(0);
            setTimeout(() => inputRef.current?.focus(), 10);
        }
    }, [isOpen]);

    // Handle Keyboard Navigation
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (!isOpen) return;
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSelectedIndex(i => Math.min(i + 1, filteredActions.length + filteredProjects.length - 1));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSelectedIndex(i => Math.max(i - 1, 0));
            } else if (e.key === 'Enter') {
                e.preventDefault();
                executeSelected();
            } else if (e.key === 'Escape') {
                onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, selectedIndex, query]);

    const actions = [
        { id: 'dash', label: 'Go to Dashboard', icon: <LayoutDashboard size={14} />, action: () => router.push('/dashboard') },
        { id: 'admin', label: 'Open Administration', icon: <Settings2 size={14} />, action: () => router.push('/admin') },
        { id: 'logs', label: 'Show Diagnostics', icon: <Terminal size={14} />, action: () => { if (onToggleLogs) onToggleLogs(); } },
    ];

    const filteredActions = actions.filter(a => a.label.toLowerCase().includes(query.toLowerCase()));
    const filteredProjects = projects.filter(p => p.name.toLowerCase().includes(query.toLowerCase()));

    const executeSelected = () => {
        if (selectedIndex < filteredActions.length) {
            filteredActions[selectedIndex].action();
        } else {
            const project = filteredProjects[selectedIndex - filteredActions.length];
            router.push(`/workspace?id=${project.id}`);
        }
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[200] flex items-start justify-center pt-32 px-4">
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-in fade-in duration-200" onClick={onClose} />

            <div className="w-full max-w-xl bg-[var(--surface)] border border-[var(--border)] rounded-2xl shadow-2xl overflow-hidden animate-in slide-in-from-top-4 duration-300">
                {/* Input Area */}
                <div className="flex items-center px-6 py-4 border-b border-[var(--border)] bg-[var(--surface-elevated)]">
                    <Search className="text-[var(--text-tertiary)] mr-4" size={20} />
                    <input
                        ref={inputRef}
                        value={query}
                        onChange={e => setQuery(e.target.value)}
                        placeholder="Search projects, stages or execute commands..."
                        className="flex-1 bg-transparent text-[var(--text-primary)] text-sm outline-none placeholder-[var(--text-tertiary)] font-bold"
                    />
                    <div className="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-[var(--surface)] border border-[var(--border)] text-[9px] font-black text-[var(--text-tertiary)] uppercase tracking-widest">
                        <span>ESC</span>
                    </div>
                </div>

                {/* Results Area */}
                <div className="max-h-[400px] overflow-y-auto p-2 custom-scrollbar">
                    {/* Actions Group */}
                    {filteredActions.length > 0 && (
                        <div className="mb-4">
                            <h4 className="px-4 py-2 text-[10px] font-black text-[var(--text-tertiary)] uppercase tracking-widest">Global Commands</h4>
                            {filteredActions.map((action, idx) => (
                                <CommandItem
                                    key={action.id}
                                    active={selectedIndex === idx}
                                    label={action.label}
                                    icon={action.icon}
                                    onClick={() => { action.action(); onClose(); }}
                                />
                            ))}
                        </div>
                    )}

                    {/* Projects Group */}
                    {filteredProjects.length > 0 && (
                        <div>
                            <h4 className="px-4 py-2 text-[10px] font-black text-[var(--text-tertiary)] uppercase tracking-widest">Active Projects</h4>
                            {filteredProjects.map((project, idx) => (
                                <CommandItem
                                    key={project.id}
                                    active={selectedIndex === (idx + filteredActions.length)}
                                    label={project.name}
                                    icon={<Box size={14} className="text-cyan-500" />}
                                    onClick={() => { router.push(`/workspace?id=${project.id}`); onClose(); }}
                                    shortcut="OPEN"
                                />
                            ))}
                        </div>
                    )}

                    {filteredActions.length === 0 && filteredProjects.length === 0 && (
                        <div className="px-6 py-10 text-center">
                            <p className="text-xs font-bold text-[var(--text-secondary)] uppercase tracking-widest">No results found for "{query}"</p>
                        </div>
                    )}
                </div>

                {/* Footer Tips */}
                <div className="px-6 py-3 border-t border-[var(--border)] bg-[var(--surface-elevated)] flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Tip icon={<ArrowRight size={10} />} label="Navigate" />
                        <Tip icon={<Command size={10} />} label="Execute" />
                    </div>
                    <span className="text-[9px] font-black text-cyan-500/50 uppercase tracking-[0.2em]">Legacy2Lake Power Console</span>
                </div>
            </div>
        </div>
    );
}

function CommandItem({ active, label, icon, onClick, shortcut }: any) {
    return (
        <button
            onClick={onClick}
            className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all ${active ? 'bg-cyan-600 text-white shadow-xl shadow-cyan-600/20 translate-x-1' : 'text-[var(--text-secondary)] hover:bg-[var(--surface-elevated)]'}`}
        >
            <div className="flex items-center gap-4">
                <div className={`p-2 rounded-lg ${active ? 'bg-white/20' : 'bg-[var(--surface-elevated)] text-[var(--text-tertiary)]'}`}>
                    {icon}
                </div>
                <span className="text-xs font-black uppercase tracking-widest">{label}</span>
            </div>
            {shortcut && !active && (
                <span className="text-[9px] font-bold text-[var(--text-tertiary)] border border-[var(--border)] px-1.5 py-0.5 rounded uppercase tracking-widest">{shortcut}</span>
            )}
        </button>
    );
}

function Tip({ icon, label }: any) {
    return (
        <div className="flex items-center gap-1.5 text-[9px] font-black text-[var(--text-tertiary)] uppercase tracking-widest">
            <span className="p-0.5 bg-[var(--surface-elevated)] rounded">{icon}</span>
            <span>{label}</span>
        </div>
    );
}
