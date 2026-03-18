"use client";

import { useEffect, useState, useCallback } from "react";
import type { Client, Job } from "@/lib/db";

interface ClientWithJobs extends Client {
  jobs?: Job[];
}

const TYPE_BADGE: Record<string, string> = {
  residential: "bg-blue-100 text-blue-700 border border-blue-200",
  commercial: "bg-purple-100 text-purple-700 border border-purple-200",
};

const TYPE_LABEL: Record<string, string> = {
  residential: "Résidentiel",
  commercial: "Commercial",
};

const JOB_STATUS_STYLES: Record<string, string> = {
  pending: "bg-amber-100 text-amber-700",
  active: "bg-emerald-100 text-emerald-700",
  completed: "bg-blue-100 text-blue-700",
};

const JOB_STATUS_LABEL: Record<string, string> = {
  pending: "En attente",
  active: "Actif",
  completed: "Complété",
};

interface ClientsTableProps {
  onClientAdded?: () => void;
}

export function ClientsTable({ onClientAdded: _onClientAdded }: ClientsTableProps = {}) {
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
        const d = (await res.json()) as { clients: Client[] };
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
        const d = (await res.json()) as { client: ClientWithJobs };
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
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="search"
            className="pl-9 pr-4 py-2 rounded-lg border border-gray-300 bg-white text-sm text-gray-900 placeholder-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 w-64"
            placeholder="Rechercher un client..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <span className="text-sm text-gray-500">
          {clients.length} client{clients.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                Nom
              </th>
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 hidden sm:table-cell">
                Contact
              </th>
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                Type
              </th>
              <th className="px-5 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 hidden md:table-cell">
                Créé le
              </th>
              <th className="px-5 py-3 text-right text-xs font-semibold uppercase tracking-wider text-gray-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              [...Array(4)].map((_, i) => (
                <tr key={i}>
                  <td colSpan={5} className="px-5 py-3.5">
                    <div className="h-4 animate-pulse rounded-lg bg-gray-100" />
                  </td>
                </tr>
              ))
            ) : clients.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-10 text-center">
                  <div className="flex flex-col items-center gap-2">
                    <svg className="h-8 w-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <p className="text-sm text-gray-500">
                      {search ? "Aucun résultat pour cette recherche." : "Aucun client enregistré."}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              clients.map((client) => (
                <>
                  <tr
                    key={client.id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => void expandClient(client.id)}
                  >
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2.5">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-sm font-semibold text-emerald-700 shrink-0">
                          {client.name.charAt(0).toUpperCase()}
                        </div>
                        <span className="font-medium text-gray-900">{client.name}</span>
                      </div>
                    </td>
                    <td className="px-5 py-3.5 hidden sm:table-cell">
                      <div className="text-gray-700">{client.phone ?? "—"}</div>
                      {client.email && (
                        <div className="text-xs text-gray-400">{client.email}</div>
                      )}
                    </td>
                    <td className="px-5 py-3.5">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          TYPE_BADGE[client.type] ?? "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {TYPE_LABEL[client.type] ?? client.type}
                      </span>
                    </td>
                    <td className="px-5 py-3.5 text-gray-400 text-xs hidden md:table-cell">
                      {new Date(client.created_at).toLocaleDateString("fr-CA")}
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <div className="flex items-center justify-end gap-3">
                        <svg
                          className={`h-4 w-4 text-gray-400 transition-transform ${expanded === client.id ? "rotate-180" : ""}`}
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            void deleteClient(client.id);
                          }}
                          className="text-xs text-gray-400 hover:text-red-500 transition-colors"
                        >
                          Supprimer
                        </button>
                      </div>
                    </td>
                  </tr>

                  {/* Expanded row */}
                  {expanded === client.id && (
                    <tr key={`${client.id}-expanded`} className="bg-gray-50/80">
                      <td colSpan={5} className="px-8 py-4">
                        {expandLoading ? (
                          <div className="h-8 animate-pulse rounded-lg bg-gray-200 w-1/3" />
                        ) : expandedData ? (
                          <div className="space-y-3">
                            {expandedData.address && (
                              <p className="text-sm text-gray-600">
                                <span className="font-medium text-gray-700">Adresse:</span>{" "}
                                {expandedData.address}
                              </p>
                            )}
                            {expandedData.notes && (
                              <p className="text-sm text-gray-600">
                                <span className="font-medium text-gray-700">Notes:</span>{" "}
                                {expandedData.notes}
                              </p>
                            )}
                            <div>
                              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
                                Jobs associés
                              </p>
                              {expandedData.jobs && expandedData.jobs.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                  {expandedData.jobs.map((job) => (
                                    <div
                                      key={job.id}
                                      className="flex items-center gap-2 rounded-lg bg-white border border-gray-200 px-3 py-1.5 text-xs shadow-sm"
                                    >
                                      <span
                                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                          JOB_STATUS_STYLES[job.status] ?? "bg-gray-100 text-gray-600"
                                        }`}
                                      >
                                        {JOB_STATUS_LABEL[job.status] ?? job.status}
                                      </span>
                                      <span className="text-gray-700">{job.title}</span>
                                      <span className="font-semibold text-gray-900">
                                        ${job.amount_usd.toLocaleString("fr-CA", { minimumFractionDigits: 2 })}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-gray-400">Aucun job pour ce client.</p>
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
