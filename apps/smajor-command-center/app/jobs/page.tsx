"use client";

import { useState } from "react";
import { JobsList } from "@/components/jobs-list";
import { NewJobModal } from "@/components/new-job-modal";

export default function JobsPage() {
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
          <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
          <p className="mt-0.5 text-sm text-gray-500">
            Suivez l&apos;avancement de tous vos chantiers et services.
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
          Nouveau job
        </button>
      </div>

      {/* Jobs list with filter tabs */}
      <JobsList key={refreshKey} />

      {/* Modal */}
      {showModal && (
        <NewJobModal
          onClose={() => setShowModal(false)}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  );
}
