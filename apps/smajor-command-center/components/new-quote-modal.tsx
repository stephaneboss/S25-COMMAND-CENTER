"use client";

import { useState, useEffect } from "react";
import type { Client, QuoteItem } from "@/lib/db";

interface NewQuoteModalProps {
  onClose: () => void;
  onCreated: () => void;
}

const inputCls =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 transition-colors";

const labelCls = "block text-xs font-medium text-gray-600 mb-1";

interface LineItem {
  description: string;
  qty: string;
  unit_price: string;
}

function emptyLine(): LineItem {
  return { description: "", qty: "1", unit_price: "" };
}

function lineToQuoteItem(line: LineItem): QuoteItem {
  const quantity = parseFloat(line.qty) || 1;
  const unit_price = parseFloat(line.unit_price) || 0;
  return {
    description: line.description,
    quantity,
    unit_price,
    total: quantity * unit_price,
  };
}

function computeTotal(lines: LineItem[]): number {
  return lines.reduce((sum, l) => {
    const qty = parseFloat(l.qty) || 0;
    const price = parseFloat(l.unit_price) || 0;
    return sum + qty * price;
  }, 0);
}

export function NewQuoteModal({ onClose, onCreated }: NewQuoteModalProps) {
  const [clientId, setClientId] = useState("");
  const [lines, setLines] = useState<LineItem[]>([emptyLine()]);
  const [validUntil, setValidUntil] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [clients, setClients] = useState<Client[]>([]);
  const [loadingClients, setLoadingClients] = useState(true);

  useEffect(() => {
    fetch("/api/clients")
      .then((r) => r.json() as Promise<{ clients: Client[] }>)
      .then((d) => setClients(d.clients ?? []))
      .catch(() => null)
      .finally(() => setLoadingClients(false));
  }, []);

  function updateLine(index: number, field: keyof LineItem, value: string) {
    setLines((prev) =>
      prev.map((l, i) => (i === index ? { ...l, [field]: value } : l))
    );
  }

  function addLine() {
    setLines((prev) => [...prev, emptyLine()]);
  }

  function removeLine(index: number) {
    setLines((prev) => prev.filter((_, i) => i !== index));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!clientId) {
      setError("Veuillez sélectionner un client.");
      return;
    }
    if (lines.length === 0) {
      setError("Ajoutez au moins une ligne au devis.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const items = lines.map(lineToQuoteItem);
      const amount_usd = computeTotal(lines);
      const res = await fetch("/api/quotes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          client_id: clientId,
          items,
          amount_usd,
          valid_until: validUntil || null,
        }),
      });
      if (!res.ok) throw new Error("Erreur serveur");
      onCreated();
    } catch {
      setError("Impossible de créer le devis. Veuillez réessayer.");
    } finally {
      setSaving(false);
    }
  }

  const total = computeTotal(lines);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-xl rounded-2xl bg-white shadow-xl border border-gray-200 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4 shrink-0">
          <h3 className="text-base font-semibold text-gray-900">Nouveau devis</h3>
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

        {/* Scrollable form body */}
        <form
          id="new-quote-form"
          onSubmit={(e) => void submit(e)}
          className="p-6 space-y-4 overflow-y-auto flex-1"
        >
          {/* Client selector */}
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

          {/* Line items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className={labelCls}>Lignes du devis *</label>
              <button
                type="button"
                onClick={addLine}
                className="text-xs font-medium text-emerald-600 hover:text-emerald-700"
              >
                + Ajouter une ligne
              </button>
            </div>

            <div className="space-y-2">
              {/* Column headers */}
              <div className="grid grid-cols-12 gap-2 px-0.5">
                <span className="col-span-6 text-xs text-gray-400 font-medium">Description</span>
                <span className="col-span-2 text-xs text-gray-400 font-medium text-right">Qté</span>
                <span className="col-span-3 text-xs text-gray-400 font-medium text-right">Prix unit.</span>
                <span className="col-span-1" />
              </div>

              {lines.map((line, i) => (
                <div key={i} className="grid grid-cols-12 gap-2 items-center">
                  <input
                    className={`${inputCls} col-span-6`}
                    value={line.description}
                    onChange={(e) => updateLine(i, "description", e.target.value)}
                    placeholder="Description du service"
                  />
                  <input
                    className={`${inputCls} col-span-2 text-right`}
                    type="number"
                    min="0"
                    step="0.01"
                    value={line.qty}
                    onChange={(e) => updateLine(i, "qty", e.target.value)}
                    placeholder="1"
                  />
                  <input
                    className={`${inputCls} col-span-3 text-right`}
                    type="number"
                    min="0"
                    step="0.01"
                    value={line.unit_price}
                    onChange={(e) => updateLine(i, "unit_price", e.target.value)}
                    placeholder="0.00"
                  />
                  <div className="col-span-1 flex justify-center">
                    {lines.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeLine(i)}
                        className="text-gray-300 hover:text-red-400 transition-colors"
                        title="Retirer cette ligne"
                      >
                        <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Auto-computed total */}
            <div className="flex justify-end mt-3 pt-3 border-t border-gray-100">
              <span className="text-sm text-gray-500 mr-3">Total</span>
              <span className="text-sm font-bold text-gray-900">
                ${total.toLocaleString("fr-CA", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          </div>

          {/* Valid until */}
          <div>
            <label className={labelCls}>Valide jusqu&apos;au</label>
            <input
              className={inputCls}
              type="date"
              value={validUntil}
              onChange={(e) => setValidUntil(e.target.value)}
            />
          </div>

          {/* Notes */}
          <div>
            <label className={labelCls}>Notes</label>
            <textarea
              className={`${inputCls} resize-none`}
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Conditions, remarques..."
            />
          </div>

          {error && (
            <p className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-600">
              {error}
            </p>
          )}
        </form>

        {/* Footer actions — outside scroll area */}
        <div className="px-6 pb-6 pt-2 flex gap-3 border-t border-gray-100 shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-lg border border-gray-300 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Annuler
          </button>
          <button
            type="submit"
            form="new-quote-form"
            disabled={saving}
            className="flex-1 rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
          >
            {saving ? "Création..." : "Créer le devis"}
          </button>
        </div>
      </div>
    </div>
  );
}
