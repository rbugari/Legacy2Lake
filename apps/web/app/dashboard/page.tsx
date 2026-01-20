"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { API_BASE_URL } from "../lib/config";
// import TranspilationView from "../components/stages/TranspilationView";
import DraftingView from "../components/stages/DraftingView";
import RefinementView from "../components/stages/RefinementView";
import WorkflowToolbar from "../components/WorkflowToolbar";
import { Upload, Github, FolderPlus, X, Trash2, RefreshCw, Settings } from "lucide-react";

export default function Dashboard() {
    const [projects, setProjects] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const router = useRouter();

    // Modal State
    const [projectName, setProjectName] = useState("");
    const [sourceType, setSourceType] = useState<"zip" | "github">("zip");
    const [githubUrl, setGithubUrl] = useState("");
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [overwrite, setOverwrite] = useState(false);
    const [isCreating, setIsCreating] = useState(false);

    // Fetching projects from backend
    useEffect(() => {
        const fetchProjects = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/projects`);
                if (response.ok) {
                    const data = await response.json();
                    // Basic mapping if needed, otherwise rely on matching shape
                    setProjects(data.map((p: any) => ({
                        ...p,
                        // Defaults for visual properties if missing in DB
                        progress: p.progress || 0,
                        alerts: p.alerts || 0,
                        origin: p.source_type || "Unknown",
                        stage: p.stage || "DRAFT"
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

    const handleCreateProject = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsCreating(true);

        const projectId = projectName.toLowerCase().replace(/[^a-z0-9]/g, '-');

        // Construct Payload
        const formData = new FormData();
        formData.append("name", projectName);
        formData.append("project_id", projectId);
        formData.append("source_type", sourceType);
        formData.append("overwrite", overwrite.toString());

        if (sourceType === "github") {
            formData.append("github_url", githubUrl);
        } else if (selectedFile) {
            formData.append("file", selectedFile);
        }

        try {
            const response = await fetch(`${API_BASE_URL}/projects/create`, {
                method: "POST",
                body: formData,
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    // Redirect to new workspace
                    router.push(`/workspace/${projectId}`);
                } else {
                    alert(`Error: ${data.error || "No se pudo crear el proyecto."}`);
                }
            } else {
                alert("Error al crear el proyecto. Revisa la consola.");
            }
        } catch (error) {
            console.error("Error creating project:", error);
            alert("Error de conexión con el backend.");
        } finally {
            setIsCreating(false);
        }
    };

    const handleDeleteProject = async (e: React.MouseEvent, projectId: string) => {
        e.preventDefault();
        // Use window.confirm explicitly
        if (!window.confirm("¿Estás seguro de que quieres eliminar este proyecto?")) {
            return;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                setProjects(prev => prev.filter(p => p.id !== projectId));
            } else {
                alert("Error al eliminar el proyecto.");
            }
        } catch (error) {
            console.error("Error deleting project:", error);
            alert("Error al conectar con el servidor.");
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 relative">
            <div className="max-w-7xl mx-auto p-8">
                <header className="flex justify-between items-center mb-10">
                    <div>
                        <h1 className="text-3xl font-bold">Consola de Soluciones</h1>
                        <p className="text-gray-500">Gestiona tus proyectos de modernización.</p>
                    </div>
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="bg-primary text-white px-6 py-2 rounded-lg font-bold hover:bg-secondary transition-all flex items-center gap-2 shadow-lg shadow-primary/20"
                    >
                        <FolderPlus size={18} /> Nueva Solución
                    </button>
                </header>

                {/* List of Projects */}
                {loading ? (
                    <div className="flex justify-center py-20">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-in slide-in-from-bottom-4">
                        {projects.map((p) => {
                            // Mappings
                            const stageMap: { [key: string]: string } = { "1": "TRIAGE", "2": "DRAFTING", "3": "REFINEMENT", "4": "GOVERNANCE" };
                            const displayStage = stageMap[p.stage.toString()] || p.stage;

                            const originMap: { [key: string]: string } = { "zip": "Local ZIP", "github": "GitHub" };
                            const displayOrigin = originMap[p.origin] || (p.origin === "Unknown" ? "" : p.origin);

                            return (
                                <div key={p.id} className="group bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 hover:border-primary/50 hover:shadow-xl transition-all h-full flex flex-col justify-between overflow-hidden">
                                    <Link href={`/workspace/${p.id}`} className="block p-6 flex-grow">
                                        <div className="flex justify-between items-start mb-4">
                                            <span className="text-gray-400 text-xs font-mono uppercase tracking-wider flex items-center gap-1">
                                                {displayOrigin === "GitHub" && <Github size={12} />}
                                                {displayOrigin === "Local ZIP" && <FolderPlus size={12} />}
                                                {displayOrigin}
                                            </span>
                                            <div className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-wider uppercase border ${getStageColor(displayStage)}`}>
                                                {displayStage}
                                            </div>
                                        </div>
                                        <h3 className="text-xl font-bold mb-2 group-hover:text-primary transition-colors">{p.name}</h3>
                                        <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2 mb-4 overflow-hidden">
                                            <div className="bg-primary h-full rounded-full transition-all duration-1000" style={{ width: `${p.progress}%` }}></div>
                                        </div>
                                    </Link>

                                    <div className="flex justify-between items-center border-t border-gray-100 dark:border-gray-800 px-6 py-4 bg-gray-50/50 dark:bg-gray-800/20">
                                        <div className="text-xs text-gray-500">
                                            <span className="block font-bold text-lg text-gray-900 dark:text-white">
                                                {p.assets_count !== undefined ? p.assets_count : p.progress + "%"}
                                            </span>
                                            {p.assets_count !== undefined ? "Paques / Assets" : "Completado"}
                                        </div>

                                        <div className="flex items-center gap-2">
                                            {/* Reset Button (Only if NOT in Stage 1/Triage) */}
                                            {p.stage > 1 && (
                                                <button
                                                    onClick={async (e) => {
                                                        e.preventDefault();
                                                        if (!confirm("¿Resetear proyecto a etapa TRIAGE? Se perderá el progreso.")) return;
                                                        await fetch(`${API_BASE_URL}/projects/${p.id}/reset`, { method: "POST" });
                                                        window.location.reload(); // Simple reload to refresh state
                                                    }}
                                                    className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors z-10"
                                                    title="Reiniciar a Triage (Rollback)"
                                                >
                                                    <RefreshCw size={16} /> {/* Using Refresh as Reset icon */}
                                                </button>
                                            )}

                                            <Link
                                                href={`/workspace/${p.id}/settings`}
                                                className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors z-10"
                                                title="Configuración"
                                            >
                                                <Settings size={16} />
                                            </Link>
                                            <button
                                                onClick={(e) => handleDeleteProject(e, p.id)}
                                                className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors z-10"
                                                title="Eliminar Solución"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Create Project Modal */}
                {isModalOpen && (
                    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
                        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border border-gray-200 dark:border-gray-800">
                            <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex justify-between items-center bg-gray-50 dark:bg-gray-800/50">
                                <h2 className="text-lg font-bold">Crear Nueva Solución</h2>
                                <button onClick={() => setIsModalOpen(false)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                                    <X size={20} />
                                </button>
                            </div>

                            <form onSubmit={handleCreateProject} className="p-6 space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Nombre del Proyecto</label>
                                    <input
                                        type="text"
                                        required
                                        value={projectName}
                                        onChange={(e) => setProjectName(e.target.value)}
                                        className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                                        placeholder="Ej: Migración CRM Legacy"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-2">Origen del Código</label>
                                    <div className="grid grid-cols-2 gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setSourceType("zip")}
                                            className={`p-3 rounded-lg border text-sm font-medium flex flex-col items-center gap-2 transition-all ${sourceType === "zip"
                                                ? "border-primary bg-primary/5 text-primary"
                                                : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                                                }`}
                                        >
                                            <Upload size={20} />
                                            Subir .ZIP Local
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setSourceType("github")}
                                            className={`p-3 rounded-lg border text-sm font-medium flex flex-col items-center gap-2 transition-all ${sourceType === "github"
                                                ? "border-primary bg-primary/5 text-primary"
                                                : "border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600"
                                                }`}
                                        >
                                            <Github size={20} />
                                            Repositorio GitHub
                                        </button>
                                    </div>
                                </div>

                                {sourceType === "zip" ? (
                                    <div className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg p-6 text-center hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer group relative">
                                        <input
                                            type="file"
                                            accept=".zip"
                                            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                        />
                                        <div className="pointer-events-none">
                                            <Upload className="mx-auto h-8 w-8 text-gray-400 group-hover:text-primary mb-2" />
                                            <p className="text-sm text-gray-500">
                                                {selectedFile ? <span className="text-primary font-bold">{selectedFile.name}</span> : "Arrastra tu .zip aquí o haz clic"}
                                            </p>
                                        </div>
                                    </div>
                                ) : (
                                    <div>
                                        <label className="block text-sm font-medium mb-1">URL del Repositorio</label>
                                        <input
                                            type="url"
                                            value={githubUrl}
                                            onChange={(e) => setGithubUrl(e.target.value)}
                                            className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                                            placeholder="https://github.com/usuario/repo"
                                        />
                                    </div>
                                )}

                                <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-100 dark:border-red-900/30">
                                    <input
                                        type="checkbox"
                                        id="overwrite"
                                        checked={overwrite}
                                        onChange={(e) => setOverwrite(e.target.checked)}
                                        className="w-4 h-4 text-red-600 rounded bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-700"
                                    />
                                    <label htmlFor="overwrite" className="text-xs font-bold text-red-700 dark:text-red-400 cursor-pointer">
                                        Sobrescribir proyecto si ya existe (Peligro: Borra datos previos)
                                    </label>
                                </div>

                                <div className="pt-4 flex gap-3">
                                    <button
                                        type="button"
                                        onClick={() => setIsModalOpen(false)}
                                        className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-700 font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                                    >
                                        Cancelar
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={isCreating || (sourceType === 'zip' && !selectedFile) || (sourceType === 'github' && !githubUrl)}
                                        className="flex-1 bg-primary text-white px-4 py-2 rounded-lg font-bold hover:bg-secondary transition-all disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
                                    >
                                        {isCreating ? <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span> : "Crear Solución"}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function getStageColor(stage: string) {
    switch (stage) {
        case 'TRIAGE': return 'bg-purple-100 text-purple-700 border-purple-200';
        case 'DRAFT': return 'bg-blue-100 text-blue-700 border-blue-200';
        case 'REFINEMENT': return 'bg-orange-100 text-orange-700 border-orange-200';
        case 'GOVERNANCE': return 'bg-green-100 text-green-700 border-green-200';
        default: return 'bg-gray-100 text-gray-700';
    }
}
