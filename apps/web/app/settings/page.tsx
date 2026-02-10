
"use client";

import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import VaultEditor from "../components/settings/VaultEditor";
import ModelCatalog from "../components/settings/ModelCatalog";
import StrategicIntelligenceHub from "../components/settings/StrategicIntelligenceHub";
import UserManagement from "../components/settings/UserManagement";
import ProjectAccess from "../components/settings/ProjectAccess";
import Link from "next/link";
import { ArrowLeft, Building, Database, Sparkles, FileKey, Users, FolderOpen } from "lucide-react";

export default function SettingsPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState<"vault" | "models" | "matrix" | "users" | "projects">("vault");
    
    const isManager = user?.role === "MANAGER" || user?.role === "ADMIN";

    return (
        <div className="min-h-screen bg-[var(--background)] text-[var(--text-primary)] relative transition-colors duration-300">
            <div className="max-w-5xl mx-auto p-8">

                {/* Header */}
                <div className="flex items-center gap-4 mb-8">
                    <Link href="/dashboard" className="p-2 -ml-2 rounded-full hover:bg-[var(--text-primary)]/5 transition-colors">
                        <ArrowLeft className="w-6 h-6" />
                    </Link>
                    <div>
                        <h1 className="text-2xl font-bold">Tenant Console</h1>
                        <p className="text-[var(--text-secondary)]">Manage your AI supply chain and security.</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-4 border-b border-[var(--border)] mb-8">
                    <TabButton
                        active={activeTab === "vault"}
                        onClick={() => setActiveTab("vault")}
                        icon={<FileKey size={18} />}
                        label="Provider Vault"
                    />
                    <TabButton
                        active={activeTab === "models"}
                        onClick={() => setActiveTab("models")}
                        icon={<Database size={18} />}
                        label="Model Catalog"
                    />
                    <TabButton
                        active={activeTab === "matrix"}
                        onClick={() => setActiveTab("matrix")}
                        icon={<Sparkles size={18} />}
                        label="Intelligence Hub & Matrix"
                    />
                    {isManager && (
                        <TabButton
                            active={activeTab === "users"}
                            onClick={() => setActiveTab("users")}
                            icon={<Users size={18} />}
                            label="User Management"
                        />
                    )}
                    {isManager && (
                        <TabButton
                            active={activeTab === "projects"}
                            onClick={() => setActiveTab("projects")}
                            icon={<FolderOpen size={18} />}
                            label="Project Access"
                        />
                    )}
                </div>

                {/* Tab Content */}
                <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                    {activeTab === "vault" && (
                        <section className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-6">
                            <h2 className="text-xl font-semibold mb-2 flex items-center gap-2">
                                <Building className="w-5 h-5" /> Provider Vault
                            </h2>
                            <p className="text-sm text-[var(--text-secondary)] mb-6">
                                Connect your own Model Providers (Bring Your Own Keys). These keys are encrypted and stored securely.
                            </p>
                            <VaultEditor />
                        </section>
                    )}

                    {activeTab === "models" && (
                        <section>
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h2 className="text-xl font-semibold flex items-center gap-2">
                                        <Database className="w-5 h-5" /> Artificial Intelligence Catalog
                                    </h2>
                                    <p className="text-sm text-[var(--text-secondary)]">
                                        Explore available models supported by your platform credentials.
                                    </p>
                                </div>
                            </div>
                            <ModelCatalog />
                        </section>
                    )}

                    {activeTab === "matrix" && (
                        <section>
                            <div className="flex justify-between items-center mb-1">
                                <div>
                                    <h2 className="text-xl font-semibold flex items-center gap-2">
                                        <Sparkles className="w-5 h-5 text-blue-500" /> Strategic Intelligence Hub
                                    </h2>
                                    <p className="text-sm text-[var(--text-secondary)]">
                                        Audit agent instructions, manage model assignments, and preview cross-technology expertise.
                                    </p>
                                </div>
                            </div>
                            <StrategicIntelligenceHub />
                        </section>
                    )}
                    
                    {activeTab === "users" && isManager && (
                        <section className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-6">
                            <UserManagement />
                        </section>
                    )}
                    
                    {activeTab === "projects" && isManager && (
                        <section className="bg-[var(--surface)] border border-[var(--border)] rounded-xl p-6">
                            <ProjectAccess />
                        </section>
                    )}
                </div>

            </div>
        </div>
    );
}

function TabButton({ active, onClick, icon, label }: any) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm transition-all ${active
                ? "border-[var(--color-primary)] text-[var(--color-primary)]"
                : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--text-primary)]/5 rounded-t-lg"
                }`}
        >
            {icon}
            {label}
        </button>
    );
}
