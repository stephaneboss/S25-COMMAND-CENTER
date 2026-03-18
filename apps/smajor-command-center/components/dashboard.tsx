"use client";

import { useEffect, useState, useCallback } from "react";
import type { CommandCenterSnapshot } from "@/lib/s25-api";
import type { Job, Client, Quote } from "@/lib/db";

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

// ─── Sub-components ───────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "neon" | "ember" | "danger" | "default";
}) {
  const accentClass = {
    neon: "text-neon",
    ember: "text-ember",
    danger: "text-danger",
    default: "text-slate-100",
  }[accent ?? "default"];

  return (
    <div className="rounded-xl border border-slate-700 bg-panel p-5 shadow-neon">
      <p className="text-xs uppercase tracking-widest text-slate-400">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${accentClass}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

function AgentDot({ status }: { status: string }) {
  const color =
    status === "online"
      ? "bg-neon shadow-[0_0_6px_#67ffd8]"
      : status === "degraded"
      ? "bg-ember shadow-[0_0_6px_#ff9958]"
      : status === "offline"
      ? "bg-danger shadow-[0_0_6px_#ff5f7a]"
      : "bg-slate-600";
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${color}`} />;
}

const JOB_STATUS_BADGE: Record<string, string> = {
  pending: "bg-slate-700 text-slate-300",
  active: "bg-neon/20 text-neon border border-neon/40",
  completed: "bg-emerald-900/40 text-emerald-400 border border-emerald-700/40",
};

const JOB_TYPE_LABEL: Record<string, string> = {
  excavation: "Excavation",
  deneigement: "Déneigement",
  consulting: "Consulting AI",
};

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export function Dashboard({ snapshot: initialSnapshot }: DashboardProps) {
  const [snapshot, setSnapshot] = useState<CommandCenterSnapshot>(initialSnapshot);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentJobs, setRecentJobs] = useState<(Job & { client_name?: string })[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewClient, setShowNewClient] = useState(false);
  const [showNewJob, setShowNewJob] = useState(false);
  const [showNewQuote, setShowNewQuote] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [jobsRes, clientsRes, quotesRes, statusRes] = await Promise.allSettled([
        fetch("/api/jobs?status=active", { cache: "no-store" }),
        fetch("/api/clients", { cache: "no-store" }),
        fetch("/api/quotes?status=draft", { cache: "no-store" }),
        fetch("/api/s25/status", { cache: "no-store" }),
      ]);

      let clients: Client[] = [];
      let jobs: Job[] = [];
      let pendingQuoteCount = 0;
      let monthlyRevenue = 0;

      if (clientsRes.status === "fulfilled" && clientsRes.value.ok) {
        const d = await clientsRes.value.json() as { clients: Client[] };
        clients = d.clients ?? [];
      }

      if (jobsRes.status === "fulfilled" && jobsRes.value.ok) {
        const d = await jobsRes.value.json() as { jobs: Job[] };
        jobs = d.jobs ?? [];
      }

      if (quotesRes.status === "fulfilled" && quotesRes.value.ok) {
        const d = await quotesRes.value.json() as { quotes: Quote[] };
        pendingQuoteCount = d.quotes?.length ?? 0;
      }

      // Completed jobs this month for revenue
      const completedRes = await fetch("/api/jobs?status=completed", { cache: "no-store" });
      if (completedRes.ok) {
        const d = await completedRes.value?.json?.() ?? await completedRes.json() as { jobs: Job[] };
        const thisMonth = new Date();
        thisMonth.setDate(1);
        thisMonth.setHours(0, 0, 0, 0);
        monthlyRevenue = (d.jobs as Job[] ?? [])
          .filter((j) => j.created_at && new Date(j.created_at) >= thisMonth)
          .reduce((sum, j) => sum + (j.amount_usd ?? 0), 0);
      }

      setStats({
        total_clients: clients.length,
        active_jobs: jobs.length,
        pending_quotes: pendingQuoteCount,
        monthly_revenue_usd: monthlyRevenue,
      });

      // Last 5 jobs across all statuses
      const allJobsRes = await fetch("/api/jobs", { cache: "no-store" });
      if (allJobsRes.ok) {
        const d = await allJobsRes.json() as { jobs: Job[] };
        const allJobs = (d.jobs ?? []).slice(0, 5);
        const clientMap = Object.fromEntries(clients.map((c) => [c.id, c.name]));
        setRecentJobs(allJobs.map((j) => ({ ...j, client_name: clientMap[j.client_id] })));
      }

      if (statusRes.status === "fulfilled" && statusRes.value.ok) {
        const snap = await statusRes.value.json() as CommandCenterSnapshot;
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
    // Refresh S25 status every 30 seconds
    const interval = setInterval(() => void fetchData(), 30_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neon tracking-tight">Smajor Command Center</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {new Date().toLocaleDateString("fr-CA", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowNewClient(true)}
            className="rounded-lg bg-neon/10 border border-neon/30 px-3 py-1.5 text-xs text-neon hover:bg-neon/20 transition-colors"
          >
            + Nouveau Client
          </button>
          <button
            onClick={() => setShowNewJob(true)}
            className="rounded-lg bg-ember/10 border border-ember/30 px-3 py-1.5 text-xs text-ember hover:bg-ember/20 transition-colors"
          >
            + Nouveau Job
          </button>
          <button
            onClick={() => setShowNewQuote(true)}
            className="rounded-lg bg-slate-700 border border-slate-600 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-600 transition-colors"
          >
            + Nouvelle Soumission
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          label="Clients"
          value={stats?.total_clients ?? "—"}
          sub="total actifs"
          accent="neon"
        />
        <StatCard
          label="Jobs Actifs"
          value={stats?.active_jobs ?? "—"}
          sub="en cours"
          accent="ember"
        />
        <StatCard
          label="Soumissions"
          value={stats?.pending_quotes ?? "—"}
          sub="draft + envoyées"
        />
        <StatCard
          label="Revenu Mensuel"
          value={stats ? `$${stats.monthly_revenue_usd.toLocaleString("fr-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—"}
          sub="jobs complétés ce mois"
          accent="neon"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {/* Recent Jobs */}
        <div className="md:col-span-2 rounded-xl border border-slate-700 bg-panel p-5">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-widest text-slate-400">
            Jobs Récents
          </h2>
          {loading ? (
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-10 animate-pulse rounded bg-slate-800" />
              ))}
            </div>
          ) : recentJobs.length === 0 ? (
            <p className="text-sm text-slate-500">Aucun job pour l&apos;instant.</p>
          ) : (
            <ul className="divide-y divide-slate-800">
              {recentJobs.map((job) => (
                <li key={job.id} className="flex items-center justify-between py-2.5">
                  <div>
                    <p className="text-sm font-medium text-slate-100">{job.title}</p>
                    <p className="text-xs text-slate-500">
                      {job.client_name ?? job.client_id} · {JOB_TYPE_LABEL[job.type] ?? job.type}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-mono text-neon">
                      ${job.amount_usd.toLocaleString("fr-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${JOB_STATUS_BADGE[job.status] ?? "bg-slate-700 text-slate-300"}`}
                    >
                      {job.status}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* S25 Agent Status */}
        <div className="rounded-xl border border-slate-700 bg-panel p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold uppercase tracking-widest text-slate-400">
              Agents S25
            </h2>
            <span
              className={`text-xs font-medium ${
                snapshot.pipeline_active ? "text-neon" : "text-slate-500"
              }`}
            >
              {snapshot.pipeline_active ? "● Pipeline actif" : "○ Inactif"}
            </span>
          </div>

          <ul className="space-y-3">
            {snapshot.agents.map((agent) => (
              <li key={agent.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AgentDot status={agent.status} />
                  <span className="text-sm font-medium text-slate-200">{agent.name}</span>
                </div>
                <div className="text-right">
                  <span
                    className={`text-xs ${
                      agent.status === "online"
                        ? "text-neon"
                        : agent.status === "degraded"
                        ? "text-ember"
                        : agent.status === "offline"
                        ? "text-danger"
                        : "text-slate-500"
                    }`}
                  >
                    {agent.status}
                  </span>
                  <p className="text-xs text-slate-600">{agent.model}</p>
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-4 border-t border-slate-800 pt-3 space-y-1">
            <p className="text-xs text-slate-500">
              HA:{" "}
              <span className={snapshot.ha_connected ? "text-neon" : "text-danger"}>
                {snapshot.ha_connected ? "Connected" : "Disconnected"}
              </span>
            </p>
            <p className="text-xs text-slate-500">
              Signaux aujourd&apos;hui:{" "}
              <span className="text-slate-300">{snapshot.total_signals_today}</span>
            </p>
            <p className="text-xs text-slate-500">
              Cockpit: <span className="text-slate-300">v{snapshot.cockpit_version}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Quick action modals — minimal inline forms */}
      {showNewClient && (
        <NewClientModal
          onClose={() => setShowNewClient(false)}
          onSuccess={() => { setShowNewClient(false); void fetchData(); }}
        />
      )}
      {showNewJob && (
        <NewJobModal
          onClose={() => setShowNewJob(false)}
          onSuccess={() => { setShowNewJob(false); void fetchData(); }}
        />
      )}
      {showNewQuote && (
        <NewQuoteModal
          onClose={() => setShowNewQuote(false)}
          onSuccess={() => { setShowNewQuote(false); void fetchData(); }}
        />
      )}
    </div>
  );
}

// ─── Inline Modals ────────────────────────────────────────────────────────────

function ModalShell({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-slate-700 bg-panel p-6 shadow-neon">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-100">{title}</h3>
          <button onClick={onClose} className="text-slate-500 hover:text-slate-200 text-lg leading-none">×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <label className="text-xs text-slate-400 uppercase tracking-wider">{label}</label>
      {children}
    </div>
  );
}

const inputCls = "w-full rounded-lg bg-slate-800 border border-slate-600 px-3 py-2 text-sm text-slate-100 focus:border-neon/50 focus:outline-none focus:ring-1 focus:ring-neon/30";

function NewClientModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [type, setType] = useState<"residential" | "commercial">("residential");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setError("Le nom est requis."); return; }
    setSaving(true);
    try {
      const res = await fetch("/api/clients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, phone, email, address, type }),
      });
      if (!res.ok) throw new Error("Erreur serveur");
      onSuccess();
    } catch {
      setError("Impossible de créer le client.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <ModalShell title="Nouveau Client" onClose={onClose}>
      <form onSubmit={(e) => void submit(e)} className="space-y-3">
        <Field label="Nom *"><input className={inputCls} value={name} onChange={e => setName(e.target.value)} placeholder="Jean Tremblay" /></Field>
        <Field label="Téléphone"><input className={inputCls} value={phone} onChange={e => setPhone(e.target.value)} placeholder="514-555-0001" /></Field>
        <Field label="Email"><input className={inputCls} type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="jean@exemple.com" /></Field>
        <Field label="Adresse"><input className={inputCls} value={address} onChange={e => setAddress(e.target.value)} placeholder="123 rue Principale, Montréal" /></Field>
        <Field label="Type">
          <select className={inputCls} value={type} onChange={e => setType(e.target.value as "residential" | "commercial")}>
            <option value="residential">Résidentiel</option>
            <option value="commercial">Commercial</option>
          </select>
        </Field>
        {error && <p className="text-xs text-danger">{error}</p>}
        <div className="flex gap-2 pt-1">
          <button type="button" onClick={onClose} className="flex-1 rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700">Annuler</button>
          <button type="submit" disabled={saving} className="flex-1 rounded-lg bg-neon/20 border border-neon/40 px-4 py-2 text-sm text-neon hover:bg-neon/30 disabled:opacity-50">
            {saving ? "Création..." : "Créer"}
          </button>
        </div>
      </form>
    </ModalShell>
  );
}

function NewJobModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [clientId, setClientId] = useState("");
  const [title, setTitle] = useState("");
  const [type, setType] = useState<"excavation" | "deneigement" | "consulting">("excavation");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [clients, setClients] = useState<Client[]>([]);

  useEffect(() => {
    fetch("/api/clients")
      .then(r => r.json() as Promise<{ clients: Client[] }>)
      .then(d => setClients(d.clients ?? []))
      .catch(() => null);
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!clientId) { setError("Choisir un client."); return; }
    if (!title.trim()) { setError("Le titre est requis."); return; }
    setSaving(true);
    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: clientId, title, type, amount_usd: Number(amount || 0), date: date || null }),
      });
      if (!res.ok) throw new Error("Erreur serveur");
      onSuccess();
    } catch {
      setError("Impossible de créer le job.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <ModalShell title="Nouveau Job" onClose={onClose}>
      <form onSubmit={(e) => void submit(e)} className="space-y-3">
        <Field label="Client *">
          <select className={inputCls} value={clientId} onChange={e => setClientId(e.target.value)}>
            <option value="">— Sélectionner —</option>
            {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Titre *"><input className={inputCls} value={title} onChange={e => setTitle(e.target.value)} placeholder="Excavation fondation" /></Field>
        <Field label="Type">
          <select className={inputCls} value={type} onChange={e => setType(e.target.value as typeof type)}>
            <option value="excavation">Excavation</option>
            <option value="deneigement">Déneigement</option>
            <option value="consulting">Consulting AI</option>
          </select>
        </Field>
        <Field label="Montant ($)"><input className={inputCls} type="number" min="0" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} placeholder="0.00" /></Field>
        <Field label="Date"><input className={inputCls} type="date" value={date} onChange={e => setDate(e.target.value)} /></Field>
        {error && <p className="text-xs text-danger">{error}</p>}
        <div className="flex gap-2 pt-1">
          <button type="button" onClick={onClose} className="flex-1 rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700">Annuler</button>
          <button type="submit" disabled={saving} className="flex-1 rounded-lg bg-ember/20 border border-ember/40 px-4 py-2 text-sm text-ember hover:bg-ember/30 disabled:opacity-50">
            {saving ? "Création..." : "Créer"}
          </button>
        </div>
      </form>
    </ModalShell>
  );
}

function NewQuoteModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [clientId, setClientId] = useState("");
  const [amount, setAmount] = useState("");
  const [validUntil, setValidUntil] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [clients, setClients] = useState<Client[]>([]);

  useEffect(() => {
    fetch("/api/clients")
      .then(r => r.json() as Promise<{ clients: Client[] }>)
      .then(d => setClients(d.clients ?? []))
      .catch(() => null);
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!clientId) { setError("Choisir un client."); return; }
    setSaving(true);
    try {
      const res = await fetch("/api/quotes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ client_id: clientId, amount_usd: Number(amount || 0), valid_until: validUntil || null }),
      });
      if (!res.ok) throw new Error("Erreur serveur");
      onSuccess();
    } catch {
      setError("Impossible de créer la soumission.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <ModalShell title="Nouvelle Soumission" onClose={onClose}>
      <form onSubmit={(e) => void submit(e)} className="space-y-3">
        <Field label="Client *">
          <select className={inputCls} value={clientId} onChange={e => setClientId(e.target.value)}>
            <option value="">— Sélectionner —</option>
            {clients.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Montant ($)"><input className={inputCls} type="number" min="0" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} placeholder="0.00" /></Field>
        <Field label="Valide jusqu'au"><input className={inputCls} type="date" value={validUntil} onChange={e => setValidUntil(e.target.value)} /></Field>
        {error && <p className="text-xs text-danger">{error}</p>}
        <div className="flex gap-2 pt-1">
          <button type="button" onClick={onClose} className="flex-1 rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-700">Annuler</button>
          <button type="submit" disabled={saving} className="flex-1 rounded-lg bg-slate-700 border border-slate-500 px-4 py-2 text-sm text-slate-200 hover:bg-slate-600 disabled:opacity-50">
            {saving ? "Création..." : "Créer"}
          </button>
        </div>
      </form>
    </ModalShell>
  );
}
