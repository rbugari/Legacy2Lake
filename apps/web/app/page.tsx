"use client";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, ArrowRightLeft, Database, Cloud, Cpu, Shield, Zap, CheckCircle, MoveRight, Layers, GitMerge, BarChart3 } from "lucide-react";

export default function LandingPage() {
  const sources = ["SSIS", "DataStage", "Informatica", "Oracle ODI", "Talend", "SAP BODS", "Pentaho", "SQL Server", "Azure ADF"];
  const targets = ["Snowflake", "Databricks", "BigQuery", "MS Fabric", "AWS Glue", "Azure Synapse"];

  const stages = [
    { num: "01", label: "Discovery", icon: Database, desc: "Upload your repository. The platform scans, classifies and catalogs every asset â€” packages, jobs, mappings, schemas â€” in one pass." },
    { num: "02", label: "Triage", icon: Cpu, desc: "AI classifies objects as CORE, SUPPORT or IGNORED. Dependency graphs, PII detection and impact analysis included." },
    { num: "03", label: "Drafting", icon: Zap, desc: "Generators produce cloud-native code following the architectural patterns of your chosen target platform â€” not just translated syntax." },
    { num: "04", label: "Refinement", icon: ArrowRightLeft, desc: "An autonomous Auditor loop self-corrects, optimizes and validates output against predefined compliance rules and quality thresholds." },
    { num: "05", label: "Certification", icon: Shield, desc: "Every object receives a quality score. Automated governance trails capture every decision for sign-off and audit readiness." },
    { num: "06", label: "Handover", icon: Cloud, desc: "Production-ready code bundles with runbooks, deployment guides and full lineage documentation â€” ready to deploy." },
  ];

  const proofPoints = [
    "From months to days â€” modernization at migration-factory speed",
    "Zero access to your production data â€” only code and schema are analyzed",
    "Complete governance trail for every decision and every transformation",
    "Multi-platform coverage: legacy origins and cloud targets across the major ecosystems",
  ];

  return (
    <div className="min-h-screen w-full bg-black text-white overflow-hidden">

      {/* â”€â”€ HERO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="relative min-h-screen flex items-center justify-center">
        {/* Background */}
        <div className="absolute inset-0 z-0">
          <Image
            src="/brand/1 Front.png"
            alt="Legacy2Lake"
            fill
            className="object-cover opacity-55"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-black" />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto px-6 text-center space-y-10 pt-20">

          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-cyan-500/30 bg-cyan-500/8 text-cyan-300 text-xs font-bold tracking-widest uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            Legacy Modernization Â· AI-Powered Â· Multi-Cloud
          </div>

          {/* Headline */}
          <h1 className="text-6xl md:text-8xl font-black tracking-tight leading-[1.05]">
            Your Legacy ETL,<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-300 via-blue-400 to-purple-500">
              Modernized for the Cloud.
            </span>
          </h1>

          {/* Sub */}
          <p className="text-lg md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed font-light">
            Stop spending quarters on manual rewrites. A team of specialized AI agents analyzes, classifies,
            and regenerates your pipelines{" — "}from{" "}
            <strong className="text-white font-semibold">SSIS, Informatica or DataStage</strong> to{" "}
            <strong className="text-white font-semibold">Snowflake, Databricks or BigQuery</strong>{" — "}with the depth of a senior architect and the speed of automation.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/dashboard"
              className="group px-8 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 rounded-xl font-bold text-lg transition-all shadow-2xl shadow-cyan-600/35 flex items-center justify-center gap-2"
            >
              Launch Console
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="#how-it-works"
              className="px-8 py-4 border border-white/15 hover:border-white/35 bg-white/5 hover:bg-white/10 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2"
            >
              See How It Works
            </a>
          </div>

          {/* Migration Flow Pill */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <div className="flex flex-col items-center gap-2">
              <span className="text-xs text-gray-500 font-bold uppercase tracking-widest">Legacy Origins</span>
              <div className="flex flex-wrap justify-center gap-2 max-w-xs">
                {sources.map(s => (
                  <span key={s} className="px-2.5 py-1 text-xs font-semibold bg-white/5 border border-white/10 rounded-md text-gray-300">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-cyan-500/20 border border-cyan-500/40 shrink-0">
              <MoveRight size={20} className="text-cyan-400" />
            </div>

            <div className="flex flex-col items-center gap-2">
              <span className="text-xs text-gray-500 font-bold uppercase tracking-widest">Cloud Targets</span>
              <div className="flex flex-wrap justify-center gap-2 max-w-xs">
                {targets.map(t => (
                  <span key={t} className="px-2.5 py-1 text-xs font-semibold bg-cyan-500/10 border border-cyan-500/20 rounded-md text-cyan-300">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* â”€â”€ PROOF POINTS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="py-16 px-6 border-y border-white/5 bg-white/2">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-2 gap-4">
          {proofPoints.map((p, i) => (
            <div key={i} className="flex items-start gap-3">
              <CheckCircle size={18} className="text-cyan-400 mt-0.5 shrink-0" />
              <span className="text-gray-300 text-sm leading-relaxed">{p}</span>
            </div>
          ))}
        </div>
      </section>

      {/* â”€â”€ HOW IT WORKS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section id="how-it-works" className="py-32 px-6 bg-gradient-to-b from-black to-gray-950">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-20">
            <p className="text-xs font-bold tracking-widest text-cyan-400 uppercase mb-4">The Process</p>
            <h2 className="text-5xl md:text-6xl font-black mb-6">
              From Legacy to Cloud in Six Stages
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
              Every modernization runs through the same battle-tested, AI-supervised pipeline â€” structured, auditable, reproducible.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {stages.map((s) => (
              <div
                key={s.num}
                className="group relative bg-white/[0.03] border border-white/8 rounded-2xl p-7 hover:bg-white/[0.06] hover:border-cyan-500/25 transition-all duration-300 hover:-translate-y-1"
              >
                <div className="flex items-start gap-4 mb-5">
                  <span className="text-5xl font-black text-white/8 leading-none select-none">{s.num}</span>
                  <div className="w-10 h-10 bg-cyan-500/15 rounded-lg flex items-center justify-center border border-cyan-500/20 group-hover:bg-cyan-500/25 transition-colors">
                    <s.icon size={20} className="text-cyan-400" />
                  </div>
                </div>
                <h3 className="text-xl font-bold mb-3 group-hover:text-cyan-300 transition-colors">{s.label}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* â”€â”€ WHY L2L â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="py-32 px-6 bg-black">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-20">
            <p className="text-xs font-bold tracking-widest text-purple-400 uppercase mb-4">Why Legacy2Lake</p>
            <h2 className="text-5xl font-black mb-6">Built for Modernization</h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Not a code translator. An intelligent modernization factory that understands your architecture the way a senior engineer would â€” and moves with the speed of automation.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-7">
            {[
              {
                color: "cyan",
                icon: Cpu,
                title: "Crew of Specialized Agents",
                body: "Multiple AI agents, each owning a distinct role â€” scanning, classifying, generating, auditing, certifying. No single model doing everything poorly; a coordinated crew doing each step exceptionally."
              },
              {
                color: "purple",
                icon: Layers,
                title: "Platform-Native Code Generation",
                body: "Technology cartridges inject platform-specific patterns at generation time. Output follows the idioms of the target â€” Snowflake SQL, PySpark on Databricks, Fabric Notebooks â€” not generic code in disguise."
              },
              {
                color: "emerald",
                icon: Shield,
                title: "Governance by Design",
                body: "Every decision, every mapping, every transformation is recorded and scored. Audit-ready governance trails ensure that nothing reaches production without full traceability and sign-off."
              }
            ].map((card) => (
              <div
                key={card.title}
                className={`group relative rounded-2xl p-8 border transition-all duration-300 hover:-translate-y-2
                  ${card.color === "cyan" ? "bg-cyan-500/5 border-cyan-500/15 hover:border-cyan-500/35 hover:shadow-2xl hover:shadow-cyan-500/15" : ""}
                  ${card.color === "purple" ? "bg-purple-500/5 border-purple-500/15 hover:border-purple-500/35 hover:shadow-2xl hover:shadow-purple-500/15" : ""}
                  ${card.color === "emerald" ? "bg-emerald-500/5 border-emerald-500/15 hover:border-emerald-500/35 hover:shadow-2xl hover:shadow-emerald-500/15" : ""}
                `}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-6
                  ${card.color === "cyan" ? "bg-cyan-500/20" : ""}
                  ${card.color === "purple" ? "bg-purple-500/20" : ""}
                  ${card.color === "emerald" ? "bg-emerald-500/20" : ""}
                `}>
                  <card.icon size={24} className={`
                    ${card.color === "cyan" ? "text-cyan-400" : ""}
                    ${card.color === "purple" ? "text-purple-400" : ""}
                    ${card.color === "emerald" ? "text-emerald-400" : ""}
                  `} />
                </div>
                <h3 className="text-xl font-bold mb-4">{card.title}</h3>
                <p className="text-gray-400 text-sm leading-relaxed">{card.body}</p>
              </div>
            ))}
          </div>

          {/* Secondary pillars */}
          <div className="grid md:grid-cols-2 gap-5 mt-7">
            {[
              {
                icon: GitMerge,
                title: "Deep Dependency Intelligence",
                body: "The platform resolves cross-object dependencies, lineage chains and impact trees before generating a single line â€” so the output is architecturally coherent, not just syntactically correct."
              },
              {
                icon: BarChart3,
                title: "Quality Scoring at Every Step",
                body: "Completeness, compliance, complexity and risk are scored per object and in aggregate. You enter production knowing exactly what passed, what was flagged, and why."
              }
            ].map((card) => (
              <div
                key={card.title}
                className="group relative rounded-2xl p-7 border bg-white/[0.02] border-white/8 hover:border-white/20 hover:bg-white/[0.05] transition-all duration-300 flex gap-5"
              >
                <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0 bg-white/5 border border-white/10 group-hover:border-white/20 transition-colors">
                  <card.icon size={20} className="text-gray-300" />
                </div>
                <div>
                  <h3 className="text-lg font-bold mb-2 group-hover:text-white transition-colors">{card.title}</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">{card.body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* â”€â”€ CTA â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <section className="relative py-32 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-cyan-900/20 via-black to-purple-900/20 pointer-events-none" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none" />

        <div className="relative max-w-4xl mx-auto text-center space-y-8">
          <h2 className="text-5xl md:text-7xl font-black leading-tight">
            Your modernization starts<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500">
              today, not next quarter.
            </span>
          </h2>
          <p className="text-xl text-gray-400 max-w-xl mx-auto">
            Create your first project, upload your legacy repository, and let the platform do what your team has been postponing for years.
          </p>
          <Link
            href="/dashboard"
            className="group inline-flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 rounded-xl font-bold text-xl transition-all shadow-2xl shadow-cyan-500/30"
          >
            Start Your First Migration
            <ArrowRight size={24} className="group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </section>

      {/* â”€â”€ FOOTER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€ */}
      <footer className="border-t border-white/8 py-10 px-6 bg-black">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <Image
            src="/brand/logo.png"
            alt="Legacy2Lake"
            width={140}
            height={28}
            className="h-6 w-auto opacity-50 hover:opacity-90 transition-opacity"
          />
          <div className="flex gap-8 text-sm text-gray-500">
            <Link href="/help" className="hover:text-cyan-400 transition-colors">Documentation</Link>
            <Link href="/dashboard" className="hover:text-cyan-400 transition-colors">Console</Link>
          </div>
          <div className="text-sm text-gray-600">
            © {new Date().getFullYear()} Legacy2Lake Platform. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}

