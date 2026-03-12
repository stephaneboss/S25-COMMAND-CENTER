const HOP_BY_HOP_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "host",
]);

const RETRYABLE_STATUS_CODES = new Set([502, 503, 504]);
const ALLOWED_PATH_PREFIXES = ["/api/", "/health", "/favicon.ico"];
const BUSINESS_PREFIX = "/api/business";
const MASTER_WALLET_ADDRESS = "akash1mw0trq8xgmdyqqjn482r9pfr05hfw06rzq2u9v";

const BUSINESS_REGISTRIES = {
  clients: {
    title: "Clients registry MVP",
    description: "Registre minimum pour nouveaux clients, sans reprendre l'ancien hiver.",
    records: [
      "client_id",
      "organization_name",
      "contact_name",
      "contact_channel",
      "service_address",
      "service_type",
      "account_status",
    ],
    workflows: [
      "create_client",
      "activate_services",
      "attach_quote",
      "attach_job",
      "invoice_and_collect",
    ],
  },
  jobs: {
    title: "Jobs registry MVP",
    description: "Registre des interventions terrain en execution.",
    records: [
      "job_id",
      "client_id",
      "service_type",
      "assigned_team",
      "equipment_required",
      "scheduled_window",
      "job_status",
    ],
    workflows: [
      "open_job",
      "dispatch_team",
      "track_execution",
      "capture_report",
      "close_job",
    ],
  },
  quotes_invoices: {
    title: "Quotes and invoices registry MVP",
    description: "Registre devis, factures et suivi paiements.",
    records: [
      "quote_id",
      "invoice_id",
      "client_id",
      "job_id",
      "amount",
      "payment_status",
      "billing_stage",
    ],
    workflows: [
      "issue_quote",
      "approve_quote",
      "issue_invoice",
      "track_payment",
      "report_margin",
    ],
  },
  identities: {
    title: "Identity registry MVP",
    description: "Registre des identites reliees aux roles, badges, scopes et portails.",
    records: [
      "identity_id",
      "organization_id",
      "identity_type",
      "role_id",
      "badge_id",
      "scope_id",
      "credential_state",
      "portal_state",
    ],
    workflows: [
      "create_identity",
      "assign_badge_template",
      "assign_role_scope",
      "enable_portal",
      "rotate_credential",
    ],
  },
};

const BUSINESS_CLIENT_REGISTRY_LIVE = {
  title: "Client registry live",
  summary: "Premier registre vivant pour porter de vrais comptes client au-dessus du RBAC Smajor.",
  records: [
    {
      client_id: "client-alpha-001",
      organization_id: "org-alpha-001",
      organization_name: "Alpha Yard Services",
      identity_id: "ident-alpha-contact-001",
      role_id: "client_contact",
      badge_id: "client_badge",
      scope_id: "client_scope_alpha",
      service_mix: ["deneigement", "excavation", "multi_service_exterior"],
      account_status: "active",
      portal_state: "pending_secure_access",
      billing_state: "invoice_ready",
    },
    {
      client_id: "client-major-lab-001",
      organization_id: "org-major-lab-001",
      organization_name: "Major AI Lab Pilot",
      identity_id: "ident-major-lab-contact-001",
      role_id: "client_contact",
      badge_id: "client_badge",
      scope_id: "client_scope_major_lab",
      service_mix: ["ai_automation", "ops_design"],
      account_status: "pilot_active",
      portal_state: "live",
      billing_state: "quote_prepared",
    },
  ],
};

const BUSINESS_JOB_REGISTRY_LIVE = {
  title: "Job registry live",
  summary: "Premier registre vivant pour porter les jobs terrain et les jobs IA dans le meme cadre de gouvernance.",
  records: [
    {
      job_id: "job-alpha-yard-001",
      client_id: "client-alpha-001",
      service_type: "excavation",
      assigned_team: "crew-east-01",
      equipment_required: ["truck-07", "mini-excavator-02"],
      scheduled_window: "2026-03-13 AM",
      job_status: "scheduled",
      dispatch_scope: "field_scope_east",
    },
    {
      job_id: "job-major-lab-ops-001",
      client_id: "client-major-lab-001",
      service_type: "ai_automation",
      assigned_team: "ai-ops-s25",
      equipment_required: ["trinity", "merlin", "comet"],
      scheduled_window: "2026-03-14 PM",
      job_status: "briefing",
      dispatch_scope: "ai_scope_smajor",
    },
  ],
};

const BUSINESS_QUOTES_INVOICES_LIVE = {
  title: "Quotes and invoices live",
  summary: "Premier registre vivant pour devis, factures et tunnel de paiement sur les comptes actifs.",
  records: [
    {
      quote_id: "quote-alpha-001",
      invoice_id: "invoice-alpha-001",
      client_id: "client-alpha-001",
      job_id: "job-alpha-yard-001",
      amount: 4800,
      currency: "CAD",
      payment_status: "awaiting_collection",
      billing_stage: "invoice_issued",
    },
    {
      quote_id: "quote-major-lab-001",
      invoice_id: null,
      client_id: "client-major-lab-001",
      job_id: "job-major-lab-ops-001",
      amount: 3200,
      currency: "CAD",
      payment_status: "quote_pending",
      billing_stage: "quote_prepared",
    },
  ],
};

const BUSINESS_COLLECTION_KEYS = {
  clients: "clients",
  jobs: "jobs",
  quotes_invoices: "quotes_invoices",
  identities: "identities",
  wallets_custody: "wallets_custody",
};

const BUSINESS_EMPIRE_MANIFEST = {
  title: "Smajor empire manifest",
  summary: "Manifeste central de l'entreprise: business reel, administration stricte, backend IA et routes critiques.",
  doctrine: [
    "S25 mesh reste la source de verite operationnelle.",
    "smajor.org est la facade business et admin de l'empire.",
    "Toute autorite passe par identity_id -> role_id -> badge_id -> scope_id -> service_entitlements.",
    "Les agents servent les operations; ils ne remplacent pas la gouvernance.",
  ],
  domains: {
    public: ["smajor.org", "www.smajor.org", "app.smajor.org"],
    business_api: ["api.smajor.org"],
    runtime: ["s25.smajor.org"],
    validation: ["merlin.smajor.org"],
  },
  control_towers: [
    "customer_success",
    "field_ops",
    "admin_governance",
    "vendor_finance",
    "ai_ops",
    "secure_growth",
  ],
  registries: [
    "organization_registry",
    "identity_registry",
    "service_registry",
    "asset_registry",
    "job_registry",
    "finance_registry",
    "vendor_registry",
    "agent_registry",
  ],
  live_business: [
    "client-registry-live",
    "job-registry-live",
    "quotes-invoices-live",
  ],
  critical_routes: [
    `${BUSINESS_PREFIX}/client-registry-live`,
    `${BUSINESS_PREFIX}/job-registry-live`,
    `${BUSINESS_PREFIX}/quotes-invoices-live`,
    `${BUSINESS_PREFIX}/identity-registry-live`,
    `${BUSINESS_PREFIX}/internal-ops`,
    `${BUSINESS_PREFIX}/role-governance`,
    `${BUSINESS_PREFIX}/rbac-matrix`,
    `${BUSINESS_PREFIX}/agent-catalog`,
    `${BUSINESS_PREFIX}/wallets-custody`,
    `${BUSINESS_PREFIX}/vaults-treasury`,
    `${BUSINESS_PREFIX}/wallet-classes`,
    `${BUSINESS_PREFIX}/wallet-scopes`,
    `${BUSINESS_PREFIX}/wallet-policy-matrix`,
    `${BUSINESS_PREFIX}/secure/live-registries`,
    `${BUSINESS_PREFIX}/secure/wallets-custody`,
    `${BUSINESS_PREFIX}/secure/operator-roster`,
    `${BUSINESS_PREFIX}/secure/alpha-client`,
    `${BUSINESS_PREFIX}/secure/billing-tunnel`,
  ],
  command_chain: [
    "TRINITY -> mission_control",
    "MERLIN -> validation + memory",
    "COMET -> provider_watch + ops_followup",
    "KIMI/ORACLE/ONCHAIN_GUARDIAN -> sensor lanes",
    "GOUV4 -> policy + arbitration",
    "ARKON -> build + runtime wiring",
  ],
};

