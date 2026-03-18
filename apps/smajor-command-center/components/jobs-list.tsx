"use client";

import { useEffect, useState, useCallback } from "react";
import type { Job, JobStatus } from "@/lib/db";

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700 border border-amber-200",
  active: "bg-emerald-100 text-emerald-700 border border-emerald-200",
  completed: "bg-blue-100 text-blue-700 border border-blue-200",
};

const STATUS_LABEL: Record<string, string> = {
  pending: "En attente",
  active: "Actif",
  completed: "Complété",
};

const TYPE_LABEL: Record<string, string> = {
  excavation: "Excavation",
  deneigement: "Déneigement",
  consulting: "Consulting IA",
};

const TYPE_ICON: Record<string, string> = {
  excavation: "⛏",
  deneigement: "❄️",
  consulting: "🤖",
};

const ALL_STATUSES: JobStatus[] = ["pending", "active", "completed"];

interface JobWithClient extends Job {
  client_name?: string;
}

export function JobsList() {
  const [jobs, setJobs] = useState<JobWithClient[]>([]);
  const [filter, setFilter] = useState<JobStatus | "all">("all");
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params = filter !== "all" ? `?status=${filter}` : "";
      const [jobsRes, clientsRes] = await Promise.all([
        fetch(`/api/jobs${params}`, { cache: "no-store" }),
        fetch("/api/clients", { cache: "no-store" }),
      ]);

      const jobsData = jobsRes.ok
        ? ((await jobsRes.json()) as { jobs: Job[] }).jobs ?? []
        : [];
      const clientsData = clientsRes.ok
        ? ((await clientsRes.json()) as { clients: { id: string; name: string }[] }).clients ?? []
        : [];

      const clientMap = Object.fromEntries(clientsData.map((c) => [c.id, c.name]));
      setJobs(jobsData.map((j) => ({ ...j, client_name: clientMap[j.client_id] })));
    } catch (err) {
      console.error("[JobsList] fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void fetchJobs();
  }, [fetchJobs]);

  async function advanceStatus(job: Job) {
    const next: Record<JobStatus, JobStatus | null> = {
      pending: "active",
      active: "completed",
      completed: null,
    };
    const nextStatus = next[job.status];
    if (!nextStatus) return;

    setUpdating(job.id);
    try {
      const res = await fetch(`/api/jobs/${job.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (res.ok) void fetchJobs();
    } catch (err) {
      console.error("[JobsList] update error:", err);
    } finally {
      setUpdating(null);
    }
  }

  async function deleteJob(id: string) {
    if (!confirm("Supprimer ce job?")) return;
    try {
      const res = await fetch(`/api/jobs/${id}`, { method: "DELETE" });
      if (res.ok) setJobs((prev) => prev.filter((j) => j.id !== id));
    } catch (err) {
      console.error("[JobsList] delete error:", err);
    }
  }

  return (
    <div className="space-y-4">
      {/* Filter tabs */}
      <div className="flex items-center gap-1 border-b border-gray-200 pb-0">
        <button
          type="button"
          onClick={() => setFilter("all")}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            filter === "all"
              ? "border-emerald-600 text-emerald-700"
              : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
          }`}
        >
          Tous
          <span className={`ml-1.5 rounded-full px-1.5 py-0.5 text-xs ${filter === "all" ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>
            {jobs.length}
          </span>
        </button>
        {ALL_STATUSES.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setFilter(s)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              filter === s
                ? "border-emerald-600 text-emerald-700"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            {STATUS_LABEL[s]}
          </button>
        ))}
      </div>

      {/* Jobs list */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        ) : jobs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
            <svg className="h-10 w-10 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="text-sm text-gray-500">
              {filter === "all"
                ? "Aucun job enregistré."
                : `Aucun job "${STATUS_LABEL[filter]?.toLowerCase()}".`}
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {jobs.map((job) => (
              <li
                key={job.id}
                className="flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
              >
                {/* Left: icon + info */}
                <div className="flex items-start gap-4 min-w-0">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 text-base shrink-0">
                    {TYPE_ICON[job.type] ?? "📋"}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-semibold text-gray-900">{job.title}</p>
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          STATUS_STYLES[job.status] ?? "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {STATUS_LABEL[job.status] ?? job.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {job.client_name ?? "—"}
                      {" · "}
                      {TYPE_LABEL[job.type] ?? job.type}
                      {job.date && ` · ${new Date(job.date).toLocaleDateString("fr-CA")}`}
                    </p>
                    {job.notes && (
                      <p className="text-xs text-gray-400 mt-0.5 italic">{job.notes}</p>
                    )}
                  </div>
                </div>

                {/* Right: amount + actions */}
                <div className="flex items-center gap-3 shrink-0 ml-4">
                  <span className="text-sm font-bold text-gray-900">
                    ${job.amount_usd.toLocaleString("fr-CA", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </span>

                  {job.status !== "completed" && (
                    <button
                      type="button"
                      onClick={() => void advanceStatus(job)}
                      disabled={updating === job.id}
                      className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-emerald-50 hover:border-emerald-300 hover:text-emerald-700 disabled:opacity-40 transition-colors"
                    >
                      {updating === job.id
                        ? "..."
                        : job.status === "pending"
                        ? "→ Actif"
                        : "→ Complété"}
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => void deleteJob(job.id)}
                    className="text-gray-300 hover:text-red-500 transition-colors"
                    title="Supprimer"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
