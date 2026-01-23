"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import ThemeToggle from "./ThemeToggle";
import { useAuth } from "../context/AuthContext";
import { User, Shield, Briefcase, Settings } from "lucide-react";

function IdentityBadge() {
  const { user } = useAuth();

  if (!user) return null;

  const isAdmin = user.role === "ADMIN";
  const badgeColor = isAdmin
    ? "bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800"
    : "bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800";

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
            <span className="text-xl font-bold tracking-tighter text-[var(--color-primary)] hidden sm:block">Legacy2Lake</span>
          </Link>
        </div>
        <div className="flex items-center gap-3">
          {/* Identity Badge */}
          <IdentityBadge />

          {/* System Console (Transparency Mode) - Visible to All */}
          <Link href="/system" className="p-2 text-[var(--text-secondary)] hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-full transition-colors" title="System Architecture">
            <Shield className="w-5 h-5" />
          </Link>

          {/* Tenant Settings */}
          <Link href="/settings" className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--text-primary)]/5 rounded-full transition-colors" title="Settings">
            <Settings className="w-5 h-5" />
          </Link>

          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
