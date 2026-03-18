import { Dashboard } from "@/components/dashboard";
import { getCommandCenterSnapshot } from "@/lib/s25-api";

/**
 * Main dashboard page — fetches S25 snapshot server-side for initial render.
 * The Dashboard component refreshes client-side every 30s.
 */
export default async function Page() {
  const snapshot = await getCommandCenterSnapshot();
  return <Dashboard snapshot={snapshot} />;
}
