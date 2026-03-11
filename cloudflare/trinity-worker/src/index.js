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
    `${BUSINESS_PREFIX}/role-governance`,
    `${BUSINESS_PREFIX}/rbac-matrix`,
    `${BUSINESS_PREFIX}/agent-catalog`,
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
    { key: "empire_manifest", path: `${BUSINESS_PREFIX}/empire-manifest`, purpose: "Unified manifest of domains, towers, registries and command chain" },
    { key: "total_mesh_protocol", path: `${BUSINESS_PREFIX}/total-mesh-protocol`, purpose: "Protocol de synchronisation totale des agents vers le hub" },
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
    return businessResponse(requestId, pathname, BUSINESS_CLIENT_REGISTRY_LIVE);
  }
  if (pathname === `${BUSINESS_PREFIX}/job-registry-live`) {
    return businessResponse(requestId, pathname, BUSINESS_JOB_REGISTRY_LIVE);
  }
  if (pathname === `${BUSINESS_PREFIX}/quotes-invoices-live`) {
    return businessResponse(requestId, pathname, BUSINESS_QUOTES_INVOICES_LIVE);
  }
  if (pathname === `${BUSINESS_PREFIX}/empire-manifest`) {
    return businessResponse(requestId, pathname, BUSINESS_EMPIRE_MANIFEST);
  }
  if (pathname === `${BUSINESS_PREFIX}/total-mesh-protocol`) {
    return businessResponse(requestId, pathname, BUSINESS_TOTAL_MESH_PROTOCOL);
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
