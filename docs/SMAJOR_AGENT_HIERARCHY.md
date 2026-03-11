# Smajor Agent Hierarchy

## But

Donner une lecture unique de l'armee derriere `smajor.org`:
- quel agent existe deja dans le backend
- quel role RBAC il porte
- quel scope d'action il a exactement
- ce qu'il ne doit pas faire

## Regle mere

Le systeme opere par:

`identity_id -> role_id -> badge_id -> scope_id -> service_entitlements`

Donc:
- un agent n'est jamais une "personne magique"
- un agent porte un `role_id`
- son pouvoir vient de son scope
- ses limites doivent survivre a un remplacement de modele, de machine ou d'operateur

## Hierarchie officielle

### Niveau 0 — Autorite systeme

| Agent | role_id | badge_id | Scope exact | Hors scope |
|---|---|---|---|---|
| Major / Founder surface | `founder` | `major_badge` | vision, priorites, arbitrage final, activation budget, validation des pouvoirs critiques | execution terrain detaillee, operations mecaniques de routine |
| Admin operators | `operator_admin` | `major_badge` | identites, roles, scopes, secrets, services actives, politiques agents, finance approval | prendre des decisions business sans trace, contourner l'audit |

### Niveau 1 — Commandement IA coeur

| Agent | role_id | badge_id | Scope exact | Hors scope |
|---|---|---|---|---|
| TRINITY | `trinity_orchestrator` | `ai_badge` | orchestration vocale/texte, boot du mesh, creation de missions, lecture status/memory/missions, delegation vers MERLIN/COMET/KIMI | devenir source unique de verite finance/client, bypass des garde-fous RBAC |
| MERLIN | `merlin_validator` | `ai_badge` | validation, synthese, feedback structure, lecture MCP, memoire Gemini, confirmation de decisions et d'architecture | execution autonome d'actions critiques sans mission ni cadre |
| COMET | `comet_watch` | `ai_badge` | veille provider, surveillance web, handoff operatoire, remontée intel, suivi de missions navigateur/web | gouvernance systeme, ecriture de politique d'acces finale |
| GOUV4 | `policy_admin` | `major_badge` | routage de taches, arbitrage cout/quota/modele, mapping task_type -> agent | operations terrain, relation client directe |

### Niveau 2 — Capteurs et defense backend

| Agent | role_id | badge_id | Scope exact | Hors scope |
|---|---|---|---|---|
| KIMI | `kimi_sensor` | `ai_badge` | pompage data Web3, scans memecoins, signaux externes, alimentation intel | arbitrage final, gouvernance, execution de trade sans validation |
| ORACLE | `oracle_sensor` | `ai_badge` | verification prix multi-source, mediane, snapshots market/intel, heartbeat ORACLE | prise de position seule, narration produit |
| ONCHAIN_GUARDIAN | `guardian_watch` | `ai_badge` | surveillance whales, rugs, LP risk, anomalies on-chain, snapshots risque | execution commerciale, permissions admin |

### Niveau 3 — Builder / maintenance

| Agent | role_id | badge_id | Scope exact | Hors scope |
|---|---|---|---|---|
| ARKON | `builder_operator` | `employee_badge` | build backend, refactor, migration runtime, wiring infra, outillage, patchs repo | redefinir seul la politique business, prendre un role de source de verite client |
| code-validator | `validator_worker` | `ai_badge` | validation de code, verification avant deploy, garde-fou de qualite | deploy prod autonome sans politique admin |
| smart-refactor | `builder_worker` | `employee_badge` | refactor ciblé async/Flask/runtime | gouvernance, secrets, finance |
| auto-documenter | `documentation_worker` | `employee_badge` | mise a jour docs, handoff, snapshot runtime, journaux de progression | changer les permissions, changer la verite business |

### Niveau 4 — Agents backlog specialises

| Agent | role_id | badge_id | Scope exact | Hors scope |
|---|---|---|---|---|
| defi-liquidity-manager | `defi_operator` | `ai_badge` | APY, IL, positions DeFi, opportunites/risques DeFi | depenser ou engager des fonds sans couche de validation |

## Mapping par grande fonction

### Business / entreprise reelle

- portail client:
  - humains: `client_owner`, `client_contact`
  - IA support: `trinity_orchestrator`, `comet_watch`
- portail staff:
  - humains: `dispatcher`, `field_manager`, `staff_member`, `contractor`
  - IA support: `trinity_orchestrator`
- portail vendors:
  - humains: `vendor_manager`, `vendor_contact`
  - IA support: `operator_admin`, `comet_watch`
- admin console:
  - humains: `founder`, `operator_admin`
  - IA support: `trinity_orchestrator`, `merlin_validator`, `policy_admin`

### Infra / S25

- cockpit public:
  - commandement: `trinity_orchestrator`
  - validation: `merlin_validator`
  - routage/policy: `policy_admin`
- feed intel:
  - `comet_watch`
  - `kimi_sensor`
  - `oracle_sensor`
  - `guardian_watch`
- backend code/runtime:
  - `builder_operator`
  - `validator_worker`
  - `documentation_worker`

## Agents presents aujourd'hui dans le backend

### Presents dans le runtime cockpit / memory

- `TRINITY`
- `ARKON`
- `MERLIN`
- `COMET`
- `KIMI`
- `ORACLE`
- `ONCHAIN_GUARDIAN`

### Presents dans l'architecture et la gouvernance

- `GOUV4`

### Presents comme sous-agents documentes

- `defi-liquidity-manager`
- `code-validator`
- `smart-refactor`
- `auto-documenter`

## Doctrine d'immortalite

1. Aucune fonction critique ne doit etre attachee a un nom fixe.
2. On remplace une cle, une credential ou une identity, pas la structure.
3. Le badge et le role sont les moules durables.
4. Les agents IA servent la chaine de pouvoir; ils ne sont pas la loi.
5. `smajor.org` montre la structure. `S25` l'applique.
