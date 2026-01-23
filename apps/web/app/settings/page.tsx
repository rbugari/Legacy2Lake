
"use client";

import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import VaultEditor from "../components/settings/VaultEditor";
import ModelCatalog from "../components/settings/ModelCatalog";
import AgentMatrix from "../components/settings/AgentMatrix";
import Link from "next/link";
import { ArrowLeft, Building, Database, GitMerge, FileKey } from "lucide-react";

export default function SettingsPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState<"vault" | "models" | "matrix">("vault");

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
                        icon={<GitMerge size={18} />}
                        label="Agent Matrix"
                    />
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
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h2 className="text-xl font-semibold flex items-center gap-2">
                                        <GitMerge className="w-5 h-5" /> Strategic Agent Matrix
                                    </h2>
                                    <p className="text-sm text-[var(--text-secondary)]">
                                        Assign specific models to each Agent role to optimize for cost or performance.
                                    </p>
                                </div>
                            </div>
                            <AgentMatrix />
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
