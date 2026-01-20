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
    <nav className="border-b border-gray-200 dark:border-gray-800 p-4 bg-white/80 dark:bg-black/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="flex items-center gap-2">
          {/* Logo updated to use image */}
          <Link href="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            {/* <img src="/logo.png" alt="Shift-T Logo" className="h-8 w-auto object-contain" /> */}
            <span className="text-xl font-bold tracking-tighter text-primary dark:text-secondary hidden sm:block">Legacy2Lake</span>
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/docs" className="text-sm font-medium hover:text-primary transition-colors">
            Documentación
          </Link>
          <ThemeToggle />
        </div>
      </div>
    </nav>
  );
}
