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
        label: "Separation",
        title: "Front distinct du back",
        text: "smajor.org montre, collecte et pilote. S25, api.smajor.org et MERLIN portent la logique, les secrets et la persistence.",
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
      {
        label: "Back-end",
        title: "Le portail n'est pas le cerveau",
        text: "Les devis, jobs, acces et paiements restent gouvernes par api.smajor.org et S25 Lumiere, pas par le front seul.",
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
        label: "Architecture",
        title: "Front securise, back souverain",
        text: "L'admin agit via sessions signees et routes gouvernees; la persistence, le coffre et les policies restent dans le backend.",
      },
      {
        label: "Separation",
        title: "Control plane, pas base de donnees",
        text: "Le portail admin montre et commande. Les registres, policies, secrets et ecritures durables restent dans S25 et api.smajor.org.",
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
      {
        label: "Back-end",
        title: "Dispatch reste souverain",
        text: "Le dashboard staff n'est qu'une surface terrain. Le dispatch, les jobs et les scopes restent ancres dans le backend.",
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
      {
        label: "Back-end",
        title: "Achats pilotes par policy",
        text: "Le portail vendors montre l'etat. Les approvals, budgets et rattachements cout restent dans la couche souveraine.",
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
  "/trade": {
    label: "Trade",
    eyebrow: "War room",
    heroTitle: "Une salle de guerre pour les agents trader.",
    heroText:
      "Le trade showroom separe signal, risk, treasury et execution pour que la folie reste lisible et gouvernee.",
    cards: [
      {
        label: "Signal",
        title: "Collecte multi-agent",
        text: "TRINITY, KIMI et ORACLE collectent et confirment sans toucher directement a la custody.",
      },
      {
        label: "Risk",
        title: "Validation avant feu",
        text: "MERLIN, ONCHAIN_GUARDIAN et GOUV4 filtrent, cadrent et peuvent bloquer toute execution.",
      },
      {
        label: "Execution",
        title: "Lane bornee",
        text: "ARKON et les wallets mirror executent seulement apres policy, audit et allocation treasury.",
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
  "/wallet": {
    label: "Wallet",
    eyebrow: "S25 wallet",
    heroTitle: "Voir l'adresse maitre sans exposer la seed.",
    heroText:
      "Cette page publie uniquement l'adresse derivee du wallet creator et l'etat de connexion du runtime S25. La seed phrase reste dans Google Secret Manager.",
    cards: [
      {
        label: "Wallet",
        title: "Adresse publique seulement",
        text: "Le site expose l'adresse Akash maitre comme identite publique. Aucune seed, aucun secret runtime, aucune cle privee.",
      },
      {
        label: "Etat",
        title: "Connexion S25",
        text: "Le statut vient du cockpit public et du mesh. L'objectif est de voir si le coeur repond sans toucher au coffre.",
      },
      {
        label: "Doctrine",
        title: "Secret en coffre, adresse en facade",
        text: "Le coffre Google garde le secret. smajor.org ne montre que les informations publiables et utiles a l'operateur.",
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
  "/trade": {
    title: "Trade showroom",
    intro: "Le trade doit ressembler a une salle de guerre: signaux, risque, treasury et execution separes, auditables, lisibles.",
    columns: [
      {
        label: "Signal lane",
        items: [
          "TRINITY orchestre les hypotheses.",
          "KIMI pompe les signaux Web3.",
          "ORACLE confirme les prix et conditions.",
        ],
      },
      {
        label: "Risk lane",
        items: [
          "MERLIN valide la coherence.",
          "ONCHAIN_GUARDIAN surveille les risques.",
          "GOUV4 applique les policies et le cout.",
        ],
      },
      {
        label: "Execution lane",
        items: [
          "TREASURY alloue le capital.",
          "ARKON prepare l'execution.",
          "mirror wallets servent de couche de test et de dry-run.",
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
  trade: {
    title: "Trading control blueprint",
    records: [
      "signal_batch",
      "risk_gate",
      "capital_allocation",
      "execution_window",
      "profit_report",
      "audit_event",
    ],
    pipeline: [
      "collect_signal",
      "confirm_market",
      "validate_risk",
      "allocate_treasury",
      "execute_guarded",
      "report_profit",
    ],
    automations: [
      "TRINITY coordonne les lanes.",
      "MERLIN bloque si la policy ou le risk gate derape.",
      "Le showroom reste visuel; la vraie execution vit dans S25 et les wallets scopes.",
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
        "/api/business/secure/operator-roster",
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

const OPERATOR_ACCOUNT_MODEL = {
  title: "Operator account",
  summary: "Le Major entre lui aussi dans le pipeline: identite, role, badge, scope et services actives.",
  columns: [
    {
      label: "Identity",
      items: ["ident-major-stef-001", "Stephane Major", "human_operator"],
    },
    {
      label: "Authority",
      items: ["executive_operator", "major_badge", "founder_scope"],
    },
    {
      label: "Services",
      items: ["admin_console", "finance_approval", "ai_control_plane", "governance"],
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

const ADMIN_COMMAND_KIT_MODEL = {
  title: "Admin command kit",
  summary: "Kit de commande pour operer l'entreprise via un pipeline strict: lecture secure, creation securisee, et audit par role.",
  columns: [
    {
      label: "Read surfaces",
      items: [
        "GET /admin/api/live-registries",
        "GET /admin/api/operator-roster",
        "GET /admin/api/runtime-business",
        "GET /admin/api/wallets-custody",
        "GET /admin/api/vaults-treasury",
        "GET /admin/api/secret-custody",
        "GET /admin/api/secret-fallback-policy",
        "GET /api/business/frontend-surfaces",
        "GET /api/business/backend-surfaces",
        "GET /api/business/separation-architecture",
        "GET /api/business/admin-architecture",
        "GET /api/business/portal-separation",
        "GET /admin/api/gemini-layer",
        "GET /admin/api/wallet-classes",
        "GET /admin/api/wallet-scopes",
        "GET /admin/api/wallet-policy-matrix",
      ],
    },
    {
      label: "Write surfaces",
      items: [
        "POST /admin/api/create-client",
        "POST /admin/api/create-job",
        "POST /admin/api/issue-invoice",
        "POST /admin/api/create-identity",
      ],
    },
    {
      label: "Payload roots",
      items: [
        "organization_name + role_id + badge_id + scope_id",
        "client_id -> job_id -> quote_or_invoice",
        "identity_id survives user rotation",
      ],
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

  const executiveReportHtml = moduleSection && moduleSection.executiveReport
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Executive report</div>
            <h2>${moduleSection.executiveReport.title}</h2>
          </div>
          <p>${moduleSection.executiveReport.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.executiveReport.columns
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

  const masterWalletHtml = moduleSection && moduleSection.masterWallet
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Master wallet</div>
            <h2>${moduleSection.masterWallet.title}</h2>
          </div>
          <p>${moduleSection.masterWallet.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.masterWallet.columns
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

  const adminConsoleHtml = moduleSection && moduleSection.adminConsole
    ? `
      <section class="blueprint-panel admin-console-panel">
        <div class="section-head">
          <div>
            <div class="label">Operator console</div>
            <h2>${moduleSection.adminConsole.title}</h2>
          </div>
          <p>${moduleSection.adminConsole.intro}</p>
        </div>
        <div class="admin-console-grid">
          <article class="blueprint-card admin-console-main">
            <div class="label">Operator access</div>
            <label class="field-label" for="operator-secret">Operator bootstrap secret</label>
            <input id="operator-secret" class="field-input" type="password" placeholder="Coller le secret une fois pour ouvrir une session operateur" />
            <div class="action-row">
              <button class="action-button" type="button" data-admin-session="true">Unlock operator session</button>
              <button class="action-button secondary" type="button" data-admin-refresh="true">Reload runtime</button>
            </div>
            <div class="label" style="margin-top:18px;">Write flow</div>
            <ul class="stack-list">
              ${moduleSection.adminConsole.flow.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </article>
          <article class="blueprint-card admin-console-main">
            <div class="label">Runtime overview</div>
            <div class="metrics">
              ${moduleSection.adminConsole.metrics
                .map(
                  (metric) => `
                    <div class="metric">
                      <span>${metric.label}</span>
                      <strong>${metric.value}</strong>
                    </div>
                  `,
                )
                .join("")}
            </div>
            <div class="label" style="margin-top:18px;">Active endpoints</div>
            <div class="pill-row">
              ${moduleSection.adminConsole.endpoints.map((item) => `<span class="pill">${item}</span>`).join("")}
            </div>
          </article>
        </div>
        <div class="admin-forms-grid">
          ${moduleSection.adminConsole.forms
            .map(
              (form) => `
                <article class="blueprint-card admin-form-card">
                  <div class="label">${form.label}</div>
                  <h3>${form.title}</h3>
                  <p>${form.text}</p>
                  <form class="admin-form" data-admin-form="${form.endpoint}">
                    ${form.fields
                      .map(
                        (field) => `
                          <label class="field-label">
                            ${field.label}
                            <input
                              class="field-input"
                              name="${field.name}"
                              type="${field.type || "text"}"
                              placeholder="${field.placeholder || ""}"
                              value="${field.value || ""}"
                              ${field.required ? "required" : ""}
                            />
                          </label>
                        `,
                      )
                      .join("")}
                    <div class="action-row">
                      <button class="action-button" type="submit">${form.actionLabel}</button>
                    </div>
                  </form>
                </article>
              `,
            )
            .join("")}
        </div>
        <article class="blueprint-card admin-console-log">
          <div class="label">Console log</div>
          <pre id="admin-console-log">${moduleSection.adminConsole.initialLog}</pre>
        </article>
      </section>
    `
    : "";

  const adminArchitectureHtml = moduleSection && moduleSection.adminArchitecture
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Admin architecture</div>
            <h2>${moduleSection.adminArchitecture.title}</h2>
          </div>
          <p>${moduleSection.adminArchitecture.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.adminArchitecture.columns
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

  const geminiLayerHtml = moduleSection && moduleSection.geminiLayer
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Gemini layer</div>
            <h2>${moduleSection.geminiLayer.title}</h2>
          </div>
          <p>${moduleSection.geminiLayer.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.geminiLayer.columns
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

  const clientConsoleHtml = moduleSection && moduleSection.clientConsole
    ? `
      <section class="blueprint-panel client-console-panel">
        <div class="section-head">
          <div>
            <div class="label">Client session</div>
            <h2>${moduleSection.clientConsole.title}</h2>
          </div>
          <p>${moduleSection.clientConsole.intro}</p>
        </div>
        <div class="admin-console-grid">
          <article class="blueprint-card admin-console-main">
            <div class="label">Client access token</div>
            <label class="field-label" for="client-token">Client bearer token</label>
            <input id="client-token" class="field-input" type="password" placeholder="Coller le token client emis par l'admin" />
            <div class="action-row">
              <button class="action-button" type="button" data-client-load="true">Load client account</button>
            </div>
            <div class="label" style="margin-top:18px;">Client flow</div>
            <ul class="stack-list">
              ${moduleSection.clientConsole.flow.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </article>
          <article class="blueprint-card admin-console-main">
            <div class="label">Live metrics</div>
            <div class="metrics">
              ${moduleSection.clientConsole.metrics
                .map(
                  (metric) => `
                    <div class="metric">
                      <span>${metric.label}</span>
                      <strong>${metric.value}</strong>
                    </div>
                  `,
                )
                .join("")}
            </div>
            <div class="label" style="margin-top:18px;">Account surface</div>
            <div class="pill-row">
              ${moduleSection.clientConsole.endpoints.map((item) => `<span class="pill">${item}</span>`).join("")}
            </div>
          </article>
        </div>
        <div class="admin-console-log">
          <pre id="client-console-log">${moduleSection.clientConsole.initialLog}</pre>
        </div>
      </section>
    `
    : "";

  const portalSeparationHtml = moduleSection && moduleSection.portalSeparation
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Portal separation</div>
            <h2>${moduleSection.portalSeparation.title}</h2>
          </div>
          <p>${moduleSection.portalSeparation.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.portalSeparation.columns
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

  const staffConsoleHtml = moduleSection && moduleSection.staffConsole
    ? `
      <section class="blueprint-panel client-console-panel">
        <div class="section-head">
          <div>
            <div class="label">Staff session</div>
            <h2>${moduleSection.staffConsole.title}</h2>
          </div>
          <p>${moduleSection.staffConsole.intro}</p>
        </div>
        <div class="admin-console-grid">
          <article class="blueprint-card admin-console-main">
            <div class="label">Staff access token</div>
            <label class="field-label" for="staff-token">Staff bearer token</label>
            <input id="staff-token" class="field-input" type="password" placeholder="Coller le token staff emis par l'admin" />
            <div class="action-row">
              <button class="action-button" type="button" data-staff-load="true">Load staff dashboard</button>
            </div>
            <div class="label" style="margin-top:18px;">Staff flow</div>
            <ul class="stack-list">
              ${moduleSection.staffConsole.flow.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </article>
          <article class="blueprint-card admin-console-main">
            <div class="label">Staff metrics</div>
            <div class="metrics">
              ${moduleSection.staffConsole.metrics
                .map(
                  (metric) => `
                    <div class="metric">
                      <span>${metric.label}</span>
                      <strong>${metric.value}</strong>
                    </div>
                  `,
                )
                .join("")}
            </div>
            <div class="label" style="margin-top:18px;">Dashboard surface</div>
            <div class="pill-row">
              ${moduleSection.staffConsole.endpoints.map((item) => `<span class="pill">${item}</span>`).join("")}
            </div>
          </article>
        </div>
        <div class="admin-console-log">
          <pre id="staff-console-log">${moduleSection.staffConsole.initialLog}</pre>
        </div>
      </section>
    `
    : "";

  const vendorConsoleHtml = moduleSection && moduleSection.vendorConsole
    ? `
      <section class="blueprint-panel client-console-panel">
        <div class="section-head">
          <div>
            <div class="label">Vendor session</div>
            <h2>${moduleSection.vendorConsole.title}</h2>
          </div>
          <p>${moduleSection.vendorConsole.intro}</p>
        </div>
        <div class="admin-console-grid">
          <article class="blueprint-card admin-console-main">
            <div class="label">Vendor access token</div>
            <label class="field-label" for="vendor-token">Vendor bearer token</label>
            <input id="vendor-token" class="field-input" type="password" placeholder="Coller le token vendor emis par l'admin" />
            <div class="action-row">
              <button class="action-button" type="button" data-vendor-load="true">Load vendor dashboard</button>
            </div>
            <div class="label" style="margin-top:18px;">Vendor flow</div>
            <ul class="stack-list">
              ${moduleSection.vendorConsole.flow.map((item) => `<li>${item}</li>`).join("")}
            </ul>
          </article>
          <article class="blueprint-card admin-console-main">
            <div class="label">Vendor metrics</div>
            <div class="metrics">
              ${moduleSection.vendorConsole.metrics
                .map(
                  (metric) => `
                    <div class="metric">
                      <span>${metric.label}</span>
                      <strong>${metric.value}</strong>
                    </div>
                  `,
                )
                .join("")}
            </div>
            <div class="label" style="margin-top:18px;">Dashboard surface</div>
            <div class="pill-row">
              ${moduleSection.vendorConsole.endpoints.map((item) => `<span class="pill">${item}</span>`).join("")}
            </div>
          </article>
        </div>
        <div class="admin-console-log">
          <pre id="vendor-console-log">${moduleSection.vendorConsole.initialLog}</pre>
        </div>
      </section>
    `
    : "";

  const businessTimelineHtml = moduleSection && moduleSection.businessTimeline
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Business timeline</div>
            <h2>${moduleSection.businessTimeline.title}</h2>
          </div>
          <p>${moduleSection.businessTimeline.intro}</p>
        </div>
        <div class="module-grid">
          <article class="module-card">
            <div class="label">Recent events</div>
            <ul class="stack-list">
              ${moduleSection.businessTimeline.rows.map((row) => `<li><strong>${row.timestamp}</strong><br/>${row.title}<br/><span class="muted">${row.detail}</span></li>`).join("")}
            </ul>
          </article>
        </div>
      </section>
    `
    : "";

  const operationalChainHtml = moduleSection && moduleSection.operationalChain
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Operational chain</div>
            <h2>${moduleSection.operationalChain.title}</h2>
          </div>
          <p>${moduleSection.operationalChain.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.operationalChain.rows
            .map(
              (row) => `
                <article class="module-card">
                  <div class="label">${row.title}</div>
                  <ul>
                    ${row.items.map((item) => `<li>${item}</li>`).join("")}
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

  const tradingShowroomHtml = moduleSection && moduleSection.tradingShowroom
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Trading showroom</div>
            <h2>${moduleSection.tradingShowroom.title}</h2>
          </div>
          <p>${moduleSection.tradingShowroom.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.tradingShowroom.columns
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

  const tradingLaneMetricsHtml = moduleSection && moduleSection.tradingLaneMetrics
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Trade metrics</div>
            <h2>${moduleSection.tradingLaneMetrics.title}</h2>
          </div>
          <p>${moduleSection.tradingLaneMetrics.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.tradingLaneMetrics.columns
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

  const operatorAccountHtml = moduleSection && moduleSection.operatorAccount
    ? `
      <section class="module-panel">
        <div class="section-head">
          <div>
            <div class="label">Operator account</div>
            <h2>${moduleSection.operatorAccount.title}</h2>
          </div>
          <p>${moduleSection.operatorAccount.intro}</p>
        </div>
        <div class="module-grid">
          ${moduleSection.operatorAccount.columns
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
      .admin-console-grid, .admin-forms-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 14px;
      }
      .admin-console-panel h3, .admin-form-card h3 {
        margin: 0 0 8px;
        font-size: 22px;
      }
      .admin-form-card p {
        margin: 0 0 14px;
        color: var(--muted);
        line-height: 1.55;
      }
      .admin-form {
        display: grid;
        gap: 12px;
      }
      .field-label {
        display: grid;
        gap: 6px;
        font-size: 13px;
        color: var(--muted);
      }
      .field-input {
        border: 1px solid rgba(124,246,212,0.18);
        background: rgba(255,255,255,0.04);
        color: var(--text);
        border-radius: 14px;
        padding: 12px 14px;
        font: inherit;
      }
      .action-row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }
      .action-button {
        border: 1px solid rgba(124,246,212,0.28);
        background: linear-gradient(135deg, rgba(124,246,212,0.18) 0%, rgba(39,84,72,0.95) 100%);
        color: var(--text);
        border-radius: 999px;
        padding: 12px 16px;
        font: inherit;
        cursor: pointer;
      }
      .action-button.secondary {
        background: rgba(255,255,255,0.04);
      }
      .admin-console-log {
        margin-top: 14px;
      }
      .admin-console-log pre {
        margin: 0;
        padding: 14px;
        border-radius: 18px;
        background: rgba(0,0,0,0.34);
        border: 1px solid rgba(124,246,212,0.14);
        color: #bdfce8;
        overflow-x: auto;
        white-space: pre-wrap;
        word-break: break-word;
        font-size: 12px;
        line-height: 1.55;
      }
      @media (max-width: 900px) {
        .hero, .grid, .live-grid, .metrics, .module-grid, .blueprint-grid, .omega-header, .omega-grid, .admin-console-grid, .admin-forms-grid { grid-template-columns: 1fr; }
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
      ${executiveReportHtml}
      ${masterWalletHtml}
      ${adminConsoleHtml}
      ${adminArchitectureHtml}
      ${geminiLayerHtml}
      ${empireManifestHtml}
      ${totalMeshProtocolHtml}
      ${controlPlaneHtml}
      ${roleGovernanceHtml}
      ${identityRegistryHtml}
      ${portalActivationHtml}
      ${portalSeparationHtml}
      ${businessTimelineHtml}
      ${operationalChainHtml}
      ${clientFormHtml}
      ${staffDashboardHtml}
      ${alphaPilotHtml}
      ${secureRoutesHtml}
      ${agentActivationHtml}
      ${agentServiceBindingsHtml}
      ${tradingShowroomHtml}
      ${tradingLaneMetricsHtml}
      ${foundationHtml}
      ${registryWriteContractHtml}
      ${clientConsoleHtml}
      ${staffConsoleHtml}
      ${vendorConsoleHtml}
      ${internalOpsHtml}
      ${operatorAccountHtml}
      <div class="footer">Smajor est la facade. S25 Lumiere reste le backend central multi-agent.</div>
    </main>
    ${moduleSection && (moduleSection.adminConsole || moduleSection.clientConsole || moduleSection.staffConsole) ? `
      <script>
        (() => {
          const secretInput = document.getElementById("operator-secret");
          const logNode = document.getElementById("admin-console-log");
          const refreshButton = document.querySelector("[data-admin-refresh='true']");
          const sessionButton = document.querySelector("[data-admin-session='true']");
          const forms = Array.from(document.querySelectorAll("[data-admin-form]"));
          const secretStorageKey = "smajor_admin_secret";
          const tokenStorageKey = "smajor_admin_token";
          const sessionMetaKey = "smajor_admin_session_meta";
          const clientTokenInput = document.getElementById("client-token");
          const clientLogNode = document.getElementById("client-console-log");
          const clientLoadButton = document.querySelector("[data-client-load='true']");
          const clientTokenStorageKey = "smajor_client_token";
          const staffTokenInput = document.getElementById("staff-token");
          const staffLogNode = document.getElementById("staff-console-log");
          const staffLoadButton = document.querySelector("[data-staff-load='true']");
          const staffTokenStorageKey = "smajor_staff_token";
          const vendorTokenInput = document.getElementById("vendor-token");
          const vendorLogNode = document.getElementById("vendor-console-log");
          const vendorLoadButton = document.querySelector("[data-vendor-load='true']");
          const vendorTokenStorageKey = "smajor_vendor_token";

          const writeLog = (title, payload) => {
            if (!logNode) return;
            const lines = [
              "[" + new Date().toISOString() + "] " + title,
              typeof payload === "string" ? payload : JSON.stringify(payload, null, 2),
            ];
            logNode.textContent = lines.join("\\n");
          };

          const writeClientLog = (title, payload) => {
            if (!clientLogNode) return;
            const lines = [
              "[" + new Date().toISOString() + "] " + title,
              typeof payload === "string" ? payload : JSON.stringify(payload, null, 2),
            ];
            clientLogNode.textContent = lines.join("\\n");
          };

          const writeStaffLog = (title, payload) => {
            if (!staffLogNode) return;
            const lines = [
              "[" + new Date().toISOString() + "] " + title,
              typeof payload === "string" ? payload : JSON.stringify(payload, null, 2),
            ];
            staffLogNode.textContent = lines.join("\\n");
          };

          const writeVendorLog = (title, payload) => {
            if (!vendorLogNode) return;
            const lines = [
              "[" + new Date().toISOString() + "] " + title,
              typeof payload === "string" ? payload : JSON.stringify(payload, null, 2),
            ];
            vendorLogNode.textContent = lines.join("\\n");
          };

          const getSecret = () => {
            const value = secretInput.value.trim();
            if (!value) {
              throw new Error("operator_secret_missing");
            }
            sessionStorage.setItem(secretStorageKey, value);
            return value;
          };

          const getToken = () => sessionStorage.getItem(tokenStorageKey);

          const createOperatorSession = async () => {
            const secret = getSecret();
            const response = await fetch("/admin/api/session", {
              method: "POST",
              headers: {
                "accept": "application/json",
                "content-type": "application/json",
                "x-s25-secret": secret,
              },
            });
            const payload = await response.json().catch(() => ({ ok: false, error: "invalid_json" }));
            if (!response.ok || !payload.ok || !payload.token) {
              throw new Error(JSON.stringify(payload, null, 2));
            }
            sessionStorage.setItem(tokenStorageKey, payload.token);
            sessionStorage.setItem(sessionMetaKey, JSON.stringify({
              expires_at: payload.expires_at,
              profile: payload.profile,
            }));
            return payload;
          };

          const requestJson = async (endpoint, options = {}) => {
            const token = getToken();
            if (!token) {
              throw new Error("operator_session_missing");
            }
            const response = await fetch(endpoint, {
              method: options.method || "GET",
              headers: {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": "Bearer " + token,
              },
              body: options.body ? JSON.stringify(options.body) : undefined,
            });
            const payload = await response.json().catch(() => ({ ok: false, error: "invalid_json" }));
            if (!response.ok) {
              throw new Error(JSON.stringify(payload, null, 2));
            }
            return payload;
          };

          const refreshRuntime = async () => {
            try {
              writeLog("Reload runtime", { state: "pending" });
              const payload = await requestJson("/admin/api/runtime-business");
              writeLog("Runtime business snapshot", payload);
            } catch (error) {
              writeLog("Runtime reload failed", String(error.message || error));
            }
          };

          const hydrateSecret = () => {
            const stored = sessionStorage.getItem(secretStorageKey);
            if (stored && !secretInput.value) {
              secretInput.value = stored;
            }
          };

          const hydrateClientToken = () => {
            if (!clientTokenInput) return;
            const stored = sessionStorage.getItem(clientTokenStorageKey);
            if (stored && !clientTokenInput.value) {
              clientTokenInput.value = stored;
            }
          };

          const hydrateStaffToken = () => {
            if (!staffTokenInput) return;
            const stored = sessionStorage.getItem(staffTokenStorageKey);
            if (stored && !staffTokenInput.value) {
              staffTokenInput.value = stored;
            }
          };

          const hydrateVendorToken = () => {
            if (!vendorTokenInput) return;
            const stored = sessionStorage.getItem(vendorTokenStorageKey);
            if (stored && !vendorTokenInput.value) {
              vendorTokenInput.value = stored;
            }
          };

          const getClientToken = () => {
            if (!clientTokenInput) {
              throw new Error("client_token_input_missing");
            }
            const value = clientTokenInput.value.trim();
            if (!value) {
              throw new Error("client_token_missing");
            }
            sessionStorage.setItem(clientTokenStorageKey, value);
            return value;
          };

          const getStaffToken = () => {
            if (!staffTokenInput) {
              throw new Error("staff_token_input_missing");
            }
            const value = staffTokenInput.value.trim();
            if (!value) {
              throw new Error("staff_token_missing");
            }
            sessionStorage.setItem(staffTokenStorageKey, value);
            return value;
          };

          const getVendorToken = () => {
            if (!vendorTokenInput) {
              throw new Error("vendor_token_input_missing");
            }
            const value = vendorTokenInput.value.trim();
            if (!value) {
              throw new Error("vendor_token_missing");
            }
            sessionStorage.setItem(vendorTokenStorageKey, value);
            return value;
          };

          const loadClientAccount = async () => {
            const token = getClientToken();
            const response = await fetch("/clients/api/account", {
              method: "GET",
              headers: {
                "accept": "application/json",
                "authorization": "Bearer " + token,
              },
            });
            const payload = await response.json().catch(() => ({ ok: false, error: "invalid_json" }));
            if (!response.ok) {
              throw new Error(JSON.stringify(payload, null, 2));
            }
            return payload;
          };

          const loadStaffDashboard = async () => {
            const token = getStaffToken();
            const response = await fetch("/staff/api/dashboard", {
              method: "GET",
              headers: {
                "accept": "application/json",
                "authorization": "Bearer " + token,
              },
            });
            const payload = await response.json().catch(() => ({ ok: false, error: "invalid_json" }));
            if (!response.ok) {
              throw new Error(JSON.stringify(payload, null, 2));
            }
            return payload;
          };

          const loadVendorDashboard = async () => {
            const token = getVendorToken();
            const response = await fetch("/vendors/api/dashboard", {
              method: "GET",
              headers: {
                "accept": "application/json",
                "authorization": "Bearer " + token,
              },
            });
            const payload = await response.json().catch(() => ({ ok: false, error: "invalid_json" }));
            if (!response.ok) {
              throw new Error(JSON.stringify(payload, null, 2));
            }
            return payload;
          };

          if (sessionButton) {
            sessionButton.addEventListener("click", async () => {
              try {
                writeLog("Operator session", { state: "pending" });
                const payload = await createOperatorSession();
                writeLog("Operator session ready", payload);
              } catch (error) {
                writeLog("Operator session failed", String(error.message || error));
              }
            });
          }

          if (refreshButton) {
            refreshButton.addEventListener("click", refreshRuntime);
          }

          if (clientLoadButton) {
            clientLoadButton.addEventListener("click", async () => {
              try {
                writeClientLog("Client account", { state: "pending" });
                const payload = await loadClientAccount();
                writeClientLog("Client account ready", payload);
              } catch (error) {
                writeClientLog("Client account failed", String(error.message || error));
              }
            });
          }

          if (staffLoadButton) {
            staffLoadButton.addEventListener("click", async () => {
              try {
                writeStaffLog("Staff dashboard", { state: "pending" });
                const payload = await loadStaffDashboard();
                writeStaffLog("Staff dashboard ready", payload);
              } catch (error) {
                writeStaffLog("Staff dashboard failed", String(error.message || error));
              }
            });
          }

          if (vendorLoadButton) {
            vendorLoadButton.addEventListener("click", async () => {
              try {
                writeVendorLog("Vendor dashboard", { state: "pending" });
                const payload = await loadVendorDashboard();
                writeVendorLog("Vendor dashboard ready", payload);
              } catch (error) {
                writeVendorLog("Vendor dashboard failed", String(error.message || error));
              }
            });
          }

          forms.forEach((form) => {
            form.addEventListener("submit", async (event) => {
              event.preventDefault();
              const formData = new FormData(form);
              const payload = Object.fromEntries(formData.entries());
              Object.keys(payload).forEach((key) => {
                if (payload[key] === "") {
                  delete payload[key];
                }
              });
              try {
                writeLog("Submit " + form.dataset.adminForm, { state: "pending", payload });
                const response = await requestJson(form.dataset.adminForm, {
                  method: "POST",
                  body: payload,
                });
                writeLog("Action completed", response);
              } catch (error) {
                writeLog("Action failed", String(error.message || error));
              }
            });
          });

          hydrateSecret();
          hydrateClientToken();
          hydrateStaffToken();
          hydrateVendorToken();
          if (getToken()) {
            const meta = sessionStorage.getItem(sessionMetaKey);
            writeLog("Operator session restored", meta ? JSON.parse(meta) : { restored: true });
          }
          if (sessionStorage.getItem(clientTokenStorageKey)) {
            writeClientLog("Client token restored", { restored: true });
          }
          if (sessionStorage.getItem(staffTokenStorageKey)) {
            writeStaffLog("Staff token restored", { restored: true });
          }
          if (sessionStorage.getItem(vendorTokenStorageKey)) {
            writeVendorLog("Vendor token restored", { restored: true });
          }
        })();
      </script>
    ` : ""}
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
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`upstream_${response.status}`);
  }

  return response.json();
}

async function fetchMasterWalletBalance(address) {
  if (!address) {
    return {
      akt_balance: null,
      akt_price_usd: null,
      akt_value_usd: null,
    };
  }

  const [balanceResult, priceResult] = await Promise.allSettled([
    fetchJson(`https://rest.cosmos.directory/akash/cosmos/bank/v1beta1/balances/${address}`),
    fetchJson("https://api.coingecko.com/api/v3/simple/price?ids=akash-network&vs_currencies=usd"),
  ]);

  let aktBalance = null;
  let aktPriceUsd = null;

  if (balanceResult.status === "fulfilled") {
    const balances = balanceResult.value?.balances || [];
    const match = balances.find((item) => item?.denom === "uakt");
    if (match?.amount) {
      aktBalance = Number(match.amount) / 1000000;
    }
  }

  if (priceResult.status === "fulfilled") {
    aktPriceUsd = priceResult.value?.["akash-network"]?.usd ?? null;
  }

  return {
    akt_balance: aktBalance,
    akt_price_usd: aktPriceUsd,
    akt_value_usd:
      aktBalance != null && aktPriceUsd != null
        ? Number((aktBalance * aktPriceUsd).toFixed(2))
        : null,
  };
}

async function fetchSecureJson(url, env, method = "GET", body = null) {
  if (!env.S25_SHARED_SECRET) {
    throw new Error("shared_secret_missing");
  }
  const headers = {
    accept: "application/json",
    "user-agent": "smajor-hub/1.0",
    "x-s25-secret": env.S25_SHARED_SECRET,
  };
  if (body) {
    headers["content-type"] = "application/json";
  }
  const response = await fetch(url, {
    method,
    headers,
    body,
    cache: "no-store",
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`secure_upstream_${response.status}:${text}`);
  }
  return response.json();
}

async function fetchOpsSnapshot(env) {
  const runtimeBase = env.DIRECT_RUNTIME_URL || env.PUBLIC_S25_URL;
  const [statusResult, missionsResult, meshResult, memoryResult, vaultResult, infraResult] = await Promise.allSettled([
    fetchJson(`${runtimeBase}/api/status`),
    fetchJson(`${runtimeBase}/api/missions`),
    fetchJson(`${runtimeBase}/api/mesh/status`),
    fetchSecureJson(`${runtimeBase}/api/memory/state`, env),
    fetchJson(`${env.PUBLIC_API_URL}/api/vault/mexc`),
    fetchJson(`${env.PUBLIC_API_URL}/api/akash/infra`),
  ]);
  const registry =
    memoryResult.status === "fulfilled"
      ? memoryResult.value?.state?.intel?.business_registry || memoryResult.value?.state?.business || {}
      : {};
  const statusPayload = statusResult.status === "fulfilled" ? statusResult.value : null;
  const masterWalletAddress =
    statusPayload?.wallet_creator_address || env.MASTER_WALLET_ADDRESS || null;
  const walletFallback = await fetchMasterWalletBalance(masterWalletAddress);
  if (statusPayload) {
    statusPayload.wallet_creator_akt_balance ??= walletFallback.akt_balance;
    statusPayload.wallet_creator_akt_price_usd ??= walletFallback.akt_price_usd;
    statusPayload.wallet_creator_akt_value_usd ??= walletFallback.akt_value_usd;
  }
  const walletsCustody = {
    title: "Wallets and custody registry",
    records: [
      {
        wallet_id: "wallet-creator-001",
        label: env.MASTER_WALLET_LABEL || "Wallet creator",
        network: "akash",
        address: masterWalletAddress || "unconfigured",
        connected: Boolean(statusPayload?.wallet_creator_connected ?? masterWalletAddress),
        custody: statusPayload?.wallet_custody || "google_secret_manager",
        akt_balance: statusPayload?.wallet_creator_akt_balance ?? walletFallback.akt_balance ?? null,
        akt_value_usd: statusPayload?.wallet_creator_akt_value_usd ?? walletFallback.akt_value_usd ?? null,
      },
    ],
  };
  const vaultsTreasury = {
    title: "Vaults and treasury command",
    treasury: {
      wallet_id: "wallet-creator-001",
      address: masterWalletAddress || "unconfigured",
      connected: Boolean(statusPayload?.wallet_creator_connected ?? masterWalletAddress),
      custody: statusPayload?.wallet_custody || "google_secret_manager",
      akt_balance: statusPayload?.wallet_creator_akt_balance ?? walletFallback.akt_balance ?? null,
      akt_value_usd: statusPayload?.wallet_creator_akt_value_usd ?? walletFallback.akt_value_usd ?? null,
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
  const internalOps = {
    title: "Smajor internal operations",
    account_live: Boolean(
      (Array.isArray(registry.clients) ? registry.clients : []).find(
        (record) =>
          record.client_id === "client-smajor-internal-001" ||
          record.organization_name === "Smajor Internal Operations",
      ),
    ),
    client:
      (Array.isArray(registry.clients) ? registry.clients : []).find(
        (record) =>
          record.client_id === "client-smajor-internal-001" ||
          record.organization_name === "Smajor Internal Operations",
      ) || null,
    jobs_open: (Array.isArray(registry.jobs) ? registry.jobs : []).filter(
      (record) => record.client_id === "client-smajor-internal-001",
    ).length,
    finance_entries: (Array.isArray(registry.quotes_invoices) ? registry.quotes_invoices : []).filter(
      (record) => record.client_id === "client-smajor-internal-001",
    ).length,
    last_write_at: registry.last_write_at || null,
  };

  return {
    status: statusPayload,
    missions: missionsResult.status === "fulfilled" ? missionsResult.value : null,
    mesh: meshResult.status === "fulfilled" ? meshResult.value : null,
    vault: vaultResult.status === "fulfilled" ? vaultResult.value : null,
    infra: infraResult.status === "fulfilled" ? infraResult.value : null,
    business: {
      clients: { records: Array.isArray(registry.clients) ? registry.clients : [] },
      jobs: { records: Array.isArray(registry.jobs) ? registry.jobs : [] },
      quotes_invoices: { records: Array.isArray(registry.quotes_invoices) ? registry.quotes_invoices : [] },
      wallets_custody: walletsCustody,
      vaults_treasury: vaultsTreasury,
      internal_ops: internalOps,
    },
    errors: [statusResult, missionsResult, meshResult, memoryResult, vaultResult, infraResult]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "upstream_error"),
  };
}

async function fetchAdminSnapshot(env) {
  const runtimeBase = env.DIRECT_RUNTIME_URL || env.PUBLIC_S25_URL;
  const [memoryResult, walletsResult, treasuryResult, secretCustodyResult, secretFallbackResult, geminiLayerResult] = await Promise.allSettled([
    fetchSecureJson(`${runtimeBase}/api/memory/state`, env),
    fetchJson(`${env.PUBLIC_API_URL}/api/business/wallets-custody`),
    fetchJson(`${env.PUBLIC_API_URL}/api/business/vaults-treasury`),
    fetchJson(`${env.PUBLIC_API_URL}/api/business/secret-custody`),
    fetchJson(`${env.PUBLIC_API_URL}/api/business/secret-fallback-policy`),
    fetchJson(`${env.PUBLIC_API_URL}/api/business/gemini-layer`),
  ]);
  const registry = memoryResult.status === "fulfilled"
    ? memoryResult.value?.state?.intel?.business_registry || memoryResult.value?.state?.business || {}
    : {};
  const business = {
    title: "Live business registries",
    secure: true,
    clients: Array.isArray(registry.clients) ? registry.clients : [],
    jobs: Array.isArray(registry.jobs) ? registry.jobs : [],
    quotes_invoices: Array.isArray(registry.quotes_invoices) ? registry.quotes_invoices : [],
    identities: Array.isArray(registry.identities) ? registry.identities : [],
    events: Array.isArray(registry.events) ? registry.events : [],
    last_write_at: registry.last_write_at || null,
  };
  const operatorRoster = {
    secure: true,
    title: "Operator roster",
    summary: "Racine humaine de gouvernance: les comptes major entrent dans la meme matrice RBAC que le reste du systeme.",
    identities: business.identities.filter((identity) => identity.badge_id === "major_badge"),
    total_operator_identities: business.identities.filter((identity) => identity.badge_id === "major_badge").length,
    last_write_at: business.last_write_at,
  };
  return {
    liveRegistries: business,
    businessTimeline: {
      secure: true,
      title: "Business timeline",
      summary: "Audit trail vivant des creations, acces et ecritures du control plane.",
      records: business.events,
      total_events: business.events.length,
      last_write_at: business.last_write_at,
    },
    operatorRoster,
    walletsCustody: walletsResult.status === "fulfilled" ? walletsResult.value : null,
    vaultsTreasury: treasuryResult.status === "fulfilled" ? treasuryResult.value : null,
    secretCustody: secretCustodyResult.status === "fulfilled" ? secretCustodyResult.value : null,
    secretFallbackPolicy: secretFallbackResult.status === "fulfilled" ? secretFallbackResult.value : null,
    geminiLayer: geminiLayerResult.status === "fulfilled" ? geminiLayerResult.value : null,
    errors: [memoryResult, walletsResult, treasuryResult, secretCustodyResult, secretFallbackResult, geminiLayerResult]
      .filter((result) => result.status === "rejected")
      .map((result) => result.reason?.message || "secure_memory_upstream_error"),
  };
}

function buildRuntimeBusinessState(seed = {}) {
  return {
    clients: Array.isArray(seed.clients) ? seed.clients : [],
    jobs: Array.isArray(seed.jobs) ? seed.jobs : [],
    quotes_invoices: Array.isArray(seed.quotes_invoices) ? seed.quotes_invoices : [],
    identities: Array.isArray(seed.identities) ? seed.identities : [],
    events: Array.isArray(seed.events) ? seed.events : [],
    last_write_at: seed.last_write_at || null,
  };
}

async function readRuntimeBusinessState(env) {
  const runtimeBase = env.DIRECT_RUNTIME_URL || env.PUBLIC_S25_URL;
  const memory = await fetchSecureJson(`${runtimeBase}/api/memory/state`, env);
  return buildRuntimeBusinessState(
    memory?.state?.intel?.business_registry || memory?.state?.business || {},
  );
}

function createHubRecordId(prefix) {
  return `${prefix}-${crypto.randomUUID().slice(0, 8)}`;
}

function appendBusinessEvent(business, event) {
  const auditEvent = {
    event_id: createHubRecordId("event"),
    event_type: event.event_type || "business_write",
    lane: event.lane || "admin",
    actor_type: event.actor_type || "operator",
    actor_id: event.actor_id || "smajor_operator_console",
    subject_type: event.subject_type || "record",
    subject_id: event.subject_id || null,
    collection: event.collection || null,
    scope_id: event.scope_id || "governance_scope",
    summary: event.summary || "Business event written",
    created_at: event.created_at || new Date().toISOString(),
    metadata: event.metadata || {},
  };
  business.events = [auditEvent, ...(business.events || [])].slice(0, 120);
  return auditEvent;
}

function buildHubBusinessRecord(kind, body) {
  const now = new Date().toISOString();
  if (kind === "client") {
    return {
      client_id: body.client_id || createHubRecordId("client"),
      organization_id: body.organization_id || createHubRecordId("org"),
      organization_name: body.organization_name || "Unnamed Organization",
      identity_id: body.identity_id || createHubRecordId("ident"),
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
      job_id: body.job_id || createHubRecordId("job"),
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
      identity_id: body.identity_id || createHubRecordId("ident"),
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
    quote_id: body.quote_id || createHubRecordId("quote"),
    invoice_id: body.invoice_id || null,
    client_id: body.client_id || "",
    job_id: body.job_id || "",
    amount: body.amount ? Number(body.amount) : 0,
    currency: body.currency || "CAD",
    payment_status: body.payment_status || "quote_pending",
    billing_stage: body.billing_stage || "quote_prepared",
    created_at: now,
  };
}

async function writeRuntimeBusinessState(env, business) {
  const runtimeBase = env.DIRECT_RUNTIME_URL || env.PUBLIC_S25_URL;
  return fetchSecureJson(
    `${runtimeBase}/api/memory/state`,
    env,
    "POST",
    JSON.stringify({
      agent: "TRINITY",
      intel: {
        business_registry: business,
      },
      business,
    }),
  );
}

async function handleHubBusinessCreate(request, env, kind) {
  const body = await request.json().catch(() => ({}));
  const business = await readRuntimeBusinessState(env);
  const record = buildHubBusinessRecord(kind, body);
  const collectionKey =
    kind === "client"
      ? "clients"
      : kind === "job"
        ? "jobs"
        : kind === "identity"
          ? "identities"
          : "quotes_invoices";
  business[collectionKey] = [record, ...(business[collectionKey] || [])];
  business.last_write_at = new Date().toISOString();
  const subjectId =
    record.client_id ||
    record.job_id ||
    record.identity_id ||
    record.invoice_id ||
    record.quote_id ||
    null;
  const event = appendBusinessEvent(business, {
    event_type: `${kind}_created`,
    lane: kind === "job" ? "operations" : kind === "identity" ? "identity" : kind === "quote" ? "billing" : "client",
    subject_type: kind,
    subject_id: subjectId,
    collection: collectionKey,
    scope_id: record.scope_id || record.dispatch_scope || "governance_scope",
    summary: `${kind} ${subjectId || "record"} created`,
    metadata: {
      role_id: record.role_id || null,
      badge_id: record.badge_id || null,
      organization_id: record.organization_id || null,
    },
  });
  await writeRuntimeBusinessState(env, business);
  return {
    ok: true,
    kind,
    created: record,
    event,
    collection: collectionKey,
    total_records: business[collectionKey].length,
    last_write_at: business.last_write_at,
  };
}

async function handleHubClientPipelineCreate(request, env) {
  const body = await request.json().catch(() => ({}));
  const business = await readRuntimeBusinessState(env);
  const organizationId = body.organization_id || createHubRecordId("org");
  const identityId = body.identity_id || createHubRecordId("ident");
  const serviceType = body.service_type || "multi_service_exterior";
  const now = new Date().toISOString();

  const identityRecord = {
    identity_id: identityId,
    organization_id: organizationId,
    identity_type: body.identity_type || "client_contact",
    display_name: body.display_name || body.contact_name || body.organization_name || "Client Contact",
    role_id: body.identity_role_id || "client_contact",
    badge_id: body.identity_badge_id || "client_badge",
    scope_id: body.identity_scope_id || body.scope_id || "client_scope_default",
    service_entitlements: Array.isArray(body.service_entitlements) ? body.service_entitlements : ["client_portal"],
    credential_state: body.credential_state || "pending_issue",
    portal_state: body.identity_portal_state || "pending_secure_access",
    audit_state: body.audit_state || "watching",
    created_at: now,
  };

  const clientRecord = {
    client_id: body.client_id || createHubRecordId("client"),
    organization_id: organizationId,
    organization_name: body.organization_name || "Unnamed Organization",
    identity_id: identityId,
    role_id: body.client_role_id || "client_contact",
    badge_id: body.client_badge_id || "client_badge",
    scope_id: body.scope_id || "client_scope_default",
    service_mix: Array.isArray(body.service_mix) ? body.service_mix : [serviceType],
    account_status: body.account_status || "active",
    portal_state: body.client_portal_state || "pending_secure_access",
    billing_state: body.billing_state || "quote_pending",
    created_at: now,
  };

  business.identities = [identityRecord, ...(business.identities || [])];
  business.clients = [clientRecord, ...(business.clients || [])];
  business.last_write_at = now;
  const event = appendBusinessEvent(business, {
    event_type: "client_pipeline_created",
    lane: "client",
    subject_type: "client_pipeline",
    subject_id: clientRecord.client_id,
    collection: "clients",
    scope_id: clientRecord.scope_id,
    summary: `Client pipeline created for ${clientRecord.organization_name}`,
    metadata: {
      identity_id: identityRecord.identity_id,
      organization_id: organizationId,
    },
  });
  await writeRuntimeBusinessState(env, business);

  return {
    ok: true,
    kind: "client_pipeline",
    created: {
      identity: identityRecord,
      client: clientRecord,
    },
    event,
    collections: {
      identities: business.identities.length,
      clients: business.clients.length,
    },
    last_write_at: business.last_write_at,
  };
}

async function handleHubClientJobBillingCreate(request, env) {
  const body = await request.json().catch(() => ({}));
  const business = await readRuntimeBusinessState(env);
  const now = new Date().toISOString();
  const organizationId = body.organization_id || createHubRecordId("org");
  const identityId = body.identity_id || createHubRecordId("ident");
  const clientId = body.client_id || createHubRecordId("client");
  const jobId = body.job_id || createHubRecordId("job");
  const quoteId = body.quote_id || createHubRecordId("quote");
  const amount = body.amount ? Number(body.amount) : 0;

  const identityRecord = {
    identity_id: identityId,
    organization_id: organizationId,
    identity_type: body.identity_type || "client_contact",
    display_name: body.display_name || body.contact_name || body.organization_name || "Client Contact",
    role_id: "client_contact",
    badge_id: "client_badge",
    scope_id: body.scope_id || "client_scope_default",
    service_entitlements: ["client_portal"],
    credential_state: body.credential_state || "pending_issue",
    portal_state: "pending_secure_access",
    audit_state: body.audit_state || "watching",
    created_at: now,
  };

  const clientRecord = {
    client_id: clientId,
    organization_id: organizationId,
    organization_name: body.organization_name || "Unnamed Organization",
    identity_id: identityId,
    role_id: "client_contact",
    badge_id: "client_badge",
    scope_id: body.scope_id || "client_scope_default",
    service_mix: Array.isArray(body.service_mix) ? body.service_mix : [body.service_type || "multi_service_exterior"],
    account_status: body.account_status || "active",
    portal_state: "pending_secure_access",
    billing_state: body.billing_state || "quote_pending",
    created_at: now,
  };

  const jobRecord = {
    job_id: jobId,
    client_id: clientId,
    service_type: body.service_type || "multi_service_exterior",
    assigned_team: body.assigned_team || "unassigned",
    equipment_required: Array.isArray(body.equipment_required) ? body.equipment_required : [],
    scheduled_window: body.scheduled_window || "pending_schedule",
    job_status: body.job_status || "scheduled",
    dispatch_scope: body.dispatch_scope || "field_scope_default",
    created_at: now,
  };

  const billingRecord = {
    quote_id: quoteId,
    invoice_id: body.invoice_id || null,
    client_id: clientId,
    job_id: jobId,
    amount,
    currency: body.currency || "CAD",
    payment_status: body.payment_status || "quote_pending",
    billing_stage: body.billing_stage || "quote_prepared",
    created_at: now,
  };

  business.identities = [identityRecord, ...(business.identities || [])];
  business.clients = [clientRecord, ...(business.clients || [])];
  business.jobs = [jobRecord, ...(business.jobs || [])];
  business.quotes_invoices = [billingRecord, ...(business.quotes_invoices || [])];
  business.last_write_at = now;
  const event = appendBusinessEvent(business, {
    event_type: "client_job_billing_created",
    lane: "operations",
    subject_type: "job_billing_bundle",
    subject_id: jobRecord.job_id,
    collection: "jobs",
    scope_id: clientRecord.scope_id,
    summary: `Operational bundle created for ${clientRecord.organization_name}`,
    metadata: {
      client_id: clientRecord.client_id,
      identity_id: identityRecord.identity_id,
      quote_id: billingRecord.quote_id,
      amount: billingRecord.amount,
      currency: billingRecord.currency,
    },
  });
  await writeRuntimeBusinessState(env, business);

  return {
    ok: true,
    kind: "client_job_billing_pipeline",
    created: {
      identity: identityRecord,
      client: clientRecord,
      job: jobRecord,
      billing: billingRecord,
    },
    event,
    collections: {
      identities: business.identities.length,
      clients: business.clients.length,
      jobs: business.jobs.length,
      quotes_invoices: business.quotes_invoices.length,
    },
    last_write_at: business.last_write_at,
  };
}

function requireHubSecret(request, env) {
  if (!env.S25_SHARED_SECRET) {
    return jsonResponse({
      ok: false,
      error: "hub_secret_missing",
    }, 500);
  }
  const provided = request.headers.get("x-s25-secret");
  if (!provided || provided !== env.S25_SHARED_SECRET) {
    return jsonResponse({
      ok: false,
      error: "unauthorized",
      required_header: "x-s25-secret",
    }, 401);
  }
  return null;
}

function encodeBase64Url(input) {
  const bytes = input instanceof Uint8Array ? input : new TextEncoder().encode(String(input));
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function decodeBase64Url(input) {
  const normalized = String(input).replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new TextDecoder().decode(bytes);
}

async function signOperatorSession(payload, env) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(env.S25_SHARED_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const header = encodeBase64Url(JSON.stringify({ alg: "HS256", typ: "S25" }));
  const body = encodeBase64Url(JSON.stringify(payload));
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(`${header}.${body}`));
  return `${header}.${body}.${encodeBase64Url(new Uint8Array(signature))}`;
}

async function verifyOperatorSession(token, env) {
  if (!token || !env.S25_SHARED_SECRET) {
    return { ok: false, error: "operator_session_missing" };
  }
  const parts = String(token).split(".");
  if (parts.length !== 3) {
    return { ok: false, error: "operator_session_invalid" };
  }
  const [header, body, signature] = parts;
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(env.S25_SHARED_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  const valid = await crypto.subtle.verify(
    "HMAC",
    key,
    Uint8Array.from(atob(String(signature).replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (signature.length % 4)) % 4)), (c) => c.charCodeAt(0)),
    new TextEncoder().encode(`${header}.${body}`),
  );
  if (!valid) {
    return { ok: false, error: "operator_session_signature_invalid" };
  }
  const payload = JSON.parse(decodeBase64Url(body));
  if (!payload.exp || Date.now() > payload.exp) {
    return { ok: false, error: "operator_session_expired" };
  }
  return { ok: true, payload };
}

async function requireOperatorAccess(request, env) {
  if (!env.S25_SHARED_SECRET) {
    return jsonResponse({ ok: false, error: "hub_secret_missing" }, 500);
  }
  const authHeader = request.headers.get("authorization") || "";
  const bearer = authHeader.startsWith("Bearer ") ? authHeader.slice(7).trim() : "";
  if (bearer) {
    const verified = await verifyOperatorSession(bearer, env);
    if (verified.ok) {
      return null;
    }
  }
  return requireHubSecret(request, env);
}

async function createOperatorSession(request, env) {
  const denied = requireHubSecret(request, env);
  if (denied) {
    return denied;
  }
  const now = Date.now();
  const payload = {
    sub: "smajor_operator_console",
    role_id: "operator_admin",
    badge_id: "major_badge",
    scope_id: "founder_scope",
    issued_at: new Date(now).toISOString(),
    exp: now + (1000 * 60 * 60 * 8),
  };
  const token = await signOperatorSession(payload, env);
  return jsonResponse({
    ok: true,
    session_type: "operator_bearer",
    token,
    expires_at: new Date(payload.exp).toISOString(),
    profile: {
      role_id: payload.role_id,
      badge_id: payload.badge_id,
      scope_id: payload.scope_id,
    },
  });
}

function buildClientPortalSnapshot(business, clientId) {
  const client = (business.clients || []).find((record) => record.client_id === clientId) || null;
  if (!client) {
    return null;
  }
  const jobs = (business.jobs || []).filter((record) => record.client_id === clientId);
  const billing = (business.quotes_invoices || []).filter((record) => record.client_id === clientId);
  const identities = (business.identities || []).filter((record) => record.organization_id === client.organization_id);
  return {
    ok: true,
    client,
    jobs,
    billing,
    identities,
    metrics: {
      jobs_total: jobs.length,
      billing_total: billing.length,
      portal_state: client.portal_state || "pending_secure_access",
      billing_state: client.billing_state || "quote_pending",
    },
    last_write_at: business.last_write_at || null,
  };
}

function buildStaffPortalSnapshot(business, access) {
  const identity = (business.identities || []).find((record) => record.identity_id === access.identity_id) || null;
  if (!identity) {
    return null;
  }
  const jobs = (business.jobs || []).filter((record) => {
    if (access.assigned_team && record.assigned_team === access.assigned_team) {
      return true;
    }
    if (access.scope_id && record.scope_id === access.scope_id) {
      return true;
    }
    return false;
  });
  const organizationIds = Array.from(new Set(jobs.map((record) => record.organization_id).filter(Boolean)));
  const clients = (business.clients || []).filter((record) => organizationIds.includes(record.organization_id));
  const billing = (business.quotes_invoices || []).filter((record) => organizationIds.includes(record.organization_id));
  return {
    ok: true,
    identity,
    jobs,
    clients,
    billing,
    metrics: {
      jobs_total: jobs.length,
      clients_total: clients.length,
      billing_total: billing.length,
      assigned_team: access.assigned_team || "unassigned",
      scope_id: access.scope_id || "field_scope_default",
    },
    last_write_at: business.last_write_at || null,
  };
}

function buildVendorPortalSnapshot(business, access) {
  const identity = (business.identities || []).find((record) => record.identity_id === access.identity_id) || null;
  if (!identity) {
    return null;
  }
  const vendorHints = ["vendor", "supply", "purchase", "delivery", "material", "rental"];
  const billing = (business.quotes_invoices || []).filter((record) => {
    const stage = String(record.billing_stage || "").toLowerCase();
    return vendorHints.some((hint) => stage.includes(hint));
  });
  const jobs = (business.jobs || []).filter((record) => {
    const equipment = Array.isArray(record.equipment_required) ? record.equipment_required.join(" ").toLowerCase() : "";
    return vendorHints.some((hint) => equipment.includes(hint));
  });
  const events = (business.events || [])
    .filter((event) => {
      const summary = String(event.summary || "").toLowerCase();
      return event.lane === "vendor" || vendorHints.some((hint) => summary.includes(hint));
    })
    .slice(0, 8);
  return {
    ok: true,
    identity,
    jobs,
    billing,
    events,
    metrics: {
      jobs_total: jobs.length,
      billing_total: billing.length,
      event_total: events.length,
      scope_id: access.scope_id || "vendor_scope_default",
    },
    last_write_at: business.last_write_at || null,
  };
}

async function issueClientAccess(request, env) {
  const body = await request.json().catch(() => ({}));
  const business = await readRuntimeBusinessState(env);
  const clientId = body.client_id;
  if (!clientId) {
    return jsonResponse({ ok: false, error: "client_id_required" }, 400);
  }
  const client = (business.clients || []).find((record) => record.client_id === clientId);
  if (!client) {
    return jsonResponse({ ok: false, error: "client_not_found", client_id: clientId }, 404);
  }
  const payload = {
    sub: client.identity_id || client.client_id,
    session_type: "client_portal",
    client_id: client.client_id,
    organization_id: client.organization_id,
    identity_id: client.identity_id,
    role_id: client.role_id || "client_contact",
    badge_id: client.badge_id || "client_badge",
    scope_id: client.scope_id || "client_scope_default",
    service_mix: Array.isArray(client.service_mix) ? client.service_mix : [],
    issued_at: new Date().toISOString(),
    exp: Date.now() + (1000 * 60 * 60 * 24 * 7),
  };
  const token = await signOperatorSession(payload, env);
  const event = appendBusinessEvent(business, {
    event_type: "client_access_issued",
    lane: "client",
    subject_type: "client_access",
    subject_id: client.client_id,
    collection: "clients",
    scope_id: payload.scope_id,
    summary: `Client access issued for ${client.organization_name}`,
    metadata: {
      identity_id: client.identity_id,
      role_id: payload.role_id,
    },
  });
  business.last_write_at = new Date().toISOString();
  await writeRuntimeBusinessState(env, business);
  return jsonResponse({
    ok: true,
    session_type: "client_portal_bearer",
    client_id: client.client_id,
    organization_name: client.organization_name,
    token,
    event,
    expires_at: new Date(payload.exp).toISOString(),
    portal_url: `${env.PUBLIC_APP_URL || "https://app.smajor.org"}/clients`,
  });
}

async function issueStaffAccess(request, env) {
  const body = await request.json().catch(() => ({}));
  const business = await readRuntimeBusinessState(env);
  const identityId = body.identity_id;
  if (!identityId) {
    return jsonResponse({ ok: false, error: "identity_id_required" }, 400);
  }
  const identity = (business.identities || []).find((record) => record.identity_id === identityId);
  if (!identity) {
    return jsonResponse({ ok: false, error: "identity_not_found", identity_id: identityId }, 404);
  }
  const roleId = identity.role_id || "staff_member";
  const allowedRoles = ["dispatcher", "field_manager", "staff_member", "contractor", "executive_operator"];
  if (!allowedRoles.includes(roleId)) {
    return jsonResponse({ ok: false, error: "identity_not_staff_eligible", role_id: roleId }, 400);
  }
  const payload = {
    sub: identity.identity_id,
    session_type: "staff_portal",
    identity_id: identity.identity_id,
    organization_id: identity.organization_id,
    role_id: roleId,
    badge_id: identity.badge_id || "employee_badge",
    scope_id: body.scope_id || identity.scope_id || "field_scope_default",
    assigned_team: body.assigned_team || identity.assigned_team || "crew-north-01",
    issued_at: new Date().toISOString(),
    exp: Date.now() + (1000 * 60 * 60 * 24 * 3),
  };
  const token = await signOperatorSession(payload, env);
  const event = appendBusinessEvent(business, {
    event_type: "staff_access_issued",
    lane: "staff",
    subject_type: "staff_access",
    subject_id: identity.identity_id,
    collection: "identities",
    scope_id: payload.scope_id,
    summary: `Staff access issued for ${identity.display_name || identity.identity_id}`,
    metadata: {
      role_id: roleId,
      assigned_team: payload.assigned_team,
    },
  });
  business.last_write_at = new Date().toISOString();
  await writeRuntimeBusinessState(env, business);
  return jsonResponse({
    ok: true,
    session_type: "staff_portal_bearer",
    identity_id: identity.identity_id,
    display_name: identity.display_name,
    token,
    event,
    expires_at: new Date(payload.exp).toISOString(),
    portal_url: `${env.PUBLIC_APP_URL || "https://app.smajor.org"}/staff`,
  });
}

async function issueVendorAccess(request, env) {
  const body = await request.json().catch(() => ({}));
  const business = await readRuntimeBusinessState(env);
  const identityId = body.identity_id;
  if (!identityId) {
    return jsonResponse({ ok: false, error: "identity_id_required" }, 400);
  }
  const identity = (business.identities || []).find((record) => record.identity_id === identityId) || null;
  if (!identity) {
    return jsonResponse({ ok: false, error: "identity_not_found", identity_id: identityId }, 404);
  }
  const roleId = identity.role_id || "vendor_contact";
  const allowedRoles = ["vendor_manager", "vendor_contact", "executive_operator"];
  if (!allowedRoles.includes(roleId)) {
    return jsonResponse({ ok: false, error: "identity_not_vendor_eligible", role_id: roleId }, 400);
  }
  const payload = {
    sub: identity.identity_id,
    session_type: "vendor_portal",
    identity_id: identity.identity_id,
    organization_id: identity.organization_id,
    role_id: roleId,
    badge_id: identity.badge_id || "vendor_badge",
    scope_id: body.scope_id || identity.scope_id || "vendor_scope_default",
    vendor_class: body.vendor_class || "supplier",
    issued_at: new Date().toISOString(),
    exp: Date.now() + (1000 * 60 * 60 * 24 * 7),
  };
  const token = await signOperatorSession(payload, env);
  const event = appendBusinessEvent(business, {
    event_type: "vendor_access_issued",
    lane: "vendor",
    subject_type: "vendor_access",
    subject_id: identity.identity_id,
    collection: "identities",
    scope_id: payload.scope_id,
    summary: `Vendor access issued for ${identity.display_name || identity.identity_id}`,
    metadata: {
      role_id: roleId,
      vendor_class: payload.vendor_class,
    },
  });
  business.last_write_at = new Date().toISOString();
  await writeRuntimeBusinessState(env, business);
  return jsonResponse({
    ok: true,
    session_type: "vendor_portal_bearer",
    identity_id: identity.identity_id,
    display_name: identity.display_name,
    token,
    event,
    expires_at: new Date(payload.exp).toISOString(),
    portal_url: `${env.PUBLIC_APP_URL || "https://app.smajor.org"}/vendors`,
  });
}

async function requireVendorAccess(request, env) {
  const authHeader = request.headers.get("authorization") || "";
  const bearer = authHeader.startsWith("Bearer ") ? authHeader.slice(7).trim() : "";
  const verified = await verifyOperatorSession(bearer, env);
  if (!verified.ok) {
    return {
      denied: jsonResponse({ ok: false, error: "vendor_access_required", detail: verified.error }, 401),
    };
  }
  if (verified.payload.session_type !== "vendor_portal") {
    return {
      denied: jsonResponse({ ok: false, error: "vendor_access_invalid_session_type", session_type: verified.payload.session_type }, 403),
    };
  }
  return { denied: null, payload: verified.payload };
}

async function requireClientAccess(request, env) {
  const authHeader = request.headers.get("authorization") || "";
  const bearer = authHeader.startsWith("Bearer ") ? authHeader.slice(7).trim() : "";
  const verified = await verifyOperatorSession(bearer, env);
  if (!verified.ok) {
    return { denied: jsonResponse({ ok: false, error: verified.error || "client_session_missing" }, 401) };
  }
  if (verified.payload.session_type !== "client_portal") {
    return { denied: jsonResponse({ ok: false, error: "client_session_required" }, 403) };
  }
  return { denied: null, payload: verified.payload };
}

async function requireStaffAccess(request, env) {
  const authHeader = request.headers.get("authorization") || "";
  const bearer = authHeader.startsWith("Bearer ") ? authHeader.slice(7).trim() : "";
  const verified = await verifyOperatorSession(bearer, env);
  if (!verified.ok) {
    return { denied: jsonResponse({ ok: false, error: verified.error || "staff_session_missing" }, 401) };
  }
  if (verified.payload.session_type !== "staff_portal") {
    return { denied: jsonResponse({ ok: false, error: "staff_session_required" }, 403) };
  }
  return { denied: null, payload: verified.payload };
}

function buildOmegaDeck(env, snapshot) {
  const status = snapshot.status || {};
  const mesh = snapshot.mesh || {};
  const roster = Array.isArray(mesh.roster) ? mesh.roster : [];
  const missions = snapshot.missions || {};
  const activeMissions = Array.isArray(missions.active) ? missions.active : [];
  const vault = snapshot.vault || {};
  const treasury = snapshot.business?.vaults_treasury || {};
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
        label: "Master Wallet",
        value:
          status.wallet_creator_akt_balance != null
            ? `${status.wallet_creator_akt_balance} AKT`
            : "AKT pending",
        text:
          status.wallet_creator_akt_value_usd != null
            ? `Adresse ${status.wallet_creator_address || env.MASTER_WALLET_ADDRESS || "unknown"} · ~$${status.wallet_creator_akt_value_usd}`
            : `Adresse ${status.wallet_creator_address || env.MASTER_WALLET_ADDRESS || "unknown"} · custody ${status.wallet_custody || "gsm"}`,
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
          {
            title: "Custody policy",
            value: treasury.policies?.join(" · ") || "seed_gsm_only · audit_before_trading",
            status: "online",
          },
          {
            title: "Secret fallback",
            value:
              snapshot.admin?.secretFallbackPolicy?.fallback_order
                ?.map((entry) => entry.source)
                ?.join(" -> ") || "google_secret_manager -> local_keyring_vault -> encrypted_sync_bundle -> break_glass_offline",
            status: "online",
          },
          {
            title: "Master treasury",
            value:
              treasury.treasury?.akt_balance != null
                ? `${treasury.treasury.akt_balance} AKT`
                : status.wallet_creator_akt_balance != null
                  ? `${status.wallet_creator_akt_balance} AKT`
                  : "wallet staged",
            status:
              treasury.treasury?.connected != null
                ? treasury.treasury.connected
                  ? "online"
                  : "degraded"
                : status.wallet_creator_connected
                  ? "online"
                  : "degraded",
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
  const secure = snapshot.admin?.liveRegistries;
  const clients = secure?.clients || snapshot.business?.clients?.records || [];
  const jobs = secure?.jobs || snapshot.business?.jobs?.records || [];
  const quotes = secure?.quotes_invoices || snapshot.business?.quotes_invoices?.records || [];
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

function masterWalletSection(pathname, env, snapshot) {
  if (pathname !== "/wallet" && pathname !== "/admin" && pathname !== "/ai") {
    return null;
  }
  const status = snapshot.status || {};
  const walletAddress = status.wallet_creator_address || env.MASTER_WALLET_ADDRESS || "unconfigured";
  const walletLabel = env.MASTER_WALLET_LABEL || "Wallet master";
  const walletConnected = status.wallet_creator_connected != null ? Boolean(status.wallet_creator_connected) : Boolean(walletAddress && walletAddress !== "unconfigured");
  const walletCustody = status.wallet_custody || "google_secret_manager";
  const aktBalance = status.wallet_creator_akt_balance;
  const aktValueUsd = status.wallet_creator_akt_value_usd;
  return {
    title: "Master wallet status",
    intro: "Adresse publique du wallet creator et connexion live au cockpit S25.",
    columns: [
      {
        label: walletLabel,
        items: [
          walletAddress,
          `prefix=akash`,
          `connected=${walletConnected ? "true" : "false"}`,
          `akt_balance=${aktBalance != null ? aktBalance : "--"}`,
        ],
      },
      {
        label: "S25 connection",
        items: [
          `pipeline=${status.pipeline_status || "unknown"}`,
          `agents_online=${status.mesh_agents_online ?? "--"}`,
          `missions_active=${status.missions_active ?? "--"}`,
        ],
      },
      {
        label: "Runtime",
        items: [
          `custody=${walletCustody}`,
          `akt_value_usd=${aktValueUsd != null ? `$${aktValueUsd}` : "--"}`,
          `signal=${status.arkon5_action || "--"}`,
          `tunnel=${status.system?.tunnel || (status.tunnel_active ? "online" : "offline")}`,
          `ha=${status.ha_connected ? "linked" : "off"}`,
        ],
      },
    ],
    model: {
      title: "Master wallet status",
      label: walletLabel,
      wallet_address: walletAddress,
      wallet_prefix: "akash",
      creator_connected: walletConnected,
      custody: walletCustody,
      akt_balance: aktBalance,
      akt_value_usd: aktValueUsd,
      source_of_truth: "S25 Lumiere runtime status + Google Secret Manager derived public address",
      s25_connection: {
        pipeline_status: status.pipeline_status || "unknown",
        mesh_agents_online: status.mesh_agents_online ?? null,
        missions_active: status.missions_active ?? null,
        arkon5_action: status.arkon5_action || null,
        tunnel: status.system?.tunnel || (status.tunnel_active ? "online" : "offline"),
        ha_connected: Boolean(status.ha_connected),
      },
    },
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

function staffConsoleSection(pathname, snapshot) {
  if (pathname !== "/staff") {
    return null;
  }
  const business = snapshot.business || {};
  const jobs = business.jobs?.records || [];
  const billing = business.quotes_invoices?.records || [];
  const identities = business.identities?.records || [];
  return {
    title: "Staff dashboard console",
    intro: "Console legere pour charger un dashboard terrain signe, borne a l'identite staff, a son scope et a son equipe.",
    metrics: [
      { label: "Identites visibles", value: String(identities.length) },
      { label: "Jobs visibles", value: String(jobs.length) },
      { label: "Finance visible", value: String(billing.length) },
      { label: "Mode", value: "Signed staff access" },
    ],
    endpoints: [
      "/staff/api/dashboard",
      "bearer token staff requis",
      "lecture limitee au scope terrain",
    ],
    flow: [
      "Recevoir un token staff emis par l'admin.",
      "Coller le token dans la session staff.",
      "Charger le dashboard terrain live, les jobs et la facturation visibles.",
      "Garder l'acces borne a l'identite, a l'equipe et au scope terrain.",
    ],
    initialLog: JSON.stringify(
      {
        mode: "staff_portal_ready",
        note: "Coller un token staff signe puis charger le dashboard live.",
        sample_identity: identities[0]?.identity_id || null,
      },
      null,
      2,
    ),
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

function executiveReportSection(pathname, snapshot) {
  if (!["/", "/admin", "/ai"].includes(pathname)) {
    return null;
  }
  const status = snapshot.status || {};
  const mesh = snapshot.mesh || {};
  const business = snapshot.business || {};
  const admin = snapshot.admin || {};
  const clients = business.clients?.records || [];
  const jobs = business.jobs?.records || [];
  const billing = business.quotes_invoices?.records || [];
  const identities = business.identities?.records || [];
  const treasury = business.vaults_treasury || {};
  const operators = admin.operatorRoster?.identities || [];
  const activeMissions = snapshot.missions?.active || [];
  const roster = mesh.roster || [];
  return {
    title: "Rapport executif Smajor",
    intro: "Vue courte pour voir si la base tient: mesh, operations business, portails signes et posture mirror fleet.",
    columns: [
      {
        label: "Mesh",
        items: [
          `pipeline=${status.pipeline_status || "UNKNOWN"}`,
          `agents_online=${mesh.agents_online ?? roster.length ?? 0}`,
          `missions_active=${activeMissions.length}`,
          `arkon_action=${status.arkon5_action || "UNKNOWN"}`,
        ],
      },
      {
        label: "Business",
        items: [
          `clients=${clients.length}`,
          `jobs=${jobs.length}`,
          `quotes_invoices=${billing.length}`,
          `identities=${identities.length}`,
        ],
      },
      {
        label: "Portals",
        items: [
          "admin=operator session signed",
          "clients=client bearer access live",
          "staff=staff bearer access live",
          "vendors=vendor bearer access live",
          `operators=${operators.length}`,
        ],
      },
      {
        label: "Mirror fleet",
        items: [
          "fleet=10 containers defined",
          "merlin_authority=established",
          "google_project=gen-lang-client-0046423999",
          "next=create Secret Manager values",
        ],
      },
      {
        label: "Treasury",
        items: [
          `custody=${treasury.treasury?.custody || "google_secret_manager"}`,
          `wallet_connected=${treasury.treasury?.connected ? "true" : "false"}`,
          `akt_balance=${treasury.treasury?.akt_balance ?? "--"}`,
          `policy=${treasury.policies?.[0] || "seed_gsm_only"}`,
        ],
      },
    ],
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

function operatorAccountSection(pathname) {
  if (!["/admin", "/ai"].includes(pathname)) {
    return null;
  }
  return {
    title: OPERATOR_ACCOUNT_MODEL.title,
    intro: OPERATOR_ACCOUNT_MODEL.summary,
    columns: OPERATOR_ACCOUNT_MODEL.columns,
  };
}

function operatorRosterSection(pathname, snapshot) {
  if (!["/admin", "/ai"].includes(pathname)) {
    return null;
  }
  const identities = snapshot.admin?.operatorRoster?.identities || [];
  if (!identities.length) {
    return null;
  }
  return {
    title: "Operator roster live",
    intro: "Lecture admin protegee des comptes major qui portent la gouvernance reelle.",
    columns: identities.map((identity) => ({
      label: identity.display_name || identity.identity_id,
      items: [
        identity.identity_id,
        identity.role_id,
        identity.badge_id,
        identity.scope_id,
      ],
    })),
  };
}

function adminActionSection(pathname) {
  if (pathname !== "/admin") {
    return null;
  }
  return {
    title: "Admin live actions",
    intro: "Endpoints operables du hub pour creer des clients, jobs et factures sans sortir du portail.",
    columns: [
      {
        label: "Read",
        items: ["/admin/api/live-registries", "/admin/api/operator-roster", "/admin/api/business-timeline", "/admin/api/operational-chain"],
      },
      {
        label: "Write",
        items: ["/admin/api/create-client", "/admin/api/create-job", "/admin/api/issue-invoice", "/admin/api/issue-vendor-access"],
      },
      {
        label: "Rule",
        items: ["server-side secret only", "same RBAC chain", "audit-first"],
      },
    ],
  };
}

function adminArchitectureSection(pathname) {
  if (pathname !== "/admin") {
    return null;
  }
  return {
    title: "Admin architecture",
    intro: "Le poste admin est une surface de commandement. La logique durable, les secrets et la persistence restent dans le backend souverain.",
    columns: [
      {
        label: "Frontend plane",
        items: [
          "admin shell",
          "signed operator session",
          "live runtime views",
          "form submissions",
        ],
      },
      {
        label: "Backend plane",
        items: [
          "S25 runtime business registry",
          "business API gateway",
          "wallet and secret custody policy",
          "audit trail and RBAC enforcement",
        ],
      },
      {
        label: "Contracts",
        items: [
          "admin_reads_runtime_snapshot",
          "admin_writes_via_signed_routes_only",
          "admin_never_holds_raw_secret_values",
          "admin_actions_must_leave_audit_trace",
        ],
      },
    ],
  };
}

function portalSeparationSection(pathname) {
  if (!["/clients", "/staff", "/vendors", "/admin"].includes(pathname)) {
    return null;
  }
  const maps = {
    "/clients": [
      "frontend=request services, read quotes and invoices",
      "backend=client registry, billing state, secure access tokens",
      "rule=portal simple, orchestration sovereign",
    ],
    "/staff": [
      "frontend=assignments, shifts and field dashboard",
      "backend=dispatch engine, jobs, audit trail and scopes",
      "rule=dashboard terrain, dispatch souverain",
    ],
    "/vendors": [
      "frontend=purchase requests and vendor-facing documents",
      "backend=purchase state, cost linkage and approval gates",
      "rule=etat visible, approvals backend",
    ],
    "/admin": [
      "frontend=operate through signed control surfaces",
      "backend=RBAC, runtime persistence, treasury, agents and secrets",
      "rule=control plane, pas base de donnees",
    ],
  };
  return {
    title: "Portal separation",
    intro: "Chaque portail garde une interface simple. Toute logique durable reste dans le backend S25 et la gateway business.",
    columns: [
      {
        label: pathname.replace("/", "") || "overview",
        items: maps[pathname] || [],
      },
    ],
  };
}

function geminiLayerSection(pathname, snapshot) {
  if (!["/admin", "/ai", "/omega"].includes(pathname)) {
    return null;
  }
  const gemini = snapshot.admin?.geminiLayer || {
    title: "Gemini unified layer",
    summary: "Gemini intelligence layer unavailable",
    doctrine: [],
    split: { intelligence_plane: { responsibilities: [] }, infrastructure_plane: { responsibilities: [] } },
  };
  return {
    title: gemini.title,
    intro: gemini.summary,
    columns: [
      {
        label: gemini.split?.intelligence_plane?.title || "Intelligence plane",
        items: gemini.split?.intelligence_plane?.responsibilities || [],
      },
      {
        label: gemini.split?.infrastructure_plane?.title || "Infrastructure plane",
        items: gemini.split?.infrastructure_plane?.responsibilities || [],
      },
      {
        label: "Doctrine",
        items: gemini.doctrine || [],
      },
    ],
  };
}

function tradingShowroomSection(pathname) {
  if (!["/trade", "/ai", "/omega"].includes(pathname)) {
    return null;
  }
  return {
    title: "Trading showroom",
    intro: "Salle de guerre pour les agents trader: signal, risk, treasury et execution separent la folie sans perdre la gouvernance.",
    columns: [
      {
        label: "Signal lane",
        items: [
          "TRINITY",
          "KIMI",
          "ORACLE",
          "collecte et confirmation",
        ],
      },
      {
        label: "Risk lane",
        items: [
          "MERLIN",
          "ONCHAIN_GUARDIAN",
          "GOUV4",
          "validation et policy gate",
        ],
      },
      {
        label: "Treasury lane",
        items: [
          "TREASURY",
          "capital allocation",
          "custody awareness",
          "runway protection",
        ],
      },
      {
        label: "Execution lane",
        items: [
          "ARKON",
          "mirror_wallet",
          "dry-run",
          "execution bornee",
        ],
      },
    ],
  };
}

function tradingLaneMetricsSection(pathname, snapshot) {
  if (!["/trade", "/omega"].includes(pathname)) {
    return null;
  }
  const roster = snapshot.mesh?.mesh?.agents || {};
  const activeMissions = Array.isArray(snapshot.missions?.active) ? snapshot.missions.active : [];
  const status = snapshot.status || {};
  const columns = [
    {
      label: "Signal lane",
      members: ["TRINITY", "KIMI", "ORACLE"],
      headline: status.arkon5_action || "READY",
    },
    {
      label: "Risk lane",
      members: ["MERLIN", "ONCHAIN_GUARDIAN", "GOUV4"],
      headline: status.pipeline_status || "MESH_READY",
    },
    {
      label: "Treasury lane",
      members: ["TREASURY"],
      headline: status.wallet_creator_akt_balance != null ? `${status.wallet_creator_akt_balance} AKT` : "treasury online",
    },
    {
      label: "Execution lane",
      members: ["ARKON"],
      headline: "mirror wallet armed",
    },
  ].map((lane) => {
    const onlineCount = lane.members.filter((agentId) => !["offline", "unknown"].includes(roster[agentId]?.status || "offline")).length;
    const missionCount = activeMissions.filter((mission) => lane.members.includes(mission.target)).length;
    return {
      label: lane.label,
      items: [
        `headline=${lane.headline}`,
        `online=${onlineCount}/${lane.members.length}`,
        `missions=${missionCount}`,
        `members=${lane.members.join(", ")}`,
      ],
    };
  });
  return {
    title: "Trading lane metrics",
    intro: "Metrices live des lanes trader. Le front montre la pression lane par lane sans exposer les secrets ni les cles.",
    columns,
  };
}

function adminConsoleSection(pathname, snapshot) {
  if (pathname !== "/admin") {
    return null;
  }
  const business = snapshot.admin?.liveRegistries || {};
  const wallets = snapshot.admin?.walletsCustody?.records || [];
  const treasury = snapshot.admin?.vaultsTreasury?.treasury || {};
  const operatorCount = snapshot.admin?.operatorRoster?.total_operator_identities || 0;
  return {
    title: "Admin operator console",
    intro: "Console d'action live pour injecter des clients, jobs, identites et factures directement dans le runtime business S25.",
    metrics: [
      { label: "Clients live", value: String((business.clients || []).length) },
      { label: "Jobs live", value: String((business.jobs || []).length) },
      { label: "Finance live", value: String((business.quotes_invoices || []).length) },
      { label: "Operators", value: String(operatorCount) },
      { label: "Wallets", value: String(wallets.length) },
      { label: "Treasury AKT", value: treasury.akt_balance != null ? String(treasury.akt_balance) : "--" },
    ],
    endpoints: [
      "/admin/api/create-client-job-billing",
      "/admin/api/create-client-pipeline",
      "/admin/api/create-client",
      "/admin/api/create-job",
      "/admin/api/issue-invoice",
      "/admin/api/create-identity",
      "/admin/api/issue-client-access",
      "/admin/api/issue-staff-access",
      "/admin/api/issue-vendor-access",
      "/admin/api/business-timeline",
      "/admin/api/wallets-custody",
      "/admin/api/vaults-treasury",
    ],
    flow: [
      "Ouvrir une session operateur signee avec le secret bootstrap.",
      "Utiliser le pipeline complet quand il faut onboarder un client avec premier job et premiere facture.",
      "Creer un compte client complet ou une identite seule.",
      "Lier ensuite le job au client actif.",
      "Sortir la quote ou la facture sans quitter le hub.",
      "Lire la posture wallet/custody avant toute route treasury ou trading.",
      "Recharger le runtime pour verifier la persistence live.",
    ],
    forms: [
      {
        label: "Full onboarding",
        title: "Create client + job + billing",
        text: "Onboarde un nouveau compte avec contact, client, premier job et premier flux commercial en une seule commande.",
        endpoint: "/admin/api/create-client-job-billing",
        actionLabel: "Create full operational account",
        fields: [
          { name: "organization_name", label: "Organization name", placeholder: "Gamma Excavation", required: true },
          { name: "display_name", label: "Primary contact", placeholder: "Alex Gamma", required: true },
          { name: "service_type", label: "Service type", placeholder: "excavation" },
          { name: "assigned_team", label: "Assigned team", placeholder: "crew-north-01" },
          { name: "scheduled_window", label: "Scheduled window", placeholder: "2026-03-13 PM" },
          { name: "amount", label: "Amount", placeholder: "6500", type: "number" },
          { name: "billing_stage", label: "Billing stage", placeholder: "quote_prepared", value: "quote_prepared" },
        ],
      },
      {
        label: "Client pipeline",
        title: "Create full client account",
        text: "Cree en une seule action l'identite client et le compte business lies a la meme organisation.",
        endpoint: "/admin/api/create-client-pipeline",
        actionLabel: "Create full client account",
        fields: [
          { name: "organization_name", label: "Organization name", placeholder: "Nouveau client multiservice", required: true },
          { name: "display_name", label: "Primary contact", placeholder: "Contact principal client", required: true },
          { name: "scope_id", label: "Scope id", placeholder: "client_scope_north" },
          { name: "service_type", label: "Service type", placeholder: "excavation" },
          { name: "billing_state", label: "Billing state", placeholder: "quote_pending", value: "quote_pending" },
        ],
      },
      {
        label: "Identity",
        title: "Create operator or staff identity",
        text: "Injecte une identite vivante dans la matrice RBAC avec role, badge, scope et services actives.",
        endpoint: "/admin/api/create-identity",
        actionLabel: "Create identity",
        fields: [
          { name: "display_name", label: "Display name", placeholder: "Nouvel operateur Smajor", required: true },
          { name: "organization_id", label: "Organization id", placeholder: "org-smajor-core" },
          { name: "role_id", label: "Role id", placeholder: "dispatcher" },
          { name: "badge_id", label: "Badge id", placeholder: "employee_badge" },
          { name: "scope_id", label: "Scope id", placeholder: "field_scope_dispatch" },
        ],
      },
      {
        label: "Client access",
        title: "Issue client portal access",
        text: "Genere un bearer token client limite a un seul compte pour ouvrir le portail sans exposer le secret operateur.",
        endpoint: "/admin/api/issue-client-access",
        actionLabel: "Issue client access",
        fields: [
          { name: "client_id", label: "Client id", placeholder: "client-alpha-001", required: true },
        ],
      },
      {
        label: "Staff access",
        title: "Issue staff dashboard access",
        text: "Genere un bearer token staff borne a une identite terrain, a une equipe et a un scope d'action.",
        endpoint: "/admin/api/issue-staff-access",
        actionLabel: "Issue staff access",
        fields: [
          { name: "identity_id", label: "Identity id", placeholder: "ident-5a53ddda", required: true },
          { name: "assigned_team", label: "Assigned team", placeholder: "crew-north-01" },
          { name: "scope_id", label: "Scope id", placeholder: "field_scope_dispatch" },
        ],
      },
      {
        label: "Vendor access",
        title: "Issue vendor portal access",
        text: "Genere un bearer token vendor borne a une identite fournisseur et a un scope supply/billing.",
        endpoint: "/admin/api/issue-vendor-access",
        actionLabel: "Issue vendor access",
        fields: [
          { name: "identity_id", label: "Identity id", placeholder: "ident-vendor-001", required: true },
          { name: "scope_id", label: "Scope id", placeholder: "vendor_scope_default" },
          { name: "vendor_class", label: "Vendor class", placeholder: "supplier", value: "supplier" },
        ],
      },
      {
        label: "Client",
        title: "Create live client",
        text: "Ouvre un vrai compte client sur la chaine identity -> role -> badge -> scope -> portal.",
        endpoint: "/admin/api/create-client",
        actionLabel: "Create client",
        fields: [
          { name: "organization_name", label: "Organization name", placeholder: "Nouveau client chantier", required: true },
          { name: "role_id", label: "Role id", placeholder: "client_contact", value: "client_contact" },
          { name: "badge_id", label: "Badge id", placeholder: "client_badge", value: "client_badge" },
          { name: "scope_id", label: "Scope id", placeholder: "client_scope_new" },
          { name: "service_type", label: "Service type", placeholder: "excavation" },
        ],
      },
      {
        label: "Job",
        title: "Create live job",
        text: "Injecte un job reel lie a un client, a une equipe et a une fenetre de travail.",
        endpoint: "/admin/api/create-job",
        actionLabel: "Create job",
        fields: [
          { name: "client_id", label: "Client id", placeholder: "client-alpha-001", required: true },
          { name: "service_type", label: "Service type", placeholder: "deneigement" },
          { name: "assigned_team", label: "Assigned team", placeholder: "crew-east-02" },
          { name: "scheduled_window", label: "Scheduled window", placeholder: "2026-03-12 AM" },
          { name: "dispatch_scope", label: "Dispatch scope", placeholder: "field_scope_east" },
        ],
      },
      {
        label: "Billing",
        title: "Issue quote or invoice",
        text: "Pousse un flux commercial reel avec client, job, montant et etape de facturation.",
        endpoint: "/admin/api/issue-invoice",
        actionLabel: "Issue billing record",
        fields: [
          { name: "client_id", label: "Client id", placeholder: "client-alpha-001", required: true },
          { name: "job_id", label: "Job id", placeholder: "job-alpha-yard-001", required: true },
          { name: "amount", label: "Amount", placeholder: "4800", type: "number" },
          { name: "currency", label: "Currency", placeholder: "CAD", value: "CAD" },
          { name: "billing_stage", label: "Billing stage", placeholder: "invoice_issued", value: "invoice_issued" },
        ],
      },
    ],
    initialLog: JSON.stringify(
      {
        mode: "operator_console_ready",
        note: "Ouvrir une session operateur puis lancer une ecriture live.",
        last_write_at: business.last_write_at || null,
      },
      null,
      2,
    ),
  };
}

function clientConsoleSection(pathname, snapshot) {
  if (pathname !== "/clients") {
    return null;
  }
  const business = snapshot.business || {};
  const clients = business.clients?.records || [];
  const jobs = business.jobs?.records || [];
  const billing = business.quotes_invoices?.records || [];
  return {
    title: "Client portal console",
    intro: "Console legere pour charger un vrai compte client via un token signe et verifier les jobs et la facturation visibles par le client.",
    metrics: [
      { label: "Clients visibles", value: String(clients.length) },
      { label: "Jobs visibles", value: String(jobs.length) },
      { label: "Finance visible", value: String(billing.length) },
      { label: "Mode", value: "Signed client access" },
    ],
    endpoints: [
      "/clients/api/account",
      "bearer token client requis",
      "lecture limitee a un seul client",
    ],
    flow: [
      "Recevoir un token client emis par l'admin.",
      "Coller le token dans la session client.",
      "Charger le compte live, les jobs et la facturation.",
      "Garder l'acces borne a un seul client et a son scope.",
    ],
    initialLog: JSON.stringify(
      {
        mode: "client_portal_ready",
        note: "Coller un token client signe puis charger le compte live.",
        sample_client: clients[0]?.client_id || null,
      },
      null,
      2,
    ),
  };
}

function vendorConsoleSection(pathname, snapshot) {
  if (pathname !== "/vendors") {
    return null;
  }
  const business = snapshot.business || {};
  const identities = business.identities?.records || [];
  const jobs = business.jobs?.records || [];
  const billing = business.quotes_invoices?.records || [];
  const events = business.events?.records || [];
  return {
    title: "Vendor portal console",
    intro: "Console legere pour charger un acces fournisseur signe, borne a l'identite vendor, a son scope et aux surfaces supply/billing visibles.",
    metrics: [
      { label: "Identites visibles", value: String(identities.length) },
      { label: "Jobs supply", value: String(jobs.length) },
      { label: "Billing supply", value: String(billing.length) },
      { label: "Events", value: String(events.length) },
      { label: "Mode", value: "Signed vendor access" },
    ],
    endpoints: [
      "/vendors/api/dashboard",
      "bearer token vendor requis",
      "lecture limitee au scope supply",
    ],
    flow: [
      "Recevoir un token vendor emis par l'admin.",
      "Coller le token dans la session vendor.",
      "Charger le dashboard supply, les jobs visibles et les flux billing rattaches.",
      "Garder l'acces borne a l'identite fournisseur et a son scope.",
    ],
    initialLog: JSON.stringify(
      {
        mode: "vendor_portal_ready",
        note: "Coller un token vendor signe puis charger le dashboard supply.",
        sample_identity: identities.find((item) => String(item.role_id || "").includes("vendor"))?.identity_id || null,
      },
      null,
      2,
    ),
  };
}

function businessTimelineSection(pathname, snapshot) {
  if (pathname !== "/admin") {
    return null;
  }
  const events = snapshot.admin?.businessTimeline?.records || snapshot.business?.events?.records || [];
  return {
    title: "Business timeline",
    intro: "Audit trail vivant des creations, acces et ecritures. L'admin voit la chaine complete sans fouiller la memoire brute.",
    rows: events.slice(0, 12).map((event) => ({
      title: event.summary,
      detail: `${event.event_type} | ${event.lane} | ${event.subject_type} | ${event.subject_id || "--"}`,
      timestamp: event.created_at || "--",
    })),
  };
}

function operationalChainSection(pathname, snapshot) {
  if (pathname !== "/admin") {
    return null;
  }
  const business = snapshot.admin?.liveRegistries || snapshot.business || {};
  const clients = business.clients || business.clients?.records || [];
  const jobs = business.jobs || business.jobs?.records || [];
  const billing = business.quotes_invoices || business.quotes_invoices?.records || [];
  const identities = business.identities || business.identities?.records || [];
  const events = snapshot.admin?.businessTimeline?.records || business.events || [];

  const rows = clients.slice(0, 8).map((client) => {
    const identity = identities.find((item) => item.identity_id === client.identity_id) || null;
    const clientJobs = jobs.filter((item) => item.client_id === client.client_id);
    const clientBilling = billing.filter((item) => item.client_id === client.client_id);
    const clientEvents = events.filter((item) => {
      const metadata = item.metadata || {};
      return item.subject_id === client.client_id || metadata.client_id === client.client_id || metadata.identity_id === client.identity_id;
    });
    return {
      title: client.organization_name || client.client_id,
      items: [
        `client=${client.client_id}`,
        `identity=${identity?.identity_id || client.identity_id || "--"}`,
        `role=${identity?.role_id || client.role_id || "--"}`,
        `jobs=${clientJobs.length}`,
        `billing=${clientBilling.length}`,
        `portal=${client.portal_state || identity?.portal_state || "--"}`,
        `access_events=${clientEvents.length}`,
      ],
    };
  });

  return {
    title: "Operational chain",
    intro: "Vue chaine complete: identite, client, job, billing et acces sur une seule surface admin.",
    rows,
  };
}

function adminCommandKitSection(pathname) {
  if (!["/admin", "/ai"].includes(pathname)) {
    return null;
  }
  return {
    title: ADMIN_COMMAND_KIT_MODEL.title,
    intro: ADMIN_COMMAND_KIT_MODEL.summary,
    columns: ADMIN_COMMAND_KIT_MODEL.columns,
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
    executiveReport: executiveReportSection(pathname, snapshot),
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
    operatorAccount: operatorAccountSection(pathname),
    operatorRoster: operatorRosterSection(pathname, snapshot),
    adminConsole: adminConsoleSection(pathname, snapshot),
    adminArchitecture: adminArchitectureSection(pathname),
    clientConsole: clientConsoleSection(pathname, snapshot),
    staffConsole: staffConsoleSection(pathname, snapshot),
    vendorConsole: vendorConsoleSection(pathname, snapshot),
    portalSeparation: portalSeparationSection(pathname),
    geminiLayer: geminiLayerSection(pathname, snapshot),
    adminCommandKit: adminCommandKitSection(pathname),
    agentActivation: agentActivationSection(pathname),
    agentServiceBindings: agentServiceBindingsSection(pathname),
    tradingShowroom: tradingShowroomSection(pathname),
    tradingLaneMetrics: tradingLaneMetricsSection(pathname, snapshot),
    foundationStack: foundationStackSection(pathname),
    masterWallet: masterWalletSection(pathname, env, snapshot),
    registryWriteContract: registryWriteContractSection(pathname),
    businessTimeline: businessTimelineSection(pathname, snapshot),
    operationalChain: operationalChainSection(pathname, snapshot),
    adminActions: adminActionSection(pathname),
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

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/live-registries") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const snapshot = await fetchAdminSnapshot(env);
        return jsonResponse(snapshot.liveRegistries);
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_live_registries_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/operator-roster") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const snapshot = await fetchAdminSnapshot(env);
        return jsonResponse(snapshot.operatorRoster);
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_operator_roster_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/runtime-business") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const runtimeBase = env.DIRECT_RUNTIME_URL || env.PUBLIC_S25_URL;
        const memory = await fetchSecureJson(`${runtimeBase}/api/memory/state`, env);
        return jsonResponse({
          ok: true,
          source: "s25_runtime_memory",
          business_registry: memory?.state?.intel?.business_registry || memory?.state?.business || {},
        });
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_runtime_business_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/wallets-custody") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const snapshot = await fetchAdminSnapshot(env);
        return jsonResponse(snapshot.walletsCustody || { ok: false, error: "wallets_custody_unavailable" });
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_wallets_custody_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/vaults-treasury") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const snapshot = await fetchAdminSnapshot(env);
        return jsonResponse(snapshot.vaultsTreasury || { ok: false, error: "vaults_treasury_unavailable" });
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_vaults_treasury_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/secret-custody") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const snapshot = await fetchAdminSnapshot(env);
        return jsonResponse(snapshot.secretCustody || { ok: false, error: "secret_custody_unavailable" });
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_secret_custody_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/secret-fallback-policy") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const snapshot = await fetchAdminSnapshot(env);
        return jsonResponse(snapshot.secretFallbackPolicy || { ok: false, error: "secret_fallback_policy_unavailable" });
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_secret_fallback_policy_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/gemini-layer") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const snapshot = await fetchAdminSnapshot(env);
        return jsonResponse(snapshot.geminiLayer || { ok: false, error: "gemini_layer_unavailable" });
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_gemini_layer_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/wallet-classes") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        return await fetchJson(`${env.PUBLIC_API_URL}/api/business/wallet-classes`).then((payload) => jsonResponse(payload));
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_wallet_classes_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/wallet-scopes") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        return await fetchJson(`${env.PUBLIC_API_URL}/api/business/wallet-scopes`).then((payload) => jsonResponse(payload));
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_wallet_scopes_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/wallet-policy-matrix") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        return await fetchJson(`${env.PUBLIC_API_URL}/api/business/wallet-policy-matrix`).then((payload) => jsonResponse(payload));
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_wallet_policy_matrix_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/business-timeline") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const snapshot = await fetchAdminSnapshot(env);
        return jsonResponse(snapshot.businessTimeline);
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_business_timeline_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/operational-chain") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      try {
        const snapshot = await fetchAdminSnapshot(env);
        return jsonResponse({
          ok: true,
          secure: true,
          ...(operationalChainSection("/admin", snapshot) || { title: "Operational chain", rows: [] }),
        });
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_operational_chain_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/session") {
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      return createOperatorSession(request, env);
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/create-client") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      try {
        return jsonResponse(await handleHubBusinessCreate(request, env, "client"));
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_create_client_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/create-client-pipeline") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      try {
        return jsonResponse(await handleHubClientPipelineCreate(request, env));
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_create_client_pipeline_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/create-client-job-billing") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      try {
        return jsonResponse(await handleHubClientJobBillingCreate(request, env));
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_create_client_job_billing_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/create-job") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      try {
        return jsonResponse(await handleHubBusinessCreate(request, env, "job"));
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_create_job_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/issue-client-access") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      try {
        return await issueClientAccess(request, env);
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_issue_client_access_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/issue-staff-access") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      try {
        return await issueStaffAccess(request, env);
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_issue_staff_access_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/issue-vendor-access") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      try {
        return await issueVendorAccess(request, env);
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_issue_vendor_access_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/issue-invoice") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      try {
        return jsonResponse(await handleHubBusinessCreate(request, env, "quote"));
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_issue_invoice_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/admin/api/create-identity") {
      const denied = await requireOperatorAccess(request, env);
      if (denied) return denied;
      if (request.method !== "POST") {
        return jsonResponse({ ok: false, error: "method_not_allowed" }, 405);
      }
      try {
        return jsonResponse(await handleHubBusinessCreate(request, env, "identity"));
      } catch (error) {
        return jsonResponse({ ok: false, error: "admin_create_identity_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/clients/api/account") {
      const access = await requireClientAccess(request, env);
      if (access.denied) return access.denied;
      try {
        const business = await readRuntimeBusinessState(env);
        const snapshot = buildClientPortalSnapshot(business, access.payload.client_id);
        if (!snapshot) {
          return jsonResponse({ ok: false, error: "client_snapshot_not_found", client_id: access.payload.client_id }, 404);
        }
        return jsonResponse({
          ok: true,
          session: {
            client_id: access.payload.client_id,
            organization_id: access.payload.organization_id,
            role_id: access.payload.role_id,
            badge_id: access.payload.badge_id,
            scope_id: access.payload.scope_id,
            expires_at: new Date(access.payload.exp).toISOString(),
          },
          account: snapshot,
        });
      } catch (error) {
        return jsonResponse({ ok: false, error: "client_account_read_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/staff/api/dashboard") {
      const access = await requireStaffAccess(request, env);
      if (access.denied) return access.denied;
      try {
        const business = await readRuntimeBusinessState(env);
        const snapshot = buildStaffPortalSnapshot(business, access.payload);
        if (!snapshot) {
          return jsonResponse({ ok: false, error: "staff_snapshot_not_found", identity_id: access.payload.identity_id }, 404);
        }
        return jsonResponse({
          ok: true,
          session: {
            identity_id: access.payload.identity_id,
            organization_id: access.payload.organization_id,
            role_id: access.payload.role_id,
            badge_id: access.payload.badge_id,
            scope_id: access.payload.scope_id,
            assigned_team: access.payload.assigned_team,
            expires_at: new Date(access.payload.exp).toISOString(),
          },
          dashboard: snapshot,
        });
      } catch (error) {
        return jsonResponse({ ok: false, error: "staff_dashboard_read_failed", detail: String(error?.message || error) }, 500);
      }
    }

    if (hostname === "app.smajor.org" && url.pathname === "/vendors/api/dashboard") {
      const access = await requireVendorAccess(request, env);
      if (access.denied) return access.denied;
      try {
        const business = await readRuntimeBusinessState(env);
        const snapshot = buildVendorPortalSnapshot(business, access.payload);
        if (!snapshot) {
          return jsonResponse({ ok: false, error: "vendor_snapshot_not_found", identity_id: access.payload.identity_id }, 404);
        }
        return jsonResponse({
          ok: true,
          session: {
            identity_id: access.payload.identity_id,
            organization_id: access.payload.organization_id,
            role_id: access.payload.role_id,
            badge_id: access.payload.badge_id,
            scope_id: access.payload.scope_id,
            vendor_class: access.payload.vendor_class,
            expires_at: new Date(access.payload.exp).toISOString(),
          },
          dashboard: snapshot,
        });
      } catch (error) {
        return jsonResponse({ ok: false, error: "vendor_dashboard_read_failed", detail: String(error?.message || error) }, 500);
      }
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

    if (url.pathname === "/models/executive-report.json") {
      const snapshot = await fetchOpsSnapshot(env).catch(() => ({}));
      const report = executiveReportSection("/", snapshot || {}) || {
        title: "Rapport executif Smajor",
        intro: "Fallback executive report while the live snapshot recovers.",
        columns: [],
      };
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "app.smajor.org + live runtime snapshot",
        ...report,
      });
    }

    if (url.pathname === "/models/master-wallet-status.json") {
      const snapshot = await fetchOpsSnapshot(env).catch(() => ({}));
      const walletModel = masterWalletSection("/wallet", env, snapshot || {})?.model || {
        title: "Master wallet status",
        label: env.MASTER_WALLET_LABEL || "Wallet creator",
        wallet_address: env.MASTER_WALLET_ADDRESS || "unconfigured",
        wallet_prefix: "akash",
        source_of_truth: "Google Secret Manager -> derived public address",
        s25_connection: {
          pipeline_status: "unknown",
          mesh_agents_online: null,
          missions_active: null,
          arkon5_action: null,
          tunnel: "unknown",
          ha_connected: false,
        },
      };
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "Google Secret Manager derived public address + S25 live status",
        ...walletModel,
      });
    }

    if (url.pathname === "/models/wallets-custody.json") {
      const snapshot = await fetchOpsSnapshot(env).catch(() => ({}));
      const walletModel = masterWalletSection("/wallet", env, snapshot || {})?.model || {};
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "S25 Lumiere runtime + Google Secret Manager",
        title: "Wallets and custody registry",
        summary: "Registre public du wallet creator, de sa custody et de son etat live.",
        records: [
          {
            wallet_id: "wallet-creator-001",
            label: walletModel.label || env.MASTER_WALLET_LABEL || "Wallet creator",
            network: "akash",
            address: walletModel.wallet_address || env.MASTER_WALLET_ADDRESS || "unconfigured",
            connected: walletModel.creator_connected ?? false,
            custody: walletModel.custody || "google_secret_manager",
            akt_balance: walletModel.akt_balance ?? null,
            akt_value_usd: walletModel.akt_value_usd ?? null,
            source_of_truth: "S25 Lumiere runtime + Google Secret Manager",
          },
        ],
      });
    }

    if (url.pathname === "/models/vaults-treasury.json") {
      const snapshot = await fetchOpsSnapshot(env).catch(() => ({}));
      const treasury = snapshot.business?.vaults_treasury || {};
      const walletModel = masterWalletSection("/wallet", env, snapshot || {})?.model || {};
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org + S25 Lumiere runtime",
        title: "Vaults and treasury command",
        summary: "Posture treasury, custody et readiness avant le trading live.",
        treasury: {
          wallet_id: treasury.treasury?.wallet_id || "wallet-creator-001",
          address: treasury.treasury?.address || walletModel.wallet_address || env.MASTER_WALLET_ADDRESS || "unconfigured",
          connected: treasury.treasury?.connected ?? walletModel.creator_connected ?? false,
          custody: treasury.treasury?.custody || walletModel.custody || "google_secret_manager",
          akt_balance: treasury.treasury?.akt_balance ?? walletModel.akt_balance ?? null,
          akt_value_usd: treasury.treasury?.akt_value_usd ?? walletModel.akt_value_usd ?? null,
        },
        policies: treasury.policies || [
          "policy_seed_gsm_only",
          "policy_public_address_only",
          "policy_operator_session_required",
          "policy_full_audit_before_trading",
        ],
        next_steps: treasury.next_steps || [
          "brancher vault registry dans admin",
          "lier treasury a omega",
          "ajouter wallets secondaires et politiques par scope",
        ],
      });
    }

    if (url.pathname === "/models/wallet-classes.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/wallet-classes`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org wallet classes",
          title: "Wallet classes",
          summary: "Classes de wallets pour creator, treasury, trading, ops et mirror.",
          classes: [],
        },
      );
    }

    if (url.pathname === "/models/wallet-scopes.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/wallet-scopes`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org wallet scopes",
          title: "Wallet scopes",
          summary: "Scopes des wallets et territoires d'action.",
          scopes: [],
        },
      );
    }

    if (url.pathname === "/models/wallet-policy-matrix.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/wallet-policy-matrix`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org wallet policy matrix",
          title: "Wallet policy matrix",
          summary: "Policies custody, execution et audit.",
          policies: [],
        },
      );
    }

    if (url.pathname === "/models/secret-custody.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/secret-custody`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org secret custody",
          title: "Secret custody registry",
          summary: "Primary and fallback custody for critical secrets.",
          records: [],
        },
      );
    }

    if (url.pathname === "/models/secret-fallback-policy.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/secret-fallback-policy`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org secret fallback policy",
          title: "Secret fallback policy",
          summary: "Fallback order if Google Secret Manager is unavailable.",
          fallback_order: [],
        },
      );
    }

    if (url.pathname === "/models/frontend-surfaces.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/frontend-surfaces`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org frontend surfaces",
          title: "Frontend surfaces",
          summary: "Public and operator-facing surfaces.",
          surfaces: [],
        },
      );
    }

    if (url.pathname === "/models/backend-surfaces.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/backend-surfaces`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org backend surfaces",
          title: "Backend surfaces",
          summary: "Runtime and sovereign service surfaces.",
          surfaces: [],
        },
      );
    }

    if (url.pathname === "/models/separation-architecture.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/separation-architecture`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org separation architecture",
          title: "Frontend backend separation",
          summary: "Official map for front-end versus back-end separation.",
          frontend: [],
          backend: [],
        },
      );
    }

    if (url.pathname === "/models/gemini-layer.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/gemini-layer`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org gemini layer",
          title: "Gemini unified layer",
          summary: "Gemini as intelligence plane, distinct from Google Cloud infrastructure.",
          doctrine: [],
        },
      );
    }

    if (url.pathname === "/models/trading-lane-metrics.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/trading-lane-metrics`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org trading lane metrics",
          title: "Trading lane metrics",
          summary: "Live lane metrics unavailable",
          lanes: [],
        },
      );
    }

    if (url.pathname === "/models/trading-showroom.json") {
      const payload = await fetchJson(`${env.PUBLIC_API_URL}/api/business/trading-showroom`).catch(() => null);
      return jsonResponse(
        payload || {
          ok: true,
          domain: "smajor.org",
          source_of_truth: "api.smajor.org trading showroom",
          title: "Trading showroom",
          summary: "Signal, risk, treasury and execution lanes.",
          lanes: [],
        },
      );
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

    if (url.pathname === "/models/business-timeline.json") {
      const snapshot = {
        admin: await fetchAdminSnapshot(env).catch((error) => ({
          businessTimeline: { records: [] },
          errors: [error?.message || "admin_snapshot_failed"],
        })),
      };
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "s25 runtime business registry + signed admin writes",
        ...(businessTimelineSection("/admin", snapshot) || { title: "Business timeline", rows: [] }),
      });
    }

    if (url.pathname === "/models/operational-chain.json") {
      const snapshot = {
        admin: await fetchAdminSnapshot(env).catch((error) => ({
          liveRegistries: {},
          businessTimeline: { records: [] },
          errors: [error?.message || "admin_snapshot_failed"],
        })),
      };
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "s25 runtime business registry + signed admin writes",
        ...(operationalChainSection("/admin", snapshot) || { title: "Operational chain", rows: [] }),
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

    if (url.pathname === "/models/operator-account.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "api.smajor.org identity-registry-live + secure operator roster",
        ...OPERATOR_ACCOUNT_MODEL,
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

    if (url.pathname === "/models/admin-command-kit.json") {
      return jsonResponse({
        ok: true,
        domain: "smajor.org",
        source_of_truth: "app.smajor.org secure admin routes + S25 runtime memory",
        ...ADMIN_COMMAND_KIT_MODEL,
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
      const [ops, admin] = await Promise.all([
        fetchOpsSnapshot(env),
        fetchAdminSnapshot(env).catch((error) => ({
          liveRegistries: null,
          operatorRoster: null,
          errors: [error?.message || "admin_snapshot_failed"],
        })),
      ]);
      const snapshot = {
        ...ops,
        admin,
      };
      return responseHtml(renderApp(env, url.pathname, hostname, snapshot));
    }

    return responseHtml(renderPublic(env));
  },
};
