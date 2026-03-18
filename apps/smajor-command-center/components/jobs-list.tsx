"use client";

import { useEffect, useState, useCallback } from "react";
import type { Job, JobStatus } from "@/lib/db";

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-slate-700 text-slate-300 border border-slate-600",
  active: "bg-neon/20 text-neon border border-neon/40",
  completed: "bg-emerald-900/40 text-emerald-400 border border-emerald-700/40",
};

const STATUS_LABEL: Record<string, string> = {
  pending: "En attente",
  active: "Actif",
  completed: "Complété",
};

const TYPE_LABEL: Record<string, string> = {
  excavation: "Excavation",
  deneigement: "Déneigement",
  consulting: "Consulting AI",
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

      const jobsData = jobsRes.ok ? (await jobsRes.json() as { jobs: Job[] }).jobs ?? [] : [];
      const clientsData = clientsRes.ok ? (await clientsRes.json() as { clients: { id: string; name: string }[] }).clients ?? [] : [];

      const clientMap = Object.fromEntries(clientsData.map((c) => [c.id, c.name]));
      setJobs(jobsData.map((j) => ({ ...j, client_name: clientMap[j.client_id] })));
    } catch (err) {
      console.error("[JobsList] fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { void fetchJobs(); }, [fetchJobs]);

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
      <div className="flex items-center gap-2">
        <button
          onClick={() => setFilter("all")}
          className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            filter === "all"
              ? "bg-slate-600 text-slate-100"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Tous
        </button>
        {ALL_STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
              filter === s
                ? STATUS_BADGE[s]
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {STATUS_LABEL[s]}
          </button>
        ))}
      </div>

      {/* Jobs list */}
      <div className="rounded-xl border border-slate-700 overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-14 animate-pulse rounded-lg bg-slate-800" />
            ))}
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">
            {filter === "all" ? "Aucun job enregistré." : `Aucun job ${STATUS_LABEL[filter]?.toLowerCase()}.`}
          </div>
        ) : (
          <ul className="divide-y divide-slate-800">
            {jobs.map((job) => (
              <li key={job.id} className="flex items-center justify-between bg-panel px-4 py-3 hover:bg-slate-800/50 transition-colors">
                <div className="flex items-start gap-3">
                  <span className={`mt-0.5 rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_BADGE[job.status] ?? "bg-slate-700 text-slate-300"}`}>
                    {STATUS_LABEL[job.status] ?? job.status}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-slate-100">{job.title}</p>
                    <p className="text-xs text-slate-500">
                      {job.client_name ?? job.client_id} · {TYPE_LABEL[job.type] ?? job.type}
                      {job.date && ` · ${new Date(job.date).toLocaleDateString("fr-CA")}`}
                    </p>
                    {job.notes && <p className="text-xs text-slate-600 mt-0.5 italic">{job.notes}</p>}
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span className="font-mono text-neon text-sm">
                    ${job.amount_usd.toLocaleString("fr-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>

                  {job.status !== "completed" && (
                    <button
                      onClick={() => void advanceStatus(job)}
                      disabled={updating === job.id}
                      className="rounded-lg border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:border-neon/40 hover:text-neon transition-colors disabled:opacity-40"
                      title={job.status === "pending" ? "Marquer actif" : "Marquer complété"}
                    >
                      {updating === job.id
                        ? "..."
                        : job.status === "pending"
                        ? "→ Actif"
                        : "→ Complété"}
                    </button>
                  )}

                  <button
                    onClick={() => void deleteJob(job.id)}
                    className="text-xs text-slate-600 hover:text-danger transition-colors"
                  >
                    ×
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
