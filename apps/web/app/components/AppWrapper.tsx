"use client";

import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from "../context/AuthContext";
import Navbar from "./Navbar";
import Breadcrumbs from "./Breadcrumbs";
import CommandPalette from "./CommandPalette";
import NewsCenter from "./NewsCenter";
import { fetchWithAuth } from "../lib/auth-client";

export default function AppWrapper({ children }: { children: React.ReactNode }) {
    const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
    const [isNewsOpen, setIsNewsOpen] = useState(false);
    const [projects, setProjects] = useState<any[]>([]);

    // Keyboard Listener
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                setIsCommandPaletteOpen(prev => !prev);
            }
        };
        const handleToggleNews = (e: any) => {
            if (e.detail?.open !== undefined) setIsNewsOpen(e.detail.open);
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('toggle-news', handleToggleNews);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('toggle-news', handleToggleNews);
        };
    }, []);

    // Prefetch projects for the palette
    useEffect(() => {
        const loadProjects = async () => {
            try {
                const res = await fetchWithAuth('projects');
                if (res.ok) {
                    const data = await res.json();
                    setProjects(data);
                }
            } catch (e) { console.error("Palette prefetch failed", e); }
        };
        loadProjects();
    }, []);

    return (
        <AuthProvider>
            <Navbar />
            <Breadcrumbs />
            <div className="flex-1 flex flex-col">
                {children}
            </div>
            <CommandPalette
                isOpen={isCommandPaletteOpen}
                onClose={() => setIsCommandPaletteOpen(false)}
                projects={projects}
                onToggleLogs={() => {
                    const event = new CustomEvent('toggle-logs', { detail: { open: true } });
                    window.dispatchEvent(event);
                }}
            />
            <NewsCenter
                isOpen={isNewsOpen}
                onClose={() => setIsNewsOpen(false)}
            />
        </AuthProvider>
    );
}