const BUSINESS_TOTAL_MESH_PROTOCOL = {
  title: "Smajor total mesh protocol",
  summary: "Protocole de maillage total pour aligner tous les agents sur le hub S25 et pousser leur statut en temps reel.",
  doctrine: [
    "Chaque agent doit annoncer son statut au hub.",
    "Le hub consolide roles, badges, scopes et surfaces d'action.",
    "Le mesh s'auto-optimise a partir du status partage, des missions et du feed intel.",
  ],
  target_headcount: 15,
  command_mode: "mesh_total",
  chain: [
    "announce_status",
    "bind_role_and_badge",
    "attach_scope",
    "confirm_service_binding",
    "emit_audit_trail",
    "enter_mesh_ready",
  ],
  agents: [
    "TRINITY",
    "MERLIN",
    "COMET",
    "GOUV4",
    "KIMI",
    "ORACLE",
    "ONCHAIN_GUARDIAN",
    "ARKON",
    "TREASURY",
    "PROVIDER_WATCH",
    "MERLIN_MCP",
    "DEFI_LIQUIDITY_MANAGER",
    "CODE_VALIDATOR",
    "SMART_REFACTOR",
    "AUTO_DOCUMENTER",
  ],
};

const OMEGA_AGENT_ORDER = [
  "TRINITY",
  "MERLIN",
  "COMET",
  "GOUV4",
  "KIMI",
  "ORACLE",
  "ONCHAIN_GUARDIAN",
  "ARKON",
  "TREASURY",
  "PROVIDER_WATCH",
  "MERLIN_MCP",
  "DEFI_LIQUIDITY_MANAGER",
  "CODE_VALIDATOR",
  "SMART_REFACTOR",
  "AUTO_DOCUMENTER",
];

const OMEGA_AGENT_MATRIX = {
  TRINITY: { role_id: "trinity_orchestrator", badge_id: "ai_badge", scope_id: "mission_control", action_surface: "voice_ops" },
  MERLIN: { role_id: "merlin_validator", badge_id: "ai_badge", scope_id: "validation_scope", action_surface: "mcp_validation" },
  COMET: { role_id: "comet_watch", badge_id: "ai_badge", scope_id: "ops_followup", action_surface: "web_intel" },
  GOUV4: { role_id: "policy_admin", badge_id: "major_badge", scope_id: "governance_scope", action_surface: "policy_router" },
  KIMI: { role_id: "kimi_sensor", badge_id: "ai_badge", scope_id: "web3_scope", action_surface: "web3_intel" },
  ORACLE: { role_id: "oracle_sensor", badge_id: "ai_badge", scope_id: "market_scope", action_surface: "market_confirmation" },
  ONCHAIN_GUARDIAN: { role_id: "guardian_watch", badge_id: "ai_badge", scope_id: "risk_scope", action_surface: "onchain_risk" },
  ARKON: { role_id: "builder_operator", badge_id: "employee_badge", scope_id: "runtime_scope", action_surface: "build_runtime" },
  TREASURY: { role_id: "treasury_watch", badge_id: "ai_badge", scope_id: "treasury_scope", action_surface: "treasury_monitoring" },
  PROVIDER_WATCH: { role_id: "provider_watch", badge_id: "ai_badge", scope_id: "provider_scope", action_surface: "provider_intel" },
  MERLIN_MCP: { role_id: "mcp_bridge", badge_id: "ai_badge", scope_id: "mcp_scope", action_surface: "bridge_tools" },
  DEFI_LIQUIDITY_MANAGER: { role_id: "defi_operator", badge_id: "ai_badge", scope_id: "defi_scope", action_surface: "liquidity_watch" },
  CODE_VALIDATOR: { role_id: "code_validator", badge_id: "ai_badge", scope_id: "quality_scope", action_surface: "code_review" },
  SMART_REFACTOR: { role_id: "smart_refactor", badge_id: "ai_badge", scope_id: "refactor_scope", action_surface: "refactor_runtime" },
  AUTO_DOCUMENTER: { role_id: "auto_documenter", badge_id: "ai_badge", scope_id: "docs_scope", action_surface: "knowledge_capture" },
};

const AKASH_DEPLOYMENT_MODEL = [
  {
    dseq: "25883220",
    label: "s25-cockpit-primary",
    role: "cpu_runtime",
    provider: "provider.cap-test-compute.com",
    probe_url: "http://fpog7pbvepbkrfae1529ics23k.ingress.cap-test-compute.com/api/version",
    surface: "cockpit",
  },
  {
    dseq: "25878071",
    label: "s25-merlin-mesh",
    role: "mcp_bridge",
    provider: "provider.akashprovid.com",
    probe_url: "https://merlin.smajor.org/health",
    surface: "merlin_mcp",
  },
  {
    dseq: "25708774",
    label: "s25-gpu-cluster",
    role: "gpu_runtime",
    provider: "provider.unknown",
    probe_url: "",
    surface: "gpu_compute",
  },
];

const BUSINESS_ONBOARDING = {
  title: "Business onboarding chain",
  summary: "Tout nouvel acteur doit entrer par une chaine stricte: identite, role, services, acces.",
  tracks: {
    client: [
      "create_client_identity",
      "link_to_organization",
      "activate_service_contract",
      "issue_portal_access",
      "attach_quote_and_job",
    ],
    employee: [
      "create_employee_identity",
      "assign_role",
      "enable_staff_portal",
      "attach_shift_and_dispatch_scope",
      "issue_secure_credentials",
    ],
    vendor: [
      "create_vendor_identity",
      "link_vendor_org",
      "enable_vendor_portal",
      "attach_purchase_scope",
      "issue_document_access",
    ],
  },
};

const BUSINESS_ROLE_GOVERNANCE = {
  title: "Business role governance",
  summary: "Les identites passent par des roles modeles, des scopes et des services actives. Aucun acces ne depend de la confiance seule.",
  doctrine: [
    "Le role definit les pouvoirs.",
    "Le scope limite la surface reelle.",
    "Les services actives suivent le role, pas l'inverse.",
    "Toute elevation de pouvoir laisse une trace d'audit.",
    "La structure doit survivre a l'utilisateur.",
  ],
  badge_templates: [
    { key: "major_badge", audience: "Direction", binds_to: ["operator_admin"] },
    { key: "employee_badge", audience: "Employes", binds_to: ["staff_member"] },
    { key: "client_badge", audience: "Clients", binds_to: ["client_contact"] },
    { key: "vendor_badge", audience: "Fournisseurs", binds_to: ["vendor_contact"] },
  ],
  identity_binding: {
    model: "identity_id -> role_id -> badge_id -> scope_id -> entitlements",
    rule: "aucune fonction critique n'est liee a une identite fixe",
    rotation: "si une personne change, on remplace la credential et on garde le role template",
  },
  role_templates: [
    {
      key: "operator_admin",
      audience: "Direction et admins",
      services: ["admin_console", "billing_access", "ai_services"],
      powers: ["identity_control", "finance_approval", "policy_admin"],
    },
    {
      key: "staff_member",
      audience: "Employes terrain",
      services: ["staff_portal", "snow_ops", "excavation_ops"],
      powers: ["job_execution", "field_reports"],
    },
    {
      key: "client_contact",
      audience: "Clients",
      services: ["client_portal", "billing_access"],
      powers: ["service_requests", "quote_review", "invoice_review"],
    },
    {
      key: "vendor_contact",
      audience: "Fournisseurs",
      services: ["vendor_portal", "billing_access"],
      powers: ["po_review", "delivery_confirmation", "document_exchange"],
    },
  ],
  activation_flow: [
    "identity_created",
    "badge_template_selected",
    "role_template_selected",
    "scope_assigned",
    "services_enabled",
    "credentials_issued",
    "audit_watch_started",
  ],
};

