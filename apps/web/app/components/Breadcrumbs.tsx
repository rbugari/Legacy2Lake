"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { ChevronRight, Home } from "lucide-react";

const ROUTE_LABELS: Record<string, string> = {
    "dashboard": "Consola",
    "workspace": "Espacio de Trabajo",
    "admin": "Administración de Plataforma",
    "system": "Arquitectura de Sistema",
    "settings": "Configuración Tenant",
    "login": "Ingreso"
};

export default function Breadcrumbs() {
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const projectId = searchParams.get("id");

    if (pathname === "/" || pathname === "/login") return null;

    const pathSegments = pathname.split("/").filter(Boolean);

    return (
        <nav className="flex items-center gap-2 px-8 py-3 bg-[var(--background)]/50 border-b border-[var(--border)] text-[10px] uppercase font-black tracking-widest text-[var(--text-tertiary)]">
            <Link
                href="/dashboard"
                className="hover:text-cyan-500 transition-colors flex items-center gap-1"
                title="Ir al Inicio"
            >
                <Home size={12} />
            </Link>

            {pathSegments.map((segment, index) => {
                const href = `/${pathSegments.slice(0, index + 1).join("/")}`;
                const isLast = index === pathSegments.length - 1;
                const label = ROUTE_LABELS[segment] || segment;

                return (
                    <div key={href} className="flex items-center gap-2">
                        <ChevronRight size={10} className="text-gray-400" />
                        {isLast && !projectId ? (
                            <span className="text-cyan-500">{label}</span>
                        ) : (
                            <Link href={href} className="hover:text-cyan-500 transition-colors">
                                {label}
                            </Link>
                        )}
                    </div>
                );
            })}

            {projectId && (
                <div className="flex items-center gap-2">
                    <ChevronRight size={10} className="text-gray-400" />
                    <span className="text-cyan-500 truncate max-w-[200px]">{projectId}</span>
                </div>
            )}
        </nav>
    );
}
