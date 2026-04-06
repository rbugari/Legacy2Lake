'use client';

import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  X,
  Search,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { fetchWithAuth } from '../lib/auth-client';
const logger = console;

interface Report {
  report_id: string;
  name: string;
  description: string;
  type: 'pdf' | 'html' | 'json' | 'markdown';
  available_formats: string[];
  category: string;
  product_line: 'source_intelligence' | 'migration_factory';
  minimum_stage: number;
  audience: string[];
  generator_service: string;
  api_endpoint: string;
  icon: string;
  color: string;
  estimated_generation_seconds: number;
  available_filters?: string[];
  related_reports?: string[];
  metadata?: Record<string, any>;
}

interface CatalogSummary {
  total_reports: number;
  by_category: Record<string, number>;
  by_type: Record<string, number>;
  by_stage: Record<number, number>;
  by_product_line: Record<string, number>;
  available_categories: string[];
  available_types: string[];
  available_audience_profiles: string[];
  available_product_lines: string[];
  product_line_descriptions: Record<string, string>;
}

interface ReportsCatalogModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
  currentStage: number;
  activeTenantId?: string;
}

const CATEGORY_COLORS: Record<string, { bg: string; text: string; badge: string }> = {
  technical: { bg: 'bg-blue-50', text: 'text-blue-900', badge: 'bg-blue-200 text-blue-800' },
  executive: {
    bg: 'bg-purple-50',
    text: 'text-purple-900',
    badge: 'bg-purple-200 text-purple-800',
  },
  governance: {
    bg: 'bg-green-50',
    text: 'text-green-900',
    badge: 'bg-green-200 text-green-800',
  },
  handover: { bg: 'bg-amber-50', text: 'text-amber-900', badge: 'bg-amber-200 text-amber-800' },
  analysis: { bg: 'bg-cyan-50', text: 'text-cyan-900', badge: 'bg-cyan-200 text-cyan-800' },
};

