"use client";

import { useEffect, useState, useCallback } from "react";
import type { Client, Job } from "@/lib/db";

interface ClientWithJobs extends Client {
  jobs?: Job[];
}

const TYPE_BADGE: Record<string, string> = {
  residential: "bg-blue-900/40 text-blue-300 border border-blue-700/40",
  commercial: "bg-purple-900/40 text-purple-300 border border-purple-700/40",
};

const inputCls =
  "rounded-lg bg-slate-800 border border-slate-600 px-3 py-1.5 text-sm text-slate-100 focus:border-neon/50 focus:outline-none focus:ring-1 focus:ring-neon/30";

export function ClientsTable() {
  const [clients, setClients] = useState<Client[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [expandedData, setExpandedData] = useState<ClientWithJobs | null>(null);
  const [expandLoading, setExpandLoading] = useState(false);

  const fetchClients = useCallback(async () => {
    setLoading(true);
    try {
      const params = search.trim() ? `?search=${encodeURIComponent(search.trim())}` : "";
      const res = await fetch(`/api/clients${params}`, { cache: "no-store" });
      if (res.ok) {
        const d = await res.json() as { clients: Client[] };
        setClients(d.clients ?? []);
      }
    } catch (err) {
      console.error("[ClientsTable] fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    const timer = setTimeout(() => void fetchClients(), 250);
    return () => clearTimeout(timer);
  }, [fetchClients]);

  async function expandClient(id: string) {
    if (expanded === id) {
      setExpanded(null);
      setExpandedData(null);
      return;
    }
    setExpanded(id);
    setExpandLoading(true);
    try {
      const res = await fetch(`/api/clients/${id}`);
      if (res.ok) {
        const d = await res.json() as { client: ClientWithJobs };
        setExpandedData(d.client);
      }
    } catch (err) {
      console.error("[ClientsTable] expand error:", err);
    } finally {
      setExpandLoading(false);
    }
  }

  async function deleteClient(id: string) {
    if (!confirm("Supprimer ce client? Cette action est irréversible.")) return;
    try {
      const res = await fetch(`/api/clients/${id}`, { method: "DELETE" });
      if (res.ok) {
        setClients((prev) => prev.filter((c) => c.id !== id));
        if (expanded === id) setExpanded(null);
      }
    } catch (err) {
      console.error("[ClientsTable] delete error:", err);
    }
  }

  return (
    <div className="space-y-4">
      {/* Search bar */}
      <div className="flex items-center gap-3">
        <input
          type="search"
          className={`${inputCls} w-64`}
          placeholder="Rechercher..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span className="text-xs text-slate-500">{clients.length} client{clients.length !== 1 ? "s" : ""}</span>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-slate-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-800/60">
            <tr>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-slate-400 font-medium">Nom</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-slate-400 font-medium">Contact</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-slate-400 font-medium">Type</th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-slate-400 font-medium">Créé le</th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-slate-400 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {loading ? (
              [...Array(3)].map((_, i) => (
                <tr key={i}>
                  <td colSpan={5} className="px-4 py-3">
                    <div className="h-4 animate-pulse rounded bg-slate-800" />
                  </td>
                </tr>
              ))
            ) : clients.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-500">
                  {search ? "Aucun résultat." : "Aucun client enregistré."}
                </td>
              </tr>
            ) : (
              clients.map((client) => (
                <>
                  <tr
                    key={client.id}
                    className="bg-panel hover:bg-slate-800/50 cursor-pointer transition-colors"
                    onClick={() => void expandClient(client.id)}
                  >
                    <td className="px-4 py-3 font-medium text-slate-100">{client.name}</td>
                    <td className="px-4 py-3 text-slate-400">
                      <div>{client.phone ?? "—"}</div>
                      <div className="text-xs">{client.email ?? ""}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${TYPE_BADGE[client.type] ?? "bg-slate-700 text-slate-300"}`}>
                        {client.type === "residential" ? "Résidentiel" : "Commercial"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-slate-500 text-xs">
                      {new Date(client.created_at).toLocaleDateString("fr-CA")}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={(e) => { e.stopPropagation(); void deleteClient(client.id); }}
                        className="text-xs text-slate-500 hover:text-danger transition-colors"
                      >
                        Supprimer
                      </button>
                    </td>
                  </tr>

                  {/* Expanded row */}
                  {expanded === client.id && (
                    <tr key={`${client.id}-expanded`} className="bg-slate-900/50">
                      <td colSpan={5} className="px-6 py-4">
                        {expandLoading ? (
                          <div className="h-8 animate-pulse rounded bg-slate-800 w-1/3" />
                        ) : expandedData ? (
                          <div className="space-y-3">
                            {expandedData.address && (
                              <p className="text-xs text-slate-400">
                                <span className="text-slate-500">Adresse:</span> {expandedData.address}
                              </p>
                            )}
                            {expandedData.notes && (
                              <p className="text-xs text-slate-400">
                                <span className="text-slate-500">Notes:</span> {expandedData.notes}
                              </p>
                            )}
                            <div>
                              <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider">Jobs</p>
                              {expandedData.jobs && expandedData.jobs.length > 0 ? (
                                <ul className="space-y-1">
                                  {expandedData.jobs.map((job) => (
                                    <li key={job.id} className="flex items-center gap-3 text-xs">
                                      <span className={`rounded-full px-2 py-0.5 ${
                                        job.status === "active" ? "bg-neon/20 text-neon" :
                                        job.status === "completed" ? "text-emerald-400 bg-emerald-900/30" :
                                        "text-slate-400 bg-slate-800"
                                      }`}>
                                        {job.status}
                                      </span>
                                      <span className="text-slate-300">{job.title}</span>
                                      <span className="text-neon font-mono">
                                        ${job.amount_usd.toLocaleString("fr-CA", { minimumFractionDigits: 2 })}
                                      </span>
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-xs text-slate-600">Aucun job.</p>
                              )}
                            </div>
                          </div>
                        ) : null}
                      </td>
                    </tr>
                  )}
                </>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