const BUSINESS_REGISTRY_MAP = {
  title: "Smajor business registry map",
  source_of_truth: "api.smajor.org facade + S25 governance",
  registries: [
    { key: "clients", path: `${BUSINESS_PREFIX}/clients`, purpose: "Customer and account intake" },
    { key: "jobs", path: `${BUSINESS_PREFIX}/jobs`, purpose: "Field operations and execution" },
    { key: "quotes_invoices", path: `${BUSINESS_PREFIX}/quotes-invoices`, purpose: "Commercial and billing flow" },
    { key: "identities", path: `${BUSINESS_PREFIX}/identities`, purpose: "Identity to role to badge activation" },
    { key: "onboarding", path: `${BUSINESS_PREFIX}/onboarding`, purpose: "Strict actor activation chain" },
    { key: "role_governance", path: `${BUSINESS_PREFIX}/role-governance`, purpose: "Role templates, powers and service enablement" },
    { key: "rbac_matrix", path: `${BUSINESS_PREFIX}/rbac-matrix`, purpose: "Identity to role to badge to entitlement model" },
    { key: "portal_activation", path: `${BUSINESS_PREFIX}/portal-activation`, purpose: "Portal enablement chain by audience" },
    { key: "client_form", path: `${BUSINESS_PREFIX}/client-form`, purpose: "Client intake schema for portal and admin" },
    { key: "staff_dashboard", path: `${BUSINESS_PREFIX}/staff-dashboard`, purpose: "Employee work dashboard model" },
    { key: "alpha_pilot", path: `${BUSINESS_PREFIX}/alpha-pilot`, purpose: "Public pilot status for first customer journey" },
    { key: "billing_tunnel", path: `${BUSINESS_PREFIX}/billing-tunnel`, purpose: "Public billing tunnel workflow" },
    { key: "agent_catalog", path: `${BUSINESS_PREFIX}/agent-catalog`, purpose: "Live activable agent catalog" },
    { key: "agent_service_matrix", path: `${BUSINESS_PREFIX}/agent-service-matrix`, purpose: "Agent to service activation map" },
    { key: "agent_action_trail", path: `${BUSINESS_PREFIX}/agent-action-trail`, purpose: "Audit fields for agent actions" },
    { key: "client_registry_live", path: `${BUSINESS_PREFIX}/client-registry-live`, purpose: "Seeded client accounts ready for portal activation" },
    { key: "job_registry_live", path: `${BUSINESS_PREFIX}/job-registry-live`, purpose: "Seeded operations jobs aligned with dispatch scopes" },
    { key: "quotes_invoices_live", path: `${BUSINESS_PREFIX}/quotes-invoices-live`, purpose: "Seeded commercial and billing records" },
    { key: "identity_registry_live", path: `${BUSINESS_PREFIX}/identity-registry-live`, purpose: "Live identities bound to role, badge, scope and services" },
    { key: "wallets_custody", path: `${BUSINESS_PREFIX}/wallets-custody`, purpose: "Custody registry for creator wallet and sovereign vault chain" },
    { key: "vaults_treasury", path: `${BUSINESS_PREFIX}/vaults-treasury`, purpose: "Treasury readiness, custody doctrine and sovereign wallet posture" },
    { key: "wallet_classes", path: `${BUSINESS_PREFIX}/wallet-classes`, purpose: "Wallet classes for creator, treasury, trading, ops and mirror lanes" },
    { key: "wallet_scopes", path: `${BUSINESS_PREFIX}/wallet-scopes`, purpose: "Scope map for wallet territories and restrictions" },
    { key: "wallet_policy_matrix", path: `${BUSINESS_PREFIX}/wallet-policy-matrix`, purpose: "Policy matrix for custody, execution and audit" },
    { key: "internal_ops", path: `${BUSINESS_PREFIX}/internal-ops`, purpose: "Public operating summary for Smajor internal account" },
    { key: "empire_manifest", path: `${BUSINESS_PREFIX}/empire-manifest`, purpose: "Unified manifest of domains, towers, registries and command chain" },
    { key: "total_mesh_protocol", path: `${BUSINESS_PREFIX}/total-mesh-protocol`, purpose: "Protocol de synchronisation totale des agents vers le hub" },
    { key: "secure_live_registries", path: `${BUSINESS_PREFIX}/secure/live-registries`, purpose: "Protected admin view of all live business registries" },
    { key: "secure_operator_roster", path: `${BUSINESS_PREFIX}/secure/operator-roster`, purpose: "Protected operator roster and founder chain" },
    { key: "secure_alpha_client", path: `${BUSINESS_PREFIX}/secure/alpha-client`, purpose: "Protected alpha client detail route" },
    { key: "secure_billing_tunnel", path: `${BUSINESS_PREFIX}/secure/billing-tunnel`, purpose: "Protected billing tunnel detail route" },
  ],
};

const BUSINESS_RBAC_MATRIX = {
  title: "Business RBAC matrix",
  summary: "Le systeme opere par id-role-badge-scope. La personne peut changer; la matrice ne bouge pas.",
  model: [
    "identity_id",
    "role_id",
    "badge_id",
    "scope_id",
    "service_entitlements",
    "credential_state",
    "audit_state",
  ],
  critical_rules: [
    "aucune fonction critique n'est liee a une identite fixe",
    "les permissions viennent du role_id",
    "le badge_id sert de moule d'acces operatoire",
    "la rotation humaine remplace la credential, pas la structure",
  ],
};

const BUSINESS_PORTAL_ACTIVATION = {
  title: "Portal activation plan",
  summary: "Chaque portail s'ouvre a partir d'une identite, d'un role, d'un badge, d'un scope et de services actives.",
  portals: [
    {
      key: "client_portal",
      audience: "Clients",
      required_chain: ["identity_id", "client_badge", "client_contact", "client_scope", "billing_access"],
      onboarding: ["create_client_identity", "bind_role", "enable_services", "issue_access"],
    },
    {
      key: "staff_portal",
      audience: "Employes et sous-traitants",
      required_chain: ["identity_id", "employee_badge", "staff_member", "field_scope", "staff_portal"],
      onboarding: ["create_employee_identity", "bind_role", "attach_dispatch_scope", "issue_access"],
    },
    {
      key: "vendor_portal",
      audience: "Fournisseurs",
      required_chain: ["identity_id", "vendor_badge", "vendor_contact", "vendor_scope", "vendor_portal"],
      onboarding: ["create_vendor_identity", "bind_role", "attach_purchase_scope", "issue_access"],
    },
    {
      key: "admin_console",
      audience: "Direction et operateurs admin",
      required_chain: ["identity_id", "major_badge", "operator_admin", "governance_scope", "admin_console"],
      onboarding: ["create_admin_identity", "bind_role", "enable_admin_services", "issue_hardened_access"],
    },
  ],
};

const BUSINESS_CLIENT_FORM = {
  title: "Client intake form schema",
  summary: "Formulaire standard pour creer un dossier client sans casser la chaine RBAC.",
  sections: [
    {
      label: "Identity",
      fields: ["organization_name", "contact_name", "contact_email", "contact_phone"],
    },
    {
      label: "Service",
      fields: ["service_type", "site_address", "urgency_level", "service_window"],
    },
    {
      label: "Commercial",
      fields: ["quote_required", "billing_contact", "contract_mode", "notes"],
    },
  ],
  outputs: [
    "client_id",
    "organization_id",
    "identity_id",
    "role_id=client_contact",
    "badge_id=client_badge",
    "portal_state=pending_or_live",
  ],
};

const BUSINESS_STAFF_DASHBOARD = {
  title: "Staff dashboard model",
  summary: "Vue de travail terrain pour employes et sous-traitants, limitee au scope de dispatch.",
  panels: [
    {
      label: "Shift",
      widgets: ["today_assignments", "start_window", "priority_jobs"],
    },
    {
      label: "Field",
      widgets: ["job_brief", "site_address", "equipment_required", "incident_flag"],
    },
    {
      label: "Completion",
      widgets: ["report_submit", "photo_upload", "time_close", "escalation_note"],
    },
  ],
  guardrails: [
    "pas d'acces finance globale",
    "pas d'acces autres equipes hors scope",
    "pas de modification de role ou service entitlement",
  ],
};

const BUSINESS_ALPHA_PILOT = {
  title: "Alpha client pilot",
  summary: "Premier dossier client de reference pour valider intake, job, facture et paiement sans exposer la vraie data publiquement.",
  public_status: {
    pilot_key: "alpha-client-001",
    phase: "intake_to_invoice",
    account_status: "pilot_ready",
    portal_state: "pending_secure_access",
  },
  checkpoints: [
    "identity_created",
    "role_bound_to_client_badge",
    "service_scope_attached",
    "quote_prepared",
    "invoice_channel_ready",
    "payment_receipt_tracking_ready",
  ],
  secure_detail_route: `${BUSINESS_PREFIX}/secure/alpha-client`,
};

const BUSINESS_BILLING_TUNNEL = {
  title: "Billing and payment tunnel",
  summary: "Tunnel de facture et paiement pour faire passer un client du devis au recu sans sortir du cadre RBAC.",
  stages: [
    "quote_prepared",
    "quote_approved",
    "invoice_issued",
    "payment_link_or_instruction_sent",
    "payment_received_or_pending",
    "receipt_logged",
  ],
  secure_detail_route: `${BUSINESS_PREFIX}/secure/billing-tunnel`,
};

