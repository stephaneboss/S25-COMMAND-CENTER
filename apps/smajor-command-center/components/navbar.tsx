"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/", label: "Dashboard" },
  { href: "/clients", label: "Clients" },
  { href: "/jobs", label: "Jobs" },
  { href: "/devis", label: "Devis" },
];

export function Navbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [cockpitAlive, setCockpitAlive] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function checkCockpit() {
      try {
        const res = await fetch("/api/s25/status", { cache: "no-store" });
        if (!cancelled) setCockpitAlive(res.ok);
      } catch {
        if (!cancelled) setCockpitAlive(false);
      }
    }
    void checkCockpit();
    const interval = setInterval(() => void checkCockpit(), 60_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-[#0f172a] shadow-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link
          href="/"
          className="flex items-center gap-2 text-white hover:text-emerald-400"
          onClick={() => setMobileOpen(false)}
        >
          <span className="text-xl">⛏</span>
          <span className="text-lg font-bold tracking-tight">smajor.org</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map((link) => {
            const isActive =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-white/10 text-white"
                    : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        {/* Right side: S25 indicator + mobile toggle */}
        <div className="flex items-center gap-3">
          {/* S25 status dot */}
          <div className="hidden sm:flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                cockpitAlive === null
                  ? "bg-gray-400 animate-pulse"
                  : cockpitAlive
                  ? "bg-emerald-400"
                  : "bg-red-400"
              }`}
            />
            <span className="text-xs font-medium text-gray-300">S25</span>
          </div>

          {/* Mobile hamburger */}
          <button
            type="button"
            className="md:hidden rounded-md p-2 text-gray-300 hover:bg-white/10 hover:text-white"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Menu"
          >
            {mobileOpen ? (
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-white/10 bg-[#0f172a] px-4 py-3 space-y-1">
          {NAV_LINKS.map((link) => {
            const isActive =
              link.href === "/"
                ? pathname === "/"
                : pathname.startsWith(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-white/10 text-white"
                    : "text-gray-300 hover:bg-white/5 hover:text-white"
                }`}
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </Link>
            );
          })}
          <div className="flex items-center gap-2 px-3 py-2">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                cockpitAlive === null
                  ? "bg-gray-400 animate-pulse"
                  : cockpitAlive
                  ? "bg-emerald-400"
                  : "bg-red-400"
              }`}
            />
            <span className="text-xs text-gray-400">
              S25 — {cockpitAlive === null ? "..." : cockpitAlive ? "En ligne" : "Hors ligne"}
            </span>
          </div>
        </div>
      )}
    </header>
  );
}
