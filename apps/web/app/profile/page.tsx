"use client";

import { useAuth } from "../context/AuthContext";
import { User, Shield, Briefcase, Clock, ShieldCheck, Tag, Key, Save, Loader2, X } from "lucide-react";
import { useState } from "react";
import { fetchWithAuth } from "../lib/auth-client";

export default function ProfilePage() {
    const { user } = useAuth();

    const [isChangingPassword, setIsChangingPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [passData, setPassData] = useState({
        current_password: "",
        new_password: "",
        confirm_password: ""
    });

    if (!user) return null;

    const handlePasswordUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (passData.new_password !== passData.confirm_password) {
            setError("New passwords do not match");
            return;
        }

        if (passData.new_password.length < 8) {
            setError("Password must be at least 8 characters");
            return;
        }

        setLoading(true);
        try {
            const res = await fetchWithAuth("auth/change-password", {
                method: "POST",
                body: JSON.stringify({
                    current_password: passData.current_password,
                    new_password: passData.new_password
                })
            });
            const data = await res.json();

            if (res.ok) {
                alert("Password updated successfully!");
                setIsChangingPassword(false);
                setPassData({ current_password: "", new_password: "", confirm_password: "" });
            } else {
                setError(data.detail || "Failed to update password");
            }
        } catch (err) {
            setError("Network error");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[var(--background)] text-[var(--text-primary)]">
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
                                {!isChangingPassword ? (
                                    <button
                                        className="w-full py-3 bg-[var(--text-primary)] text-[var(--background)] rounded-2xl text-[10px] font-black uppercase tracking-widest hover:opacity-90 transition-all active:scale-95 flex items-center justify-center gap-2"
                                        onClick={() => setIsChangingPassword(true)}
                                    >
                                        <Key size={14} /> Update Password
                                    </button>
                                ) : (
                                    <form onSubmit={handlePasswordUpdate} className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
                                        <div className="flex justify-between items-center mb-2">
                                            <p className="text-[10px] font-black uppercase tracking-widest text-cyan-500">Change Password</p>
                                            <button type="button" onClick={() => setIsChangingPassword(false)} className="text-[var(--text-tertiary)] hover:text-white">
                                                <X size={14} />
                                            </button>
                                        </div>

                                        <input
                                            type="password"
                                            required
                                            placeholder="Current Password"
                                            className="w-full px-4 py-2 text-sm bg-[var(--background)] border border-[var(--border)] rounded-xl outline-none focus:ring-1 focus:ring-cyan-500/50"
                                            value={passData.current_password}
                                            onChange={e => setPassData({ ...passData, current_password: e.target.value })}
                                        />
                                        <input
                                            type="password"
                                            required
                                            placeholder="New Password"
                                            className="w-full px-4 py-2 text-sm bg-[var(--background)] border border-[var(--border)] rounded-xl outline-none focus:ring-1 focus:ring-cyan-500/50"
                                            value={passData.new_password}
                                            onChange={e => setPassData({ ...passData, new_password: e.target.value })}
                                        />
                                        <input
                                            type="password"
                                            required
                                            placeholder="Confirm New Password"
                                            className="w-full px-4 py-2 text-sm bg-[var(--background)] border border-[var(--border)] rounded-xl outline-none focus:ring-1 focus:ring-cyan-500/50"
                                            value={passData.confirm_password}
                                            onChange={e => setPassData({ ...passData, confirm_password: e.target.value })}
                                        />

                                        {error && <p className="text-[10px] text-red-500 font-bold uppercase tracking-tight">{error}</p>}

                                        <button
                                            type="submit"
                                            disabled={loading}
                                            className="w-full py-3 bg-cyan-600 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-cyan-500 transition-all active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
                                        >
                                            {loading ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                                            {loading ? "Saving..." : "Save Password"}
                                        </button>
                                    </form>
                                )}
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
