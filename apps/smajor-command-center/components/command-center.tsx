import type { CommandCenterSnapshot, MeshRosterEntry } from "@/lib/s25-api";

function statusTone(status: string) {
  if (status === "online") return "bg-neon shadow-neon";
  if (status === "sleep" || status === "rate_limited" || status === "degraded") return "bg-ember";
  return "bg-danger";
}

function HeaderMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="rounded-3xl border border-white/10 bg-panel/70 p-5 shadow-neon">
      <p className="text-xs uppercase tracking-[0.24em] text-neon">{label}</p>
      <h2 className="mt-3 text-3xl font-semibold text-white">{value}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-300">{detail}</p>
    </article>
  );
}

function MeshPanel({ roster }: { roster: MeshRosterEntry[] }) {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-panel/70 p-6 shadow-neon">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.24em] text-neon">Mesh</p>
        <h3 className="mt-2 text-2xl font-semibold">15 agents sous commandement</h3>
      </div>
      <div className="space-y-3">
        {roster.map((agent) => (
          <div
            key={agent.agent_id}
            className="flex items-start justify-between gap-3 rounded-2xl border border-white/10 bg-black/20 px-4 py-3"
          >
            <div>
              <div className="flex items-center gap-3">
                <span className={`mt-0.5 inline-block h-2.5 w-2.5 rounded-full ${statusTone(agent.status)}`} />
                <p className="font-semibold text-white">{agent.agent_id}</p>
              </div>
              <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">
                {agent.role_id} · {agent.badge_id}
              </p>
            </div>
            <p className="text-right text-xs text-slate-300">{agent.action_surface}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function FeedPanel({ snapshot }: { snapshot: CommandCenterSnapshot }) {
  const active = Array.isArray(snapshot.status?.missions)
    ? snapshot.status.missions
    : Array.isArray(snapshot.feed?.feed)
      ? snapshot.feed.feed
      : [];

  const history = Array.isArray(snapshot.feed?.feed) ? snapshot.feed.feed : [];

  return (
    <section className="rounded-[2rem] border border-white/10 bg-panel/70 p-6 shadow-neon">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.24em] text-neon">Terminal / Feed</p>
        <h3 className="mt-2 text-2xl font-semibold">Operations Comet, Merlin, Trinity</h3>
      </div>
      <div className="rounded-3xl border border-white/10 bg-black/40 p-4 font-mono text-sm omega-grid bg-omega-grid">
        <div className="space-y-3">
          {history.slice(0, 10).map((entry: any, index: number) => (
            <div key={`${entry.created_at || index}-${index}`} className="rounded-2xl border border-white/5 bg-black/30 p-3">
              <div className="flex items-center justify-between gap-4 text-[11px] uppercase tracking-[0.18em] text-slate-400">
                <span>{entry.source || "mesh"}</span>
                <span>{entry.level || "info"}</span>
              </div>
              <p className="mt-2 leading-6 text-slate-100">{entry.summary || entry.intent || "Event"}</p>
            </div>
          ))}
          {history.length === 0 && (
            <div className="rounded-2xl border border-white/5 bg-black/30 p-3 text-slate-300">
              Aucun feed public pour l’instant.
            </div>
          )}
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Pipeline</p>
          <p className="mt-2 text-xl font-semibold">{snapshot.status?.pipeline_status || "Unknown"}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Signal</p>
          <p className="mt-2 text-xl font-semibold">{snapshot.status?.arkon5_action || "Unknown"}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-400">Missions actives</p>
          <p className="mt-2 text-xl font-semibold">{snapshot.status?.missions_active ?? 0}</p>
        </div>
      </div>
    </section>
  );
}

function FinancePanel({ snapshot }: { snapshot: CommandCenterSnapshot }) {
  const deployments = Array.isArray(snapshot.infra?.deployments) ? snapshot.infra.deployments : [];
  const bars = [
    { label: "MEXC readiness", value: snapshot.vault?.mode === "armed_readiness" ? 68 : 32, accent: "bg-neon" },
    { label: "CPU cluster", value: Number(snapshot.infra?.cluster?.cpu_ready || 0) * 20, accent: "bg-sky-400" },
    { label: "GPU tracked", value: Number(snapshot.infra?.cluster?.gpu_tracked || 0) * 24, accent: "bg-fuchsia-400" },
  ];

  return (
    <section className="rounded-[2rem] border border-white/10 bg-panel/70 p-6 shadow-neon">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.24em] text-neon">Finance / Infra</p>
        <h3 className="mt-2 text-2xl font-semibold">Rentabilite vs cout de guerre</h3>
      </div>
      <div className="space-y-4">
        {bars.map((bar) => (
          <div key={bar.label}>
            <div className="mb-2 flex items-center justify-between text-sm text-slate-300">
              <span>{bar.label}</span>
              <span>{bar.value}%</span>
            </div>
            <div className="h-3 rounded-full bg-white/10">
              <div className={`h-3 rounded-full ${bar.accent}`} style={{ width: `${Math.min(bar.value, 100)}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="mt-6 space-y-3">
        {deployments.map((deployment: any) => (
          <div key={deployment.dseq} className="rounded-2xl border border-white/10 bg-black/20 p-4">
            <p className="font-semibold text-white">{deployment.label}</p>
            <p className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-400">
              {deployment.dseq} · {deployment.provider}
            </p>
            <p className="mt-2 text-sm text-slate-300">{deployment.role} · {deployment.uptime_state}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function CommandCenter({ snapshot }: { snapshot: CommandCenterSnapshot }) {
  const roster = Array.isArray(snapshot.mesh?.roster) ? snapshot.mesh.roster : [];

  return (
    <main className="omega-shell min-h-screen px-4 py-8 md:px-8">
      <div className="mx-auto max-w-[1680px]">
        <header className="mb-8 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-neon">S25 Supreme Architecture</p>
            <h1 className="mt-3 text-5xl font-semibold tracking-tight text-white md:text-7xl">
              Major Control Center
            </h1>
            <p className="mt-4 max-w-3xl text-base leading-7 text-slate-300">
              smajor.org devient un organisme vivant: mesh actif, runtime Akash, vault de trade, gouvernance stricte et
              surfaces operatoires pour le business reel.
            </p>
          </div>
          <div className="rounded-3xl border border-neon/30 bg-black/30 px-5 py-4 text-sm text-slate-300 shadow-neon">
            <p className="text-xs uppercase tracking-[0.24em] text-neon">Doctrine</p>
            <p className="mt-2">Akash-first · S25 mesh source de verite · RBAC par id-role-badge-scope</p>
          </div>
        </header>

        <section className="mb-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <HeaderMetric
            label="Uptime S25"
            value={snapshot.status?.pipeline_status || "Unknown"}
            detail={snapshot.status?.summary_fr || "Le hub attend le cockpit public."}
          />
          <HeaderMetric
            label="Nabu Casa / HA"
            value={snapshot.status?.ha_connected ? "Linked" : "Lateral"}
            detail={snapshot.status?.error || "HA reste lateral et ne gouverne pas la base."}
          />
          <HeaderMetric
            label="Vault MEXC"
            value={snapshot.vault?.mode || "Cold"}
            detail={snapshot.vault?.profitability?.data_state || "Binding exchange en cours."}
          />
          <HeaderMetric
            label="Akash"
            value={`${snapshot.infra?.cluster?.cpu_ready ?? 0} CPU / ${snapshot.infra?.cluster?.gpu_tracked ?? 0} GPU`}
            detail={snapshot.infra?.cluster?.doctrine || "Runtime distribue."}
          />
        </section>

        <section className="grid gap-4 xl:grid-cols-[0.95fr_1.25fr_1fr]">
          <MeshPanel roster={roster} />
          <FeedPanel snapshot={snapshot} />
          <FinancePanel snapshot={snapshot} />
        </section>
      </div>
    </main>
  );
}
