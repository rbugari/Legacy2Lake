"use client";

import { X, Code2, FileText, Save, BookOpen, Loader2, Eye } from "lucide-react";
import { useState, useEffect } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { API_BASE_URL } from "@/app/lib/config";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface CartridgeKnowledgeModalProps {
    cartridge: {
        id: string;
        tech_id?: string;
        name: string;
        type?: string;
    };
    onClose: () => void;
}

export default function CartridgeKnowledgeModal({ cartridge, onClose }: CartridgeKnowledgeModalProps) {
    const [viewMode, setViewMode] = useState<'source' | 'edit' | 'view'>('source');
    const [knowledge, setKnowledge] = useState("");
    const [editingKnowledge, setEditingKnowledge] = useState("");
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [hasChanges, setHasChanges] = useState(false);

    // Determine tech ID - prefer tech_id, fallback to trying to extract from name or id
    const getTechId = () => {
        if (cartridge.tech_id) return cartridge.tech_id;
        
        // Try to extract from name (e.g., "Oracle DB" -> "oracle")
        const nameMap: {[key: string]: string} = {
            'oracle db': 'oracle',
            'microsoft ssis': 'ssis',
            'microsoft sql server': 'sqlserver',
            'ibm datastage': 'datastage',
            'informatica powercenter': 'informatica',
            'pentaho (kettle)': 'pentaho',
            'sap bods': 'sapbods',
            'talend': 'talend',
            'mysql': 'mysql',
            'databricks (pyspark)': 'databricks',
            'snowflake': 'snowflake',
            'google bigquery': 'bigquery',
            'aws redshift': 'redshift',
            'microsoft fabric': 'fabric',
            'salesforce data cloud': 'salesforce'
        };
        
        const normalizedName = cartridge.name.toLowerCase();
        return nameMap[normalizedName] || cartridge.id;
    };

    const techId = getTechId();

    useEffect(() => {
        loadKnowledge();
    }, []);

    const loadKnowledge = async () => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/system/cartridges/${techId}/knowledge`);
            const data = await res.json();
            const content = data.knowledge || "";
            setKnowledge(content);
            setEditingKnowledge(content);
        } catch (e) {
            console.error("Failed to load knowledge:", e);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const res = await fetch(`${API_BASE_URL}/system/cartridges/${techId}/knowledge`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ knowledge: editingKnowledge })
            });
            
            if (res.ok) {
                setKnowledge(editingKnowledge);
                setHasChanges(false);
                setViewMode('source');
            }
        } catch (e) {
            console.error("Failed to save knowledge:", e);
            alert("Error saving knowledge. Please try again.");
        } finally {
            setSaving(false);
        }
    };

    const handleCancel = () => {
        if (hasChanges && !confirm("You have unsaved changes. Discard them?")) {
            return;
        }
        onClose();
    };

    const handleEditChange = (value: string) => {
        setEditingKnowledge(value);
        setHasChanges(value !== knowledge);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full h-full bg-[var(--background)] flex flex-col">
                {/* Header */}
                <div className="flex-shrink-0 border-b border-[var(--border)] bg-[var(--surface)] px-8 py-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-purple-500/10">
                                <BookOpen size={24} className="text-purple-500" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold flex items-center gap-3">
                                    Expert Knowledge
                                    <span className="text-[var(--text-tertiary)] text-base font-normal">•</span>
                                    <span className="text-cyan-500">{cartridge.name}</span>
                                </h2>
                                <p className="text-sm text-[var(--text-secondary)] mt-1">
                                    Technology-specific patterns, best practices, and migration guidance
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            {/* View Mode Toggle */}
                            <div className="flex bg-[var(--surface-elevated)] p-1 rounded-xl border border-[var(--border)] gap-1">
                                <button
                                    onClick={() => setViewMode('source')}
                                    className={`px-4 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all flex items-center gap-2 ${
                                        viewMode === 'source'
                                            ? 'bg-cyan-600 text-white shadow-lg'
                                            : 'text-[var(--text-tertiary)] hover:text-cyan-400'
                                    }`}
                                >
                                    <Code2 size={12} /> Source
                                </button>
                                <button
                                    onClick={() => setViewMode('view')}
                                    className={`px-4 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all flex items-center gap-2 ${
                                        viewMode === 'view'
                                            ? 'bg-emerald-600 text-white shadow-lg'
                                            : 'text-[var(--text-tertiary)] hover:text-emerald-400'
                                    }`}
                                >
                                    <Eye size={12} /> View
                                </button>
                                <button
                                    onClick={() => setViewMode('edit')}
                                    className={`px-4 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all flex items-center gap-2 ${
                                        viewMode === 'edit'
                                            ? 'bg-purple-600 text-white shadow-lg'
                                            : 'text-[var(--text-tertiary)] hover:text-purple-400'
                                    }`}
                                >
                                    <FileText size={12} /> Edit
                                </button>
                            </div>

                            {/* Actions */}
                            {viewMode === 'edit' && (
                                <button
                                    onClick={handleSave}
                                    disabled={saving || !hasChanges}
                                    className="px-6 py-2.5 bg-purple-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-purple-500 transition-all shadow-lg shadow-purple-600/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                                >
                                    {saving ? (
                                        <>
                                            <Loader2 size={14} className="animate-spin" />
                                            Saving...
                                        </>
                                    ) : (
                                        <>
                                            <Save size={14} />
                                            Save Changes
                                        </>
                                    )}
                                </button>
                            )}

                            <button
                                onClick={handleCancel}
                                className="p-3 rounded-xl hover:bg-[var(--surface)] transition-all text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                                title="Close"
                            >
                                <X size={20} />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-hidden">
                    {loading ? (
                        <div className="flex items-center justify-center h-full">
                            <div className="flex flex-col items-center gap-4">
                                <Loader2 size={40} className="animate-spin text-cyan-500" />
                                <p className="text-sm text-[var(--text-secondary)] font-medium">Loading expert knowledge...</p>
                            </div>
                        </div>
                    ) : viewMode === 'view' ? (
                        <div className="h-full overflow-y-auto p-8 bg-[var(--background-secondary)] custom-scrollbar">
                            <div className="max-w-6xl mx-auto bg-[var(--surface)] rounded-2xl border border-[var(--border)] shadow-xl p-12">
                                <div className="prose prose-invert prose-cyan max-w-none">
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            h1: ({ node, ...props }) => <h1 className="text-3xl font-black text-white uppercase tracking-tighter mb-6 border-b border-white/10 pb-4" {...props} />,
                                            h2: ({ node, ...props }) => <h2 className="text-xl font-bold text-cyan-400 mt-8 mb-4 border-l-4 border-cyan-500 pl-4" {...props} />,
                                            h3: ({ node, ...props }) => <h3 className="text-lg font-bold text-emerald-400 mt-6 mb-2" {...props} />,
                                            p: ({ node, ...props }) => <p className="leading-relaxed mb-4 text-gray-300 text-sm" {...props} />,
                                            ul: ({ node, ...props }) => <ul className="list-disc list-inside space-y-2 mb-4 text-gray-300 text-sm" {...props} />,
                                            ol: ({ node, ...props }) => <ol className="list-decimal list-inside space-y-2 mb-4 text-gray-300 text-sm" {...props} />,
                                            code: ({ node, inline, className, children, ...props }: any) => {
                                                const match = /language-(\w+)/.exec(className || '');
                                                return !inline && match ? (
                                                    <div className="my-6 rounded-xl overflow-hidden border border-white/5 shadow-2xl">
                                                        <div className="bg-black/40 px-4 py-2 border-b border-white/5 flex items-center justify-between">
                                                            <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest">{match[1]}</span>
                                                        </div>
                                                        <SyntaxHighlighter
                                                            style={vscDarkPlus}
                                                            language={match[1]}
                                                            PreTag="div"
                                                            customStyle={{ margin: 0, padding: '20px', fontSize: '12px', background: '#0d1117' }}
                                                            {...props}
                                                        >
                                                            {String(children).replace(/\n$/, '')}
                                                        </SyntaxHighlighter>
                                                    </div>
                                                ) : (
                                                    <code className="bg-white/10 px-1.5 py-0.5 rounded text-cyan-300 font-mono text-[11px]" {...props}>
                                                        {children}
                                                    </code>
                                                );
                                            },
                                            table: ({ node, ...props }) => (
                                                <div className="overflow-x-auto my-6 border border-white/5 rounded-xl">
                                                    <table className="min-w-full divide-y divide-white/5" {...props} />
                                                </div>
                                            ),
                                            th: ({ node, ...props }) => <th className="px-4 py-3 bg-white/5 text-left text-[10px] font-black text-gray-400 uppercase tracking-widest" {...props} />,
                                            td: ({ node, ...props }) => <td className="px-4 py-3 text-sm border-t border-white/5" {...props} />,
                                            hr: ({ node, ...props }) => <hr className="my-10 border-white/5" {...props} />,
                                            blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-cyan-500 pl-4 py-2 my-4 bg-cyan-500/5 italic text-gray-400" {...props} />,
                                        }}
                                    >
                                        {knowledge}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        </div>
                    ) : viewMode === 'source' ? (
                        <div className="h-full overflow-y-auto p-8 bg-[var(--background-secondary)] custom-scrollbar">
                            <div className="max-w-6xl mx-auto bg-[var(--surface)] rounded-2xl border border-[var(--border)] shadow-xl overflow-hidden">
                                <SyntaxHighlighter
                                    language="markdown"
                                    style={vscDarkPlus}
                                    customStyle={{
                                        background: 'transparent',
                                        padding: '40px',
                                        margin: 0,
                                        fontSize: '14px',
                                        lineHeight: '1.8',
                                        minHeight: 'calc(100vh - 200px)'
                                    }}
                                    wrapLongLines={true}
                                    showLineNumbers={true}
                                >
                                    {knowledge}
                                </SyntaxHighlighter>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full overflow-hidden p-8 bg-[var(--background-secondary)]">
                            <div className="max-w-6xl mx-auto h-full flex flex-col gap-4">
                                <textarea
                                    value={editingKnowledge}
                                    onChange={(e) => handleEditChange(e.target.value)}
                                    className="flex-1 bg-[var(--surface)] border border-[var(--border)] rounded-2xl p-8 text-[var(--text-primary)] outline-none focus:ring-2 focus:ring-purple-500/30 font-mono text-sm leading-relaxed resize-none shadow-xl custom-scrollbar"
                                    placeholder="# Expert Knowledge&#10;&#10;## Best Practices&#10;&#10;- Add technology-specific patterns...&#10;- Document migration strategies...&#10;- Include code examples..."
                                    spellCheck={false}
                                />
                                
                                {hasChanges && (
                                    <div className="flex items-center justify-between bg-amber-500/10 border border-amber-500/30 rounded-xl px-6 py-3">
                                        <p className="text-sm text-amber-600 dark:text-amber-400 font-medium">
                                            You have unsaved changes
                                        </p>
                                        <div className="flex gap-3">
                                            <button
                                                onClick={() => {
                                                    setEditingKnowledge(knowledge);
                                                    setHasChanges(false);
                                                }}
                                                className="px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest border border-[var(--border)] hover:bg-[var(--surface)] transition-all"
                                            >
                                                Discard
                                            </button>
                                            <button
                                                onClick={handleSave}
                                                disabled={saving}
                                                className="px-5 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest bg-purple-600 text-white hover:bg-purple-500 transition-all disabled:opacity-50"
                                            >
                                                {saving ? "Saving..." : "Save Now"}
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
