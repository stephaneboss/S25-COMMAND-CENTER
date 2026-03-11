const APP_SECTIONS = {
  "/": {
    label: "Overview",
    eyebrow: "Shell d'operations",
    heroTitle: "Une salle d'operations pour tenir toute la stack.",
    heroText:
      "Le shell d'operations relie les portails metier, le cockpit S25, MERLIN MCP et la future gestion business sur un seul plan de travail.",
    cards: [
      {
        label: "Ops",
        title: "Salle d'operations",
        text: "Point d'entree pour piloter le business, lire le mesh et surveiller les automatismes.",
      },
      {
        label: "Architecture",
        title: "S25 reste le backend",
        text: "Le shell ne remplace pas S25. Il organise les points d'entree humains au-dessus du mesh Akash.",
      },
      {
        label: "Priorite",
        title: "Visibilite totale",
        text: "Le but est de rendre l'ensemble lisible: clients, staff, fournisseurs, IA et missions.",
      },
    ],
  },
  "/clients": {
    label: "Clients",
    eyebrow: "Portail client",
    heroTitle: "Donner aux clients une interface propre, pas le chaos du backend.",
    heroText:
      "Le portail client doit couvrir demandes de service, devis, facturation, suivi et communication sans exposer la complexite du mesh.",
    cards: [
      {
        label: "MVP",
        title: "Demandes et suivi",
        text: "Creer un dossier, suivre un service, recuperer un devis, consulter facture et etat du contrat.",
      },
      {
        label: "S25",
        title: "Automatisation metier",
        text: "Les relances, le routage et les escalades doivent etre portes par S25, pas par du bricolage front-end.",
      },
      {
        label: "Suite",
        title: "Historique client",
        text: "A terme: historique de services, photos terrain, documents signes et rappels automatiques.",
      },
    ],
  },
  "/admin": {
    label: "Admin",
    eyebrow: "Backoffice",
    heroTitle: "Un vrai poste de commandement pour l'entreprise.",
    heroText:
      "Le backoffice centralise l'administration, les regles d'agents, le dispatch, les permissions et les tableaux de bord critiques.",
    cards: [
      {
        label: "Controle",
        title: "Regles et permissions",
        text: "Qui peut lancer quoi, quelles actions restent humaines, et quand l'automatisation doit s'arreter.",
      },
      {
        label: "Pilotage",
        title: "Etat live",
        text: "Le backoffice doit afficher le status S25, les missions, les alertes et l'etat des portails metier.",
      },
      {
        label: "Finance",
        title: "Facturation et marges",
        text: "Plus tard: marge chantier, couts fournisseurs, flux de cash, suivis de paiement et priorites commerciales.",
      },
    ],
  },
  "/staff": {
    label: "Staff",
    eyebrow: "Execution terrain",
    heroTitle: "Un portail clair pour l'equipe, pas un terminal pour nerds.",
    heroText:
      "L'espace staff doit servir au dispatch, aux horaires, aux rapports terrain et aux consignes sans exiger de comprendre l'infra.",
    cards: [
      {
        label: "Terrain",
        title: "Taches et rapports",
        text: "Recevoir des affectations, confirmer un depart, envoyer un rapport et signaler une anomalie.",
      },
      {
        label: "Coordination",
        title: "Dispatch vivant",
        text: "Le futur dispatch doit relier planning, GPS, clients, materiel et evenements meteo.",
      },
      {
        label: "IA",
        title: "Aide terrain",
        text: "S25 peut plus tard preparer les briefs de chantier et les resumes de fin de journee.",
      },
    ],
  },
  "/vendors": {
    label: "Vendors",
    eyebrow: "Fournisseurs",
    heroTitle: "Stabiliser la chaine d'approvisionnement.",
    heroText:
      "L'espace fournisseurs sert a suivre les pieces, materiaux, locations, bons de commande et documents critiques.",
    cards: [
      {
        label: "Supply",
        title: "Commandes et documents",
        text: "Centraliser commandes, prix, contacts, confirmations et documents d'achat.",
      },
      {
        label: "Ops",
        title: "Visibilite cout",
        text: "Raccrocher les couts fournisseurs a la realite de terrain et aux contrats clients.",
      },
      {
        label: "Suite",
        title: "Workflow achat",
        text: "Plus tard: approbation par role, seuils budget, relances et comparatifs fournisseurs.",
      },
    ],
  },
  "/ai": {
    label: "AI",
    eyebrow: "Branche agents",
    heroTitle: "Faire des agents des responsables de fonction, pas juste des demos.",
    heroText:
      "La branche AI doit exposer les interfaces utiles: missions, feed intel, cockpit, MCP et futurs outils d'automatisation business.",
    cards: [
      {
        label: "Agents",
        title: "Roles clairs",
        text: "TRINITY orchestre, MERLIN valide, COMET surveille, KIMI capte, ORACLE confirme, ONCHAIN_GUARDIAN surveille.",
      },
      {
        label: "Backends",
        title: "S25 + MERLIN",
        text: "Le mesh est la source de verite; le MCP et le cockpit sont les surfaces publiques stables.",
      },
      {
        label: "Evolution",
        title: "Entreprise augmentee",
        text: "A terme, cette branche doit piloter facturation, CRM, operations et automations multi-outils.",
      },
    ],
  },
};

