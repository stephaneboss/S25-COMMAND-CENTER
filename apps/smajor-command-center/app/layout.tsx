import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Smajor Command Center",
  description: "Dashboard souverain S25 Lumiere pour operations, agents, vault et Akash.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
