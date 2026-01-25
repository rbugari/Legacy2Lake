"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import ThemeToggle from "./ThemeToggle";
import { useAuth } from "../context/AuthContext";
import { User, Shield, Briefcase, Settings, Sparkles, LogOut } from "lucide-react";

function IdentityBadge() {
  const { user, logout } = useAuth();

  if (!user) return null;

  const isAdmin = user.role === "ADMIN";
  const badgeColor = isAdmin
    ? "bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800"
    : "bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800";

  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${badgeColor} text-xs font-medium transition-colors`}>
      {isAdmin ? <Shield className="w-3.5 h-3.5" /> : <Briefcase className="w-3.5 h-3.5" />}
      <span className="hidden sm:inline opacity-75">|</span>
      <span>{user.username}</span>
      {isAdmin && <span className="opacity-50 text-[10px] uppercase ml-1 tracking-wider">ADMIN</span>}
    </div>
  );
}

export default function Navbar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  // Hide Navbar on the landing page ("/")
  if (pathname === "/") {
    return null;
  }

  return (
    <nav className="border-b border-[var(--border)] p-4 bg-[var(--surface)]/80 backdrop-blur-md sticky top-0 z-50 transition-colors duration-300">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center gap-2">
          {/* Logo updated to use image */}
          <Link href="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            {/* <img src="/logo.png" alt="Shift-T Logo" className="h-8 w-auto object-contain" /> */}
            <span className="text-xl font-bold tracking-tighter text-cyan-500 hover:text-cyan-400 transition-colors hidden sm:block">Legacy2Lake</span>
          </Link>
        </div>
        <div className="flex items-center gap-3">
          {/* News Sparkles */}
          <button
            onClick={() => window.dispatchEvent(new CustomEvent('toggle-news', { detail: { open: true } }))}
            className="p-2 text-cyan-500 hover:bg-cyan-500/10 rounded-full transition-all relative group"
            title="What's New"
          >
            <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-cyan-500 rounded-full animate-ping" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-cyan-500 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.8)]" />
          </button>

          <div className="h-6 w-px bg-white/5 mx-1" />

          {/* Identity Badge */}
          <IdentityBadge />

          {/* Platform Admin Console (Transparency Mode) - Visible to All */}
          <Link href="/admin" className="p-2 text-[var(--text-secondary)] hover:text-cyan-500 hover:bg-cyan-500/10 rounded-full transition-colors" title="Platform Administration">
            <Shield className="w-5 h-5" />
          </Link>

          {/* Tenant Settings */}
          <Link href="/settings" className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--text-primary)]/5 rounded-full transition-colors" title="Settings">
            <Settings className="w-5 h-5" />
          </Link>

          <ThemeToggle />

          <div className="h-6 w-px bg-white/5 mx-1" />

          <button
            onClick={() => {
              if (window.confirm("Are you sure you want to log out?")) {
                logout();
              }
            }}
            className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-500/10 rounded-full transition-all"
            title="Log Out"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </nav>
  );
}
