"use client";

import { useEffect, useState, useCallback } from "react";
import type { CommandCenterSnapshot } from "@/lib/s25-api";
import type { Job, Client, Quote } from "@/lib/db";
import { StatsCard } from "@/components/stats-card";
import { NewClientModal } from "@/components/new-client-modal";
import { NewJobModal } from "@/components/new-job-modal";

// ─── Types ────────────────────────────────────────────────────────────────────

interface DashboardStats {
  total_clients: number;
  active_jobs: number;
  pending_quotes: number;
  monthly_revenue_usd: number;
}

interface DashboardProps {
  snapshot: CommandCenterSnapshot;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const JOB_STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700 border border-amber-200",
  active: "bg-emerald-100 text-emerald-700 border border-emerald-200",
  completed: "bg-blue-100 text-blue-700 border border-blue-200",
};

const JOB_STATUS_LABEL: Record<string, string> = {
  pending: "En attente",
  active: "Actif",
  completed: "Complété",
};

const JOB_TYPE_LABEL: Record<string, string> = {
  excavation: "Excavation",
  deneigement: "Déneigement",
  consulting: "Consulting IA",
};

const AGENT_STATUS_STYLES: Record<string, string> = {
  online: "bg-emerald-400",
  degraded: "bg-amber-400",
  offline: "bg-red-400",
  unknown: "bg-gray-300",
  sleep: "bg-amber-300",
  rate_limited: "bg-amber-300",
};

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export function Dashboard({ snapshot: initialSnapshot }: DashboardProps) {
  const [snapshot, setSnapshot] = useState<CommandCenterSnapshot>(initialSnapshot);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentJobs, setRecentJobs] = useState<(Job & { client_name?: string })[]>([]);
  const [pendingQuotes, setPendingQuotes] = useState<(Quote & { client_name?: string })[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewClient, setShowNewClient] = useState(false);
  const [showNewJob, setShowNewJob] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [jobsRes, clientsRes, quotesRes, statusRes, allJobsRes] = await Promise.allSettled([
        fetch("/api/jobs?status=active", { cache: "no-store" }),
        fetch("/api/clients", { cache: "no-store" }),
        fetch("/api/quotes?status=draft", { cache: "no-store" }),
        fetch("/api/s25/status", { cache: "no-store" }),
        fetch("/api/jobs", { cache: "no-store" }),
      ]);

      let clients: Client[] = [];
      let activeJobCount = 0;
      let pendingQuoteCount = 0;

      if (clientsRes.status === "fulfilled" && clientsRes.value.ok) {
        const d = (await clientsRes.value.json()) as { clients: Client[] };
        clients = d.clients ?? [];
      }

      if (jobsRes.status === "fulfilled" && jobsRes.value.ok) {
        const d = (await jobsRes.value.json()) as { jobs: Job[] };
        activeJobCount = (d.jobs ?? []).length;
      }

      if (quotesRes.status === "fulfilled" && quotesRes.value.ok) {
        const d = (await quotesRes.value.json()) as { quotes: Quote[] };
        pendingQuoteCount = d.quotes?.length ?? 0;
      }

      // Monthly revenue from completed jobs
      let monthlyRevenue = 0;
      try {
        const completedRes = await fetch("/api/jobs?status=completed", { cache: "no-store" });
        if (completedRes.ok) {
          const d = (await completedRes.json()) as { jobs: Job[] };
          const firstOfMonth = new Date();
          firstOfMonth.setDate(1);
          firstOfMonth.setHours(0, 0, 0, 0);
          monthlyRevenue = (d.jobs ?? [])
            .filter((j) => j.created_at && new Date(j.created_at) >= firstOfMonth)
            .reduce((sum, j) => sum + (j.amount_usd ?? 0), 0);
        }
      } catch {
        // silently fail
      }

      setStats({
        total_clients: clients.length,
        active_jobs: activeJobCount,
        pending_quotes: pendingQuoteCount,
        monthly_revenue_usd: monthlyRevenue,
      });

      const clientMap = Object.fromEntries(clients.map((c) => [c.id, c.name]));

      // Recent jobs
      if (allJobsRes.status === "fulfilled" && allJobsRes.value.ok) {
        const d = (await allJobsRes.value.json()) as { jobs: Job[] };
        const recent = (d.jobs ?? []).slice(0, 6);
        setRecentJobs(recent.map((j) => ({ ...j, client_name: clientMap[j.client_id] })));
      }

      // Pending quotes
      try {
        const quotesAllRes = await fetch("/api/quotes", { cache: "no-store" });
        if (quotesAllRes.ok) {
          const d = (await quotesAllRes.json()) as { quotes: Quote[] };
          const pending = (d.quotes ?? [])
            .filter((q) => q.status === "draft" || q.status === "sent")
            .slice(0, 4);
          setPendingQuotes(pending.map((q) => ({ ...q, client_name: clientMap[q.client_id] })));
        }
      } catch {
        // silently fail
      }

      // Update S25 snapshot
      if (statusRes.status === "fulfilled" && statusRes.value.ok) {
        const snap = (await statusRes.value.json()) as CommandCenterSnapshot;
        setSnapshot(snap);
      }
    } catch (err) {
      console.error("[Dashboard] fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchData();
    const interval = setInterval(() => void fetchData(), 30_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const today = new Date().toLocaleDateString("fr-CA", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Page header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tableau de bord</h1>
          <p className="mt-0.5 text-sm text-gray-500 capitalize">{today}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowNewClient(true)}
            className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
            Nouveau client
          </button>
          <button
            onClick={() => setShowNewJob(true)}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-emerald-700"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Nouveau job
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatsCard
          label="Clients actifs"
          value={stats?.total_clients ?? "—"}
          sub="dans la base"
          accentColor="emerald"
          icon={
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
        />
        <StatsCard
          label="Jobs en cours"
          value={stats?.active_jobs ?? "—"}
          sub="statut actif"
          accentColor="blue"
          icon={
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          }
        />
        <StatsCard
          label="Devis en attente"
          value={stats?.pending_quotes ?? "—"}
          sub="brouillons + envoyés"
          accentColor="amber"
          icon={
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />
        <StatsCard
          label="Revenus ce mois"
          value={
            stats
              ? `$${stats.monthly_revenue_usd.toLocaleString("fr-CA", {
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 0,
                })}`
              : "—"
          }
          sub="jobs complétés"
          accentColor="purple"
          icon={
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Recent Jobs — spans 2 cols */}
        <div className="lg:col-span-2 rounded-xl bg-white border border-gray-200 shadow-sm overflow-hidden">
          <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
            <h2 className="text-sm font-semibold text-gray-900">Jobs récents</h2>
            <a
              href="/jobs"
              className="text-xs font-medium text-emerald-600 hover:text-emerald-700"
            >
              Voir tous →
            </a>
          </div>

          {loading ? (
            <div className="p-6 space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-12 animate-pulse rounded-lg bg-gray-100" />
              ))}
            </div>
          ) : recentJobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
              <svg className="h-10 w-10 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-sm text-gray-500">Aucun job pour l&apos;instant.</p>
              <button
                onClick={() => setShowNewJob(true)}
                className="mt-3 text-sm font-medium text-emerald-600 hover:text-emerald-700"
              >
                Créer le premier job →
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {recentJobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between px-6 py-3.5 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                        JOB_STATUS_STYLES[job.status] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {JOB_STATUS_LABEL[job.status] ?? job.status}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{job.title}</p>
                      <p className="text-xs text-gray-400 truncate">
                        {job.client_name ?? "—"} &middot; {JOB_TYPE_LABEL[job.type] ?? job.type}
                        {job.date && ` · ${new Date(job.date).toLocaleDateString("fr-CA")}`}
                      </p>
                    </div>
                  </div>
                  <span className="shrink-0 text-sm font-semibold text-gray-900 ml-4">
                    ${job.amount_usd.toLocaleString("fr-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Devis à envoyer */}
          <div className="rounded-xl bg-white border border-gray-200 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
              <h2 className="text-sm font-semibold text-gray-900">Devis à envoyer</h2>
              <a href="/devis" className="text-xs font-medium text-emerald-600 hover:text-emerald-700">
                Voir tous →
              </a>
            </div>
            {loading ? (
              <div className="p-4 space-y-2">
                {[...Array(2)].map((_, i) => (
                  <div key={i} className="h-10 animate-pulse rounded bg-gray-100" />
                ))}
              </div>
            ) : pendingQuotes.length === 0 ? (
              <div className="flex items-center justify-center py-8 px-5 text-center">
                <p className="text-sm text-gray-400">Aucun devis en attente.</p>
              </div>
            ) : (
              <ul className="divide-y divide-gray-100">
                {pendingQuotes.map((q) => (
                  <li key={q.id} className="flex items-center justify-between px-5 py-3 hover:bg-gray-50">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">
                        {q.client_name ?? "Client inconnu"}
                      </p>
                      <p className="text-xs text-gray-400">
                        {q.status === "draft" ? "Brouillon" : "Envoyé"}
                        {q.valid_until && ` · exp. ${new Date(q.valid_until).toLocaleDateString("fr-CA")}`}
                      </p>
                    </div>
                    <span className="shrink-0 text-sm font-semibold text-gray-900 ml-3">
                      ${q.amount_usd.toLocaleString("fr-CA", { minimumFractionDigits: 0 })}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Agents S25 */}
          <div className="rounded-xl bg-white border border-gray-200 shadow-sm overflow-hidden">
            <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4">
              <h2 className="text-sm font-semibold text-gray-900">Agents S25</h2>
              <span
                className={`text-xs font-medium ${
                  snapshot.pipeline_active ? "text-emerald-600" : "text-gray-400"
                }`}
              >
                {snapshot.pipeline_active ? "● Pipeline actif" : "○ Inactif"}
              </span>
            </div>
            <ul className="divide-y divide-gray-100">
              {snapshot.agents.map((agent) => (
                <li key={agent.name} className="flex items-center justify-between px-5 py-2.5">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`inline-block h-2 w-2 rounded-full flex-shrink-0 ${
                        AGENT_STATUS_STYLES[agent.status] ?? "bg-gray-300"
                      }`}
                    />
                    <span className="text-sm font-medium text-gray-800">{agent.name}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">{agent.model}</p>
                    <p
                      className={`text-xs font-medium ${
                        agent.status === "online"
                          ? "text-emerald-600"
                          : agent.status === "degraded" || agent.status === "sleep"
                          ? "text-amber-600"
                          : agent.status === "offline"
                          ? "text-red-500"
                          : "text-gray-400"
                      }`}
                    >
                      {agent.status === "online"
                        ? "En ligne"
                        : agent.status === "degraded"
                        ? "Dégradé"
                        : agent.status === "sleep"
                        ? "Veille"
                        : agent.status === "offline"
                        ? "Hors ligne"
                        : "Inconnu"}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
            <div className="border-t border-gray-100 px-5 py-3 bg-gray-50">
              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>HA: <span className={snapshot.ha_connected ? "text-emerald-600 font-medium" : "text-red-500 font-medium"}>{snapshot.ha_connected ? "Connecté" : "Déconnecté"}</span></span>
                <span>Signaux: <span className="font-medium text-gray-700">{snapshot.total_signals_today}</span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showNewClient && (
        <NewClientModal
          onClose={() => setShowNewClient(false)}
          onSuccess={() => {
            setShowNewClient(false);
            void fetchData();
          }}
        />
      )}
      {showNewJob && (
        <NewJobModal
          onClose={() => setShowNewJob(false)}
          onSuccess={() => {
            setShowNewJob(false);
            void fetchData();
          }}
        />
      )}
    </div>
  );
}
