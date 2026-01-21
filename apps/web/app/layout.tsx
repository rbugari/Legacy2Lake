import type { Metadata } from "next";
import "./globals.css";
import ThemeToggle from "./components/ThemeToggle";
import Navbar from "./components/Navbar";

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
    <html lang="en" data-theme="light" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 w-full">
          {children}
        </main>
      </body>
    </html>
  );
}
