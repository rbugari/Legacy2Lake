"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchWithAuth } from "../lib/auth-client";
// import TranspilationView from "../components/stages/TranspilationView";

import ProjectCard from "../components/ProjectCard";
import ProjectWizard from "../components/ProjectWizard";
import { FolderPlus, Github, X, Upload } from "lucide-react";

export default function Dashboard() {
    const [projects, setProjects] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isCreating, setIsCreating] = useState(false);
    const router = useRouter();

    // Fetching projects from backend
    useEffect(() => {
        const fetchProjects = async () => {
            try {
                const response = await fetchWithAuth("projects");
                if (response.ok) {
                    const data = await response.json();
                    setProjects(data.map((p: any) => ({
                        ...p,
                        progress: p.progress || 0,
                        alerts: p.alerts || 0,
                        origin: p.source_type || "Unknown",
                        stage: p.stage || "1"
                    })));
                } else {
                    console.error("Failed to fetch projects");
                }
            } catch (error) {
                console.error("Error fetching projects:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchProjects();
    }, []);

    const handleCreateProject = async (wizardData: any) => {
        setIsCreating(true);

        const { name, sourceType, githubUrl, file } = wizardData;
        const projectId = name.toLowerCase().replace(/[^a-z0-9]/g, '-');

        const formData = new FormData();
        formData.append("name", name);
        formData.append("project_id", projectId);
        formData.append("source_type", sourceType);
        formData.append("overwrite", "true"); // Defaulting to true for demo speed

        if (sourceType === "github") {
            formData.append("github_url", githubUrl);
        } else if (file) {
            formData.append("file", file);
        }

        try {
            const response = await fetchWithAuth("projects/create", {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    router.push(`/workspace?id=${projectId}`);
                } else {
                    alert(`Error: ${data.error || "Could not create project."}`);
                }
            } else {
                alert("Error creating project.");
            }
        } catch (error) {
            console.error("Error creating project:", error);
        } finally {
            setIsCreating(false);
            setIsModalOpen(false);
        }
    };

    const handleDeleteProject = async (e: React.MouseEvent, projectId: string) => {
        e.preventDefault();
        if (!window.confirm("Are you sure you want to delete this project?")) {
            return;
        }

        try {
            const response = await fetchWithAuth(`projects/${projectId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setProjects(prev => prev.filter(p => p.id !== projectId));
            } else {
                alert("Error deleting project.");
            }
        } catch (error) {
            console.error("Error deleting project:", error);
        }
    };

    const handleResetProject = async (e: React.MouseEvent, projectId: string) => {
        e.preventDefault();
        if (!confirm("Reset project to TRIAGE stage? All progress will be lost.")) return;
        await fetchWithAuth(`projects/${projectId}/reset`, { method: "POST" });
        window.location.reload();
    };

    return (
        <div className="min-h-screen bg-[var(--background)] text-[var(--text-primary)] relative transition-colors duration-300">
            {/* Ambient background glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-5xl h-96 bg-gradient-to-b from-cyan-500/10 via-blue-500/5 to-transparent blur-3xl pointer-events-none" />

            <div className="max-w-7xl mx-auto p-8 relative z-10">
                <header className="flex justify-between items-end mb-16">
                    <div>
                        <div className="flex items-center gap-3 mb-3">
                            <div className="relative">
                                <div className="h-2.5 w-2.5 rounded-full bg-cyan-500 animate-pulse" />
                                <div className="absolute inset-0 h-2.5 w-2.5 rounded-full bg-cyan-500 animate-ping opacity-75" />
                            </div>
                            <span className="text-[11px] font-black tracking-[0.25em] text-cyan-500 uppercase">Legacy Modernization Platform</span>
                            <span className="bg-white/5 border border-white/10 px-2 py-0.5 rounded-md text-[9px] font-bold text-[var(--text-tertiary)] ml-2">
                                {projects.length} ACTIVE
                            </span>
                        </div>
                        <h1 className="text-5xl font-black tracking-tight mb-3 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                            Solutions Console
                        </h1>
                        <p className="text-[var(--text-secondary)] font-medium text-lg">
                            Manage your end-to-end modernization pipelines
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="group relative bg-gradient-to-r from-cyan-600 to-blue-600 text-white px-8 py-3.5 rounded-xl font-bold hover:from-cyan-500 hover:to-blue-500 transition-all flex items-center gap-3 shadow-2xl shadow-cyan-600/30 active:scale-95 overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                            <FolderPlus size={20} className="relative z-10" />
                            <span className="relative z-10">New Solution</span>
                        </button>
                    </div>
                </header>

                {/* List of Projects */}
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-48">
                        <div className="relative">
                            <div className="animate-spin rounded-full h-16 w-16 border-4 border-cyan-500/20 border-t-cyan-500 mb-6" />
                            <div className="absolute inset-0 rounded-full h-16 w-16 border-4 border-cyan-500/10 animate-ping" />
                        </div>
                        <p className="text-sm font-bold text-[var(--text-tertiary)] uppercase tracking-widest animate-pulse">Loading pipelines...</p>
                    </div>
                ) : projects.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-48 bg-gradient-to-br from-white/5 via-cyan-500/5 to-blue-500/5 border border-white/10 rounded-3xl backdrop-blur-sm">
                        <div className="w-20 h-20 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-2xl flex items-center justify-center mb-8 relative">
                            <FolderPlus size={40} className="text-cyan-400" />
                            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-2xl blur-xl" />
                        </div>
                        <h3 className="text-sm font-black uppercase tracking-[0.3em] mb-3 text-white">No Active Solutions</h3>
                        <p className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.25em] mb-10">Ready to modernize? Initialize your first pipeline.</p>
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="bg-gradient-to-r from-cyan-600/20 to-blue-600/20 border-2 border-cyan-600 text-cyan-400 px-10 py-4 rounded-xl text-[11px] font-black uppercase tracking-[0.25em] hover:bg-gradient-to-r hover:from-cyan-600 hover:to-blue-600 hover:text-white transition-all outline-none shadow-xl shadow-cyan-600/20"
                        >
                            Initialize Workspace
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        {projects.map((p) => (
                            <ProjectCard
                                key={p.id}
                                project={p}
                                onDelete={handleDeleteProject}
                                onReset={handleResetProject}
                            />
                        ))}
                    </div>
                )}

                <ProjectWizard
                    isOpen={isModalOpen}
                    onClose={() => setIsModalOpen(false)}
                    isCreating={isCreating}
                    onCreate={handleCreateProject}
                />
            </div>
        </div>
    );
}

function getStageColor(stage: string) {
    switch (stage) {
        case 'TRIAGE': return 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20';
        case 'DRAFT': return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';
        case 'REFINEMENT': return 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20';
        case 'GOVERNANCE': return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
        default: return 'bg-[var(--text-primary)]/5 text-[var(--text-secondary)] border-[var(--border)]';
    }
}
