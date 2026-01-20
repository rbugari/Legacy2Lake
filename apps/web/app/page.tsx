import Link from "next/link";
import Image from "next/image";

export default function LandingPage() {
  return (
    <div className="min-h-screen w-full flex flex-col items-center justify-center py-12 px-4 bg-gray-50 dark:bg-gray-950 transition-colors duration-300">

      <main className="flex flex-col items-center max-w-6xl w-full text-center space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">

        {/* Header Text */}
        <div className="space-y-6 max-w-3xl">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-gray-900 dark:text-white">
            Legacy2Lake
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 font-medium leading-relaxed">
            From Monolithic Platforms to <span className="text-primary">Medallion Architecture</span>
            <br className="hidden md:block" />
            <span className="text-base md:text-lg opacity-80 mt-2 block">
              Modernizing Legacy Data into Lakehouse Architectures.
            </span>
          </p>
        </div>

        {/* Central Illustration */}
        <div className="relative w-full max-w-4xl aspect-video rounded-2xl overflow-hidden shadow-2xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
          <Image
            src="/fondo.png"
            alt="Shift-T Platform Preview"
            fill
            className="object-cover object-top hover:scale-105 transition-transform duration-700 ease-out"
            priority
          />
          {/* Optional: subtle gradient overlay for depth */}
          <div className="absolute inset-0 bg-gradient-to-t from-gray-900/10 to-transparent pointer-events-none" />
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-5 pt-4 w-full justify-center">
          <Link
            href="/dashboard"
            className="px-8 py-4 bg-primary text-white rounded-full font-bold text-lg hover:bg-secondary hover:-translate-y-1 transition-all shadow-lg hover:shadow-primary/30 flex items-center justify-center gap-2"
          >
            Entrar a la aplicación
          </Link>
          <Link
            href="/docs"
            className="px-8 py-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-white rounded-full font-bold text-lg hover:bg-gray-50 dark:hover:bg-gray-700 hover:-translate-y-1 transition-all shadow-sm flex items-center justify-center gap-2"
          >
            Entrar a la documentación
          </Link>
        </div>

      </main>

      <footer className="mt-16 text-gray-400 text-sm">
        &copy; {new Date().getFullYear()} Legacy2Lake Platform.
      </footer>
    </div>
  );
}
