"use client";

import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import { User, Shield, Briefcase, Clock, ShieldCheck, Tag } from "lucide-react";

export default function ProfilePage() {
    const { user } = useAuth();

    if (!user) return null;

    return (
        <div className="min-h-screen bg-[var(--background)] text-[var(--text-primary)]">
            <Navbar />

            <main className="max-w-4xl mx-auto px-6 py-12">
                <header className="mb-12">
                    <h1 className="text-3xl font-black uppercase tracking-tight mb-2">User Profile</h1>
                    <p className="text-[var(--text-secondary)] font-medium">Manage your security settings and platform preferences.</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Account Details */}
                    <section className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl p-8 shadow-sm">
                        <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-500 mb-6 flex items-center gap-2">
                            <User size={14} /> Identity Information
                        </h2>

                        <div className="space-y-6">
                            <ProfileItem label="Username" value={user.username} icon={<User size={16} />} />
                            <ProfileItem label="Tenant ID" value={user.tenant_id} icon={<Tag size={16} />} />
                            <ProfileItem label="Client Affinity" value={user.client_id} icon={<Briefcase size={16} />} />
                            <ProfileItem
                                label="System Role"
                                value={user.role}
                                icon={<Shield size={16} />}
                                special={user.role === 'ADMIN'}
                            />
                        </div>
                    </section>

                    {/* Session & Security */}
                    <section className="bg-[var(--surface)] border border-[var(--border)] rounded-3xl p-8 shadow-sm">
                        <h2 className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-500 mb-6 flex items-center gap-2">
                            <ShieldCheck size={14} /> Security & Active Session
                        </h2>

                        <div className="space-y-6">
                            <div className="p-4 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl">
                                <p className="text-[10px] font-black uppercase tracking-widest text-emerald-500 mb-1">Session Status</p>
                                <p className="text-sm font-bold flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                    Authenticated Session - Active
                                </p>
                            </div>

                            <div className="p-4 bg-[var(--background)] border border-[var(--border)] rounded-2xl">
                                <p className="text-[10px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-1">Last Login</p>
                                <p className="text-sm font-bold flex items-center gap-2 text-[var(--text-secondary)]">
                                    <Clock size={14} /> {new Date().toLocaleDateString()} (Virtual)
                                </p>
                            </div>

                            <div className="pt-4 border-t border-[var(--border)]">
                                <button
                                    className="w-full py-3 bg-[var(--text-primary)] text-[var(--background)] rounded-2xl text-[10px] font-black uppercase tracking-widest hover:opacity-90 transition-all active:scale-95"
                                    onClick={() => alert("Password reset requires administrator assistance in v3.2")}
                                >
                                    Request Security Update
                                </button>
                            </div>
                        </div>
                    </section>
                </div>
            </main>
        </div>
    );
}

function ProfileItem({ label, value, icon, special }: any) {
    return (
        <div className="flex items-center gap-4 group">
            <div className="p-3 bg-[var(--background)] border border-[var(--border)] rounded-2xl text-[var(--text-tertiary)] group-hover:text-cyan-500 transition-colors">
                {icon}
            </div>
            <div>
                <p className="text-[9px] font-black uppercase tracking-widest text-[var(--text-tertiary)] mb-0.5">{label}</p>
                <p className={`text-sm font-bold uppercase tracking-wide ${special ? 'text-amber-500' : 'text-[var(--text-primary)]'}`}>
                    {value || 'Not Defined'}
                </p>
            </div>
        </div>
    );
}
