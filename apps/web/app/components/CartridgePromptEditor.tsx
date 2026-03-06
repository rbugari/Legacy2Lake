"use client";

import { useState, useEffect } from "react";
import { Package, Info, Edit, Save, Eye, ChevronDown, ChevronUp, FileText } from "lucide-react";
import { fetchWithAuth } from "../lib/auth-client";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface CartridgePromptEditorProps {
    projectId: string;
    className?: string;
}

const TECH_METADATA: Record<string, { label: string; icon: string; description: string }> = {
    pyspark: {
        label: "PySpark Generic",
        icon: "⚡",
        description: "Standard Apache Spark SQL & Python"
    },
    databricks: {
        label: "Databricks PySpark",
        icon: "🧱",
        description: "Databricks Platform & Delta Lake"
    },
    cloudera: {
        label: "Cloudera Spark",
        icon: "☁️",
        description: "CDP Datahub & Apache Spark"
    },
    snowflake: {
        label: "Snowflake SQL",
        icon: "❄️",
        description: "Cloud data warehouse SQL dialect"
    },
    dbt: {
        label: "dbt (Data Build Tool)",
        icon: "🔧",
        description: "Transform data using SQL and Jinja templates"
    },
    fabric: {
        label: "Microsoft Fabric",
        icon: "🧵",
        description: "Microsoft's unified analytics platform"
    },
    microsoft_fabric: {
        label: "Microsoft Fabric",
        icon: "🧵",
        description: "Microsoft's unified analytics platform"
    },
    bigquery: {
        label: "Google BigQuery",
        icon: "🔍",
        description: "Google Cloud data warehouse SQL"
    },
    redshift: {
        label: "Amazon Redshift",
        icon: "🚀",
        description: "AWS cloud data warehouse SQL"
    }
};