const BUSINESS_AGENT_CATALOG = {
  title: "Agent activation catalog",
  summary: "Catalogue activable live des agents relies a la matrice role-badge-service-trace.",
  agents: [
    {
      agent_id: "TRINITY",
      role_id: "trinity_orchestrator",
      badge_id: "ai_badge",
      service_bindings: ["mission_control", "voice_ops", "status_read", "memory_read"],
      action_surfaces: ["create_mission", "route_task", "status_summary"],
      trail_mode: "full_audit",
    },
    {
      agent_id: "MERLIN",
      role_id: "merlin_validator",
      badge_id: "ai_badge",
      service_bindings: ["mcp_validation", "memory_review", "architecture_review"],
      action_surfaces: ["write_feedback", "validate_chain", "confirm_design"],
      trail_mode: "validation_audit",
    },
    {
      agent_id: "COMET",
      role_id: "comet_watch",
      badge_id: "ai_badge",
      service_bindings: ["provider_watch", "web_intel", "ops_followup"],
      action_surfaces: ["watch_sources", "log_intel", "handoff_ops"],
      trail_mode: "intel_audit",
    },
    {
      agent_id: "KIMI",
      role_id: "kimi_sensor",
      badge_id: "ai_badge",
      service_bindings: ["web3_scan", "token_watch"],
      action_surfaces: ["scan_web3", "log_signal"],
      trail_mode: "sensor_audit",
    },
    {
      agent_id: "ORACLE",
      role_id: "oracle_sensor",
      badge_id: "ai_badge",
      service_bindings: ["market_verification", "price_snapshot"],
      action_surfaces: ["verify_price", "publish_snapshot"],
      trail_mode: "market_audit",
    },
    {
      agent_id: "ONCHAIN_GUARDIAN",
      role_id: "guardian_watch",
      badge_id: "ai_badge",
      service_bindings: ["onchain_watch", "risk_alerts"],
      action_surfaces: ["scan_risk", "publish_alert"],
      trail_mode: "risk_audit",
    },
    {
      agent_id: "GOUV4",
      role_id: "policy_admin",
      badge_id: "major_badge",
      service_bindings: ["routing_policy", "cost_governance"],
      action_surfaces: ["route_task", "arbitrate_model", "enforce_policy"],
      trail_mode: "policy_audit",
    },
    {
      agent_id: "ARKON",
      role_id: "builder_operator",
      badge_id: "employee_badge",
      service_bindings: ["build_ops", "migration_ops", "tooling_ops"],
      action_surfaces: ["patch_backend", "wire_infra", "ship_runtime"],
      trail_mode: "builder_audit",
    },
  ],
};

const BUSINESS_AGENT_SERVICE_MATRIX = {
  title: "Agent service matrix",
  summary: "Chaque agent porte des actions, mais seulement sur ses surfaces autorisees.",
  bindings: [
    {
      audience: "Business surfaces",
      services: ["client_portal", "staff_portal", "vendor_portal", "admin_console"],
      activators: ["TRINITY", "GOUV4", "MERLIN"],
    },
    {
      audience: "Runtime S25",
      services: ["mission_control", "memory_read", "status_read", "mcp_validation"],
      activators: ["TRINITY", "MERLIN", "COMET"],
    },
    {
      audience: "Web3 and market",
      services: ["web3_scan", "market_verification", "onchain_watch"],
      activators: ["KIMI", "ORACLE", "ONCHAIN_GUARDIAN"],
    },
    {
      audience: "Build and policy",
      services: ["build_ops", "routing_policy", "cost_governance"],
      activators: ["ARKON", "GOUV4"],
    },
  ],
};

const BUSINESS_AGENT_ACTION_TRAIL = {
  title: "Agent action trail",
  summary: "Toute action agentique doit laisser une piste de role, service et surface.",
  trail_fields: [
    "agent_id",
    "role_id",
    "badge_id",
    "service_binding",
    "action_surface",
    "scope_id",
    "request_id",
    "audit_state",
  ],
  rules: [
    "pas d'action critique sans role_id",
    "pas d'action critique sans service_binding",
    "pas d'action critique sans audit trail",
  ],
};

const SECURE_ALPHA_CLIENT_DETAIL = {
  client_id: "client-alpha-001",
  organization_id: "org-alpha-001",
  identity_id: "ident-alpha-contact-001",
  role_id: "client_contact",
  badge_id: "client_badge",
  scope_id: "client_scope_alpha",
  service_type: "multi_service_exterior",
  portal_state: "pending_secure_access",
  quote_id: "quote-alpha-001",
  invoice_id: "invoice-alpha-001",
  billing_state: "invoice_ready",
  payment_state: "awaiting_collection",
};

const SECURE_BILLING_TUNNEL_DETAIL = {
  quote_id: "quote-alpha-001",
  invoice_id: "invoice-alpha-001",
  contract_mode: "monthly_service_bundle",
  payment_channel: "manual_or_link",
  receipt_tracking: "enabled",
  audit_state: "watching",
};

function buildTargetUrl(requestUrl, originBase) {
  const incoming = new URL(requestUrl);
  const origin = new URL(originBase);
  origin.pathname = incoming.pathname;
  origin.search = incoming.search;
  return origin;
}

function businessResponse(requestId, pathname, payload, status = 200) {
  return jsonResponse(
    {
      ok: true,
      service: "trinity-s25-proxy",
      request_id: requestId,
      pathname,
      ...payload,
    },
    { status },
  );
}

function buildBusinessState(seed) {
  return {
    clients: [...BUSINESS_CLIENT_REGISTRY_LIVE.records],
    jobs: [...BUSINESS_JOB_REGISTRY_LIVE.records],
    quotes_invoices: [...BUSINESS_QUOTES_INVOICES_LIVE.records],
    identities: [],
    wallets_custody: [],
    last_write_at: null,
    ...(seed || {}),
  };
}

async function deriveWalletCustodyRegistry(env, requestId) {
  let status = {};
  try {
    status = await fetchOriginJson("/api/status", env, requestId);
  } catch {
    if (env.PUBLIC_RUNTIME_URL) {
      try {
        status = await fetchPublicRuntimeJson("/api/status", env, requestId);
      } catch {}
    }
  }

  const wallet = status?.wallet || {};
  const address = wallet.address || status.wallet_creator_address || MASTER_WALLET_ADDRESS;
  const custody = wallet.custody || status.wallet_custody || "google_secret_manager";
  const connected =
    wallet.connected != null
      ? Boolean(wallet.connected)
      : status.wallet_creator_connected != null
        ? Boolean(status.wallet_creator_connected)
        : Boolean(address);
  let aktBalance = wallet.akt_balance ?? status.wallet_creator_akt_balance ?? null;
  let aktPriceUsd = wallet.akt_price_usd ?? status.wallet_creator_akt_price_usd ?? null;
  let aktValueUsd = wallet.akt_value_usd ?? status.wallet_creator_akt_value_usd ?? null;
  const lastSync = wallet.last_sync || null;

  if (aktBalance == null && address) {
    try {
      const [balanceResponse, priceResponse] = await Promise.all([
        fetch(`https://rest.cosmos.directory/akash/cosmos/bank/v1beta1/balances/${address}`),
        fetch("https://api.coingecko.com/api/v3/simple/price?ids=akash-network&vs_currencies=usd"),
      ]);
      if (balanceResponse.ok) {
        const balancePayload = await balanceResponse.json();
        const uakt = balancePayload?.balances?.find((entry) => entry?.denom === "uakt");
        if (uakt?.amount) {
          aktBalance = Number((Number(uakt.amount) / 1_000_000).toFixed(6));
        }
      }
      if (priceResponse.ok) {
        const pricePayload = await priceResponse.json();
        aktPriceUsd = pricePayload?.["akash-network"]?.usd ?? null;
      }
      if (aktBalance != null && aktPriceUsd != null) {
        aktValueUsd = Number((aktBalance * aktPriceUsd).toFixed(2));
      }
    } catch {}
  }

  return {
    title: "Wallets and custody registry",
    summary: "Registre de custody du wallet creator et de la chaine souveraine S25.",
    records: [
      {
        wallet_id: "wallet-creator-001",
        label: wallet.label || "Wallet creator",
        network: "akash",
        address,
        connected,
        custody,
        custody_secret_ref: "gsm:s25-master-seed",
        authority_principal: "serviceAccount:merlin-agent@gen-lang-client-0046423999.iam.gserviceaccount.com",
        akt_balance: aktBalance,
        akt_price_usd: aktPriceUsd,
        akt_value_usd: aktValueUsd,
        last_sync: lastSync,
        source_of_truth: "S25 Lumiere runtime + Google Secret Manager",
      },
    ],
  };
}

