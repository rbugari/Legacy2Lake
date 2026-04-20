"use client";
import { useState, useEffect } from "react";
import { X, Trash2, FolderArchive, Download, AlertCircle, Loader2 } from "lucide-react";
import { fetchWithAuth } from "../lib/auth-client";

interface Backup {
    filename: string;
    size: number;
    size_mb: number;
    created_at: string | null;
    path: string;
}

interface BackupsModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: string;
    projectName: string;
}

export default function BackupsModal({ isOpen, onClose, projectId, projectName }: BackupsModalProps) {
    const [backups, setBackups] = useState<Backup[]>([]);
    const [loading, setLoading] = useState(false);
    const [deleting, setDeleting] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            loadBackups();
        }
    }, [isOpen, projectId]);

    const loadBackups = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const res = await fetchWithAuth(`/projects/${projectId}/backups`);
            if (!res.ok) {
                throw new Error("Failed to load backups");
            }
            
            const data = await res.json();
            setBackups(data.backups || []);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unknown error");
            console.error("[BackupsModal] Load failed:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (filename: string) => {
        if (!confirm(`Delete backup "${filename}"?\n\nThis action cannot be undone.`)) {
            return;
        }

        setDeleting(filename);
        
        try {
            const res = await fetchWithAuth(`/projects/${projectId}/backups/${encodeURIComponent(filename)}`, {
                method: "DELETE"
            });
            
            if (!res.ok && res.status !== 404) {
                throw new Error("Failed to delete backup");
            }
            
            // Remove from list
            setBackups(prev => prev.filter(b => b.filename !== filename));
        } catch (err) {
            alert(`Error deleting backup: ${err instanceof Error ? err.message : "Unknown error"}`);
            console.error("[BackupsModal] Delete failed:", err);
        } finally {
            setDeleting(null);
        }
    };

    const formatDate = (isoDate: string | null) => {
        if (!isoDate) return "Unknown date";
        try {
            const date = new Date(isoDate);
            return date.toLocaleString();
        } catch {
            return "Invalid date";
        }
    };

    if (!isOpen) return null;

    return (
        <>
            {/* Backdrop */}
            <div 
                className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="fixed inset-0 flex items-center justify-center z-50 p-4 pointer-events-none">
                <div 
                    className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col pointer-events-auto"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="flex items-center justify-between p-6 border-b border-gray-700">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-amber-500/10 rounded-lg">
                                <FolderArchive size={20} className="text-amber-500" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-white">Backup Files</h2>
                                <p className="text-xs text-gray-400">Project: {projectName}</p>
                            </div>
                        </div>
                        <button 
                            onClick={onClose}
                            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                        >
                            <X size={20} className="text-gray-400" />
                        </button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 overflow-y-auto p-6">
                        {loading && (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 size={32} className="text-amber-500 animate-spin" />
                            </div>
                        )}

                        {error && (
                            <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 flex items-start gap-3">
                                <AlertCircle size={20} className="text-red-500 shrink-0 mt-0.5" />
                                <div>
                                    <p className="text-sm font-bold text-red-400">Error loading backups</p>
                                    <p className="text-xs text-red-300 mt-1">{error}</p>
                                </div>
                            </div>
                        )}

                        {!loading && !error && backups.length === 0 && (
                            <div className="text-center py-12">
                                <FolderArchive size={48} className="text-gray-600 mx-auto mb-4" />
                                <p className="text-gray-400 text-sm">No backup files found</p>
                                <p className="text-gray-500 text-xs mt-1">
                                    Backups are created when you reset the project
                                </p>
                            </div>
                        )}

                        {!loading && !error && backups.length > 0 && (
                            <div className="space-y-2">
                                {backups.map((backup) => (
                                    <div 
                                        key={backup.filename}
                                        className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 flex items-center justify-between hover:border-gray-600 transition-colors"
                                    >
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-mono text-white truncate">
                                                {backup.filename}
                                            </p>
                                            <div className="flex items-center gap-4 mt-1">
                                                <span className="text-xs text-gray-400">
                                                    {backup.size_mb.toFixed(2)} MB
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    {formatDate(backup.created_at)}
                                                </span>
                                            </div>
                                        </div>

                                        <button
                                            onClick={() => handleDelete(backup.filename)}
                                            disabled={deleting === backup.filename}
                                            className="ml-4 p-2 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                                            title="Delete backup"
                                        >
                                            {deleting === backup.filename ? (
                                                <Loader2 size={18} className="animate-spin" />
                                            ) : (
                                                <Trash2 size={18} />
                                            )}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-gray-700 bg-gray-800/30">
                        <div className="flex items-center justify-between">
                            <p className="text-xs text-gray-400">
                                {backups.length > 0 && (
                                    <>
                                        {backups.length} backup{backups.length !== 1 ? "s" : ""} • {" "}
                                        {backups.reduce((sum, b) => sum + b.size_mb, 0).toFixed(2)} MB total
                                    </>
                                )}
                            </p>
                            <button
                                onClick={onClose}
                                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm font-medium transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