export default function CartridgePromptEditor({ projectId, className = "" }: CartridgePromptEditorProps) {
    const [techStack, setTechStack] = useState<string>("pyspark");
    const [cartridgePrompt, setCartridgePrompt] = useState<string>("");
    const [projectCustomInstructions, setProjectCustomInstructions] = useState<string>("");
    const [editedInstructions, setEditedInstructions] = useState<string>("");
    const [isEditing, setIsEditing] = useState(false);
    const [showCartridgeReference, setShowCartridgeReference] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, [projectId]);

    const loadData = async () => {
        setLoading(true);
        setError(null);

        try {
            // Load registry + settings in parallel — same priority logic as TechnologyMixer
            const [settingsRes, registryRes] = await Promise.all([
                fetchWithAuth(`/projects/${projectId}/settings`),
                fetchWithAuth(`/projects/${projectId}/registry`),
            ]);

            let resolvedTech = "pyspark";

            // 1. Read from settings (base config)
            if (settingsRes.ok) {
                const settings = await settingsRes.json();
                const fromSettings = settings.tech_stack || settings.cartridge || settings.target_tech;
                if (fromSettings) resolvedTech = fromSettings.toLowerCase().trim();

                // Load custom instructions from project settings
                const customInstructions = settings.custom_instructions || "";
                setProjectCustomInstructions(customInstructions);
                setEditedInstructions(customInstructions);
            } else {
                throw new Error("Failed to load project settings");
            }

            // 2. Registry overrides settings (same logic as TechnologyMixer)
            if (registryRes.ok) {
                const data = await registryRes.json();
                const target = data.registry?.find((r: any) => r.key === 'target_stack');
                if (target?.value) {
                    const fromRegistry = target.value.toLowerCase().trim();
                    // Use registry value if it's an explicit choice (not the auto-seeded "pyspark" default
                    // when settings already has something else)
                    if (fromRegistry && (fromRegistry !== 'pyspark' || resolvedTech === 'pyspark')) {
                        resolvedTech = fromRegistry;
                    }
                }
            }

            setTechStack(resolvedTech);

            // Load the cartridge prompt for the resolved tech
            await loadCartridgePrompt(resolvedTech);

        } catch (err) {
            console.error("[CartridgePromptEditor] Load failed:", err);
            setError(err instanceof Error ? err.message : "Failed to load data");
        } finally {
            setLoading(false);
        }
    };

    const loadCartridgePrompt = async (tech: string) => {
        try {
            const promptRes = await fetchWithAuth(`/api/v1/prompts?tech_stack=${tech}&pattern_type=direct`);

            if (promptRes.ok) {
                const data = await promptRes.json();
                if (data.prompts && data.prompts.length > 0) {
                    const prompt = data.prompts[0];
                    setCartridgePrompt(prompt.content || "");
                } else {
                    setCartridgePrompt("");
                }
            }
        } catch (err) {
            console.error("[CartridgePromptEditor] Cartridge prompt load failed:", err);
            // Non-fatal - cartridge prompt is optional reference
        }
    };

    const handleEdit = () => {
        setIsEditing(true);
        setSuccessMessage(null);
    };

    const handleCancel = () => {
        setIsEditing(false);
        setEditedInstructions(projectCustomInstructions);
        setSuccessMessage(null);
    };

    const handleSave = async () => {
        setSaving(true);
        setError(null);
        setSuccessMessage(null);

        try {
            // First, load current settings to preserve other fields
            const currentSettingsRes = await fetchWithAuth(`/projects/${projectId}/settings`);
            if (!currentSettingsRes.ok) {
                throw new Error("Failed to load current settings");
            }
            const currentSettings = await currentSettingsRes.json();

            // Merge custom instructions with existing settings
            const updatedSettings = {
                ...currentSettings,
                custom_instructions: editedInstructions
            };

            // Save merged settings
            const response = await fetchWithAuth(`/projects/${projectId}/settings`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedSettings)
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `Save failed: ${response.status}`);
            }

            setProjectCustomInstructions(editedInstructions);
            setIsEditing(false);
            setSuccessMessage("✅ Project custom instructions saved successfully!");

        } catch (err) {
            console.error("[CartridgePromptEditor] Save failed:", err);
            setError(err instanceof Error ? err.message : "Failed to save instructions");
        } finally {
            setSaving(false);
        }
    };

    const handleClearInstructions = () => {
        if (!confirm("Clear all custom instructions for this project?")) {
            return;
        }
        setEditedInstructions("");
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    const techMeta = TECH_METADATA[techStack] || {
        label: techStack.toUpperCase(),
        icon: "📦",
        description: "Custom technology stack"
    };

    return (
        <div className={`space-y-6 p-6 ${className}`}>
            {/* Success banner */}
            {successMessage && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                    <Info className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <div className="font-semibold text-green-800">Success</div>
                        <div className="text-sm text-green-700">{successMessage}</div>
                    </div>
                </div>
            )}

            {/* Error banner */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                    <Info className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <div className="flex-1">
                        <div className="font-semibold text-red-800">Error</div>
                        <div className="text-sm text-red-700">{error}</div>
                    </div>
                </div>
            )}

            {/* Info: 3-Level Architecture */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                    <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-blue-800">
                        <strong>3-Level Prompt Architecture:</strong>
                        <ol className="mt-2 ml-4 space-y-1 list-decimal">
                            <li><strong>Agent System Prompt</strong> - Agent C base instructions (managed by platform)</li>
                            <li><strong>Cartridge Prompt</strong> - Technology-specific template below (read-only reference)</li>
                            <li><strong>Project Custom Instructions</strong> - Your specific adjustments (editable)</li>
                        </ol>
                        <div className="mt-2 text-xs text-blue-700">
                            All 3 levels combine during code generation. The cartridge prompt is protected (cannot be broken).
                        </div>
                    </div>
                </div>
            </div>

            {/* Target Technology (Read-only display) */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-6">
                <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                        <Package className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-gray-800">Target Technology</h3>
                        <p className="text-sm text-gray-600">From project configuration</p>
                    </div>
                </div>

                <div className="bg-white rounded-lg p-4 border border-purple-200">
                    <div className="flex items-center gap-3">
                        <span className="text-3xl">{techMeta.icon}</span>
                        <div className="flex-1">
                            <div className="text-lg font-semibold text-gray-800">{techMeta.label}</div>
                            <div className="text-sm text-gray-600">{techMeta.description}</div>
                        </div>
                        <div className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold uppercase">
                            Active
                        </div>
                    </div>
                </div>
            </div>

            {/* Level 2: Cartridge Prompt (Reference - Collapsible) */}
            <div className="bg-white border border-gray-300 rounded-lg">
                <button
                    onClick={() => setShowCartridgeReference(!showCartridgeReference)}
                    className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
                >
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gray-100 rounded-lg">
                            <FileText className="w-5 h-5 text-gray-600" />
                        </div>
                        <div className="text-left">
                            <h3 className="text-lg font-semibold text-gray-800">
                                Level 2: Cartridge Prompt (Reference)
                                <span className="ml-2 px-2 py-1 bg-gray-100 text-gray-600 rounded text-xs font-semibold">
                                    READ-ONLY
                                </span>
                            </h3>
                            <p className="text-sm text-gray-600">
                                Generic {techMeta.label} template - {showCartridgeReference ? 'Click to hide' : 'Click to view'}
                            </p>
                        </div>
                    </div>
                    {showCartridgeReference ? (
                        <ChevronUp className="w-5 h-5 text-gray-400" />
                    ) : (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                    )}
                </button>

                {showCartridgeReference && (
                    <div className="p-4 border-t border-gray-200">
                        {cartridgePrompt ? (
                            <div className="bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
                                <SyntaxHighlighter
                                    language="markdown"
                                    style={vscDarkPlus}
                                    customStyle={{
                                        margin: 0,
                                        padding: "1rem",
                                        fontSize: "0.875rem",
                                        maxHeight: "400px",
                                        overflow: "auto"
                                    }}
                                >
                                    {cartridgePrompt}
                                </SyntaxHighlighter>
                            </div>
                        ) : (
                            <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center text-gray-500">
                                No generic cartridge prompt found for {techMeta.label}
                            </div>
                        )}
                        <div className="mt-3 text-xs text-gray-600">
                            <strong>Note:</strong> This is the protected generic template. It cannot be modified to prevent breaking code generation.
                        </div>
                    </div>
                )}
            </div>

            {/* Level 3: Project Custom Instructions (Editable) */}
            <div className="bg-white border border-green-300 rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-green-100 rounded-lg">
                            <Edit className="w-5 h-5 text-green-600" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-gray-800">
                                Level 3: Project Custom Instructions
                                <span className="ml-2 px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold">
                                    EDITABLE
                                </span>
                            </h3>
                            <p className="text-sm text-gray-600">
                                Add your project-specific adjustments, business rules, naming conventions, etc.
                            </p>
                        </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-2">
                        {!isEditing && (
                            <button
                                onClick={handleEdit}
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                <Edit className="w-4 h-4" />
                                Edit
                            </button>
                        )}
                        {isEditing && (
                            <>
                                <button
                                    onClick={handleSave}
                                    disabled={saving}
                                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                                >
                                    <Save className="w-4 h-4" />
                                    {saving ? "Saving..." : "Save"}
                                </button>
                                <button
                                    onClick={handleCancel}
                                    disabled={saving}
                                    className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50"
                                >
                                    <Eye className="w-4 h-4" />
                                    Cancel
                                </button>
                            </>
                        )}
                    </div>
                </div>

                {/* Edit mode - Textarea */}
                {isEditing ? (
                    <div className="space-y-3">
                        <textarea
                            value={editedInstructions}
                            onChange={(e) => setEditedInstructions(e.target.value)}
                            className="w-full h-64 p-4 border border-gray-300 rounded-lg font-mono text-sm text-gray-900 bg-white focus:ring-2 focus:ring-green-500 focus:border-green-500"
                            placeholder="# Project Custom Instructions

Example adjustments:
- All table names must be lowercase
- Use 'stg_' prefix for staging tables
- Add try-catch blocks for all database operations
- Include audit columns: created_at, updated_at, created_by
- Use ISO-8601 format for all timestamps

Add your specific requirements here in Markdown format..."
                            spellCheck={false}
                        />
                        <div className="flex items-center justify-between text-sm text-gray-600">
                            <span>{editedInstructions.length.toLocaleString()} characters</span>
                            <button
                                onClick={handleClearInstructions}
                                className="text-red-600 hover:text-red-700 underline text-xs"
                            >
                                Clear all
                            </button>
                        </div>
                    </div>
                ) : (
                    /* View mode */
                    <div>
                        {projectCustomInstructions ? (
                            <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
                                <pre className="whitespace-pre-wrap font-mono text-sm text-gray-900 leading-relaxed">
                                    {projectCustomInstructions}
                                </pre>
                            </div>
                        ) : (
                            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
                                <div className="text-yellow-600 mb-2">⚠️ No custom instructions defined</div>
                                <div className="text-sm text-yellow-700">
                                    Click <strong>Edit</strong> to add project-specific adjustments.
                                    These will be applied on top of the generic cartridge prompt.
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Help text */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                    <div className="flex items-start gap-3">
                        <Info className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-blue-800">
                            <strong>How it works:</strong> During code generation, Agent C combines all 3 levels:
                            <ol className="mt-2 ml-4 space-y-1 list-decimal">
                                <li>Loads Agent C system prompt (base instructions)</li>
                                <li>Applies <strong>Cartridge Prompt</strong> for {techMeta.label}</li>
                                <li>Applies your <strong>Project Custom Instructions</strong> (this section)</li>
                            </ol>
                            <div className="mt-2 text-xs">
                                The cartridge prompt ensures correct syntax and structure. Your custom instructions
                                add business rules, naming conventions, and project-specific requirements.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
