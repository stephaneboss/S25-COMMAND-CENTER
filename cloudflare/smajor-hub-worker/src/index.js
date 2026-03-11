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
        text: "Creer un dossier vivant, suivre un service, recuperer un devis, consulter facture et etat du contrat.",
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
        text: "Le backoffice doit afficher le status S25, les missions, les alertes et les registres metier modifiables.",
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
  "/omega": {
    label: "Omega",
    eyebrow: "S25 Command Center",
    heroTitle: "Le tableau souverain pour conduire l'empire en temps reel.",
    heroText:
      "Omega consolide le header strategique, le maillage des 15 agents, le terminal d'operations et la posture finance/infra sur une seule surface de commandement.",
    cards: [
      {
        label: "Header",
        title: "Uptime, HA et vault",
        text: "Le command center doit exposer la sante globale du systeme et les signaux de fragilite sans ouvrir tout le backend.",
      },
      {
        label: "Mesh",
        title: "Agents en formation",
        text: "Chaque agent garde son role, son badge, son scope et sa surface d'action. La vue doit rester lisible meme sous charge.",
      },
      {
        label: "Finance",
        title: "Profit contre cout",
        text: "La rentabilite MEXC, les couts Akash et la posture de tresorerie doivent etre surveilles sur la meme ligne de front.",
      },
    ],
  },
};

const WORKBENCH_SECTIONS = {
  "/": {
    title: "Feuille de route immediate",
    intro: "Le shell doit devenir la porte d'entree unique pour l'entreprise, sans sortir la logique critique du mesh.",
    columns: [
      {
        label: "MVP",
        items: [
          "Afficher le status, les missions et le mesh en direct.",
          "Servir de facade unique pour operators, clients et agents.",
          "Pointer les integrations vers api.smajor.org.",
        ],
      },
      {
        label: "Ensuite",
        items: [
          "Ouvrir le portail client avec demandes, devis et suivi.",
          "Ouvrir le poste admin avec dispatch, permissions et marges.",
          "Connecter staff et vendors a un workflow lisible.",
        ],
      },
      {
        label: "Regle",
        items: [
          "Aucune logique critique durable dans le front.",
          "Chaque action importante doit remonter dans S25.",
          "Le domaine est la facade, Akash reste le muscle.",
        ],
      },
    ],
  },
  "/clients": {
    title: "Portail client cible",
    intro: "On prepare une interface simple pour le client, pendant que S25 garde l'orchestration, les relances et le routage.",
    columns: [
      {
        label: "Demandes",
        items: [
          "Nouvelle demande de service.",
          "Suivi de dossier et statut chantier.",
          "Canal de contact propre avec historique.",
        ],
      },
      {
        label: "Documents",
        items: [
          "Devis a signer.",
          "Factures et paiements.",
          "Photos et preuves de service.",
        ],
      },
      {
        label: "Automations",
        items: [
          "Relances automatiques par S25.",
          "Tri des urgences selon le service.",
          "Passage propre vers admin et staff.",
        ],
      },
    ],
  },
  "/admin": {
    title: "Poste de commandement",
    intro: "L'admin doit voir la machine complete: operations, IA, cash, permissions et chaines metier.",
    columns: [
      {
        label: "Pilotage",
        items: [
          "Etat du mesh et alertes critiques.",
          "Priorite des missions et file de travail.",
          "Vue des services actifs par domaine.",
        ],
      },
      {
        label: "Gouvernance",
        items: [
          "Regles d'agents et garde-fous humains.",
          "Secrets, domaines et acces critiques.",
          "Journal de decisions majeures.",
        ],
      },
      {
        label: "Business",
        items: [
          "Marges chantier et facturation.",
          "Suivi paiements et fournisseurs.",
          "Visibilite couts infra et operations.",
        ],
      },
    ],
  },
  "/staff": {
    title: "Execution terrain",
    intro: "Le staff doit voir quoi faire, ou aller et quoi remonter, sans se battre avec le backend.",
    columns: [
      {
        label: "Dispatch",
        items: [
          "Taches assignees et priorite.",
          "Fenetre horaire et lieu d'intervention.",
          "Brief IA de terrain avant depart.",
        ],
      },
      {
        label: "Rapports",
        items: [
          "Debut / fin d'intervention.",
          "Photos, incidents et note terrain.",
          "Validation rapide de completion.",
        ],
      },
      {
        label: "Support",
        items: [
          "Escalade rapide vers admin.",
          "Historique equipement / materiel.",
          "Consignes meteos et securite.",
        ],
      },
    ],
  },
  "/vendors": {
    title: "Chaine fournisseurs",
    intro: "Les achats et locations doivent devenir tracables, relies aux chantiers et visibles pour l'admin.",
    columns: [
      {
        label: "Commandes",
        items: [
          "Bons de commande centralises.",
          "Demandes de prix et comparatifs.",
          "Pieces, carburant, materiaux, location.",
        ],
      },
      {
        label: "Controle",
        items: [
          "Approbation par seuil de cout.",
          "Suivi livraison et reception.",
          "Pieces manquantes ou retards critiques.",
        ],
      },
      {
        label: "Integration",
        items: [
          "Rattacher chaque cout a un dossier client.",
          "Remonter dans le backoffice admin.",
          "Preparer les flux de facturation et marge.",
        ],
      },
    ],
  },
  "/ai": {
    title: "Organisation agentique",
    intro: "La branche AI doit servir le business concret: surveiller, proposer, orchestrer et expliquer.",
    columns: [
      {
        label: "Roles",
        items: [
          "TRINITY orchestre les chaines.",
          "MERLIN valide et memorise.",
          "COMET surveille web et executions externes.",
        ],
      },
      {
        label: "Capteurs",
        items: [
          "KIMI pompe la data Web3.",
          "ORACLE confirme les prix.",
          "ONCHAIN_GUARDIAN surveille les signaux onchain.",
        ],
      },
      {
        label: "But",
        items: [
          "Rendre l'entreprise plus lisible et plus rapide.",
          "Diminuer la charge mentale humaine.",
          "Laisser un historique clair des decisions et actions.",
        ],
      },
    ],
  },
};

const MODULE_BLUEPRINTS = {
  clients: {
    title: "Client dossier blueprint",
    records: [
      "client_account",
      "service_site",
      "service_request",
      "quote",
      "work_order",
      "invoice",
      "payment_status",
    ],
    pipeline: [
      "lead_received",
      "qualified",
      "quote_sent",
      "approved",
      "scheduled",
      "in_service",
      "completed",
      "invoiced",
      "paid",
    ],
    automations: [
      "S25 route une demande selon service, urgence et zone.",
      "TRINITY cree une mission si un dossier bloque ou derape.",
      "COMET alimente les alertes de suivi et les escalades externes.",
    ],
  },
  admin: {
    title: "Admin command blueprint",
    records: [
      "operator",
      "role_policy",
      "dispatch_board",
      "finance_snapshot",
      "agent_guardrail",
      "audit_event",
    ],
    pipeline: [
      "observe",
      "prioritize",
      "assign",
      "validate",
      "approve",
      "close_loop",
    ],
    automations: [
      "S25 consolide status, missions, marge et alertes.",
      "MERLIN ecrit un feedback structure quand une decision critique doit etre justifiee.",
      "Le backoffice doit toujours garder une piste d'audit.",
    ],
  },
  staff: {
    title: "Field execution blueprint",
    records: [
      "crew_member",
      "shift",
      "assignment",
      "field_report",
      "equipment_usage",
      "incident",
    ],
    pipeline: [
      "assigned",
      "accepted",
      "en_route",
      "on_site",
      "report_submitted",
      "validated",
    ],
    automations: [
      "Dispatch prepare le brief terrain depuis le dossier client.",
      "S25 remonte les incidents et les bloqueurs au poste admin.",
      "Le rapport de fin de job nourrit l'historique client.",
    ],
  },
  vendors: {
    title: "Vendor flow blueprint",
    records: [
      "vendor",
      "purchase_request",
      "purchase_order",
      "delivery_receipt",
      "cost_entry",
      "approval_note",
    ],
    pipeline: [
      "requested",
      "quoted",
      "approved",
      "ordered",
      "received",
      "matched_to_job",
      "closed",
    ],
    automations: [
      "Le cout doit etre rattache a un job ou un centre de cout.",
      "Les seuils budget doivent declencher revue humaine.",
      "Admin voit l'impact marge sans lire les bons manuellement.",
    ],
  },
  ai: {
    title: "AI operating blueprint",
    records: [
      "mission",
      "intel_entry",
      "agent_state",
      "validation_note",
      "handoff",
    ],
    pipeline: [
      "observe",
      "decide",
      "route",
      "validate",
      "record",
      "review",
    ],
    automations: [
      "TRINITY orchestre.",
      "MERLIN valide et memorise.",
      "Les autres agents nourrissent le systeme sans devenir source de verite unique.",
    ],
  },
};

