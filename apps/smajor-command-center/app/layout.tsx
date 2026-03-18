import "./globals.css";
import type { Metadata } from "next";
import { Navbar } from "@/components/navbar";

export const metadata: Metadata = {
  title: "smajor.org — Excavation & Services",
  description:
    "smajor.org — Entreprise spécialisée en excavation, déneigement et consultation IA au Québec. Services professionnels résidentiels et commerciaux.",
  keywords: "excavation, déneigement, consultation IA, Québec, smajor",
  authors: [{ name: "smajor.org" }],
  openGraph: {
    title: "smajor.org — Excavation & Services",
    description: "Services d'excavation, déneigement et consultation IA au Québec.",
    locale: "fr_CA",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="min-h-[calc(100vh-64px)]">{children}</main>
      </body>
    </html>
  );
}
