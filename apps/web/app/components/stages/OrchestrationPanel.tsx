"use client";
import { useState, useEffect } from "react";
import { Copy, Download, Code, Server, Database, FileCode, Terminal, CheckCircle2 } from "lucide-react";
import { API_BASE_URL } from "../../lib/config";

interface OrchestrationPanelProps {
    projectId: string;
}

type Orchestrator = "airflow" | "databricks" | "yaml";

export default function OrchestrationPanel({ projectId }: OrchestrationPanelProps) {
    const [selectedOrchestrator, setSelectedOrchestrator] = useState<Orchestrator>("airflow");
    const [code, setCode] = useState<string>("");
    const [definition, setDefinition] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [copied, setCopied] = useState(false);
    const [filename, setFilename] = useState("");

    const fetchOrchestration = async (orchestrator: Orchestrator) => {
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/projects/${projectId}/orchestration/${orchestrator}`);
            const data = await res.json();

            if (orchestrator === "databricks") {
                setDefinition(data.definition);
                setCode(JSON.stringify(data.definition, null, 2));
            } else {
                setCode(data.code);
            }
            setFilename(data.filename);
        } catch (e) {
            console.error("Failed to fetch orchestration", e);
            setCode("# Error loading orchestration file");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchOrchestration(selectedOrchestrator);
    }, [projectId, selectedOrchestrator]);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleDownload = () => {
        const blob = new Blob([code], { type: selectedOrchestrator === "databricks" ? "application/json" : "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="flex flex-col gap-6 h-full animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Orchestrator Selector */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <OrchestratorCard
                    active={selectedOrchestrator === "airflow"}
                    onClick={() => setSelectedOrchestrator("airflow")}
                    icon={<Server className="text-blue-500" />}
                    title="Apache Airflow"
                    description="Python-based DAG for orchestrating tasks in Airflow environments."
                />
                <OrchestratorCard
                    active={selectedOrchestrator === "databricks"}
                    onClick={() => setSelectedOrchestrator("databricks")}
                    icon={<Database className="text-orange-500" />}
                    title="Databricks Workflow"
                    description="JSON definition for Databricks Jobs & Multi-Task Workflows."
                />
                <OrchestratorCard
                    active={selectedOrchestrator === "yaml"}
                    onClick={() => setSelectedOrchestrator("yaml")}
                    icon={<Terminal className="text-indigo-500" />}
                    title="Generic YAML"
                    description="Standard YAML pipeline for custom CI/CD or internal orchestrators."
                />
            </div>

            {/* Code Preview */}
            <div className="flex-1 flex flex-col bg-white dark:bg-gray-900 rounded-3xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden min-h-[500px]">
                <div className="px-6 py-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between bg-gray-50/50 dark:bg-gray-900/50">
                    <div className="flex items-center gap-2">
                        <FileCode size={20} className="text-gray-400" />
                        <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">{filename || "Preview"}</span>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={handleCopy}
                            className="p-2 text-gray-500 hover:text-primary hover:bg-white dark:hover:bg-gray-800 rounded-lg transition-all flex items-center gap-2 text-xs font-bold"
                        >
                            {copied ? <CheckCircle2 size={16} className="text-green-500" /> : <Copy size={16} />}
                            {copied ? "Copied!" : "Copy Code"}
                        </button>
                        <button
                            onClick={handleDownload}
                            className="btn-primary py-2 px-4 text-xs flex items-center gap-2"
                        >
                            <Download size={16} /> Download
                        </button>
                    </div>
                </div>

                <div className="flex-1 relative overflow-hidden flex flex-col">
                    {loading && (
                        <div className="absolute inset-0 z-10 bg-white/50 dark:bg-gray-950/50 backdrop-blur-sm flex items-center justify-center">
                            <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                        </div>
                    )}
                    <pre className="flex-1 p-6 font-mono text-sm overflow-auto custom-scrollbar bg-gray-50 dark:bg-gray-950/50 text-gray-700 dark:text-gray-300 pointer-events-auto leading-relaxed">
                        <code>{code}</code>
                    </pre>
                </div>

                {selectedOrchestrator === "databricks" && definition && (
                    <div className="px-6 py-3 bg-orange-500/5 border-t border-orange-500/10 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse" />
                        <span className="text-[10px] font-bold text-orange-600 dark:text-orange-400 uppercase tracking-widest">
                            Ready for Deployment to Databricks Jobs API
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}

function OrchestratorCard({ active, onClick, icon, title, description }: any) {
    return (
        <button
            onClick={onClick}
            className={`p-6 rounded-3xl border text-left transition-all duration-300 relative overflow-hidden group ${active
                ? "bg-white dark:bg-gray-900 border-primary shadow-xl shadow-primary/10 ring-1 ring-primary"
                : "card-glass hover:border-primary/50"
                }`}
        >
            <div className={`p-3 rounded-2xl mb-4 inline-flex ${active ? "bg-primary/10" : "bg-white dark:bg-gray-900 shadow-sm border border-gray-100 dark:border-gray-800"}`}>
                {icon}
            </div>
            <h4 className={`text-sm font-bold mb-2 ${active ? "text-primary" : "text-gray-700 dark:text-gray-300"}`}>{title}</h4>
            <p className="text-xs text-gray-500 leading-relaxed">{description}</p>

            {active && (
                <div className="absolute top-0 right-0 p-4">
                    <CheckCircle2 size={16} className="text-blue-500 text-opacity-40" />
                </div>
            )}
        </button>
    );
}