const ACCESS_MODEL = {
  title: "Strict administration chain",
  doctrine: [
    "Chaque personne ou organisation existe comme identite gerable dans le systeme.",
    "Chaque identite recoit un role, un scope et des services actives.",
    "Aucun acces implicite: tout acces doit etre assigne puis revele dans l'admin.",
  ],
  identity_types: [
    "client_org",
    "client_contact",
    "employee",
    "contractor",
    "vendor_org",
    "vendor_contact",
    "operator_admin",
  ],
  core_records: [
    "identity",
    "organization",
    "membership",
    "service_entitlement",
    "credential_state",
    "policy_scope",
    "audit_log",
  ],
  activation_flow: [
    "identity_created",
    "linked_to_org",
    "role_assigned",
    "services_enabled",
    "credentials_issued",
    "portal_access_live",
  ],
  service_catalog: [
    "snow_ops",
    "excavation_ops",
    "client_portal",
    "staff_portal",
    "vendor_portal",
    "billing_access",
    "ai_services",
    "admin_console",
  ],
};

const ROLE_GOVERNANCE = {
  title: "Role governance model",
  summary: "Le systeme ne repose pas sur la confiance humaine. Il repose sur des roles, des scopes, des services actives et une chaine d'audit.",
  doctrine: [
    "Le role passe avant la personne.",
    "Chaque pouvoir doit venir d'un role publie et tracable.",
    "Aucune elevation de privilege sans validation admin.",
    "Les services actives sont limites par role, scope et portail.",
    "La structure doit survivre a l'utilisateur.",
  ],
  badge_system: {
    summary: "Le badge represente le moule. La personne peut changer, le badge et le role restent stables.",
    badge_types: [
      { key: "major_badge", label: "Major badge", binds_to: "founder|executive_operator|operator_admin" },
      { key: "employee_badge", label: "Employee badge", binds_to: "dispatcher|field_manager|staff_member|contractor" },
      { key: "client_badge", label: "Client badge", binds_to: "client_owner|client_contact" },
      { key: "vendor_badge", label: "Vendor badge", binds_to: "vendor_manager|vendor_contact" },
      { key: "ai_badge", label: "AI badge", binds_to: "trinity_orchestrator|merlin_validator|comet_watch|kimi_sensor" },
    ],
  },
  identity_binding: [
    "identity_id -> role_id -> badge_id -> scope_id -> service_entitlements",
    "aucune fonction critique ne doit etre attachee a un nom fixe",
    "si une personne change, on revoque la cle et on rattache une nouvelle identity_id au meme role_id",
  ],
  layers: [
    {
      label: "Direction",
      roles: ["founder", "executive_operator", "operator_admin"],
      powers: ["identity_control", "finance_approval", "governance", "agent_policies"],
    },
    {
      label: "Operations",
      roles: ["dispatcher", "field_manager", "staff_member", "contractor"],
      powers: ["job_dispatch", "field_reports", "schedule_visibility", "equipment_tracking"],
    },
    {
      label: "External",
      roles: ["client_owner", "client_contact", "vendor_manager", "vendor_contact"],
      powers: ["portal_access", "document_exchange", "limited_approvals", "billing_visibility"],
    },
    {
      label: "AI",
      roles: ["trinity_orchestrator", "merlin_validator", "comet_watch", "kimi_sensor"],
      powers: ["observe", "route", "validate", "record"],
    },
  ],
  enforcement_chain: [
    "identity_created",
    "badge_template_selected",
    "role_template_selected",
    "scope_assigned",
    "services_enabled",
    "credentials_issued",
    "audit_watch_started",
  ],
};

const SYSTEM_AXES = {
  title: "Smajor three-axis system",
  summary: "Le systeme doit tenir en meme temps le business terrain, l'administration stricte et le backend IA multi-agent.",
  axes: [
    {
      key: "field_business",
      label: "Business terrain",
      scope: [
        "excavation",
        "deneigement",
        "services exterieurs",
        "clients actifs",
        "camions, pelle, equipes, jobs",
      ],
      target: "Recevoir une demande, planifier, envoyer les hommes, executer, facturer et cloturer proprement.",
    },
    {
      key: "strict_administration",
      label: "Administration temps reel",
      scope: [
        "identites",
        "roles",
        "services actives",
        "acces portail",
        "dispatch",
        "suivi fournisseurs et employes",
      ],
      target: "Controler qui accede a quoi, quel service est actif, et quelle chaine humaine ou IA porte l'action.",
    },
    {
      key: "ai_backend",
      label: "Backend IA / S25",
      scope: [
        "S25 cockpit",
        "missions",
        "MERLIN MCP",
        "TRINITY",
        "COMET",
        "mesh Akash",
      ],
      target: "Orchestrer, memoriser, surveiller et stabiliser l'infra sans casser le business reel.",
    },
  ],
};

const MASTER_REGISTRY = {
  title: "Smajor master registry",
  summary: "Une colonne vertebrale de registres pour pouvoir gerer plusieurs entreprises, plusieurs clients, plusieurs equipes et plusieurs services.",
  registries: [
    {
      key: "organization_registry",
      label: "Organizations",
      records: ["holding", "division", "brand", "operating_entity", "site"],
    },
    {
      key: "identity_registry",
      label: "Identities",
      records: ["client_contact", "employee", "contractor", "vendor_contact", "admin_operator"],
    },
    {
      key: "service_registry",
      label: "Services",
      records: ["snow_contract", "excavation_job", "exterior_service", "ai_consulting", "ai_automation"],
    },
    {
      key: "asset_registry",
      label: "Assets",
      records: ["truck", "excavator", "attachment", "equipment", "availability"],
    },
    {
      key: "job_registry",
      label: "Jobs",
      records: ["request", "quote", "work_order", "schedule", "completion"],
    },
    {
      key: "finance_registry",
      label: "Finance",
      records: ["invoice", "payment", "margin", "vendor_cost", "cash_snapshot"],
    },
    {
      key: "vendor_registry",
      label: "Vendors",
      records: ["vendor", "vendor_contact", "purchase_order", "delivery_receipt", "approval"],
    },
    {
      key: "ai_registry",
      label: "AI agents",
      records: ["agent", "role", "permission", "surface", "cost", "criticality"],
    },
  ],
};

