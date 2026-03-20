import type { JobStatus } from "@/lib/db";

const colors: Record<JobStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  active: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
};

const labels: Record<JobStatus, string> = {
  pending: "En attente",
  active: "En cours",
  completed: "Terminé",
};

export function JobStatusBadge({ status }: { status: JobStatus }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status]}`}
    >
      {labels[status]}
    </span>
  );
}
