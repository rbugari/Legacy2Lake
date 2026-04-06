'use client';

import React, { useEffect, useState } from 'react';
import { ArrowRight, Database, FileText, Library, Loader2 } from 'lucide-react';
import { fetchWithAuth } from '../lib/auth-client';

interface ReportsAccessPanelProps {
  currentStage: number;
  onOpenCatalog: () => void;
}

interface CatalogReport {
  report_id: string;
  product_line: 'source_intelligence' | 'migration_factory';
}

interface CatalogSummary {
  total_reports: number;
  product_line_descriptions: Record<string, string>;
}

const PRODUCT_LINE_COPY = {
  source_intelligence: {
    label: 'Source Intelligence',
    eyebrow: 'Understand The Legacy Estate',
    accent: 'from-cyan-500/20 via-sky-500/10 to-transparent',
    border: 'border-cyan-400/20',
    text: 'text-cyan-200',
    iconBg: 'bg-cyan-500/15',
    iconColor: 'text-cyan-300',
    bullets: ['Forensic gaps', 'Schema intelligence', 'Knowledge exports'],
  },
  migration_factory: {
    label: 'Migration Factory',
    eyebrow: 'Deliver The New Solution',
    accent: 'from-amber-500/20 via-orange-500/10 to-transparent',
    border: 'border-amber-400/20',
    text: 'text-amber-200',
    iconBg: 'bg-amber-500/15',
    iconColor: 'text-amber-300',
    bullets: ['Delivery reports', 'Rule libraries', 'Handover evidence'],
  },
} as const;

export default function ReportsAccessPanel({ currentStage, onOpenCatalog }: ReportsAccessPanelProps) {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<CatalogSummary | null>(null);
  const [availableCounts, setAvailableCounts] = useState({
    source_intelligence: 0,
    migration_factory: 0,
  });

  useEffect(() => {
    let isMounted = true;

    async function load() {
      setLoading(true);
      try {
        const [catalogRes, summaryRes] = await Promise.all([
          fetchWithAuth(`/projects/reports/catalog?stage=${currentStage}`),
          fetchWithAuth('/projects/reports/catalog-summary'),
        ]);

        if (!catalogRes.ok || !summaryRes.ok) {
          throw new Error('Failed to load reports access data');
        }

        const catalogData = await catalogRes.json();
        const summaryData = await summaryRes.json();
        const reports: CatalogReport[] = catalogData.reports || [];

        if (!isMounted) return;

        setSummary(summaryData.summary || null);
        setAvailableCounts({
          source_intelligence: reports.filter((report) => report.product_line === 'source_intelligence').length,
          migration_factory: reports.filter((report) => report.product_line === 'migration_factory').length,
        });
      } catch {
        if (!isMounted) return;
        setSummary(null);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      isMounted = false;
    };
  }, [currentStage]);

  return (
    <section className="px-6 pt-4 pb-2">
      <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(251,191,36,0.12),_transparent_24%),linear-gradient(135deg,_rgba(15,23,42,0.96),_rgba(30,41,59,0.94))] shadow-[0_18px_60px_rgba(15,23,42,0.35)]">
        <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_0%,rgba(255,255,255,0.03)_20%,transparent_45%)]" />
        <div className="relative z-10 p-6 md:p-7">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[10px] font-black uppercase tracking-[0.24em] text-cyan-200">
                <Library size={12} /> Reports Catalog
              </div>
              <h2 className="mt-4 text-2xl font-black tracking-tight text-white md:text-3xl">
                Two products, one reporting surface.
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300 md:text-[15px]">
                The catalog clearly separates origin documentation from migration delivery. First you understand the legacy. Then you download evidence, artifacts and target handover.
              </p>
              <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-300">
                <span className="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 font-semibold">
                  Stage {currentStage}
                </span>
                {summary && (
                  <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-semibold">
                    {summary.total_reports} reportes registrados
                  </span>
                )}
                <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 font-semibold">
                  Acceso por producto, formato y audiencia
                </span>
              </div>
            </div>

            <div className="flex shrink-0 items-start gap-3">
              <button
                onClick={onOpenCatalog}
                className="group inline-flex items-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-black text-slate-900 transition-all hover:translate-y-[-1px] hover:bg-cyan-50"
              >
                Open Catalog
                <ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
              </button>
            </div>
          </div>

          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            <div className="rounded-2xl border border-cyan-400/20 bg-gradient-to-br from-cyan-500/14 via-cyan-500/6 to-transparent p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.22em] text-cyan-200">{PRODUCT_LINE_COPY.source_intelligence.eyebrow}</p>
                  <h3 className="mt-2 text-lg font-black text-white">{PRODUCT_LINE_COPY.source_intelligence.label}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    {summary?.product_line_descriptions?.source_intelligence || 'Analysis and documentation of the source system.'}
                  </p>
                </div>
                <div className="rounded-2xl bg-cyan-500/15 p-3 text-cyan-300">
                  <Database size={20} />
                </div>
              </div>
              <div className="mt-4 flex items-end justify-between">
                <div className="space-y-1 text-xs text-slate-300">
                  {PRODUCT_LINE_COPY.source_intelligence.bullets.map((bullet) => (
                    <div key={bullet}>{bullet}</div>
                  ))}
                </div>
                <div className="text-right">
                  <div className="text-3xl font-black text-cyan-200">
                    {loading ? <Loader2 size={28} className="animate-spin" /> : availableCounts.source_intelligence}
                  </div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Available now</div>
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-amber-400/20 bg-gradient-to-br from-amber-500/14 via-orange-500/6 to-transparent p-5">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-[10px] font-black uppercase tracking-[0.22em] text-amber-200">{PRODUCT_LINE_COPY.migration_factory.eyebrow}</p>
                  <h3 className="mt-2 text-lg font-black text-white">{PRODUCT_LINE_COPY.migration_factory.label}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    {summary?.product_line_descriptions?.migration_factory || 'Generation, certification and handover of target artifacts.'}
                  </p>
                </div>
                <div className="rounded-2xl bg-amber-500/15 p-3 text-amber-300">
                  <FileText size={20} />
                </div>
              </div>
              <div className="mt-4 flex items-end justify-between">
                <div className="space-y-1 text-xs text-slate-300">
                  {PRODUCT_LINE_COPY.migration_factory.bullets.map((bullet) => (
                    <div key={bullet}>{bullet}</div>
                  ))}
                </div>
                <div className="text-right">
                  <div className="text-3xl font-black text-amber-200">
                    {loading ? <Loader2 size={28} className="animate-spin" /> : availableCounts.migration_factory}
                  </div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">Available now</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