function navigation(hostname) {
  const appBase = hostname === "app.smajor.org" ? "" : "https://app.smajor.org";
  return [
    { label: "Overview", href: `${appBase}/` },
    { label: "Clients", href: `${appBase}/clients` },
    { label: "Admin", href: `${appBase}/admin` },
    { label: "Staff", href: `${appBase}/staff` },
    { label: "Vendors", href: `${appBase}/vendors` },
    { label: "AI", href: `${appBase}/ai` },
  ];
}

function layout({
  title,
  eyebrow,
  heroTitle,
  heroText,
  ctas,
  blocks,
  liveBlocks = [],
  tone = "public",
  nav = [],
  activePath = "/",
}) {
  const accent = tone === "app" ? "#7cf6d4" : "#ffd166";
  const bg = tone === "app"
    ? "radial-gradient(circle at top, #133b33 0%, #071311 44%, #030807 100%)"
    : "radial-gradient(circle at top, #423111 0%, #120d04 42%, #070503 100%)";

  const ctaHtml = ctas
    .map((cta) => `<a class="cta ${cta.kind || "primary"}" href="${cta.href}">${cta.label}</a>`)
    .join("");

  const navHtml = nav
    .map((item) => `<a class="nav-link ${item.active ? "active" : ""}" href="${item.href}">${item.label}</a>`)
    .join("");

  const blocksHtml = blocks
    .map(
      (block) => `
        <article class="card">
          <div class="label">${block.label}</div>
          <h3>${block.title}</h3>
          <p>${block.text}</p>
          ${
            block.links
              ? `<div class="links">${block.links
                  .map((link) => `<a href="${link.href}">${link.label}</a>`)
                  .join("")}</div>`
              : ""
          }
        </article>
      `,
    )
    .join("");

  const liveBlocksHtml = liveBlocks.length
    ? `
      <section class="live-panel">
        <div class="section-head">
          <div>
            <div class="label">Live S25</div>
            <h2>Panneaux operations</h2>
          </div>
          <p>Le shell lit le cockpit public et affiche la realite du mesh sans inventer un faux statut front-end.</p>
        </div>
        <div class="grid live-grid">${liveBlocks
          .map(
            (block) => `
              <article class="card live-card">
                <div class="label">${block.label}</div>
                <h3>${block.title}</h3>
                <p>${block.text}</p>
                ${
                  block.metrics
                    ? `<div class="metrics">${block.metrics
                        .map(
                          (metric) => `
                            <div class="metric">
                              <span>${metric.label}</span>
                              <strong>${metric.value}</strong>
                            </div>
                          `,
                        )
                        .join("")}</div>`
                    : ""
                }
                ${
                  block.links
                    ? `<div class="links">${block.links
                        .map((link) => `<a href="${link.href}">${link.label}</a>`)
                        .join("")}</div>`
                    : ""
                }
              </article>
            `,
          )
          .join("")}
        </div>
      </section>
    `
    : "";

  return `<!doctype html>
  <html lang="fr">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${title}</title>
    <style>
      :root {
        --bg: ${bg};
        --panel: rgba(255,255,255,0.06);
        --line: rgba(255,255,255,0.15);
        --text: #f7f3e8;
        --muted: #d2c7b2;
        --accent: ${accent};
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        min-height: 100vh;
        font-family: Georgia, "Times New Roman", serif;
        color: var(--text);
        background: var(--bg);
      }
      .shell {
        width: min(1200px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 28px 0 56px;
      }
      .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        margin-bottom: 20px;
        font-size: 14px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .brand { font-weight: 700; }
      .nav {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 18px;
      }
      .nav-link {
        text-decoration: none;
        color: var(--text);
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 9px 12px;
        background: rgba(255,255,255,0.03);
        font-size: 14px;
      }
      .nav-link.active {
        border-color: var(--accent);
        color: var(--accent);
      }
      .eyebrow {
        display: inline-block;
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 8px 12px;
        color: var(--accent);
        background: rgba(255,255,255,0.04);
        margin-bottom: 16px;
      }
      .hero {
        display: grid;
        grid-template-columns: 1.45fr 1fr;
        gap: 22px;
        margin-bottom: 24px;
      }
      .hero-copy, .hero-panel, .card {
        border: 1px solid var(--line);
        background: var(--panel);
        backdrop-filter: blur(10px);
        border-radius: 28px;
        padding: 24px;
      }
      h1 {
        font-size: clamp(38px, 7vw, 74px);
        line-height: 0.95;
        margin: 0 0 16px;
      }
      h2 {
        margin: 6px 0 0;
        font-size: 30px;
      }
      .hero-copy p, .card p, .section-head p {
        color: var(--muted);
        line-height: 1.55;
        margin: 0;
      }
      .cta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 22px;
      }
      .cta {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 44px;
        padding: 0 16px;
        border-radius: 999px;
        text-decoration: none;
        color: #07110f;
        background: var(--accent);
        font-weight: 700;
      }
      .cta.secondary {
        background: transparent;
        color: var(--text);
        border: 1px solid var(--line);
      }
      .hero-panel ul {
        margin: 0;
        padding-left: 18px;
        color: var(--muted);
        line-height: 1.75;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 18px;
      }
      .live-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
      .label {
        font-size: 12px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 10px;
      }
      .card h3 {
        margin: 0 0 12px;
        font-size: 24px;
      }
      .links {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 18px;
      }
      .links a {
        color: var(--text);
        text-decoration: none;
        border-bottom: 1px solid var(--accent);
      }
      .live-panel {
        margin-top: 20px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.04);
        border-radius: 28px;
        padding: 24px;
      }
      .section-head {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 18px;
      }
      .metrics {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
        margin-top: 18px;
      }
      .metric {
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 12px 14px;
        background: rgba(255,255,255,0.03);
      }
      .metric span {
        display: block;
        color: var(--muted);
        font-size: 12px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
      }
      .metric strong {
        font-size: 24px;
      }
      .footer {
        margin-top: 24px;
        color: var(--muted);
        font-size: 14px;
      }
      @media (max-width: 900px) {
        .hero, .grid, .live-grid, .metrics { grid-template-columns: 1fr; }
        .section-head, .topbar { flex-direction: column; align-items: flex-start; }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <div class="topbar">
        <div class="brand">SMAJOR</div>
        <div>Cloudflare facade · Akash runtime · S25 mesh · ${activePath.replace("/", "") || "public"}</div>
      </div>
      ${nav.length ? `<nav class="nav">${navHtml}</nav>` : ""}
      <section class="hero">
        <div class="hero-copy">
          <div class="eyebrow">${eyebrow}</div>
          <h1>${heroTitle}</h1>
          <p>${heroText}</p>
          <div class="cta-row">${ctaHtml}</div>
        </div>
        <aside class="hero-panel">
          <div class="label">Etat de la base</div>
          <ul>
            <li>Facade domaine sur <strong>smajor.org</strong></li>
            <li>Backend S25 sur Akash</li>
            <li>MERLIN via MCP live</li>
            <li>Home Assistant conserve en lateral</li>
            <li>Le mesh reste la source de verite</li>
          </ul>
        </aside>
      </section>
      <section class="grid">${blocksHtml}</section>
      ${liveBlocksHtml}
      <div class="footer">Smajor est la facade. S25 Lumiere reste le backend central multi-agent.</div>
    </main>
  </body>
  </html>`;
}