const MVP_REGISTRIES = {
  clients: {
    title: "Clients registry MVP",
    description: "Registre minimum pour gerer de nouveaux clients sans trainer l'ancien hiver.",
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
    description: "Registre minimum pour suivre les interventions reelles sur le terrain.",
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
  finance: {
    title: "Quotes and invoices registry MVP",
    description: "Registre minimum pour devis, factures et suivi paiements.",
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
};

const MAJOR_CONTROL_PLANE = {
  title: "Major control plane",
  summary: "Le site doit agir comme un boss d'entreprise: controler le business terrain, les humains, les fournisseurs, les agents et les surfaces critiques.",
  towers: [
    {
      key: "customer_success",
      label: "Customer success",
      scope: ["lead intake", "client registry", "quotes", "contracts", "invoices", "payment follow-up"],
    },
    {
      key: "field_ops",
      label: "Field ops",
      scope: ["dispatch", "crews", "trucks", "excavator", "weather pressure", "job reports"],
    },
    {
      key: "admin_governance",
      label: "Admin governance",
      scope: ["identity access", "service entitlements", "audit", "policies", "critical approvals"],
    },
    {
      key: "vendor_finance",
      label: "Vendor finance",
      scope: ["purchase orders", "vendor costs", "margin", "cash snapshot", "billing controls"],
    },
    {
      key: "ai_ops",
      label: "AI ops",
      scope: ["TRINITY", "MERLIN", "COMET", "KIMI", "MCP", "missions", "intel"],
    },
    {
      key: "secure_growth",
      label: "Secure growth",
      scope: ["secret governance", "runtime isolation", "domain surfaces", "trade readiness", "operator review"],
    },
  ],
};

const FOUNDATION_STACK = {
  title: "Smajor foundation stack",
  summary: "Un seul backbone business, une seule facade, une seule couche IA d'orchestration.",
  layers: [
    {
      key: "business_backbone",
      label: "ERPNext / Frappe",
      role: "Backbone business pour clients, devis, factures, achats, jobs, assets et workflows.",
    },
    {
      key: "workforce_backbone",
      label: "Frappe HRMS",
      role: "Backbone RH pour employes, onboarding, shifts et structure workforce.",
    },
    {
      key: "custom_facade",
      label: "Smajor facade",
      role: "Experience sur mesure pour clients, staff, vendors, admin et control plane.",
    },
    {
      key: "ai_orchestration",
      label: "S25 + MERLIN MCP + TRINITY",
      role: "Orchestration IA, missions, intel, gouvernance runtime et multi-agent ops.",
    },
    {
      key: "optional_sales_crm",
      label: "Twenty (optional later)",
      role: "Couche CRM ventes moderne si necessaire, mais pas centre de gravite operations.",
    },
  ],
};

const VISITOR_STRUCTURE = {
  title: "Smajor visitor structure",
  intro: "Un visiteur doit comprendre en quelques secondes ou il entre, a quoi sert le portail et quel service il peut activer.",
  columns: [
    {
      label: "Clients",
      items: [
        "Demander un service.",
        "Recevoir un devis.",
        "Suivre un job.",
        "Consulter facture et statut.",
      ],
    },
    {
      label: "Employes",
      items: [
        "Voir les taches.",
        "Recevoir le dispatch.",
        "Envoyer un rapport terrain.",
        "Suivre l'organisation quotidienne.",
      ],
    },
    {
      label: "Fournisseurs",
      items: [
        "Recevoir les bons de commande.",
        "Confirmer livraison ou disponibilite.",
        "Echanger les documents utiles.",
        "Rattacher les couts aux jobs.",
      ],
    },
  ],
};

const PORTAL_MATRIX = {
  title: "Portal matrix",
  summary: "Chaque type d'acteur entre par un portail clair, avec des services actives selon son role.",
  portals: [
    {
      key: "clients_portal",
      label: "Client portal",
      audience: "Clients actifs",
      services: ["snow_ops", "excavation_ops", "billing_access", "ai_services"],
    },
    {
      key: "staff_portal",
      label: "Staff portal",
      audience: "Employes et sous-traitants",
      services: ["dispatch", "job_execution", "field_reports", "staff_portal"],
    },
    {
      key: "vendor_portal",
      label: "Vendor portal",
      audience: "Fournisseurs",
      services: ["purchase_orders", "delivery_flow", "vendor_portal", "billing_access"],
    },
    {
      key: "admin_console",
      label: "Admin console",
      audience: "Stef et operateurs admin",
      services: ["identity_access", "finance", "governance", "ai_ops", "trade_readiness"],
    },
  ],
};

const IDENTITY_REGISTRY_MODEL = {
  title: "Identity registry model",
  summary: "Chaque acteur entre dans le systeme via une identite operable reliee a un role, un badge, un scope et un portail.",
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
    "bind_role_template",
    "attach_scope",
    "enable_services",
    "issue_or_rotate_credential",
  ],
};

const PORTAL_ACTIVATION_MODEL = {
  title: "Portal activation model",
  summary: "Un portail ne s'ouvre qu'apres la chaine complete d'activation identite-role-badge-scope.",
  tracks: [
    {
      label: "Clients",
      items: ["identity_id", "client_badge", "client_contact", "client_scope", "billing_access", "portal_live"],
    },
    {
      label: "Staff",
      items: ["identity_id", "employee_badge", "staff_member", "field_scope", "dispatch_ready", "portal_live"],
    },
    {
      label: "Vendors",
      items: ["identity_id", "vendor_badge", "vendor_contact", "vendor_scope", "purchase_access", "portal_live"],
    },
    {
      label: "Admin",
      items: ["identity_id", "major_badge", "operator_admin", "governance_scope", "admin_console", "hardened_access"],
    },
  ],
};

const CLIENT_FORM_MODEL = {
  title: "Client intake form",
  summary: "Formulaire type pour faire entrer un client dans le systeme avec la bonne chaine d'identite et de service.",
  columns: [
    {
      label: "Identity",
      items: ["organization_name", "contact_name", "contact_email", "contact_phone"],
    },
    {
      label: "Service",
      items: ["service_type", "site_address", "urgency_level", "service_window"],
    },
    {
      label: "Commercial",
      items: ["quote_required", "billing_contact", "contract_mode", "notes"],
    },
  ],
};

const STAFF_DASHBOARD_MODEL = {
  title: "Staff dashboard",
  summary: "Vue terrain pour l'equipe: quoi faire, ou aller, quoi remonter et quoi ne pas toucher.",
  columns: [
    {
      label: "Shift",
      items: ["today_assignments", "start_window", "priority_jobs"],
    },
    {
      label: "Field",
      items: ["job_brief", "site_address", "equipment_required", "incident_flag"],
    },
    {
      label: "Completion",
      items: ["report_submit", "photo_upload", "time_close", "escalation_note"],
    },
  ],
};

const CLIENT_REGISTRY_LIVE_MODEL = {
  title: "Client registry live",
  summary: "Premiers comptes vivants pour piloter le portail client, la facturation et les services actives.",
  columns: [
    {
      label: "Active clients",
      items: [
        "client-alpha-001 | Alpha Yard Services | active",
        "client-major-lab-001 | Major AI Lab Pilot | pilot_active",
      ],
    },
    {
      label: "Bindings",
      items: [
        "client_contact -> client_badge -> client_scope_alpha",
        "client_contact -> client_badge -> client_scope_major_lab",
      ],
    },
    {
      label: "Commercial",
      items: [
        "invoice_ready",
        "quote_prepared",
        "portal_state pending_secure_access/live",
      ],
    },
  ],
};

const JOB_REGISTRY_LIVE_MODEL = {
  title: "Job registry live",
  summary: "Premiers jobs vivants relies a des equipes, des scopes et des fenetres d'intervention.",
  columns: [
    {
      label: "Field jobs",
      items: [
        "job-alpha-yard-001 | excavation | crew-east-01",
        "2026-03-13 AM | mini-excavator-02 | scheduled",
      ],
    },
    {
      label: "AI jobs",
      items: [
        "job-major-lab-ops-001 | ai_automation | ai-ops-s25",
        "2026-03-14 PM | trinity, merlin, comet | briefing",
      ],
    },
    {
      label: "Scopes",
      items: [
        "field_scope_east",
        "ai_scope_smajor",
      ],
    },
  ],
};

const QUOTES_INVOICES_LIVE_MODEL = {
  title: "Quotes and invoices live",
  summary: "Premiers devis et factures vivants pour valider le tunnel commercial sans ouvrir la vraie data critique.",
  columns: [
    {
      label: "Quote lane",
      items: [
        "quote-major-lab-001 | 3200 CAD",
        "quote_prepared | client-major-lab-001",
      ],
    },
    {
      label: "Invoice lane",
      items: [
        "invoice-alpha-001 | 4800 CAD",
        "awaiting_collection | client-alpha-001",
      ],
    },
    {
      label: "Links",
      items: [
        "quote-alpha-001 -> job-alpha-yard-001",
        "quote-major-lab-001 -> job-major-lab-ops-001",
      ],
    },
  ],
};

const EMPIRE_MANIFEST_MODEL = {
  title: "Empire manifest",
  summary: "Vue unifiee de la facade, des tours de controle, des registres, des agents et des routes critiques.",
  columns: [
    {
      label: "Domains",
      items: [
        "smajor.org | public facade",
        "app.smajor.org | control shell",
        "api.smajor.org | business API",
        "s25.smajor.org | runtime cockpit",
        "merlin.smajor.org | validation bridge",
      ],
    },
    {
      label: "Control towers",
      items: [
        "customer_success",
        "field_ops",
        "admin_governance",
        "vendor_finance",
        "ai_ops",
        "secure_growth",
      ],
    },
    {
      label: "Command chain",
      items: [
        "TRINITY -> mission_control",
        "MERLIN -> validation + memory",
        "COMET -> provider_watch + ops_followup",
        "GOUV4 -> policy + arbitration",
        "ARKON -> build + runtime wiring",
      ],
    },
  ],
};

const TOTAL_MESH_PROTOCOL_MODEL = {
  title: "Total mesh protocol",
  summary: "Ordre de maillage total: chaque agent declare son statut, son role, son badge et sa surface au hub S25.",
  columns: [
    {
      label: "Command mode",
      items: [
        "mesh_total",
        "target_headcount=15",
        "hub=S25",
      ],
    },
    {
      label: "Protocol chain",
      items: [
        "announce_status",
        "bind_role_and_badge",
        "attach_scope",
        "confirm_service_binding",
        "emit_audit_trail",
        "enter_mesh_ready",
      ],
    },
    {
      label: "Army lanes",
      items: [
        "TRINITY, MERLIN, COMET, GOUV4",
        "KIMI, ORACLE, ONCHAIN_GUARDIAN",
        "ARKON, TREASURY, PROVIDER_WATCH",
        "MERLIN_MCP, DEFI_LIQUIDITY_MANAGER",
        "CODE_VALIDATOR, SMART_REFACTOR, AUTO_DOCUMENTER",
      ],
    },
  ],
};

const ALPHA_CLIENT_PILOT_MODEL = {
  title: "Alpha client pilot",
  summary: "Premier client de reference pour valider le tunnel intake -> quote -> invoice -> payment sans exposer les details sensibles au public.",
  columns: [
    {
      label: "Status",
      items: ["pilot_key=alpha-client-001", "phase=intake_to_invoice", "account_status=pilot_ready"],
    },
    {
      label: "Checkpoints",
      items: [
        "identity_created",
        "role_bound_to_client_badge",
        "service_scope_attached",
        "invoice_channel_ready",
      ],
    },
    {
      label: "Protection",
      items: [
        "detail via x-s25-secret",
        "secure alpha client route",
        "secure billing tunnel route",
      ],
    },
  ],
};

const SECURE_ROUTE_MODEL = {
  title: "Secure business routes",
  summary: "Les schemas publics restent visibles. Les donnees client et paiement detaillees passent par des routes protegees.",
  columns: [
    {
      label: "Public",
      items: [
        "/api/business/client-form",
        "/api/business/staff-dashboard",
        "/api/business/alpha-pilot",
        "/api/business/billing-tunnel",
      ],
    },
    {
      label: "Protected",
      items: [
        "/api/business/secure/live-registries",
        "/api/business/secure/alpha-client",
        "/api/business/secure/billing-tunnel",
        "header x-s25-secret requis",
      ],
    },
  ],
};

const INTERNAL_OPS_MODEL = {
  title: "Internal ops account",
  summary: "Le premier vrai client de l'empire est le systeme lui-meme: il doit etre suivi, facture, pilote et audite comme un compte vivant.",
  columns: [
    {
      label: "Account",
      items: [
        "client-smajor-internal-001",
        "Smajor Internal Operations",
        "major_internal_scope",
      ],
    },
    {
      label: "Purpose",
      items: [
        "self-management",
        "infra subscriptions",
        "ai operations",
        "admin rehearsal",
      ],
    },
    {
      label: "Rule",
      items: [
        "public summary only",
        "full details via secure live registries",
        "same RBAC chain as external clients",
      ],
    },
  ],
};

const AGENT_ACTIVATION_MODEL = {
  title: "Agent activation model",
  summary: "Chaque agent existe comme acteur gouverne: role, badge, services bindes, surfaces d'action et mode de trace.",
  columns: [
    {
      label: "Command",
      items: ["TRINITY", "MERLIN", "COMET", "GOUV4"],
    },
    {
      label: "Sensors",
      items: ["KIMI", "ORACLE", "ONCHAIN_GUARDIAN"],
    },
    {
      label: "Build",
      items: ["ARKON", "code-validator", "smart-refactor", "auto-documenter"],
    },
  ],
};

const AGENT_SERVICE_BINDINGS_MODEL = {
  title: "Agent service bindings",
  summary: "Les agents ne sont pas libres. Ils agissent seulement sur les services explicitement lies a leur role.",
  columns: [
    {
      label: "Business surfaces",
      items: ["client_portal", "staff_portal", "vendor_portal", "admin_console"],
    },
    {
      label: "Runtime surfaces",
      items: ["mission_control", "memory_read", "status_read", "mcp_validation"],
    },
    {
      label: "Trail",
      items: ["agent_id", "role_id", "badge_id", "service_binding", "action_surface", "audit_state"],
    },
  ],
};

const REGISTRY_WRITE_CONTRACT_MODEL = {
  title: "Live registry write contract",
  summary: "Les registres clients, jobs et quotes/invoices sont maintenant concus pour une ecriture protegee via l'API business.",
  columns: [
    {
      label: "Create client",
      items: ["POST /api/business/client-registry-live", "x-s25-secret requis", "client_id auto-genere si absent"],
    },
    {
      label: "Create job",
      items: ["POST /api/business/job-registry-live", "liaison client_id -> job_id", "dispatch_scope par role ou default"],
    },
    {
      label: "Issue quote or invoice",
      items: ["POST /api/business/quotes-invoices-live", "client_id + job_id relies", "billing_stage trace"],
    },
  ],
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
    { label: "Omega", href: `${appBase}/omega` },
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
  commandDeck = null,
  moduleSection = null,
  visitorSection = null,
  portalMatrix = null,
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

  const commandDeckHtml = commandDeck
    ? `
      <section class="omega-shell">
        <div class="omega-header">
          ${commandDeck.header
            .map(
              (item) => `
                <article class="omega-kpi">
                  <div class="label">${item.label}</div>
                  <strong>${item.value}</strong>
                  <p>${item.text}</p>
                </article>
              `,
            )
            .join("")}
        </div>
        <div class="omega-grid">
          ${commandDeck.panels
            .map(
              (panel) => `
                <article class="omega-panel">
                  <div class="label">${panel.label}</div>
                  <h3>${panel.title}</h3>
                  <p>${panel.text}</p>
                  ${
                    panel.rows
                      ? `<div class="omega-list">${panel.rows
                          .map(
                            (row) => `
                              <div class="omega-row">
                                <div class="omega-row-title">
                                  ${
                                    row.status
                                      ? `<span class="status-dot ${row.status}"></span>`
                                      : ""
                                  }
                                  <span>${row.title}</span>
                                </div>
                                <strong>${row.value || ""}</strong>
                              </div>
                            `,
                          )
                          .join("")}</div>`
                      : ""
                  }
                  ${
                    panel.links
                      ? `<div class="links">${panel.links
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

  const moduleSectionHtml = moduleSection
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Workbench</div>
            <h2>${moduleSection.title}</h2>
          </div>
          <p>${moduleSection.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const blueprintHtml = moduleSection && moduleSection.blueprint
    ? `
      <section class="blueprint-panel">
        <div class="section-head">
          <div>
            <div class="label">Industrial kit</div>
            <h2>${moduleSection.blueprint.title}</h2>
          </div>
          <p>Ce schema sert de contrat de construction entre le front, api.smajor.org et le backend S25.</p>
        </div>
        <div class="blueprint-grid">
          <article class="blueprint-card">
            <div class="label">Records</div>
            <div class="pill-row">
              ${moduleSection.blueprint.records.map((item) => `<span class="pill">${item}</span>`).join("")}
            </div>
          </article>
          <article class="blueprint-card">
            <div class="label">Pipeline</div>
            <ol class="stack-list">
              ${moduleSection.blueprint.pipeline.map((item) => `<li>${item}</li>`).join("")}
            </ol>
          </article>
          <article class="blueprint-card">
            <div class="label">Automations</div>
            <ul class="stack-list">
              ${moduleSection.blueprint.automations.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </article>
        </div>
      </section>
    `
    : "";

  const accessHtml = moduleSection && moduleSection.accessModel
    ? `
      <section class="blueprint-panel">
        <div class="section-head">
          <div>
            <div class="label">Administration</div>
            <h2>${moduleSection.accessModel.title}</h2>
          </div>
          <p>${moduleSection.accessModel.summary}</p>
        </div>
        <div class="blueprint-grid">
          <article class="blueprint-card">
            <div class="label">Roles</div>
            <div class="pill-row">
              ${moduleSection.accessModel.highlighted_roles.map((item) => `<span class="pill">${item}</span>`).join("")}
            </div>
            <div class="label" style="margin-top:18px;">Doctrine</div>
            <ul class="stack-list">
              ${moduleSection.accessModel.doctrine.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </article>
          <article class="blueprint-card">
            <div class="label">Activation flow</div>
            <ol class="stack-list">
              ${moduleSection.accessModel.activation_flow.map((item) => `<li>${item}</li>`).join("")}
            </ol>
          </article>
          <article class="blueprint-card">
            <div class="label">Services enabled</div>
            <div class="pill-row">
              ${moduleSection.accessModel.highlighted_services.map((item) => `<span class="pill">${item}</span>`).join("")}
            </div>
            <div class="label" style="margin-top:18px;">Core records</div>
            <ul class="stack-list">
              ${moduleSection.accessModel.core_records.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </article>
        </div>
      </section>
    `
    : "";

  const registryHtml = moduleSection && moduleSection.registry
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Master registry</div>
            <h2>${moduleSection.registry.title}</h2>
          </div>
          <p>${moduleSection.registry.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.registry.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const mvpRegistryHtml = moduleSection && moduleSection.mvpRegistries
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Operational MVP</div>
            <h2>${moduleSection.mvpRegistries.title}</h2>
          </div>
          <p>${moduleSection.mvpRegistries.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.mvpRegistries.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const liveRegistryHtml = moduleSection && moduleSection.liveRegistries
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Live data</div>
            <h2>${moduleSection.liveRegistries.title}</h2>
          </div>
          <p>${moduleSection.liveRegistries.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.liveRegistries.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const empireManifestHtml = moduleSection && moduleSection.empireManifest
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Empire manifest</div>
            <h2>${moduleSection.empireManifest.title}</h2>
          </div>
          <p>${moduleSection.empireManifest.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.empireManifest.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const totalMeshProtocolHtml = moduleSection && moduleSection.totalMeshProtocol
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Total mesh</div>
            <h2>${moduleSection.totalMeshProtocol.title}</h2>
          </div>
          <p>${moduleSection.totalMeshProtocol.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.totalMeshProtocol.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const controlPlaneHtml = moduleSection && moduleSection.controlPlane
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Control plane</div>
            <h2>${moduleSection.controlPlane.title}</h2>
          </div>
          <p>${moduleSection.controlPlane.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.controlPlane.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const roleGovernanceHtml = moduleSection && moduleSection.roleGovernance
    ? `
      <section class="blueprint-panel">
        <div class="section-head">
          <div>
            <div class="label">Role governance</div>
            <h2>${moduleSection.roleGovernance.title}</h2>
          </div>
          <p>${moduleSection.roleGovernance.intro}</p>
        </div>
        <div class="blueprint-grid">
          <article class="blueprint-card">
            <div class="label">Role layers</div>
            ${moduleSection.roleGovernance.columns
              .map(
                (column) => `
                  <div style="margin-bottom: 16px;">
                    <div class="label" style="margin-bottom:8px;">${column.label}</div>
                    <div class="pill-row">
                      ${column.items.map((item) => `<span class="pill">${item}</span>`).join("")}
                    </div>
                  </div>
                `,
              )
              .join("")}
          </article>
          <article class="blueprint-card">
            <div class="label">Doctrine</div>
            <ul class="stack-list">
              ${moduleSection.roleGovernance.doctrine.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </article>
          <article class="blueprint-card">
            <div class="label">Enforcement</div>
            <ol class="stack-list">
              ${moduleSection.roleGovernance.enforcement_chain.map((item) => `<li>${item}</li>`).join("")}
            </ol>
            <div class="label" style="margin-top:18px;">Identity binding</div>
            <ul class="stack-list">
              ${moduleSection.roleGovernance.identity_binding.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </article>
          <article class="blueprint-card">
            <div class="label">Badges</div>
            <ul class="stack-list">
              ${moduleSection.roleGovernance.badge_system.badge_types
                .map((item) => `<li><strong>${item.label}</strong>: ${item.binds_to}</li>`)
                .join("")}
            </ul>
          </article>
        </div>
      </section>
    `
    : "";

  const foundationHtml = moduleSection && moduleSection.foundationStack
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Foundation stack</div>
            <h2>${moduleSection.foundationStack.title}</h2>
          </div>
          <p>${moduleSection.foundationStack.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.foundationStack.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const identityRegistryHtml = moduleSection && moduleSection.identityRegistry
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Identity registry</div>
            <h2>${moduleSection.identityRegistry.title}</h2>
          </div>
          <p>${moduleSection.identityRegistry.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.identityRegistry.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const portalActivationHtml = moduleSection && moduleSection.portalActivation
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Portal activation</div>
            <h2>${moduleSection.portalActivation.title}</h2>
          </div>
          <p>${moduleSection.portalActivation.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.portalActivation.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const clientFormHtml = moduleSection && moduleSection.clientForm
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Client form</div>
            <h2>${moduleSection.clientForm.title}</h2>
          </div>
          <p>${moduleSection.clientForm.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.clientForm.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const staffDashboardHtml = moduleSection && moduleSection.staffDashboard
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Staff dashboard</div>
            <h2>${moduleSection.staffDashboard.title}</h2>
          </div>
          <p>${moduleSection.staffDashboard.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.staffDashboard.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const alphaPilotHtml = moduleSection && moduleSection.alphaPilot
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Alpha pilot</div>
            <h2>${moduleSection.alphaPilot.title}</h2>
          </div>
          <p>${moduleSection.alphaPilot.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.alphaPilot.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const secureRoutesHtml = moduleSection && moduleSection.secureRoutes
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Secure routes</div>
            <h2>${moduleSection.secureRoutes.title}</h2>
          </div>
          <p>${moduleSection.secureRoutes.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.secureRoutes.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const agentActivationHtml = moduleSection && moduleSection.agentActivation
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Agent activation</div>
            <h2>${moduleSection.agentActivation.title}</h2>
          </div>
          <p>${moduleSection.agentActivation.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.agentActivation.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const agentServiceBindingsHtml = moduleSection && moduleSection.agentServiceBindings
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Agent service bindings</div>
            <h2>${moduleSection.agentServiceBindings.title}</h2>
          </div>
          <p>${moduleSection.agentServiceBindings.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.agentServiceBindings.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const registryWriteContractHtml = moduleSection && moduleSection.registryWriteContract
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Write contract</div>
            <h2>${moduleSection.registryWriteContract.title}</h2>
          </div>
          <p>${moduleSection.registryWriteContract.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.registryWriteContract.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>${column.items.map((item) => `<li>${item}</li>`).join("")}</ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const internalOpsHtml = moduleSection && moduleSection.internalOps
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Internal ops</div>
            <h2>${moduleSection.internalOps.title}</h2>
          </div>
          <p>${moduleSection.internalOps.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.internalOps.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>${column.items.map((item) => `<li>${item}</li>`).join("")}</ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const visitorHtml = visitorSection
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Visitor map</div>
            <h2>${visitorSection.title}</h2>
          </div>
          <p>${visitorSection.intro}</p>
        </div>
        <div class="module-grid">
          ${visitorSection.columns
            .map(
              (column) => `
                <article class="module-card">
                  <div class="label">${column.label}</div>
                  <ul>
                    ${column.items.map((item) => `<li>${item}</li>`).join("")}
                  </ul>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `
    : "";

  const portalMatrixHtml = portalMatrix
    ? `
      <section class="blueprint-panel">
        <div class="section-head">
          <div>
            <div class="label">Portal matrix</div>
            <h2>${portalMatrix.title}</h2>
          </div>
          <p>${portalMatrix.summary}</p>
        </div>
        <div class="blueprint-grid">
          ${portalMatrix.portals
            .map(
              (portal) => `
                <article class="blueprint-card">
                  <div class="label">${portal.label}</div>
                  <p style="margin:0 0 14px; color: var(--muted); line-height: 1.55;">${portal.audience}</p>
                  <div class="pill-row">
                    ${portal.services.map((service) => `<span class="pill">${service}</span>`).join("")}
                  </div>
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
      .module-panel {
        margin-top: 20px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.04);
        border-radius: 28px;
        padding: 24px;
      }
      .module-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 18px;
      }
      .module-card {
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.03);
        border-radius: 24px;
        padding: 20px;
      }
      .module-card ul {
        margin: 0;
        padding-left: 18px;
        color: var(--muted);
        line-height: 1.7;
      }
      .blueprint-panel {
        margin-top: 20px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.04);
        border-radius: 28px;
        padding: 24px;
      }
      .blueprint-grid {
        display: grid;
        grid-template-columns: 1.2fr 1fr 1fr;
        gap: 18px;
      }
      .blueprint-card {
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.03);
        border-radius: 24px;
        padding: 20px;
      }
      .stack-list {
        margin: 0;
        padding-left: 18px;
        color: var(--muted);
        line-height: 1.75;
      }
      .pill-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        min-height: 34px;
        padding: 0 12px;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.03);
        color: var(--text);
        font-size: 13px;
      }
      .footer {
        margin-top: 24px;
        color: var(--muted);
        font-size: 14px;
      }
      .omega-shell {
        margin-top: 20px;
        border: 1px solid rgba(124,246,212,0.22);
        background: linear-gradient(180deg, rgba(7,24,21,0.92) 0%, rgba(4,10,11,0.96) 100%);
        border-radius: 30px;
        padding: 22px;
        box-shadow: 0 0 40px rgba(124,246,212,0.09);
      }
      .omega-header {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 16px;
      }
      .omega-kpi, .omega-panel {
        border: 1px solid rgba(124,246,212,0.18);
        background: rgba(7, 18, 17, 0.78);
        border-radius: 24px;
        padding: 18px;
      }
      .omega-kpi strong {
        display: block;
        font-size: 28px;
        color: var(--accent);
        margin: 8px 0 10px;
      }
      .omega-kpi p, .omega-panel p {
        margin: 0;
        color: var(--muted);
        line-height: 1.55;
      }
      .omega-grid {
        display: grid;
        grid-template-columns: 0.95fr 1.2fr 1fr;
        gap: 14px;
      }
      .omega-panel h3 {
        margin: 0 0 10px;
        font-size: 24px;
      }
      .omega-list {
        display: grid;
        gap: 8px;
        margin-top: 14px;
      }
      .omega-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        border: 1px solid rgba(124,246,212,0.12);
        border-radius: 16px;
        padding: 10px 12px;
        background: rgba(255,255,255,0.02);
      }
      .omega-row-title {
        display: inline-flex;
        align-items: center;
        gap: 10px;
      }
      .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 999px;
        display: inline-block;
        box-shadow: 0 0 12px currentColor;
      }
      .status-dot.online { color: #7cf6d4; background: #7cf6d4; }
      .status-dot.degraded { color: #ffb347; background: #ffb347; }
      .status-dot.offline { color: #ff5d5d; background: #ff5d5d; }
      .status-dot.unexposed { color: #6fa8ff; background: #6fa8ff; }
      @media (max-width: 900px) {
        .hero, .grid, .live-grid, .metrics, .module-grid, .blueprint-grid, .omega-header, .omega-grid { grid-template-columns: 1fr; }
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
      ${commandDeckHtml}
      ${moduleSectionHtml}
      ${visitorHtml}
      ${portalMatrixHtml}
      ${blueprintHtml}
      ${accessHtml}
      ${registryHtml}
      ${mvpRegistryHtml}
      ${liveRegistryHtml}
      ${empireManifestHtml}
      ${totalMeshProtocolHtml}
      ${controlPlaneHtml}
      ${roleGovernanceHtml}
      ${identityRegistryHtml}
      ${portalActivationHtml}
      ${clientFormHtml}
      ${staffDashboardHtml}
      ${alphaPilotHtml}
      ${secureRoutesHtml}
      ${agentActivationHtml}
      ${agentServiceBindingsHtml}
      ${foundationHtml}
      ${registryWriteContractHtml}
      ${internalOpsHtml}
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
  const [statusResult, missionsResult, meshResult, vaultResult, infraResult, clientsResult, jobsResult, financeResult, internalOpsResult] = await Promise.allSettled([
    fetchJson(`${env.PUBLIC_S25_URL}/api/status`),
    fetchJson(`${env.PUBLIC_S25_URL}/api/missions`),
    fetchJson(`${env.PUBLIC_S25_URL}/api/mesh/status`),
    fetchJson(`${env.PUBLIC_API_URL}/api/vault/mexc`),
    fetchJson(`${env.PUBLIC_API_URL}/api/akash/infra`),
    fetchJson(`${env.PUBLIC_API_URL}/api/business/client-registry-live`),
    fetchJson(`${env.PUBLIC_API_URL}/api/business/job-registry-live`),
    fetchJson(`${env.PUBLIC_API_URL}/api/business/quotes-invoices-live`),
    fetchJson(`${env.PUBLIC_API_URL}/api/business/internal-ops`),
  ]);

  return {
    status: statusResult.status === "fulfilled" ? statusResult.value : null,
    missions: missionsResult.status === "fulfilled" ? missionsResult.value : null,
    mesh: meshResult.status === "fulfilled" ? meshResult.value : null,
    vault: vaultResult.status === "fulfilled" ? vaultResult.value : null,
    infra: infraResult.status === "fulfilled" ? infraResult.value : null,
    business: {
      clients: clientsResult.status === "fulfilled" ? clientsResult.value : null,
      jobs: jobsResult.status === "fulfilled" ? jobsResult.value : null,
      quotes_invoices: financeResult.status === "fulfilled" ? financeResult.value : null,
      internal_ops: internalOpsResult.status === "fulfilled" ? internalOpsResult.value : null,
    },
    errors: [statusResult, missionsResult, meshResult, vaultResult, infraResult, clientsResult, jobsResult, financeResult, internalOpsResult]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "upstream_error"),
  };
}

function buildOmegaDeck(env, snapshot) {
  const status = snapshot.status || {};
  const mesh = snapshot.mesh || {};
  const roster = Array.isArray(mesh.roster) ? mesh.roster : [];
  const missions = snapshot.missions || {};
  const activeMissions = Array.isArray(missions.active) ? missions.active : [];
  const vault = snapshot.vault || {};
  const infra = snapshot.infra || {};
  const deployments = Array.isArray(infra.deployments) ? infra.deployments : [];
  const history = Array.isArray(missions.history) ? missions.history.slice(0, 6) : [];

  return {
    header: [
      {
        label: "Uptime S25",
        value: status.pipeline_status || "Unknown",
        text: status.summary_fr || "Le hub attend encore la remontee complete du cockpit.",
      },
      {
        label: "Nabu Casa / HA",
        value: status.ha_connected ? "Linked" : "Lateral",
        text: status.error || "HA reste lateral tant que la base S25 tient seule.",
      },
      {
        label: "Vault MEXC",
        value: vault.mode || "Cold",
        text: vault.profitability?.data_state || "Le tunnel trade reste sous garde avant binding complet.",
      },
      {
        label: "Akash Cluster",
        value: `${infra.cluster?.cpu_ready ?? 0} CPU / ${infra.cluster?.gpu_tracked ?? 0} GPU`,
        text: infra.cluster?.doctrine || "Akash-first avec facade souveraine.",
      },
    ],
    panels: [
      {
        label: "Mesh",
        title: "15 agents en ligne de front",
        text: "Chaque agent reporte son statut, son role, son badge et sa surface d'action au hub.",
        rows: roster.map((agent) => ({
          title: `${agent.agent_id} · ${agent.role_id}`,
          value: agent.action_surface,
          status:
            agent.status === "online"
              ? "online"
              : agent.status === "sleep" || agent.status === "rate_limited"
                ? "degraded"
                : "offline",
        })),
      },
      {
        label: "Terminal / Feed",
        title: "Flux Merlin, Trinity et Comet",
        text: "Le command center met les intentions, missions et retours d'actions sur la meme ligne de commande.",
        rows: [...activeMissions.slice(0, 6), ...history.slice(0, 3)].map((mission) => ({
          title: `${mission.target || mission.recommended_agent || "MESH"} · ${mission.intent || mission.mission_id || "mission"}`,
          value: mission.status || mission.priority || "queued",
          status:
            mission.status === "completed" || mission.status === "done"
              ? "online"
              : mission.status === "queued" || mission.status === "in_progress"
                ? "degraded"
                : "unexposed",
        })),
        links: [
          { label: "Feed COMET", href: `${env.PUBLIC_S25_URL}/api/comet/feed?n=12` },
          { label: "Missions", href: `${env.PUBLIC_S25_URL}/api/missions` },
        ],
      },
      {
        label: "Finance / Infra",
        title: "MEXC contre cout Akash",
        text: "Le coffre de trade, le cout du runtime et l'etat des clusters doivent rester dans la meme fenetre de tir.",
        rows: [
          {
            title: "Arbitrage loop",
            value: (vault.arbitrage_loop || []).join(" -> ") || "BTC/USDT -> BTC/AKT -> AKT/USDT",
            status: "online",
          },
          {
            title: "Trade mode",
            value: vault.mode || "armed_readiness",
            status: vault.mode === "armed_readiness" ? "degraded" : "online",
          },
          ...deployments.map((deployment) => ({
            title: `${deployment.label} · ${deployment.provider}`,
            value: deployment.uptime_state || "unknown",
            status: deployment.uptime_state || "unexposed",
          })),
        ],
        links: [
          { label: "Vault API", href: `${env.PUBLIC_API_URL}/api/vault/mexc` },
          { label: "Akash API", href: `${env.PUBLIC_API_URL}/api/akash/infra` },
        ],
      },
    ],
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

function blueprintFromPath(pathname) {
  if (pathname === "/") {
    return null;
  }
  const key = pathname.replace(/^\//, "");
  return MODULE_BLUEPRINTS[key] || null;
}

function accessSectionFromPath(pathname) {
  if (!["/clients", "/admin", "/staff", "/vendors"].includes(pathname)) {
    return null;
  }

  const focusByPath = {
    "/clients": {
      title: "Client access chain",
      summary: "Chaque client et contact doit etre rattache a une organisation, puis recevoir seulement les services achetes.",
      highlighted_roles: ["client_org", "client_contact"],
      highlighted_services: ["client_portal", "billing_access", "snow_ops", "excavation_ops", "ai_services"],
    },
    "/admin": {
      title: "Admin access chain",
      summary: "L'admin est la seule vue qui peut creer des identites, attribuer des roles et activer les services.",
      highlighted_roles: ["operator_admin", "employee", "contractor"],
      highlighted_services: ["admin_console", "staff_portal", "billing_access", "ai_services"],
    },
    "/staff": {
      title: "Staff access chain",
      summary: "Les employes et sous-traitants doivent recevoir un portail de travail, pas un acces global au systeme.",
      highlighted_roles: ["employee", "contractor"],
      highlighted_services: ["staff_portal", "snow_ops", "excavation_ops"],
    },
    "/vendors": {
      title: "Vendor access chain",
      summary: "Les fournisseurs doivent voir seulement les flux necessaires: commandes, livraisons, factures et documents.",
      highlighted_roles: ["vendor_org", "vendor_contact"],
      highlighted_services: ["vendor_portal", "billing_access"],
    },
  };

  return {
    ...ACCESS_MODEL,
    ...focusByPath[pathname],
  };
}

function roleGovernanceSection(pathname) {
  if (!["/", "/admin", "/clients", "/staff", "/vendors", "/ai"].includes(pathname)) {
    return null;
  }

  const focusByPath = {
    "/": ROLE_GOVERNANCE.layers.slice(0, 3),
    "/admin": ROLE_GOVERNANCE.layers,
    "/clients": ROLE_GOVERNANCE.layers.filter((layer) => ["External", "Direction"].includes(layer.label)),
    "/staff": ROLE_GOVERNANCE.layers.filter((layer) => ["Operations", "Direction"].includes(layer.label)),
    "/vendors": ROLE_GOVERNANCE.layers.filter((layer) => ["External", "Direction"].includes(layer.label)),
    "/ai": ROLE_GOVERNANCE.layers.filter((layer) => ["AI", "Direction"].includes(layer.label)),
  };

  return {
    title: ROLE_GOVERNANCE.title,
    intro: ROLE_GOVERNANCE.summary,
    columns: focusByPath[pathname].map((layer) => ({
      label: layer.label,
      items: [...layer.roles, ...layer.powers],
    })),
    doctrine: ROLE_GOVERNANCE.doctrine,
    badge_system: ROLE_GOVERNANCE.badge_system,
    identity_binding: ROLE_GOVERNANCE.identity_binding,
    enforcement_chain: ROLE_GOVERNANCE.enforcement_chain,
  };
}

function systemAxesSection() {
  return {
    title: SYSTEM_AXES.title,
    intro: SYSTEM_AXES.summary,
    columns: SYSTEM_AXES.axes.map((axis) => ({
      label: axis.label,
      items: [...axis.scope, axis.target],
    })),
  };
}

function masterRegistrySection() {
  return {
    title: MASTER_REGISTRY.title,
    intro: MASTER_REGISTRY.summary,
    columns: MASTER_REGISTRY.registries.slice(0, 3).map((registry) => ({
      label: registry.label,
      items: registry.records,
    })),
  };
}

function mvpRegistrySection(pathname) {
  const mapping = {
    "/clients": [MVP_REGISTRIES.clients, MVP_REGISTRIES.jobs, MVP_REGISTRIES.finance],
    "/admin": [MVP_REGISTRIES.clients, MVP_REGISTRIES.jobs, MVP_REGISTRIES.finance],
  };
  const registries = mapping[pathname];
  if (!registries) {
    return null;
  }
  return {
    title: "MVP registries",
    intro: "Ce sont les trois premiers registres a rendre operables pour transformer le shell en vrai systeme de gestion.",
    columns: registries.map((registry) => ({
      label: registry.title,
      items: [...registry.records.slice(0, 4), ...registry.workflows.slice(0, 2)],
    })),
  };
}

function liveRegistrySection(pathname, snapshot) {
  if (!["/clients", "/admin"].includes(pathname)) {
    return null;
  }
  const clients = snapshot.business?.clients?.records || [];
  const jobs = snapshot.business?.jobs?.records || [];
  const quotes = snapshot.business?.quotes_invoices?.records || [];
  return {
    title: "Live registries",
    intro: "Premieres entrees vivantes pour sortir des schemas seuls et preparer la vraie operation business.",
    columns: [
      {
        label: "Client registry live",
        items: clients.slice(0, 4).map((record) => `${record.client_id} | ${record.organization_name} | ${record.portal_state}`),
      },
      {
        label: "Job registry live",
        items: jobs.slice(0, 4).map((record) => `${record.job_id} | ${record.service_type} | ${record.assigned_team}`),
      },
      {
        label: "Quotes and invoices live",
        items: quotes
          .slice(0, 4)
          .map((record) => `${record.quote_id || "--"} | ${record.invoice_id || "--"} | ${record.billing_stage}`),
      },
    ],
  };
}

function empireManifestSection(pathname) {
  if (!["/", "/admin", "/ai"].includes(pathname)) {
    return null;
  }
  return {
    title: EMPIRE_MANIFEST_MODEL.title,
    intro: EMPIRE_MANIFEST_MODEL.summary,
    columns: EMPIRE_MANIFEST_MODEL.columns,
  };
}

function totalMeshProtocolSection(pathname) {
  if (!["/", "/admin", "/ai"].includes(pathname)) {
    return null;
  }
  return {
    title: TOTAL_MESH_PROTOCOL_MODEL.title,
    intro: TOTAL_MESH_PROTOCOL_MODEL.summary,
    columns: TOTAL_MESH_PROTOCOL_MODEL.columns,
  };
}

function controlPlaneSection(pathname) {
  if (!["/", "/admin", "/ai"].includes(pathname)) {
    return null;
  }
  const slices = {
    "/": [0, 3],
    "/admin": [0, 5],
    "/ai": [4, 6],
  };
  const [start, end] = slices[pathname];
  return {
    title: MAJOR_CONTROL_PLANE.title,
    intro: MAJOR_CONTROL_PLANE.summary,
    columns: MAJOR_CONTROL_PLANE.towers.slice(start, end).map((tower) => ({
      label: tower.label,
      items: tower.scope,
    })),
  };
}

function foundationStackSection(pathname) {
  if (!["/", "/admin", "/ai"].includes(pathname)) {
    return null;
  }
  return {
    title: FOUNDATION_STACK.title,
    intro: FOUNDATION_STACK.summary,
    columns: FOUNDATION_STACK.layers.map((layer) => ({
      label: layer.label,
      items: [layer.role],
    })),
  };
}

function registryWriteContractSection(pathname) {
  if (!["/clients", "/admin"].includes(pathname)) {
    return null;
  }
  return {
    title: REGISTRY_WRITE_CONTRACT_MODEL.title,
    intro: REGISTRY_WRITE_CONTRACT_MODEL.summary,
    columns: REGISTRY_WRITE_CONTRACT_MODEL.columns,
  };
}

function identityRegistrySection(pathname) {
  if (!["/admin", "/clients", "/staff", "/vendors"].includes(pathname)) {
    return null;
  }
  return {
    title: IDENTITY_REGISTRY_MODEL.title,
    intro: IDENTITY_REGISTRY_MODEL.summary,
    columns: [
      { label: "Records", items: IDENTITY_REGISTRY_MODEL.records },
      { label: "Activation", items: IDENTITY_REGISTRY_MODEL.workflows },
    ],
  };
}

function portalActivationSection(pathname) {
  if (!["/admin", "/clients", "/staff", "/vendors"].includes(pathname)) {
    return null;
  }
  const focus = {
    "/admin": PORTAL_ACTIVATION_MODEL.tracks,
    "/clients": PORTAL_ACTIVATION_MODEL.tracks.filter((track) => track.label === "Clients"),
    "/staff": PORTAL_ACTIVATION_MODEL.tracks.filter((track) => track.label === "Staff"),
    "/vendors": PORTAL_ACTIVATION_MODEL.tracks.filter((track) => track.label === "Vendors"),
  };
  return {
    title: PORTAL_ACTIVATION_MODEL.title,
    intro: PORTAL_ACTIVATION_MODEL.summary,
    columns: focus[pathname].map((track) => ({
      label: track.label,
      items: track.items,
    })),
  };
}

function clientFormSection(pathname) {
  if (pathname !== "/clients" && pathname !== "/admin") {
    return null;
  }
  return {
    title: CLIENT_FORM_MODEL.title,
    intro: CLIENT_FORM_MODEL.summary,
    columns: CLIENT_FORM_MODEL.columns,
  };
}

function staffDashboardSection(pathname) {
  if (pathname !== "/staff" && pathname !== "/admin") {
    return null;
  }
  return {
    title: STAFF_DASHBOARD_MODEL.title,
    intro: STAFF_DASHBOARD_MODEL.summary,
    columns: STAFF_DASHBOARD_MODEL.columns,
  };
}

function alphaPilotSection(pathname) {
  if (pathname !== "/clients" && pathname !== "/admin") {
    return null;
  }
  return {
    title: ALPHA_CLIENT_PILOT_MODEL.title,
    intro: ALPHA_CLIENT_PILOT_MODEL.summary,
    columns: ALPHA_CLIENT_PILOT_MODEL.columns,
  };
}

function secureRoutesSection(pathname) {
  if (!["/clients", "/admin", "/staff", "/vendors"].includes(pathname)) {
    return null;
  }
  return {
    title: SECURE_ROUTE_MODEL.title,
    intro: SECURE_ROUTE_MODEL.summary,
    columns: SECURE_ROUTE_MODEL.columns,
  };
}

function internalOpsSection(pathname, snapshot) {
  if (!["/clients", "/admin", "/ai"].includes(pathname)) {
    return null;
  }
  const live = snapshot.business?.internal_ops || {};
  const columns = INTERNAL_OPS_MODEL.columns.map((column) => ({ ...column }));
  if (live.account_live) {
    columns.unshift({
      label: "Live",
      items: [
        `${live.client?.client_id || "--"} | ${live.client?.organization_name || "--"}`,
        `jobs_open=${live.jobs_open ?? 0}`,
        `finance_entries=${live.finance_entries ?? 0}`,
        `portal=${live.client?.portal_state || "--"}`,
      ],
    });
  }
  return {
    title: INTERNAL_OPS_MODEL.title,
    intro: INTERNAL_OPS_MODEL.summary,
    columns,
  };
}

function agentActivationSection(pathname) {
  if (!["/admin", "/ai"].includes(pathname)) {
    return null;
  }
  return {
    title: AGENT_ACTIVATION_MODEL.title,
    intro: AGENT_ACTIVATION_MODEL.summary,
    columns: AGENT_ACTIVATION_MODEL.columns,
  };
}

function agentServiceBindingsSection(pathname) {
  if (!["/admin", "/ai"].includes(pathname)) {
    return null;
  }
  return {
    title: AGENT_SERVICE_BINDINGS_MODEL.title,
    intro: AGENT_SERVICE_BINDINGS_MODEL.summary,
    columns: AGENT_SERVICE_BINDINGS_MODEL.columns,
  };
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
    visitorSection: VISITOR_STRUCTURE,
    portalMatrix: PORTAL_MATRIX,
  });
}

function renderApp(env, pathname, hostname, snapshot) {
  const section = APP_SECTIONS[pathname] || APP_SECTIONS["/"];
  const registrySection = pathname === "/" || pathname === "/admin"
    ? {
        title: MASTER_REGISTRY.title,
        intro: MASTER_REGISTRY.summary,
        columns: MASTER_REGISTRY.registries
          .slice(pathname === "/admin" ? 0 : 0, pathname === "/admin" ? 6 : 3)
          .map((registry) => ({
            label: registry.label,
            items: registry.records,
          })),
      }
    : null;
  const moduleSection = {
    ...(pathname === "/" ? systemAxesSection() : (WORKBENCH_SECTIONS[pathname] || WORKBENCH_SECTIONS["/"])),
    blueprint: blueprintFromPath(pathname),
    accessModel: accessSectionFromPath(pathname),
    mvpRegistries: mvpRegistrySection(pathname),
    liveRegistries: liveRegistrySection(pathname, snapshot),
    empireManifest: empireManifestSection(pathname),
    totalMeshProtocol: totalMeshProtocolSection(pathname),
    controlPlane: controlPlaneSection(pathname),
    roleGovernance: roleGovernanceSection(pathname),
    identityRegistry: identityRegistrySection(pathname),
    portalActivation: portalActivationSection(pathname),
    clientForm: clientFormSection(pathname),
    staffDashboard: staffDashboardSection(pathname),
    alphaPilot: alphaPilotSection(pathname),
    secureRoutes: secureRoutesSection(pathname),
    internalOps: internalOpsSection(pathname, snapshot),
    agentActivation: agentActivationSection(pathname),
    agentServiceBindings: agentServiceBindingsSection(pathname),
    foundationStack: foundationStackSection(pathname),
    registryWriteContract: registryWriteContractSection(pathname),
  };
  if (registrySection) {
    moduleSection.registry = registrySection;
  }
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
    commandDeck: pathname === "/omega" ? buildOmegaDeck(env, snapshot) : null,
    moduleSection,
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

    if (url.pathname.startsWith("/blueprints/") && url.pathname.endsWith(".json")) {
      const key = url.pathname.replace("/blueprints/", "").replace(".json", "");
      const blueprint = MODULE_BLUEPRINTS[key];
      if (!blueprint) {
        return jsonResponse({ ok: false, error: "blueprint_not_found", key }, 404);
      }
      return jsonResponse({
        ok: true,
        key,
        domain: "smajor.org",
        source_of_truth: "S25 mesh + api.smajor.org",
        ...blueprint,
      });
    }

    if (url.pathname === "/models/access-control.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "admin_console + api.smajor.org + S25 missions",
        ...ACCESS_MODEL,
      });
    }

    if (url.pathname === "/models/system-axes.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "business + admin + S25 mesh",
        ...SYSTEM_AXES,
      });
    }

    if (url.pathname === "/models/master-registry.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org future facade + S25 governance",
        ...MASTER_REGISTRY,
      });
    }

    if (url.pathname === "/models/mvp-registries.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "future api.smajor.org business facade",
        registries: MVP_REGISTRIES,
      });
    }

    if (url.pathname === "/models/control-plane.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "business + admin + ai ops",
        ...MAJOR_CONTROL_PLANE,
      });
    }

    if (url.pathname === "/models/foundation-stack.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "open-source backbone selection",
        ...FOUNDATION_STACK,
      });
    }

    if (url.pathname === "/models/role-governance.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "strict administration chain + role templates + service enablement",
        ...ROLE_GOVERNANCE,
      });
    }

    if (url.pathname === "/models/identity-registry.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org identities facade + admin governance",
        ...IDENTITY_REGISTRY_MODEL,
      });
    }

    if (url.pathname === "/models/portal-activation.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org portal activation facade + role governance",
        ...PORTAL_ACTIVATION_MODEL,
      });
    }

    if (url.pathname === "/models/client-form.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org client intake facade + client portal",
        ...CLIENT_FORM_MODEL,
      });
    }

    if (url.pathname === "/models/staff-dashboard.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org staff dashboard facade + staff portal",
        ...STAFF_DASHBOARD_MODEL,
      });
    }

    if (url.pathname === "/models/client-registry-live.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org client-registry-live",
        ...CLIENT_REGISTRY_LIVE_MODEL,
      });
    }

    if (url.pathname === "/models/job-registry-live.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org job-registry-live",
        ...JOB_REGISTRY_LIVE_MODEL,
      });
    }

    if (url.pathname === "/models/quotes-invoices-live.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org quotes-invoices-live",
        ...QUOTES_INVOICES_LIVE_MODEL,
      });
    }

    if (url.pathname === "/models/empire-manifest.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org empire-manifest + control plane",
        ...EMPIRE_MANIFEST_MODEL,
      });
    }

    if (url.pathname === "/models/total-mesh-protocol.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org total-mesh-protocol",
        ...TOTAL_MESH_PROTOCOL_MODEL,
      });
    }

    if (url.pathname === "/models/alpha-client-pilot.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org alpha pilot + secure client detail routes",
        ...ALPHA_CLIENT_PILOT_MODEL,
      });
    }

    if (url.pathname === "/models/secure-routes.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org secure business route map",
        ...SECURE_ROUTE_MODEL,
      });
    }

    if (url.pathname === "/models/internal-ops.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org internal ops summary + secure live registries",
        ...INTERNAL_OPS_MODEL,
      });
    }

    if (url.pathname === "/models/agent-activation.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org agent activation catalog + hierarchy",
        ...AGENT_ACTIVATION_MODEL,
      });
    }

    if (url.pathname === "/models/agent-service-bindings.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org agent service matrix + audit trail",
        ...AGENT_SERVICE_BINDINGS_MODEL,
      });
    }

    if (url.pathname === "/models/registry-write-contract.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org live write facade + protected business routes",
        ...REGISTRY_WRITE_CONTRACT_MODEL,
      });
    }

    if (url.pathname === "/models/visitor-structure.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "public facade + portal onboarding",
        ...VISITOR_STRUCTURE,
      });
    }

    if (url.pathname === "/models/portal-matrix.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "strict administration chain + service enablement",
        ...PORTAL_MATRIX,
      });
    }

    if (hostname === "app.smajor.org") {
      const snapshot = await fetchOpsSnapshot(env);
      return responseHtml(renderApp(env, url.pathname, hostname, snapshot));
    }

    return responseHtml(renderPublic(env));
  },
};