async function deriveVaultsTreasuryView(env, requestId) {
  const registry = await deriveWalletCustodyRegistry(env, requestId);
  const wallet = registry.records?.[0] || {};
  return {
    title: "Vaults and treasury command",
    summary: "Posture de treasury souverain, coffre wallet creator et doctrine custody avant les routes de trading live.",
    doctrine: [
      "Le wallet creator reste sous Google Secret Manager.",
      "Les seeds ne sont jamais exposees en facade publique.",
      "Le trading reste sous politique de custody et d'audit avant execution live.",
      "Akash et S25 pilotent l'operation; les exchanges restent secondaires.",
    ],
    treasury: {
      wallet_id: wallet.wallet_id || "wallet-creator-001",
      address: wallet.address || MASTER_WALLET_ADDRESS,
      connected: wallet.connected ?? true,
      custody: wallet.custody || "google_secret_manager",
      akt_balance: wallet.akt_balance ?? null,
      akt_price_usd: wallet.akt_price_usd ?? null,
      akt_value_usd: wallet.akt_value_usd ?? null,
      authority_principal:
        wallet.authority_principal ||
        "serviceAccount:merlin-agent@gen-lang-client-0046423999.iam.gserviceaccount.com",
    },
    policies: [
      "policy_seed_gsm_only",
      "policy_public_address_only",
      "policy_operator_session_required",
      "policy_full_audit_before_trading",
    ],
    next_steps: [
      "brancher vault registry dans admin",
      "lier treasury a omega",
      "ajouter wallets secondaires et politiques par scope",
    ],
  };
}

function deriveWalletClasses() {
  return {
    title: "Wallet classes",
    summary: "Classes de wallets qui survivent aux utilisateurs et cadrent la structure de pouvoir Smajor.",
    classes: [
      {
        wallet_class_id: "creator_wallet",
        badge_id: "major_badge",
        scope_id: "founder_scope",
        purpose: "racine souveraine, bootstrap et recovery",
        allowed_actions: ["derive_public_address", "bootstrap_authority", "emergency_rotation"],
      },
      {
        wallet_class_id: "treasury_wallet",
        badge_id: "ai_badge",
        scope_id: "treasury_scope",
        purpose: "reserve, runway et financement infra",
        allowed_actions: ["read_balance", "fund_runtime", "record_treasury_state"],
      },
      {
        wallet_class_id: "trading_wallet",
        badge_id: "ai_badge",
        scope_id: "trading_scope",
        purpose: "execution bornee des strategies et bots",
        allowed_actions: ["signal_only", "execution_after_policy", "profit_report"],
      },
      {
        wallet_class_id: "operations_wallet",
        badge_id: "employee_badge",
        scope_id: "ops_scope",
        purpose: "paiements operationnels et frais terrain",
        allowed_actions: ["vendor_payment", "fuel_ops", "ops_expense_log"],
      },
      {
        wallet_class_id: "mirror_wallet",
        badge_id: "ai_badge",
        scope_id: "mirror_scope",
        purpose: "tests mirror et conteneurs d'execution cloisonnes",
        allowed_actions: ["bootstrap_test", "container_auth", "dry_run_validation"],
      },
    ],
  };
}

function deriveWalletScopes() {
  return {
    title: "Wallet scopes",
    summary: "Territoires d'action imposes aux wallets pour que la structure survive aux personnes et aux agents.",
    scopes: [
      { scope_id: "founder_scope", territory: "authority_root", restrictions: ["no_public_seed", "manual_recovery_only"] },
      { scope_id: "treasury_scope", territory: "runway_and_funding", restrictions: ["no_strategy_override", "audit_required"] },
      { scope_id: "trading_scope", territory: "strategy_execution", restrictions: ["policy_gate", "risk_limit", "profit_log"] },
      { scope_id: "ops_scope", territory: "field_and_vendor_operations", restrictions: ["invoice_link_required", "ops_budget_only"] },
      { scope_id: "mirror_scope", territory: "container_bootstrap", restrictions: ["test_first", "fleet_gate", "authority_check"] },
    ],
  };
}

function deriveWalletPolicyMatrix() {
  return {
    title: "Wallet policy matrix",
    summary: "Matrice de policy qui lie custody, signature, execution et audit a une classe et un scope, jamais a une personne fixe.",
    policies: [
      {
        policy_id: "policy_seed_gsm_only",
        applies_to: ["creator_wallet", "mirror_wallet"],
        rule: "seed phrase uniquement dans Google Secret Manager",
      },
      {
        policy_id: "policy_public_address_only",
        applies_to: ["creator_wallet", "treasury_wallet", "trading_wallet", "operations_wallet"],
        rule: "seule l'adresse publique peut etre exposee en facade",
      },
      {
        policy_id: "policy_operator_session_required",
        applies_to: ["treasury_wallet", "operations_wallet"],
        rule: "toute action admin passe par session operateur signee",
      },
      {
        policy_id: "policy_full_audit_before_trading",
        applies_to: ["trading_wallet"],
        rule: "aucune execution tant que le trail, le scope et la policy ne sont pas confirmes",
      },
      {
        policy_id: "policy_fleet_authority_gate",
        applies_to: ["mirror_wallet"],
        rule: "aucune flotte complete sans autorite etablie sur MERLIN MCP",
      },
    ],
  };
}

function findInternalOpsClient(business) {
  return (business.clients || []).find(
    (record) =>
      record.client_id === "client-smajor-internal-001" ||
      record.organization_name === "Smajor Internal Operations",
  ) || null;
}

function deriveInternalOpsSummary(business) {
  const client = findInternalOpsClient(business);
  const jobs = (business.jobs || []).filter((record) => record.client_id === client?.client_id);
  const quotes = (business.quotes_invoices || []).filter((record) => record.client_id === client?.client_id);
  return {
    title: "Smajor internal operations",
    summary: "Compte operatoire interne pour faire gerer l'empire par sa propre infrastructure.",
    account_live: Boolean(client),
    client: client
      ? {
          client_id: client.client_id,
          organization_name: client.organization_name,
          scope_id: client.scope_id,
          portal_state: client.portal_state,
          billing_state: client.billing_state,
          service_mix: client.service_mix,
        }
      : null,
    jobs_open: jobs.length,
    finance_entries: quotes.length,
    last_write_at: business.last_write_at,
  };
}

function buildOperatorRoster(business) {
  const identities = business.identities || [];
  const operators = identities.filter((record) => record.badge_id === "major_badge");
  return {
    title: "Operator roster",
    summary: "Racine humaine de gouvernance: les comptes major entrent dans la meme matrice RBAC que le reste du systeme.",
    total_operator_identities: operators.length,
    identities: operators,
    last_write_at: business.last_write_at,
  };
}

function extractBusinessState(payload) {
  const candidate = payload?.state?.intel?.business_registry || payload?.state?.business || {};
  return buildBusinessState(candidate);
}

function hasBusinessWrites(state) {
  return Boolean(
    state?.last_write_at ||
    (Array.isArray(state?.clients) && state.clients.some((item) => item?.created_at)) ||
    (Array.isArray(state?.jobs) && state.jobs.some((item) => item?.created_at)) ||
    (Array.isArray(state?.quotes_invoices) && state.quotes_invoices.some((item) => item?.created_at)) ||
    (Array.isArray(state?.identities) && state.identities.some((item) => item?.created_at || item?.identity_id)),
  );
}

function createRecordId(prefix) {
  return `${prefix}-${crypto.randomUUID().slice(0, 8)}`;
}

async function readBusinessState(env, requestId) {
  try {
    const payload = await fetchOriginJson("/api/memory/state", env, requestId);
    const business = extractBusinessState(payload);
    if (hasBusinessWrites(business)) {
      return business;
    }
  } catch {}

  if (env.PUBLIC_RUNTIME_URL) {
    try {
      const payload = await fetchPublicRuntimeJson("/api/memory/state", env, requestId);
      const business = extractBusinessState(payload);
      if (hasBusinessWrites(business)) {
        return business;
      }
    } catch {}
  }

  return buildBusinessState();
}

