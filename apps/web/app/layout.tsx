import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google"; // [NEW] Use next/font
import "./globals.css";
import ThemeToggle from "./components/ThemeToggle";
import Navbar from "./components/Navbar";
import { AuthProvider } from "./context/AuthContext";


// [NEW] Configure Fonts
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono", display: "swap" });

export const metadata: Metadata = {
  title: "Shift-T | Modernization Mesh",
  description: "AI-Assisted Data Engineering Modernization",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    // [NEW] Default to dark mode as requested by "Antigravity Deep Space" spec
    <html lang="en" data-theme="dark" suppressHydrationWarning className={`${inter.variable} ${jetbrains.variable}`}>
      <body suppressHydrationWarning={true} className="min-h-screen flex flex-col font-sans bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-50 transition-colors duration-300">
        <main className="flex-1 w-full">
          <AuthProvider>
            <Navbar />
            {children}
          </AuthProvider>
        </main>


      </body>
    </html>
  );
}