function responseHtml(html) {
  return new Response(html, {
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
    },
  });
}

async function fetchJson(url) {
  const response = await fetch(url, {
    headers: {
      accept: "application/json",
      "user-agent": "smajor-hub/1.0",
    },
    cf: {
      cacheTtl: 15,
      cacheEverything: false,
    },
  });

  if (!response.ok) {
    throw new Error(`upstream_${response.status}`);
  }

  return response.json();
}

async function fetchOpsSnapshot(env) {
  const [statusResult, missionsResult, meshResult] = await Promise.allSettled([
    fetchJson(`${env.PUBLIC_S25_URL}/api/status`),
    fetchJson(`${env.PUBLIC_S25_URL}/api/missions`),
    fetchJson(`${env.PUBLIC_S25_URL}/api/mesh/status`),
  ]);

  return {
    status: statusResult.status === "fulfilled" ? statusResult.value : null,
    missions: missionsResult.status === "fulfilled" ? missionsResult.value : null,
    mesh: meshResult.status === "fulfilled" ? meshResult.value : null,
    errors: [statusResult, missionsResult, meshResult]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "upstream_error"),
  };
}

function buildLiveBlocks(env, snapshot) {
  const status = snapshot.status || {};
  const missions = snapshot.missions || {};
  const mesh = snapshot.mesh?.mesh || {};
  const agents = mesh.agents || {};
  const onlineAgents = Object.entries(agents)
    .filter(([, agent]) => agent?.status === "online")
    .map(([name]) => name);
  const activeMissions = Array.isArray(missions.active) ? missions.active : [];
  const recentHistory = Array.isArray(missions.history) ? missions.history : [];

  return [
    {
      label: "Status",
      title: status.pipeline_status || "Snapshot indisponible",
      text:
        status.summary_fr ||
        "Le shell attend le retour du cockpit public pour afficher l'etat live du mesh.",
      metrics: [
        { label: "Agents online", value: String(status.mesh_agents_online ?? onlineAgents.length ?? 0) },
        { label: "Missions actives", value: String(status.missions_active ?? activeMissions.length ?? 0) },
        { label: "Signal", value: status.arkon5_action || status.system?.signal || "--" },
        { label: "Tunnel", value: status.system?.tunnel || (status.tunnel_active ? "online" : "offline") },
      ],
      links: [
        { label: "Status JSON", href: `${env.PUBLIC_S25_URL}/api/status` },
        { label: "Mesh JSON", href: `${env.PUBLIC_S25_URL}/api/mesh/status` },
      ],
    },
    {
      label: "Missions",
      title: activeMissions[0]?.intent || "Aucune mission prioritaire visible",
      text:
        activeMissions[0]?.target
          ? `Agent recommande: ${activeMissions[0].recommended_agent || activeMissions[0].target}. Priorite: ${activeMissions[0].priority || "n/a"}.`
          : "Le shell affichera ici la mission de tete, son agent recommande et la priorite de traitement.",
      metrics: [
        { label: "Actives", value: String(activeMissions.length) },
        { label: "Historique", value: String(recentHistory.length) },
        { label: "Top target", value: activeMissions[0]?.target || "--" },
        { label: "Top type", value: activeMissions[0]?.task_type || "--" },
      ],
      links: [
        { label: "Missions", href: `${env.PUBLIC_S25_URL}/api/missions` },
      ],
    },
    {
      label: "Mesh",
      title: onlineAgents.slice(0, 4).join(" · ") || "Agents en cours de remontée",
      text:
        status.comet_intel ||
        "COMET et les autres agents rempliront ce panneau quand le cockpit remonte une lecture intel stable.",
      metrics: [
        { label: "BTC", value: status.btc_usd ? `$${Math.round(status.btc_usd)}` : "--" },
        { label: "ETH", value: status.eth_usd ? `$${Math.round(status.eth_usd)}` : "--" },
        { label: "Confiance", value: status.arkon5_conf != null ? `${status.arkon5_conf}` : "--" },
        { label: "HA lateral", value: status.ha_connected ? "linked" : "off" },
      ],
      links: [
        { label: "MERLIN MCP", href: `${env.PUBLIC_MERLIN_URL}/health` },
        { label: "API", href: `${env.PUBLIC_API_URL}/api/version` },
      ],
    },
    {
      label: "Resilience",
      title: snapshot.errors.length ? "Degradation partielle detectee" : "Facade et mesh alignes",
      text: snapshot.errors.length
        ? `Le shell a detecte ${snapshot.errors.length} erreur(s) upstream: ${snapshot.errors.join(", ")}.`
        : "Le domaine public, le cockpit Akash et MERLIN MCP repondent dans le meme modele operationnel.",
      metrics: [
        { label: "Facade", value: "Cloudflare" },
        { label: "Runtime", value: "Akash" },
        { label: "Backend", value: "S25" },
        { label: "Mode", value: "Mesh-first" },
      ],
      links: [
        { label: "Cockpit", href: env.PUBLIC_S25_URL },
        { label: "Public API", href: `${env.PUBLIC_API_URL}/api/version` },
      ],
    },
  ];
}

