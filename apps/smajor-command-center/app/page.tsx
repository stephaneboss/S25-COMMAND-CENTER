import { CommandCenter } from "@/components/command-center";
import { getCommandCenterSnapshot } from "@/lib/s25-api";

export default async function Page() {
  const snapshot = await getCommandCenterSnapshot();
  return <CommandCenter snapshot={snapshot} />;
}
