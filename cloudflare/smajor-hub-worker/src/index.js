function layout({ title, eyebrow, heroTitle, heroText, ctas, blocks, tone = "public" }) {
  const accent = tone === "app" ? "#7cf6d4" : "#ffd166";
  const bg = tone === "app"
    ? "radial-gradient(circle at top, #133b33 0%, #071311 44%, #030807 100%)"
    : "radial-gradient(circle at top, #423111 0%, #120d04 42%, #070503 100%)";

  const ctaHtml = ctas.map(
    (cta) =>
      `<a class="cta ${cta.kind || "primary"}" href="${cta.href}">${cta.label}</a>`
  ).join("");

  const blocksHtml = blocks.map(
    (block) => `
      <article class="card">
        <div class="label">${block.label}</div>
        <h3>${block.title}</h3>
        <p>${block.text}</p>
        ${block.links ? `<div class="links">${block.links.map((link) => `<a href="${link.href}">${link.label}</a>`).join("")}</div>` : ""}
      </article>
    `
  ).join("");

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
        width: min(1180px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 28px 0 56px;
      }
      .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        margin-bottom: 38px;
        font-size: 14px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
      .brand { font-weight: 700; }
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
        grid-template-columns: 1.5fr 1fr;
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
      .hero-copy p, .card p {
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
      .footer {
        margin-top: 24px;
        color: var(--muted);
        font-size: 14px;
      }
      @media (max-width: 900px) {
        .hero, .grid { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <div class="topbar">
        <div class="brand">SMAJOR</div>
        <div>Cloudflare facade · Akash runtime · S25 mesh</div>
      </div>
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

function renderPublic(env) {
  return layout({
    title: "Smajor",
    eyebrow: "Entreprise multi-service + IA industrielle",
    heroTitle: "Unifier l’entreprise réelle et le système S25.",
    heroText:
      "Smajor devient la facade unique pour l’excavation, le déneigement, l’automatisation métier et l’infrastructure IA. Les clients voient une entreprise claire. Le mesh S25 fait tourner la machine derrière.",
    ctas: [
      { label: "Entrer dans l’app", href: env.PUBLIC_APP_URL },
      { label: "Cockpit S25", href: env.PUBLIC_S25_URL, kind: "secondary" },
      { label: "MERLIN MCP", href: `${env.PUBLIC_MERLIN_URL}/health`, kind: "secondary" },
    ],
    blocks: [
      {
        label: "Public",
        title: "Services terrain",
        text: "Excavation, déneigement, demandes client, suivi des opérations et portail de service.",
        links: [
          { label: "Excavation", href: "/#excavation" },
          { label: "Déneigement", href: "/#deneigement" },
        ],
      },
      {
        label: "Ops",
        title: "Backend S25",
        text: "Le cockpit public, les missions, le feed intel et le mesh multi-agent restent centralisés sur Akash.",
        links: [
          { label: "Status", href: `${env.PUBLIC_S25_URL}/api/status` },
          { label: "Mesh", href: `${env.PUBLIC_S25_URL}/api/mesh/status` },
        ],
      },
      {
        label: "IA",
        title: "MERLIN + TRINITY",
        text: "MERLIN valide, TRINITY orchestre, COMET surveille, KIMI capte le Web3. Le domaine ne remplace pas le mesh, il le rend présentable.",
        links: [
          { label: "MERLIN health", href: `${env.PUBLIC_MERLIN_URL}/health` },
          { label: "API", href: `${env.PUBLIC_API_URL}/api/version` },
        ],
      },
    ],
  });
}

function renderApp(env) {
  return layout({
    title: "Smajor Ops",
    eyebrow: "Shell d’opérations",
    heroTitle: "Une salle d’opérations pour tenir toute la stack.",
    heroText:
      "Ce shell est le futur point d’entrée pour le backoffice, les portails métiers et le pilotage agent. Pour l’instant, il centralise les routes stables qui comptent vraiment.",
    ctas: [
      { label: "Status public", href: `${env.PUBLIC_S25_URL}/api/status` },
      { label: "Missions", href: `${env.PUBLIC_S25_URL}/api/missions`, kind: "secondary" },
      { label: "MERLIN MCP", href: `${env.PUBLIC_MERLIN_URL}/health`, kind: "secondary" },
    ],
    blocks: [
      {
        label: "Clients",
        title: "Portail client",
        text: "Réservé pour demandes de service, devis, facturation et suivi d’intervention.",
      },
      {
        label: "Interne",
        title: "Backoffice",
        text: "Réservé pour admin, dispatch, employés, fournisseurs et règles d’automatisation.",
      },
      {
        label: "Infra",
        title: "S25 Mesh",
        text: "La vérité opérationnelle reste sur le cockpit S25 et le bridge MCP MERLIN, pas dans l’interface seule.",
        links: [
          { label: "Cockpit", href: env.PUBLIC_S25_URL },
          { label: "API", href: env.PUBLIC_API_URL },
        ],
      },
    ],
    tone: "app",
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
      });
    }

    if (hostname === "app.smajor.org") {
      return responseHtml(renderApp(env));
    }

    return responseHtml(renderPublic(env));
  },
};