function renderPublic(env) {
  return layout({
    title: "Smajor",
    eyebrow: "Entreprise multi-service + IA industrielle",
    heroTitle: "Unifier l'entreprise reelle et le systeme S25.",
    heroText:
      "Smajor devient la facade unique pour l'excavation, le deneigement, l'automatisation metier et l'infrastructure IA. Les clients voient une entreprise claire. Le mesh S25 fait tourner la machine derriere.",
    ctas: [
      { label: "Entrer dans l'app", href: env.PUBLIC_APP_URL },
      { label: "Cockpit S25", href: env.PUBLIC_S25_URL, kind: "secondary" },
      { label: "MERLIN MCP", href: `${env.PUBLIC_MERLIN_URL}/health`, kind: "secondary" },
    ],
    blocks: [
      {
        label: "Public",
        title: "Services terrain",
        text: "Excavation, deneigement, demandes client, suivi des operations et portail de service.",
        links: [
          { label: "Excavation", href: "https://app.smajor.org/clients" },
          { label: "Deneigement", href: "https://app.smajor.org/clients" },
        ],
      },
      {
        label: "Ops",
        title: "Backend S25",
        text: "Le cockpit public, les missions, le feed intel et le mesh multi-agent restent centralises sur Akash.",
        links: [
          { label: "Status", href: `${env.PUBLIC_S25_URL}/api/status` },
          { label: "Mesh", href: `${env.PUBLIC_S25_URL}/api/mesh/status` },
        ],
      },
      {
        label: "IA",
        title: "MERLIN + TRINITY",
        text: "MERLIN valide, TRINITY orchestre, COMET surveille, KIMI capte le Web3. Le domaine ne remplace pas le mesh, il le rend presentable.",
        links: [
          { label: "MERLIN health", href: `${env.PUBLIC_MERLIN_URL}/health` },
          { label: "API", href: `${env.PUBLIC_API_URL}/api/version` },
        ],
      },
    ],
  });
}

