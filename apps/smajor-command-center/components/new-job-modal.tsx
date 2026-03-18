"use client";

import { useState, useEffect } from "react";
import type { Client } from "@/lib/db";

interface NewJobModalProps {
  onClose: () => void;
  onSuccess: () => void;
  defaultClientId?: string;
}

const inputCls =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 transition-colors";

const labelCls = "block text-xs font-medium text-gray-600 mb-1";

export function NewJobModal({ onClose, onSuccess, defaultClientId }: NewJobModalProps) {
  const [clientId, setClientId] = useState(defaultClientId ?? "");
  const [title, setTitle] = useState("");
  const [type, setType] = useState<"excavation" | "deneigement" | "consulting">("excavation");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [clients, setClients] = useState<Client[]>([]);
  const [loadingClients, setLoadingClients] = useState(true);

  useEffect(() => {
    fetch("/api/clients")
      .then((r) => r.json() as Promise<{ clients: Client[] }>)
      .then((d) => {
        setClients(d.clients ?? []);
        if (!defaultClientId && d.clients?.length === 1) {
          setClientId(d.clients[0].id);
        }
      })
      .catch(() => null)
      .finally(() => setLoadingClients(false));
  }, [defaultClientId]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!clientId) {
      setError("Veuillez sélectionner un client.");
      return;
    }
    if (!title.trim()) {
      setError("Le titre est requis.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const res = await fetch("/api/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_id: clientId,
          title,
          type,
          amount_usd: parseFloat(amount) || 0,
          date: date || null,
          notes: notes || null,
        }),
      });
      if (!res.ok) throw new Error("Erreur serveur");
      onSuccess();
    } catch {
      setError("Impossible de créer le job. Veuillez réessayer.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-xl border border-gray-200">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h3 className="text-base font-semibold text-gray-900">Nouveau job</h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={(e) => void submit(e)} className="p-6 space-y-4">
          <div>
            <label className={labelCls}>Client *</label>
            <select
              className={inputCls}
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              disabled={loadingClients}
            >
              <option value="">— Sélectionner un client —</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className={labelCls}>Titre du job *</label>
            <input
              className={inputCls}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Excavation fondation, Déneigement entrée..."
              autoFocus
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelCls}>Type de service</label>
              <select
                className={inputCls}
                value={type}
                onChange={(e) => setType(e.target.value as typeof type)}
              >
                <option value="excavation">Excavation</option>
                <option value="deneigement">Déneigement</option>
                <option value="consulting">Consulting IA</option>
              </select>
            </div>
            <div>
              <label className={labelCls}>Montant ($)</label>
              <input
                className={inputCls}
                type="number"
                min="0"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
              />
            </div>
          </div>

          <div>
            <label className={labelCls}>Date prévue</label>
            <input
              className={inputCls}
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </div>

          <div>
            <label className={labelCls}>Notes</label>
            <textarea
              className={`${inputCls} resize-none`}
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Détails supplémentaires..."
            />
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-600">
              {error}
            </p>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              {saving ? "Création..." : "Créer le job"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