async function writeBusinessState(env, requestId, business) {
  const target = new URL("/api/memory/state", env.ORIGIN_BASE);
  const headers = new Headers({
    "content-type": "application/json",
    accept: "application/json",
    "user-agent": "trinity-s25-proxy/omega",
    "x-trinity-request-id": requestId,
  });
  if (env.ORIGIN_HOST_HEADER) {
    headers.set("host", env.ORIGIN_HOST_HEADER);
  }
  if (env.S25_SHARED_SECRET) {
    headers.set("x-s25-secret", env.S25_SHARED_SECRET);
  }
  const response = await fetch(target, {
    method: "POST",
    headers,
    body: JSON.stringify({
      agent: "TRINITY",
      intel: {
        business_registry: business,
      },
    }),
  });
  if (!response.ok) {
    throw new Error(`origin_write_${response.status}`);
  }
  return response.json();
}

function buildCreatedRecord(kind, body) {
  const now = new Date().toISOString();
  if (kind === "client") {
    return {
      client_id: body.client_id || createRecordId("client"),
      organization_id: body.organization_id || createRecordId("org"),
      organization_name: body.organization_name || "Unnamed Organization",
      identity_id: body.identity_id || createRecordId("ident"),
      role_id: body.role_id || "client_contact",
      badge_id: body.badge_id || "client_badge",
      scope_id: body.scope_id || "client_scope_default",
      service_mix: Array.isArray(body.service_mix) ? body.service_mix : [body.service_type || "multi_service_exterior"],
      account_status: body.account_status || "active",
      portal_state: body.portal_state || "pending_secure_access",
      billing_state: body.billing_state || "quote_pending",
      created_at: now,
    };
  }
  if (kind === "job") {
    return {
      job_id: body.job_id || createRecordId("job"),
      client_id: body.client_id || "",
      service_type: body.service_type || "multi_service_exterior",
      assigned_team: body.assigned_team || "unassigned",
      equipment_required: Array.isArray(body.equipment_required) ? body.equipment_required : [],
      scheduled_window: body.scheduled_window || "pending_schedule",
      job_status: body.job_status || "scheduled",
      dispatch_scope: body.dispatch_scope || "field_scope_default",
      created_at: now,
    };
  }
  if (kind === "identity") {
    return {
      identity_id: body.identity_id || createRecordId("ident"),
      organization_id: body.organization_id || "",
      identity_type: body.identity_type || "human_operator",
      display_name: body.display_name || "Unnamed Operator",
      role_id: body.role_id || "operator_admin",
      badge_id: body.badge_id || "major_badge",
      scope_id: body.scope_id || "governance_scope",
      service_entitlements: Array.isArray(body.service_entitlements) ? body.service_entitlements : ["admin_console"],
      credential_state: body.credential_state || "issued",
      portal_state: body.portal_state || "live",
      audit_state: body.audit_state || "watching",
      created_at: now,
    };
  }
  return {
    quote_id: body.quote_id || createRecordId("quote"),
    invoice_id: body.invoice_id || null,
    client_id: body.client_id || "",
    job_id: body.job_id || "",
    amount: body.amount ?? 0,
    currency: body.currency || "CAD",
    payment_status: body.payment_status || "quote_pending",
    billing_stage: body.billing_stage || "quote_prepared",
    created_at: now,
  };
}

async function handleBusinessCreate(request, pathname, requestId, env, kind) {
  const denied = requireBusinessSecret(request, env, requestId, pathname);
  if (denied) return denied;

  const body = await request.json().catch(() => ({}));
  const business = await readBusinessState(env, requestId);
  const collectionKey =
    kind === "client"
      ? BUSINESS_COLLECTION_KEYS.clients
      : kind === "job"
        ? BUSINESS_COLLECTION_KEYS.jobs
        : kind === "identity"
          ? BUSINESS_COLLECTION_KEYS.identities
          : BUSINESS_COLLECTION_KEYS.quotes_invoices;
  const created = buildCreatedRecord(kind, body);
  business[collectionKey] = [created, ...(business[collectionKey] || [])];
  business.last_write_at = new Date().toISOString();
  await writeBusinessState(env, requestId, business);
  return businessResponse(
    requestId,
    pathname,
    {
      created,
      collection: collectionKey,
      total_records: business[collectionKey].length,
      last_write_at: business.last_write_at,
    },
    201,
  );
}

function readSharedSecret(request, env) {
  const headerSecret = request.headers.get("x-s25-secret") || "";
  const bearer = request.headers.get("authorization") || "";
  const bearerSecret = bearer.toLowerCase().startsWith("bearer ") ? bearer.slice(7).trim() : "";
  return headerSecret || bearerSecret || "";
}

function requireBusinessSecret(request, env, requestId, pathname) {
  if (!env.S25_SHARED_SECRET) {
    return businessResponse(requestId, pathname, {
      ok: false,
      error: "shared_secret_not_configured",
      protection: "x-s25-secret required once worker secret is configured",
    }, 503);
  }

  const presented = readSharedSecret(request, env);
  if (!presented || presented !== env.S25_SHARED_SECRET) {
    return businessResponse(requestId, pathname, {
      ok: false,
      error: "unauthorized",
      protection: "present x-s25-secret or bearer token matching the shared secret",
    }, 401);
  }

  return null;
}

