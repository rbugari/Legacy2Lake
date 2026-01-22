"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import ThemeToggle from "./ThemeToggle";

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
        <div className="flex items-center gap-4">
          <Link href="/docs" className="text-sm font-medium hover:text-[var(--color-primary)] transition-colors text-[var(--text-secondary)] hover:bg-[var(--text-primary)]/5 px-3 py-2 rounded-lg">
            Documentación
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