export default function ReportsCatalogModal({
  isOpen,
  onClose,
  projectId,
  projectName,
  currentStage,
  activeTenantId,
}: ReportsCatalogModalProps) {
  const [reports, setReports] = useState<Report[]>([]);
  const [filteredReports, setFilteredReports] = useState<Report[]>([]);
  const [summary, setSummary] = useState<CatalogSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloadingReports, setDownloadingReports] = useState<Set<string>>(new Set());
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedProductLine, setSelectedProductLine] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [selectedAudience, setSelectedAudience] = useState<string | null>(null);
  // Tracks the active download format per report (reportId → format string)
  const [selectedFormats, setSelectedFormats] = useState<Record<string, string>>({});

  const getSelectedFormat = (report: Report): string =>
    selectedFormats[report.report_id] ?? report.type;

  // Load catalog on mount
  useEffect(() => {
    if (isOpen) {
      loadCatalog();
    }
  }, [isOpen]);

  // Filter reports
  useEffect(() => {
    let filtered = reports;

    if (selectedProductLine) {
      filtered = filtered.filter((r) => r.product_line === selectedProductLine);
    }

    // Category filter
    if (selectedCategory) {
      filtered = filtered.filter((r) => r.category === selectedCategory);
    }

    // Type filter
    if (selectedType) {
      filtered = filtered.filter((r) => r.type === selectedType);
    }

    // Audience filter
    if (selectedAudience) {
      filtered = filtered.filter((r) => r.audience.includes(selectedAudience));
    }

    // Search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(
        (r) =>
          r.name.toLowerCase().includes(term) ||
          r.description.toLowerCase().includes(term) ||
          r.report_id.toLowerCase().includes(term)
      );
    }

    setFilteredReports(filtered);
  }, [reports, selectedProductLine, selectedCategory, selectedType, selectedAudience, searchTerm]);

  const loadCatalog = async () => {
    setLoading(true);
    try {
      const [catalogRes, summaryRes] = await Promise.all([
        fetchWithAuth(`/projects/reports/catalog?stage=${currentStage}`),
        fetchWithAuth('/projects/reports/catalog-summary'),
      ]);

      if (!catalogRes.ok) throw new Error('Failed to load reports');
      if (!summaryRes.ok) throw new Error('Failed to load summary');

      const catalogData = await catalogRes.json();
      const summaryData = await summaryRes.json();

      setReports(catalogData.reports || []);
      setSummary(summaryData.summary || null);
    } catch (err) {
      logger.error('Failed to load catalog:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async (report: Report) => {
    const fmt = getSelectedFormat(report);
    setDownloadingReports((prev) => new Set(prev).add(report.report_id));
    setErrors((prev) => ({ ...prev, [report.report_id]: '' }));

    try {
      const endpoint = report.api_endpoint
        .replace('{project_id}', projectId)
        .replace('{format}', fmt);
      // Only triage and final PDF reports require POST; everything else is GET
      const method = (endpoint.endsWith('/triage') || endpoint.endsWith('/final')) ? 'POST' : 'GET';

      const res = await fetchWithAuth(endpoint, {
        method,
        headers: activeTenantId ? { 'X-Tenant-ID': activeTenantId } : {},
      });

      if (!res.ok) {
        let errorMsg = 'Failed to generate report';
        try {
          const errorData = await res.json();
          errorMsg = errorData.detail || errorData.error || errorMsg;
        } catch {}
        throw new Error(errorMsg);
      }

      // Handle different response types
      if (fmt === 'pdf') {
        // Download PDF
        const blob = await res.blob();
        const filename = `${projectName}_${report.report_id}.pdf`;
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      } else {
        // Download JSON/Markdown/HTML
        const content = await res.text();
        const ext = fmt === 'markdown' ? 'md' : fmt;
        const mimeType =
          fmt === 'json'
            ? 'application/json'
            : fmt === 'html'
              ? 'text/html'
              : 'text/plain';

        const blob = new Blob([content], { type: mimeType });
        const filename = `${projectName}_${report.report_id}.${ext ?? fmt}`;
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown error';
      setErrors((prev) => ({ ...prev, [report.report_id]: errorMsg }));
    } finally {
      setDownloadingReports((prev) => {
        const updated = new Set(prev);
        updated.delete(report.report_id);
        return updated;
      });
    }
  };

  const getReportStatus = (report: Report) => {
    if (currentStage >= report.minimum_stage) {
      return { available: true, label: 'Available', icon: CheckCircle };
    }
    return {
      available: false,
      label: `Available at Stage ${report.minimum_stage}`,
      icon: Clock,
    };
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl max-w-5xl w-full border border-gray-200 dark:border-gray-700 overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-cyan-500/10 via-purple-500/10 to-blue-500/10 dark:from-cyan-500/20 dark:via-purple-500/20 dark:to-blue-500/20 border-b border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                📚 Reports Catalog
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Browse and download all available reports for:{' '}
                <span className="font-semibold text-gray-900 dark:text-gray-100">{projectName}</span>
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <X size={24} />
            </button>
          </div>

          {/* Summary Stats */}
          {summary && (
            <div className="mt-4 grid grid-cols-4 gap-2 text-xs">
              <div className="bg-white/50 dark:bg-gray-800/50 rounded px-2 py-1">
                <div className="font-bold text-cyan-600">{summary.total_reports}</div>
                <div className="text-gray-600 dark:text-gray-400">Reports Available</div>
              </div>
              <div className="bg-white/50 dark:bg-gray-800/50 rounded px-2 py-1">
                <div className="font-bold text-purple-600">
                  {Object.keys(summary.by_product_line).length}
                </div>
                <div className="text-gray-600 dark:text-gray-400">Product Lines</div>
              </div>
              <div className="bg-white/50 dark:bg-gray-800/50 rounded px-2 py-1">
                <div className="font-bold text-amber-600">
                  {Object.keys(summary.by_type).length}
                </div>
                <div className="text-gray-600 dark:text-gray-400">Formats</div>
              </div>
              <div className="bg-white/50 dark:bg-gray-800/50 rounded px-2 py-1">
                <div className="font-bold text-green-600">Stage {currentStage}</div>
                <div className="text-gray-600 dark:text-gray-400">Current</div>
              </div>
            </div>
          )}

          {summary && (
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="rounded-xl border border-cyan-200 bg-cyan-50/80 px-3 py-3 text-cyan-900">
                <div className="font-bold uppercase tracking-wide text-[11px]">Source Intelligence</div>
                <div className="mt-1 text-cyan-800">{summary.product_line_descriptions.source_intelligence}</div>
              </div>
              <div className="rounded-xl border border-purple-200 bg-purple-50/80 px-3 py-3 text-purple-900">
                <div className="font-bold uppercase tracking-wide text-[11px]">Migration Factory</div>
                <div className="mt-1 text-purple-800">{summary.product_line_descriptions.migration_factory}</div>
              </div>
            </div>
          )}
        </div>

        {/* Filters & Search */}
        <div className="border-b border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800/50">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {/* Search */}
            <div className="flex items-center gap-2 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 px-3 py-2">
              <Search size={16} className="text-gray-400" />
              <input
                type="text"
                placeholder="Search reports..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 bg-transparent outline-none text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400"
              />
            </div>

            <select
              value={selectedProductLine || ''}
              onChange={(e) => setSelectedProductLine(e.target.value || null)}
              className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 font-medium"
            >
              <option value="">All Product Lines</option>
              {summary?.available_product_lines.map((line) => (
                <option key={line} value={line}>
                  {line === 'source_intelligence' ? 'Source Intelligence' : 'Migration Factory'}
                </option>
              ))}
            </select>

            {/* Category Filter */}
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value || null)}
              className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 font-medium"
            >
              <option value="">All Categories</option>
              {summary?.available_categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>

            {/* Type Filter */}
            <select
              value={selectedType || ''}
              onChange={(e) => setSelectedType(e.target.value || null)}
              className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 font-medium"
            >
              <option value="">All Formats</option>
              {summary?.available_types.map((typ) => (
                <option key={typ} value={typ}>
                  {typ.toUpperCase()}
                </option>
              ))}
            </select>

            {/* Audience Filter */}
            <select
              value={selectedAudience || ''}
              onChange={(e) => setSelectedAudience(e.target.value || null)}
              className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 font-medium"
            >
              <option value="">All Profiles</option>
              {summary?.available_audience_profiles.map((prof) => (
                <option key={prof} value={prof}>
                  {prof.split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 size={32} className="text-cyan-500 animate-spin" />
            </div>
          ) : filteredReports.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <FileText size={48} className="mx-auto mb-4 opacity-20" />
              <p className="font-medium">No reports match your filters</p>
              <p className="text-sm">Try adjusting your search or filters</p>
            </div>
          ) : (
            ['source_intelligence', 'migration_factory'].map((productLine) => {
              const sectionReports = filteredReports.filter((report) => report.product_line === productLine);
              if (sectionReports.length === 0) return null;

              const sectionTitle = productLine === 'source_intelligence' ? 'Source Intelligence' : 'Migration Factory';
              const sectionClasses = productLine === 'source_intelligence'
                ? 'border-cyan-200 bg-cyan-50/40 dark:border-cyan-900 dark:bg-cyan-950/10'
                : 'border-purple-200 bg-purple-50/40 dark:border-purple-900 dark:bg-purple-950/10';

              return (
                <div key={productLine} className={`rounded-2xl border p-4 ${sectionClasses}`}>
                  <div className="mb-3">
                    <h4 className="text-sm font-bold uppercase tracking-wide text-gray-900 dark:text-gray-100">
                      {sectionTitle}
                    </h4>
                    <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                      {summary?.product_line_descriptions?.[productLine]}
                    </p>
                  </div>

                  <div className="space-y-3">
                    {sectionReports.map((report) => {
                      const status = getReportStatus(report);
                      const isDownloading = downloadingReports.has(report.report_id);
                      const error = errors[report.report_id];
                      const colors = CATEGORY_COLORS[report.category] || CATEGORY_COLORS.technical;
                      const StatusIcon = status.icon;

                      return (
                        <div
                          key={report.report_id}
                          className={`p-4 rounded-xl border-2 transition-all ${
                            status.available
                              ? 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-cyan-300 dark:hover:border-cyan-700 hover:shadow-lg'
                              : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-800 opacity-75'
                          }`}
                        >
                          <div className="flex items-start gap-4">
                            <div className="text-3xl flex-shrink-0">{report.icon}</div>

                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between gap-4 mb-2">
                                <div>
                                  <h4 className="text-base font-bold text-gray-900 dark:text-gray-100 mb-1">
                                    {report.name}
                                  </h4>
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className={`text-xs font-semibold px-2 py-1 rounded ${colors.badge}`}>
                                      {report.category}
                                    </span>
                                    <span className="text-xs font-semibold px-2 py-1 rounded bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-200">
                                      {report.product_line === 'source_intelligence' ? 'Origin' : 'Migration'}
                                    </span>
                                    <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
                                      <StatusIcon size={13} className={status.available ? 'text-green-500' : 'text-amber-500'} />
                                      {status.label}
                                    </div>
                                  </div>

                                  {/* Format selector chips — show when multiple formats available */}
                                  {report.available_formats && report.available_formats.length > 1 && (
                                    <div className="flex items-center gap-1 mt-2 flex-wrap">
                                      <span className="text-[11px] text-gray-500 dark:text-gray-400 mr-1">Format:</span>
                                      {report.available_formats.map((fmt) => {
                                        const active = getSelectedFormat(report) === fmt;
                                        return (
                                          <button
                                            key={fmt}
                                            onClick={() =>
                                              setSelectedFormats((prev) => ({ ...prev, [report.report_id]: fmt }))
                                            }
                                            className={`text-[11px] font-semibold px-2 py-0.5 rounded border transition-all ${
                                              active
                                                ? 'bg-cyan-500 text-white border-cyan-500'
                                                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-cyan-400'
                                            }`}
                                          >
                                            {fmt.toUpperCase()}
                                          </button>
                                        );
                                      })}
                                    </div>
                                  )}

                                  {/* Single-format badge when no choice */}
                                  {(!report.available_formats || report.available_formats.length <= 1) && (
                                    <div className="mt-1">
                                      <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                                        {report.type.toUpperCase()}
                                      </span>
                                    </div>
                                  )}
                                </div>

                                <button
                                  onClick={() => handleGenerateReport(report)}
                                  disabled={!status.available || isDownloading}
                                  className={`px-3 py-2 rounded-lg font-medium text-xs flex items-center gap-2 transition-all whitespace-nowrap ${
                                    status.available && !isDownloading
                                      ? 'bg-cyan-500 text-white hover:bg-cyan-600 active:scale-95'
                                      : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                                  }`}
                                >
                                  {isDownloading ? (
                                    <>
                                      <Loader2 size={14} className="animate-spin" />
                                      Generating...
                                    </>
                                  ) : (
                                    <>
                                      <Download size={14} />
                                      Download
                                    </>
                                  )}
                                </button>
                              </div>

                              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                {report.description}
                              </p>

                              {report.metadata && (
                                <div className="text-xs text-gray-500 dark:text-gray-500 space-y-1">
                                  {report.metadata.product_story && (
                                    <div>
                                      <strong>Role in product:</strong> {report.metadata.product_story}
                                    </div>
                                  )}
                                  {report.metadata.highlights && (
                                    <div>
                                      <strong>Highlights:</strong> {report.metadata.highlights.join(', ')}
                                    </div>
                                  )}
                                  {report.estimated_generation_seconds && (
                                    <div>
                                      ⏱️ ~{report.estimated_generation_seconds}s to generate
                                    </div>
                                  )}
                                </div>
                              )}

                              {error && (
                                <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-xs text-red-700 dark:text-red-300 flex items-center gap-2">
                                  <AlertCircle size={14} />
                                  {error}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-800/50 text-xs text-gray-600 dark:text-gray-400 flex items-center justify-between">
          <div>
            Showing {filteredReports.length} of {reports.length} reports
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={loadCatalog}
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
            >
              Refresh
            </button>
            <button
              onClick={onClose}
              className="px-3 py-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded font-medium transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
