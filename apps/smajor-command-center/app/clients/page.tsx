"use client";

import { useState } from "react";
import { ClientsTable } from "@/components/clients-table";
import { NewClientModal } from "@/components/new-client-modal";

export default function ClientsPage() {
  const [showModal, setShowModal] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  function handleSuccess() {
    setShowModal(false);
    setRefreshKey((k) => k + 1);
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Page header */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
          <p className="mt-0.5 text-sm text-gray-500">
            Gérez votre base de clients résidentiels et commerciaux.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 self-start rounded-lg bg-emerald-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-emerald-700 transition-colors sm:self-auto"
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
          Nouveau client
        </button>
      </div>

      {/* Clients table */}
      <ClientsTable key={refreshKey} />

      {/* Modal */}
      {showModal && (
        <NewClientModal
          onClose={() => setShowModal(false)}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  );
}
