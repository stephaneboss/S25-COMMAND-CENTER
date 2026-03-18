import { Dashboard } from "@/components/dashboard";
import { getCommandCenterSnapshot } from "@/lib/s25-api";

/**
 * Main page — shows the Smajor business dashboard.
 * Fetches live S25 snapshot server-side for the initial render.
 * The dashboard component refreshes the S25 status panel every 30s client-side.
 */
export default async function Page() {
  const snapshot = await getCommandCenterSnapshot();
  return <Dashboard snapshot={snapshot} />;
}