function handleBusinessRequest(request, pathname, requestId, env) {
  if (pathname === `${BUSINESS_PREFIX}` || pathname === `${BUSINESS_PREFIX}/`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRY_MAP);
  }
  if (pathname === `${BUSINESS_PREFIX}/registry-map`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRY_MAP);
  }
  if (pathname === `${BUSINESS_PREFIX}/clients`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRIES.clients);
  }
  if (pathname === `${BUSINESS_PREFIX}/jobs`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRIES.jobs);
  }
  if (pathname === `${BUSINESS_PREFIX}/quotes-invoices`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRIES.quotes_invoices);
  }
  if (pathname === `${BUSINESS_PREFIX}/identities`) {
    return businessResponse(requestId, pathname, BUSINESS_REGISTRIES.identities);
  }
  if (pathname === `${BUSINESS_PREFIX}/onboarding`) {
    return businessResponse(requestId, pathname, BUSINESS_ONBOARDING);
  }
  if (pathname === `${BUSINESS_PREFIX}/role-governance`) {
    return businessResponse(requestId, pathname, BUSINESS_ROLE_GOVERNANCE);
  }
  if (pathname === `${BUSINESS_PREFIX}/rbac-matrix`) {
    return businessResponse(requestId, pathname, BUSINESS_RBAC_MATRIX);
  }
  if (pathname === `${BUSINESS_PREFIX}/portal-activation`) {
    return businessResponse(requestId, pathname, BUSINESS_PORTAL_ACTIVATION);
  }
  if (pathname === `${BUSINESS_PREFIX}/client-form`) {
    return businessResponse(requestId, pathname, BUSINESS_CLIENT_FORM);
  }
  if (pathname === `${BUSINESS_PREFIX}/staff-dashboard`) {
    return businessResponse(requestId, pathname, BUSINESS_STAFF_DASHBOARD);
  }
  if (pathname === `${BUSINESS_PREFIX}/alpha-pilot`) {
    return businessResponse(requestId, pathname, BUSINESS_ALPHA_PILOT);
  }
  if (pathname === `${BUSINESS_PREFIX}/billing-tunnel`) {
    return businessResponse(requestId, pathname, BUSINESS_BILLING_TUNNEL);
  }
  if (pathname === `${BUSINESS_PREFIX}/agent-catalog`) {
    return businessResponse(requestId, pathname, BUSINESS_AGENT_CATALOG);
  }
  if (pathname === `${BUSINESS_PREFIX}/agent-service-matrix`) {
    return businessResponse(requestId, pathname, BUSINESS_AGENT_SERVICE_MATRIX);
  }
  if (pathname === `${BUSINESS_PREFIX}/agent-action-trail`) {
    return businessResponse(requestId, pathname, BUSINESS_AGENT_ACTION_TRAIL);
  }
  if (pathname === `${BUSINESS_PREFIX}/client-registry-live`) {
    if (request.method === "POST") {
      return handleBusinessCreate(request, pathname, requestId, env, "client");
    }
    return readBusinessState(env, requestId).then((business) =>
      businessResponse(requestId, pathname, {
        ...BUSINESS_CLIENT_REGISTRY_LIVE,
        records: business.clients,
        live_store: true,
        last_write_at: business.last_write_at,
      }),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/job-registry-live`) {
    if (request.method === "POST") {
      return handleBusinessCreate(request, pathname, requestId, env, "job");
    }
    return readBusinessState(env, requestId).then((business) =>
      businessResponse(requestId, pathname, {
        ...BUSINESS_JOB_REGISTRY_LIVE,
        records: business.jobs,
        live_store: true,
        last_write_at: business.last_write_at,
      }),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/quotes-invoices-live`) {
    if (request.method === "POST") {
      return handleBusinessCreate(request, pathname, requestId, env, "quote");
    }
    return readBusinessState(env, requestId).then((business) =>
      businessResponse(requestId, pathname, {
        ...BUSINESS_QUOTES_INVOICES_LIVE,
        records: business.quotes_invoices,
        live_store: true,
        last_write_at: business.last_write_at,
      }),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/identity-registry-live`) {
    if (request.method === "POST") {
      return handleBusinessCreate(request, pathname, requestId, env, "identity");
    }
    return readBusinessState(env, requestId).then((business) =>
      businessResponse(requestId, pathname, {
        title: "Identity registry live",
        summary: "Identites vivantes reliees aux roles, badges, scopes et services actives.",
        records: business.identities,
        live_store: true,
        last_write_at: business.last_write_at,
      }),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/wallets-custody`) {
    return deriveWalletCustodyRegistry(env, requestId).then((registry) =>
      businessResponse(requestId, pathname, registry),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/vaults-treasury`) {
    return deriveVaultsTreasuryView(env, requestId).then((view) =>
      businessResponse(requestId, pathname, view),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/wallet-classes`) {
    return businessResponse(requestId, pathname, deriveWalletClasses());
  }
  if (pathname === `${BUSINESS_PREFIX}/wallet-scopes`) {
    return businessResponse(requestId, pathname, deriveWalletScopes());
  }
  if (pathname === `${BUSINESS_PREFIX}/wallet-policy-matrix`) {
    return businessResponse(requestId, pathname, deriveWalletPolicyMatrix());
  }
  if (pathname === `${BUSINESS_PREFIX}/internal-ops`) {
    return readBusinessState(env, requestId).then((business) =>
      businessResponse(requestId, pathname, deriveInternalOpsSummary(business)),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/empire-manifest`) {
    return businessResponse(requestId, pathname, BUSINESS_EMPIRE_MANIFEST);
  }
  if (pathname === `${BUSINESS_PREFIX}/total-mesh-protocol`) {
    return businessResponse(requestId, pathname, BUSINESS_TOTAL_MESH_PROTOCOL);
  }
  if (pathname === `${BUSINESS_PREFIX}/secure/live-registries`) {
    const denied = requireBusinessSecret(request, env, requestId, pathname);
    if (denied) return denied;
    return readBusinessState(env, requestId).then((business) =>
      businessResponse(requestId, pathname, {
        secure: true,
        title: "Live business registries",
        last_write_at: business.last_write_at,
        clients: business.clients,
        jobs: business.jobs,
        quotes_invoices: business.quotes_invoices,
        identities: business.identities,
        wallets_custody: business.wallets_custody,
      }),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/secure/wallets-custody`) {
    const denied = requireBusinessSecret(request, env, requestId, pathname);
    if (denied) return denied;
    return deriveWalletCustodyRegistry(env, requestId).then((registry) =>
      businessResponse(requestId, pathname, {
        secure: true,
        ...registry,
      }),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/secure/operator-roster`) {
    const denied = requireBusinessSecret(request, env, requestId, pathname);
    if (denied) return denied;
    return readBusinessState(env, requestId).then((business) =>
      businessResponse(requestId, pathname, {
        secure: true,
        ...buildOperatorRoster(business),
      }),
    );
  }
  if (pathname === `${BUSINESS_PREFIX}/secure/alpha-client`) {
    const denied = requireBusinessSecret(request, env, requestId, pathname);
    if (denied) return denied;
    return businessResponse(requestId, pathname, {
      secure: true,
      ...SECURE_ALPHA_CLIENT_DETAIL,
    });
  }
  if (pathname === `${BUSINESS_PREFIX}/secure/billing-tunnel`) {
    const denied = requireBusinessSecret(request, env, requestId, pathname);
    if (denied) return denied;
    return businessResponse(requestId, pathname, {
      secure: true,
      ...SECURE_BILLING_TUNNEL_DETAIL,
    });
  }
  return null;
}

function shouldProxyPath(pathname) {
  return ALLOWED_PATH_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

function jsonResponse(payload, init = {}) {
  const headers = new Headers(init.headers || {});
  headers.set("content-type", "application/json; charset=utf-8");
  headers.set("cache-control", "no-store");
  headers.set("access-control-allow-origin", "*");
  headers.set("access-control-allow-methods", "GET,HEAD,POST,OPTIONS");
  headers.set("access-control-allow-headers", "*");
  return new Response(JSON.stringify(payload, null, 2), {
    ...init,
    headers,
  });
}

async function fetchOriginJson(pathname, env, requestId) {
  const target = new URL(pathname, env.ORIGIN_BASE);
  target.searchParams.set("_r", requestId);
  const headers = new Headers({
    accept: "application/json",
    "user-agent": "trinity-s25-proxy/omega",
    "x-trinity-request-id": requestId,
    "cache-control": "no-store",
  });
  if (env.ORIGIN_HOST_HEADER) {
    headers.set("host", env.ORIGIN_HOST_HEADER);
  }
  if (env.S25_SHARED_SECRET) {
    headers.set("x-s25-secret", env.S25_SHARED_SECRET);
  }
  const response = await fetch(target, {
    headers,
    redirect: "follow",
    cache: "no-store",
    cf: {
      cacheEverything: false,
      cacheTtl: 0,
    },
  });
  if (!response.ok) {
    throw new Error(`origin_${response.status}_${pathname}`);
  }
  return response.json();
}

async function fetchPublicRuntimeJson(pathname, env, requestId) {
  const target = new URL(pathname, env.PUBLIC_RUNTIME_URL || env.PUBLIC_GATEWAY_URL);
  target.searchParams.set("_r", requestId);
  const headers = new Headers({
    accept: "application/json",
    "user-agent": "trinity-s25-proxy/omega",
    "x-trinity-request-id": requestId,
    "cache-control": "no-store",
  });
  if (env.S25_SHARED_SECRET) {
    headers.set("x-s25-secret", env.S25_SHARED_SECRET);
  }
  const response = await fetch(target, {
    headers,
    redirect: "follow",
    cache: "no-store",
    cf: {
      cacheEverything: false,
      cacheTtl: 0,
    },
  });
  if (!response.ok) {
    throw new Error(`public_runtime_${response.status}_${pathname}`);
  }
  return response.json();
}

async function probeJson(url) {
  const response = await fetch(url, {
    headers: {
      accept: "application/json",
      "user-agent": "trinity-s25-proxy/omega",
    },
    redirect: "follow",
  });
  return {
    ok: response.ok,
    status: response.status,
    payload: response.ok ? await response.json() : null,
  };
}

async function probeUrl(url) {
  if (!url) {
    return {
      state: "unexposed",
      http_status: null,
      ok: false,
    };
  }
  try {
    const response = await fetch(url, {
      headers: {
        accept: "application/json,text/plain,*/*",
        "user-agent": "trinity-s25-proxy/omega",
      },
      redirect: "follow",
    });
    return {
      state: response.ok ? "online" : "degraded",
      http_status: response.status,
      ok: response.ok,
    };
  } catch (error) {
    return {
      state: "offline",
      http_status: null,
      ok: false,
      error: String(error),
    };
  }
}

async function handleMeshGateway(requestId, env) {
  const [meshResult, statusResult, missionsResult] = await Promise.allSettled([
    fetchOriginJson("/api/mesh/status", env, requestId),
    fetchOriginJson("/api/status", env, requestId),
    fetchOriginJson("/api/missions", env, requestId),
  ]);
  const meshPayload = meshResult.status === "fulfilled" ? meshResult.value : { mesh: { agents: {} } };
  const statusPayload = statusResult.status === "fulfilled" ? statusResult.value : {};
  const missionsPayload = missionsResult.status === "fulfilled" ? missionsResult.value : { active: [] };
  const liveAgents = meshPayload?.mesh?.agents || {};
  const roster = OMEGA_AGENT_ORDER.map((name) => {
    const runtime = liveAgents[name] || {};
    const matrix = OMEGA_AGENT_MATRIX[name] || {};
    return {
      agent_id: name,
      status: runtime.status || "offline",
      last_seen: runtime.last_seen || null,
      last_task: runtime.last_task || null,
      role_id: matrix.role_id || "unbound",
      badge_id: matrix.badge_id || "unbound",
      scope_id: matrix.scope_id || "unbound",
      action_surface: matrix.action_surface || "unbound",
    };
  });
  const onlineCount = roster.filter((agent) => !["offline", "unknown"].includes(agent.status)).length;
  const readiness = onlineCount >= 12 ? "mesh_total" : onlineCount >= 8 ? "mesh_partial" : "mesh_fragile";
  return jsonResponse({
    ...(meshPayload || {}),
    omega: {
      protocol: "S25_OMEGA_PROTOCOL",
      readiness,
      online_count: onlineCount,
      target_headcount: OMEGA_AGENT_ORDER.length,
      mission_head: missionsPayload?.active?.[0] || null,
      command_chain: [
        "TRINITY -> mission_control",
        "MERLIN -> validation",
        "COMET -> ops_followup",
        "GOUV4 -> policy",
        "ARKON -> runtime",
      ],
      status_summary: statusPayload.summary_fr || null,
    },
    roster,
  });
}

async function handleVaultMexcGateway(requestId, env) {
  const [statusResult, missionsResult] = await Promise.allSettled([
    fetchOriginJson("/api/status", env, requestId),
    fetchOriginJson("/api/missions", env, requestId),
  ]);
  const statusPayload = statusResult.status === "fulfilled" ? statusResult.value : {};
  const missionsPayload = missionsResult.status === "fulfilled" ? missionsResult.value : { active: [] };
  const treasuryMission = (missionsPayload.active || []).find((mission) => mission.target === "TREASURY") || null;
  return jsonResponse({
    ok: true,
    request_id: requestId,
    service: "vault_mexc",
    exchange: "MEXC",
    mode: statusPayload.pipeline_status === "MESH_READY" ? "armed_readiness" : "cold_start",
    arbitrage_loop: ["BTC/USDT", "BTC/AKT", "AKT/USDT"],
    profitability: {
      realized_profit_24h: null,
      realized_profit_currency: "USDT",
      vault_balance: null,
      vault_balance_currency: "AKT",
      spread_capture_bps: null,
      execution_state: treasuryMission ? treasuryMission.status : "awaiting_trade_binding",
      data_state: "exchange_binding_pending_secure_runtime",
    },
    price_context: {
      btc_usd: statusPayload.btc_usd ?? null,
      eth_usd: statusPayload.eth_usd ?? null,
      arkon5_action: statusPayload.arkon5_action ?? null,
      arkon5_conf: statusPayload.arkon5_conf ?? null,
    },
    guardrails: {
      route_protected: true,
      secret_required_for_trade_write: true,
      operator_mode: "read_only_until_exchange_worker_bound",
    },
  });
}

async function handleAkashInfraGateway(requestId) {
  const deployments = await Promise.all(
    AKASH_DEPLOYMENT_MODEL.map(async (deployment) => {
      const probe = await probeUrl(deployment.probe_url);
      return {
        ...deployment,
        uptime_state: probe.state,
        http_status: probe.http_status,
        probe_ok: probe.ok,
      };
    }),
  );
  const cpuReady = deployments.filter((deployment) => deployment.role === "cpu_runtime" && deployment.probe_ok).length;
  const gpuTracked = deployments.filter((deployment) => deployment.role === "gpu_runtime").length;
  return jsonResponse({
    ok: true,
    request_id: requestId,
    service: "akash_infra",
    cluster: {
      cpu_ready: cpuReady,
      gpu_tracked: gpuTracked,
      mesh_bridge_ready: deployments.some((deployment) => deployment.role === "mcp_bridge" && deployment.probe_ok),
      doctrine: "Akash-first with sovereign facade on smajor.org",
    },
    deployments,
  });
}

function copyRequestHeaders(headers, requestId, env, clientIp) {
  const out = new Headers();
  for (const [key, value] of headers.entries()) {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      out.set(key, value);
    }
  }
  if (env.ORIGIN_HOST_HEADER) {
    out.set("host", env.ORIGIN_HOST_HEADER);
  }
  if (env.S25_SHARED_SECRET) {
    out.set("x-s25-secret", env.S25_SHARED_SECRET);
  }
  out.set("x-trinity-request-id", requestId);
  if (clientIp) {
    out.set("x-forwarded-for", clientIp);
    out.set("cf-connecting-ip", clientIp);
  }
  return out;
}

function copyResponseHeaders(headers, requestId) {
  const out = new Headers();
  for (const [key, value] of headers.entries()) {
    if (!HOP_BY_HOP_HEADERS.has(key.toLowerCase())) {
      out.set(key, value);
    }
  }
  out.set("cache-control", "no-store");
  out.set("access-control-allow-origin", "*");
  out.set("access-control-allow-methods", "GET,HEAD,POST,OPTIONS");
  out.set("access-control-allow-headers", "*");
  out.set("x-trinity-request-id", requestId);
  out.set("x-trinity-proxy", "trinity-s25-proxy");
  return out;
}

function buildProxyMeta(env, requestId, targetUrl) {
  return {
    ok: true,
    service: "trinity-s25-proxy",
    request_id: requestId,
    target_origin: new URL(env.ORIGIN_BASE).origin,
    target_url: targetUrl.toString(),
    timeout_ms: Number(env.PROXY_TIMEOUT_MS || 15000),
    retries: Number(env.PROXY_RETRIES || 1),
    shared_secret_configured: Boolean(env.S25_SHARED_SECRET),
  };
}

async function fetchWithPolicy(target, request, env, requestId) {
  const timeoutMs = Number(env.PROXY_TIMEOUT_MS || 15000);
  const maxRetries = Math.max(0, Number(env.PROXY_RETRIES || 1));
  const clientIp = request.headers.get("cf-connecting-ip") || "";
  const method = request.method.toUpperCase();
  const canRetry = method === "GET" || method === "HEAD";
  const bodyBuffer =
    method === "GET" || method === "HEAD" ? undefined : await request.arrayBuffer();

  let attempt = 0;
  let lastError = null;

  while (attempt <= maxRetries) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort("proxy-timeout"), timeoutMs);
    try {
      const upstream = await fetch(target, {
        method,
        headers: copyRequestHeaders(request.headers, requestId, env, clientIp),
        redirect: "follow",
        body: bodyBuffer,
        signal: controller.signal,
      });

      if (!canRetry || !RETRYABLE_STATUS_CODES.has(upstream.status) || attempt === maxRetries) {
        return upstream;
      }
      lastError = new Error(`upstream-status-${upstream.status}`);
    } catch (error) {
      lastError = error;
      if (!canRetry || attempt === maxRetries) {
        throw error;
      }
    } finally {
      clearTimeout(timeout);
    }

    attempt += 1;
  }

  throw lastError || new Error("proxy-failed");
}

export default {
  async fetch(request, env) {
    const incoming = new URL(request.url);
    const requestId = crypto.randomUUID();

    if (request.method === "OPTIONS") {
      return jsonResponse(
        { ok: true, request_id: requestId, methods: ["GET", "HEAD", "POST", "OPTIONS"] },
        { status: 204 }
      );
    }

    if (incoming.pathname === "/health" || incoming.pathname === "/api/health") {
      return jsonResponse(buildProxyMeta(env, requestId, buildTargetUrl(request.url, env.ORIGIN_BASE)));
    }

    if (incoming.pathname === "/api/mesh/status") {
      return handleMeshGateway(requestId, env);
    }

    if (incoming.pathname === "/api/vault/mexc") {
      return handleVaultMexcGateway(requestId, env);
    }

    if (incoming.pathname === "/api/akash/infra") {
      return handleAkashInfraGateway(requestId);
    }

    const businessRoute = handleBusinessRequest(request, incoming.pathname, requestId, env);
    if (businessRoute) {
      return businessRoute;
    }

    if (!shouldProxyPath(incoming.pathname)) {
      return jsonResponse(
        {
          ok: false,
          error: "path_not_allowed",
          request_id: requestId,
          pathname: incoming.pathname,
        },
        { status: 404 }
      );
    }

    const target = buildTargetUrl(request.url, env.ORIGIN_BASE);
    try {
      const upstream = await fetchWithPolicy(target, request, env, requestId);
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: copyResponseHeaders(upstream.headers, requestId),
      });
    } catch (error) {
      return jsonResponse(
        {
          ok: false,
          error: "upstream_unreachable",
          request_id: requestId,
          detail: String(error),
          target: target.toString(),
        },
        { status: 502 }
      );
    }
  },
};
