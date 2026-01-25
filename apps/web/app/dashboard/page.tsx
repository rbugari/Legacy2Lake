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
                    alert(`Error: ${data.error || "No se pudo crear el proyecto."}`);
                }
            } else {
                alert("Error al crear el proyecto.");
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
        if (!window.confirm("¿Estás seguro de que quieres eliminar este proyecto?")) {
            return;
        }

        try {
            const response = await fetchWithAuth(`projects/${projectId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setProjects(prev => prev.filter(p => p.id !== projectId));
            } else {
                alert("Error al eliminar el proyecto.");
            }
        } catch (error) {
            console.error("Error deleting project:", error);
        }
    };

    const handleResetProject = async (e: React.MouseEvent, projectId: string) => {
        e.preventDefault();
        if (!confirm("¿Resetear proyecto a etapa TRIAGE? Se perderá el progreso.")) return;
        await fetchWithAuth(`projects/${projectId}/reset`, { method: "POST" });
        window.location.reload();
    };

    return (
        <div className="min-h-screen bg-[var(--background)] text-[var(--text-primary)] relative transition-colors duration-300">
            {/* Top accent light */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-64 bg-cyan-500/10 blur-[120px] pointer-events-none" />

            <div className="max-w-7xl mx-auto p-8 relative z-10">
                <header className="flex justify-between items-end mb-12">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <div className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse" />
                            <span className="text-[10px] font-bold tracking-[0.2em] text-cyan-500 uppercase">Legacy Modernization</span>
                        </div>
                        <h1 className="text-4xl font-extrabold tracking-tight mb-2">Consola de Soluciones</h1>
                        <p className="text-[var(--text-secondary)] font-medium">Gestiona tus proyectos de modernización de extremo a extremo.</p>
                    </div>
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="bg-cyan-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-cyan-500 transition-all flex items-center gap-2 shadow-xl shadow-cyan-600/20 active:scale-95"
                        >
                            <FolderPlus size={20} /> Nueva Solución
                        </button>
                    </div>
                </header>

                {/* List of Projects */}
                {loading ? (
                    <div className="flex flex-col items-center justify-center py-40">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-500 mb-4"></div>
                        <p className="text-sm font-medium text-[var(--text-tertiary)]">Cargando orquestaciones...</p>
                    </div>
                ) : projects.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-40 bg-white/5 border border-white/5 rounded-3xl">
                        <div className="w-16 h-16 bg-white/5 rounded-2xl flex items-center justify-center mb-6">
                            <FolderPlus size={32} className="text-gray-400" />
                        </div>
                        <h3 className="text-sm font-black uppercase tracking-widest mb-2">No active solutions</h3>
                        <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-8">Ready to modernize? Initialize your first pipeline.</p>
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="bg-cyan-600/10 text-cyan-600 px-8 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-cyan-600 hover:text-white transition-all outline-none"
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
