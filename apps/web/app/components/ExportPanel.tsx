/**
 * Export Panel Component - Block 4 Downstreams
 * 
 * Displays documentation exports, rule candidates, and recommendation actions
 * with support for multiple formats (markdown, HTML, JSON) and interactive preview.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { fetchWithAuth } from '@/app/lib/auth-client';

interface ExportResult {
  format: 'markdown' | 'html' | 'json';
  project_id: string;
  project_name: string;
  project_status: string;
  content: string;
  metadata: Record<string, any>;
  toc?: Array<{ level: number; title: string; anchor: string }>;
  generated_at: string;
}

interface RuleCandidate {
  name: string;
  description: string;
  source_columns: string[];
  reusability_score: 'HIGH' | 'MEDIUM' | 'LOW';
  implementation_status: 'DRAFT' | 'VALIDATED' | 'IMPLEMENTED';
  subset_extraction: Record<string, any>;
  reusability_markers: string[];
}

interface RecommendationAction {
  recommendation_id: string;
  title: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  actions: Array<{ action_type: string; artifact_type: string }>;
  implementation_path: string;
  estimated_effort: 'LOW' | 'MEDIUM' | 'HIGH';
}

interface ExportPanelProps {
  projectId: string;
  projectName: string;
}

const ExportPanel: React.FC<ExportPanelProps> = ({ projectId, projectName }) => {
  const [activeTab, setActiveTab] = useState<'documentation' | 'rules' | 'actions'>('documentation');
  const [format, setFormat] = useState<'markdown' | 'html' | 'json'>('markdown');
  const [loading, setLoading] = useState(false);
  const [exportData, setExportData] = useState<ExportResult | null>(null);
  const [rulesData, setRulesData] = useState<{
    rule_candidates: RuleCandidate[];
    consolidation_opportunities: any[];
    summary: any;
  } | null>(null);
  const [actionsData, setActionsData] = useState<{
    recommendation_actions: RecommendationAction[];
    action_summary: any;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExportDocumentation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchWithAuth(
        `/projects/${projectId}/export/documentation?format=${format}`
      );
      if (!response.ok) throw new Error(`Failed to export: ${response.statusText}`);
      const data = await response.json();
      setExportData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleExportRules = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchWithAuth(`/projects/${projectId}/export/rule-candidates`);
      if (!response.ok) throw new Error(`Failed to export rules: ${response.statusText}`);
      const data = await response.json();
      setRulesData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const handleExportActions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchWithAuth(
        `/projects/${projectId}/export/recommendation-actions`
      );
      if (!response.ok)
        throw new Error(`Failed to export actions: ${response.statusText}`);
      const data = await response.json();
      setActionsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const downloadFile = (content: string, filename: string, mediaType: string) => {
    const blob = new Blob([content], { type: mediaType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleDownloadDocumentation = () => {
    if (!exportData) return;
    const ext = format === 'html' ? 'html' : format === 'json' ? 'json' : 'md';
    const mediaType =
      format === 'html'
        ? 'text/html'
        : format === 'json'
          ? 'application/json'
          : 'text/markdown';
    downloadFile(
      exportData.content,
      `${exportData.project_name} - Documentation.${ext}`,
      mediaType
    );
  };

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-indigo-900 mb-2">
          📦 Documentation Exports
        </h3>
        <p className="text-sm text-indigo-700 mb-4">
          Generate handover-ready documentation packages from discovered knowledge artifacts.
        </p>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 border-b">
          <button
            onClick={() => {
              setActiveTab('documentation');
              setExportData(null);
            }}
            className={`px-4 py-2 text-sm font-medium transition ${activeTab === 'documentation' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            📄 Documentation
          </button>
          <button
            onClick={() => {
              setActiveTab('rules');
              setRulesData(null);
            }}
            className={`px-4 py-2 text-sm font-medium transition ${activeTab === 'rules' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            ⚙️ Rule Candidates
          </button>
          <button
            onClick={() => {
              setActiveTab('actions');
              setActionsData(null);
            }}
            className={`px-4 py-2 text-sm font-medium transition ${activeTab === 'actions' ? 'border-b-2 border-indigo-600 text-indigo-600' : 'text-gray-600 hover:text-gray-900'}`}
          >
            ✅ Actions
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
            <p className="text-sm text-red-700">⚠️ {error}</p>
          </div>
        )}

        {/* Documentation Tab */}
        {activeTab === 'documentation' && (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-3">
              <button
                onClick={() => {
                  setFormat('markdown');
                  setExportData(null);
                }}
                className={`px-3 py-2 text-sm rounded border transition ${
                  format === 'markdown'
                    ? 'bg-indigo-100 border-indigo-300 text-indigo-900'
                    : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300'
                }`}
              >
                Markdown
              </button>
              <button
                onClick={() => {
                  setFormat('html');
                  setExportData(null);
                }}
                className={`px-3 py-2 text-sm rounded border transition ${
                  format === 'html'
                    ? 'bg-indigo-100 border-indigo-300 text-indigo-900'
                    : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300'
                }`}
              >
                HTML
              </button>
              <button
                onClick={() => {
                  setFormat('json');
                  setExportData(null);
                }}
                className={`px-3 py-2 text-sm rounded border transition ${
                  format === 'json'
                    ? 'bg-indigo-100 border-indigo-300 text-indigo-900'
                    : 'bg-white border-gray-200 text-gray-700 hover:border-gray-300'
                }`}
              >
                JSON
              </button>
            </div>

            <button
              onClick={handleExportDocumentation}
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded transition"
            >
              {loading ? '⏳ Generating...' : '📥 Generate Documentation'}
            </button>

            {exportData && (
              <div className="border border-gray-200 rounded-lg p-4 bg-white">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className="text-sm font-semibold text-gray-900">
                      {exportData.project_name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {exportData.metadata.lines} lines • {exportData.metadata.size_bytes} bytes
                    </p>
                  </div>
                  <button
                    onClick={handleDownloadDocumentation}
                    className="text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-1 rounded transition"
                  >
                    ⬇️ Download
                  </button>
                </div>

                {format === 'markdown' && exportData.toc && (
                  <div className="mb-4 p-3 bg-gray-50 rounded">
                    <p className="text-xs font-semibold text-gray-700 mb-2">Table of Contents</p>
                    <ul className="text-xs space-y-1 text-gray-600">
                      {exportData.toc.slice(0, 5).map((item, i) => (
                        <li key={i} style={{ paddingLeft: `${(item.level - 2) * 8}px` }}>
                          • {item.title}
                        </li>
                      ))}
                      {exportData.toc.length > 5 && (
                        <li className="text-gray-500">... {exportData.toc.length - 5} more sections</li>
                      )}
                    </ul>
                  </div>
                )}

                <div className="bg-gray-50 rounded p-3 max-h-48 overflow-auto">
                  <pre className="text-xs text-gray-700 whitespace-pre-wrap break-words">
                    {exportData.content.substring(0, 500)}...
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Rules Tab */}
        {activeTab === 'rules' && (
          <div className="space-y-4">
            <button
              onClick={handleExportRules}
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded transition"
            >
              {loading ? '⏳ Extracting...' : '🔧 Extract Rule Candidates'}
            </button>

            {rulesData && (
              <div className="border border-gray-200 rounded-lg p-4 bg-white space-y-3">
                <div className="text-sm">
                  <p className="font-semibold text-gray-900">
                    {rulesData.summary.total_rules} Rules Found
                  </p>
                  <p className="text-xs text-gray-500">
                    {rulesData.summary.high_reusability} High Reusability •{' '}
                    {rulesData.summary.consolidation_candidates} Consolidation Candidates
                  </p>
                </div>

                <div className="space-y-2">
                  {rulesData.rule_candidates.slice(0, 5).map((rule, i) => (
                    <div key={i} className="text-xs border-l-2 border-indigo-300 pl-3 py-2">
                      <p className="font-semibold text-gray-900">{rule.name}</p>
                      <p className="text-gray-600">{rule.description}</p>
                      <div className="flex gap-2 mt-1">
                        <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                          {rule.reusability_score} Reuse
                        </span>
                        <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                          {rule.implementation_status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Actions Tab */}
        {activeTab === 'actions' && (
          <div className="space-y-4">
            <button
              onClick={handleExportActions}
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded transition"
            >
              {loading ? '⏳ Mapping...' : '🎯 Map Recommendation Actions'}
            </button>

            {actionsData && (
              <div className="border border-gray-200 rounded-lg p-4 bg-white space-y-3">
                <div className="text-sm">
                  <p className="font-semibold text-gray-900">
                    {actionsData.action_summary.total_recommendations} Recommendations
                  </p>
                  <p className="text-xs text-gray-500">
                    {actionsData.action_summary.document_generation} Docs •{' '}
                    {actionsData.action_summary.code_generation} Code •{' '}
                    {actionsData.action_summary.process_updates} Process
                  </p>
                </div>

                <div className="space-y-2">
                  {actionsData.recommendation_actions.slice(0, 5).map((action, i) => (
                    <div key={i} className="text-xs border-l-2 border-green-300 pl-3 py-2">
                      <p className="font-semibold text-gray-900">{action.title}</p>
                      <div className="flex gap-2 mt-1">
                        <span
                          className={`px-2 py-0.5 rounded ${
                            action.severity === 'CRITICAL'
                              ? 'bg-red-100 text-red-700'
                              : action.severity === 'HIGH'
                                ? 'bg-orange-100 text-orange-700'
                                : action.severity === 'MEDIUM'
                                  ? 'bg-yellow-100 text-yellow-700'
                                  : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          {action.severity}
                        </span>
                        <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                          {action.implementation_path}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ExportPanel;
