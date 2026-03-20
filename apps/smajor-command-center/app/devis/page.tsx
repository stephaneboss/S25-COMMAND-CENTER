"use client";

import { useState, useEffect, useCallback } from "react";
import type { Quote, Client, QuoteStatus } from "@/lib/db";
import { NewQuoteModal } from "@/components/new-quote-modal";
import { QuoteStatusBadge } from "@/components/quote-status-badge";

// ─── Constants ────────────────────────────────────────────────────────────────

const STATUS_LABEL: Record<QuoteStatus, string> = {
  draft: "Brouillon",
  sent: "Envoyé",
  accepted: "Accepté",
  rejected: "Refusé",
};

const ALL_STATUSES: QuoteStatus[] = ["draft", "sent", "accepted", "rejected"];

interface QuoteWithClient extends Quote {
  client_name?: string;
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function DevisPage() {
  const [quotes, setQuotes] = useState<QuoteWithClient[]>([]);
  const [filter, setFilter] = useState<QuoteStatus | "all">("all");
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [updating, setUpdating] = useState<string | null>(null);

  const fetchQuotes = useCallback(async () => {
    setLoading(true);
    try {
      const params = filter !== "all" ? `?status=${filter}` : "";
      const [quotesRes, clientsRes] = await Promise.all([
        fetch(`/api/quotes${params}`, { cache: "no-store" }),
        fetch("/api/clients", { cache: "no-store" }),
      ]);

      const quotesData = quotesRes.ok
        ? ((await quotesRes.json()) as { quotes: Quote[] }).quotes ?? []
        : [];
      const clientsData = clientsRes.ok
        ? ((await clientsRes.json()) as { clients: Client[] }).clients ?? []
        : [];

      const clientMap = Object.fromEntries(clientsData.map((c) => [c.id, c.name]));
      setQuotes(quotesData.map((q) => ({ ...q, client_name: clientMap[q.client_id] })));
    } catch (err) {
      console.error("[DevisPage] fetch error:", err);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    void fetchQuotes();
  }, [fetchQuotes]);

  async function advanceStatus(quote: Quote) {
    const next: Record<QuoteStatus, QuoteStatus | null> = {
      draft: "sent",
      sent: "accepted",
      accepted: null,
      rejected: null,
    };
    const nextStatus = next[quote.status];
    if (!nextStatus) return;

    setUpdating(quote.id);
    try {
      const res = await fetch(`/api/quotes/${quote.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (res.ok) void fetchQuotes();
    } catch (err) {
      console.error("[DevisPage] update error:", err);
    } finally {
      setUpdating(null);
    }
  }

  async function rejectQuote(quote: Quote) {
    if (!confirm("Marquer ce devis comme refusé?")) return;
    setUpdating(quote.id);
    try {
      const res = await fetch(`/api/quotes/${quote.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "rejected" }),
      });
      if (res.ok) void fetchQuotes();
    } catch (err) {
      console.error("[DevisPage] reject error:", err);
    } finally {
      setUpdating(null);
    }
  }

  async function deleteQuote(id: string) {
    if (!confirm("Supprimer ce devis?")) return;
    try {
      const res = await fetch(`/api/quotes/${id}`, { method: "DELETE" });
      if (res.ok) setQuotes((prev) => prev.filter((q) => q.id !== id));
    } catch (err) {
      console.error("[DevisPage] delete error:", err);
    }
  }

  const advanceLabel: Record<QuoteStatus, string | null> = {
    draft: "→ Envoyer",
    sent: "→ Accepté",
    accepted: null,
    rejected: null,
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Page header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Devis / Soumissions</h1>
          <p className="mt-0.5 text-sm text-gray-500">
            Créez et suivez vos soumissions pour chaque client.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 self-start rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 transition-colors sm:self-auto"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Nouveau devis
        </button>
      </div>

      {/* Filter tabs */}
      <div className="mb-4 flex items-center gap-1 border-b border-gray-200">
        <button
          type="button"
          onClick={() => setFilter("all")}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            filter === "all"
              ? "border-emerald-600 text-emerald-700"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Tous
          <span className={`ml-1.5 rounded-full px-1.5 py-0.5 text-xs ${filter === "all" ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>
            {quotes.length}
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
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {STATUS_LABEL[s]}
          </button>
        ))}
      </div>

      {/* Quotes list */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-6 space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-gray-100" />
            ))}
          </div>
        ) : quotes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
            <svg className="h-10 w-10 text-gray-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-sm text-gray-500">
              {filter === "all"
                ? "Aucun devis créé."
                : `Aucun devis "${STATUS_LABEL[filter]?.toLowerCase()}".`}
            </p>
            {filter === "all" && (
              <button
                type="button"
                onClick={() => setShowModal(true)}
                className="mt-3 text-sm font-medium text-emerald-600 hover:text-emerald-700"
              >
                Créer le premier devis →
              </button>
            )}
          </div>
        ) : (
          <ul className="divide-y divide-gray-100">
            {quotes.map((q) => (
              <li
                key={q.id}
                className="flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
              >
                {/* Left: status + client info */}
                <div className="flex items-start gap-4 min-w-0">
                  <div className="flex flex-col items-center pt-0.5 shrink-0">
                    <svg className="h-8 w-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="text-sm font-semibold text-gray-900">
                        {q.client_name ?? "Client inconnu"}
                      </p>
                      <QuoteStatusBadge status={q.status} />
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Créé le {new Date(q.created_at).toLocaleDateString("fr-CA")}
                      {q.valid_until && (
                        <>
                          {" · "}
                          Valide jusqu&apos;au {new Date(q.valid_until).toLocaleDateString("fr-CA")}
                        </>
                      )}
                    </p>
                  </div>
                </div>

                {/* Right: amount + actions */}
                <div className="flex items-center gap-3 shrink-0 ml-4">
                  <span className="text-sm font-bold text-gray-900">
                    ${q.amount_usd.toLocaleString("fr-CA", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </span>

                  {/* Advance button */}
                  {advanceLabel[q.status] && (
                    <button
                      type="button"
                      onClick={() => void advanceStatus(q)}
                      disabled={updating === q.id}
                      className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-emerald-50 hover:border-emerald-300 hover:text-emerald-700 disabled:opacity-40 transition-colors"
                    >
                      {updating === q.id ? "..." : advanceLabel[q.status]}
                    </button>
                  )}

                  {/* Reject button for draft/sent */}
                  {(q.status === "draft" || q.status === "sent") && (
                    <button
                      type="button"
                      onClick={() => void rejectQuote(q)}
                      disabled={updating === q.id}
                      className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-500 hover:bg-red-50 hover:border-red-200 hover:text-red-600 disabled:opacity-40 transition-colors"
                    >
                      Refuser
                    </button>
                  )}

                  {/* Delete */}
                  <button
                    type="button"
                    onClick={() => void deleteQuote(q.id)}
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

      {/* Modal */}
      {showModal && (
        <NewQuoteModal
          onClose={() => setShowModal(false)}
          onCreated={() => {
            setShowModal(false);
            void fetchQuotes();
          }}
        />
      )}
    </div>
  );
}