function renderApp(env, pathname, hostname, snapshot) {
  const section = APP_SECTIONS[pathname] || APP_SECTIONS["/"];
  return layout({
    title: `Smajor Ops - ${section.label}`,
    eyebrow: section.eyebrow,
    heroTitle: section.heroTitle,
    heroText: section.heroText,
    ctas: [
      { label: "Status public", href: `${env.PUBLIC_S25_URL}/api/status` },
      { label: "Missions", href: `${env.PUBLIC_S25_URL}/api/missions`, kind: "secondary" },
      { label: "MERLIN MCP", href: `${env.PUBLIC_MERLIN_URL}/health`, kind: "secondary" },
    ],
    blocks: section.cards,
    liveBlocks: buildLiveBlocks(env, snapshot),
    tone: "app",
    nav: navigation(hostname).map((item) => ({
      ...item,
      active: item.href.endsWith(pathname) || (pathname === "/" && item.href.endsWith("/")),
    })),
    activePath: pathname,
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const hostname = url.hostname.toLowerCase();

    if (url.pathname === "/health") {
      return jsonResponse({
        ok: true,
        service: "smajor-hub",
        hostname,
        app_url: env.PUBLIC_APP_URL,
        api_url: env.PUBLIC_API_URL,
        s25_url: env.PUBLIC_S25_URL,
        merlin_url: env.PUBLIC_MERLIN_URL,
        app_sections: Object.keys(APP_SECTIONS),
      });
    }

    if (url.pathname === "/manifest.json") {
      return jsonResponse({
        name: "Smajor Ops",
        short_name: "Smajor",
        start_url: "/",
        display: "standalone",
        background_color: "#071311",
        theme_color: "#7cf6d4",
      });
    }

    if (hostname === "app.smajor.org") {
      const snapshot = await fetchOpsSnapshot(env);
      return responseHtml(renderApp(env, url.pathname, hostname, snapshot));
    }

    return responseHtml(renderPublic(env));
  },
};
