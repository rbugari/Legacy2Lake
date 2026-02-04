"use client";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, Zap, Shield, Cpu, Database, Cloud, Code, CheckCircle, Sparkles } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen w-full bg-black text-white overflow-hidden">


      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center pt-20">
        {/* Background Image */}
        <div className="absolute inset-0 z-0">
          <Image
            src="/brand/1 Front.png"
            alt="Legacy to Modern Transformation"
            fill
            className="object-cover opacity-60"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/60 to-black"></div>
        </div>

        {/* Hero Content */}
        <div className="relative z-10 max-w-6xl mx-auto px-6 text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-full text-cyan-400 text-sm font-bold mb-4">
            <Sparkles size={16} />
            <span>AI-Powered Migration Engine</span>
          </div>

          <h1 className="text-6xl md:text-8xl font-black tracking-tight leading-tight">
            Transform Legacy Data
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600">
              Into Modern Assets
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Migrate from monolithic platforms (SSIS, Oracle, SQL Server) to cloud-native lakehouses
            (Snowflake, Databricks, BigQuery) with intelligent automation.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
            <Link
              href="/dashboard"
              className="group px-8 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-xl font-bold text-lg transition-all shadow-2xl shadow-cyan-600/40 flex items-center justify-center gap-2"
            >
              Start Your Migration
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              href="/help-en.html"
              className="px-8 py-4 bg-white/5 backdrop-blur border border-white/10 hover:bg-white/10 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2"
            >
              View Documentation
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 pt-12 max-w-3xl mx-auto">
            <div className="text-center">
              <div className="text-4xl font-black text-cyan-400">9</div>
              <div className="text-sm text-gray-400 font-medium mt-1">Source Platforms</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-black text-blue-400">6</div>
              <div className="text-sm text-gray-400 font-medium mt-1">Cloud Targets</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-black text-purple-400">7</div>
              <div className="text-sm text-gray-400 font-medium mt-1">AI Agents</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-32 px-6 bg-gradient-to-b from-black to-gray-950">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-5xl font-black mb-6">
              Why Teams Choose Legacy2Lake
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Built for enterprise-scale migrations with AI-driven intelligence and technology expertise.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="group relative bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-2xl p-8 hover:border-cyan-500/40 transition-all">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative">
                <div className="w-14 h-14 bg-cyan-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Cpu size={28} className="text-cyan-400" />
                </div>
                <h3 className="text-2xl font-bold mb-4">AI-Powered Agents</h3>
                <p className="text-gray-400 leading-relaxed">
                  7 specialized agents handle discovery, classification, code generation, and quality assurance—no manual translation needed.
                </p>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="group relative bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-2xl p-8 hover:border-purple-500/40 transition-all">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-pink-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative">
                <div className="w-14 h-14 bg-purple-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Zap size={28} className="text-purple-400" />
                </div>
                <h3 className="text-2xl font-bold mb-4">Technology Expertise</h3>
                <p className="text-gray-400 leading-relaxed">
                  Built-in knowledge of 9 source platforms and 6 cloud targets. Best practices injected automatically—no research required.
                </p>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="group relative bg-gradient-to-br from-emerald-500/10 to-teal-500/10 border border-emerald-500/20 rounded-2xl p-8 hover:border-emerald-500/40 transition-all">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-teal-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="relative">
                <div className="w-14 h-14 bg-emerald-500/20 rounded-xl flex items-center justify-center mb-6">
                  <Shield size={28} className="text-emerald-400" />
                </div>
                <h3 className="text-2xl font-bold mb-4">Compliance Ready</h3>
                <p className="text-gray-400 leading-relaxed">
                  Automatic PII detection, COP scoring, and audit trails for enterprise governance and regulatory compliance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="relative py-32 px-6 bg-black">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-5xl font-black mb-6">
              6-Stage Migration Pipeline
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              From legacy chaos to production-ready cloud assets in a structured, auditable process.
            </p>
          </div>

          <div className="space-y-6">
            {[
              { stage: "1. Discovery", icon: Database, desc: "Upload your legacy repository. Agent S scans and catalogs all assets." },
              { stage: "2. Triage", icon: Code, desc: "Classify objects as CORE, SUPPORT, or IGNORED. Define load strategies and PII flags." },
              { stage: "3. Drafting", icon: Cpu, desc: "Agent C generates cloud-native code with technology-specific best practices." },
              { stage: "4. Refinement", icon: Zap, desc: "Agent F applies cartridges for self-correction and optimization." },
              { stage: "5. Certification", icon: Shield, desc: "Compliance scoring (COP) and validation against quality gates." },
              { stage: "6. Handover", icon: Cloud, desc: "Download production-ready artifacts with deployment guides." },
            ].map((item, idx) => (
              <div key={idx} className="flex items-start gap-6 bg-white/5 border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-all">
                <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <item.icon size={24} className="text-white" />
                </div>
                <div>
                  <h3 className="text-xl font-bold mb-2">{item.stage}</h3>
                  <p className="text-gray-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-32 px-6 bg-gradient-to-b from-gray-950 to-black">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h2 className="text-5xl md:text-6xl font-black">
            Ready to Modernize?
          </h2>
          <p className="text-xl text-gray-400">
            Join teams migrating thousands of legacy assets to modern cloud platforms with confidence.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
            <Link
              href="/dashboard"
              className="px-10 py-5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 rounded-xl font-bold text-xl transition-all shadow-2xl shadow-cyan-600/40 flex items-center justify-center gap-2"
            >
              Create Your First Project
              <ArrowRight size={24} />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-12 px-6 bg-black">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <Image
              src="/brand/logo.png"
              alt="Legacy2Lake"
              width={150}
              height={30}
              className="h-6 w-auto opacity-60"
            />
          </div>
          <div className="flex gap-8 text-sm text-gray-400">
            <Link href="/help" className="hover:text-white transition-colors">Documentation</Link>
            <Link href="/help/philosophy" className="hover:text-white transition-colors">About</Link>
            <Link href="/dashboard" className="hover:text-white transition-colors">Console</Link>
          </div>
          <div className="text-sm text-gray-500">
            © {new Date().getFullYear()} Legacy2Lake Platform. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
