# Smajor Operating Model

## But

Faire de `smajor.org` la couche visible et industrielle du systeme:
- entreprise reelle
- portail clients
- operations internes
- IA / agents
- backend S25

Le domaine devient la facade.
Le mesh S25 sur Akash reste le coeur operationnel.

Reference de construction business:
- voir `docs/SMAJOR_INDUSTRIAL_STACK.md`

## Principe directeur

- `smajor.org` = presentation, acces, marque, portail
- `S25 Lumiere` = backend central, orchestration, missions, etat runtime
- `MERLIN MCP` = couche tools/validation multi-agent
- `HA` = chaine laterale d'execution terrain, pas point de verite principal

## Architecture officielle

### 1. Public

- `www.smajor.org`
  - site vitrine principal
  - presentation entreprise
  - prise de contact
  - services
- `excavation.smajor.org`
  - branche excavation
- `deneigement.smajor.org`
  - branche deneigement
- `majorai.smajor.org`
  - branche IA / automations / products

### 2. Operations

- `app.smajor.org`
  - interface centrale
  - point d'entree unique pour operator / equipe
  - shell vivant avec panneaux `status / missions / mesh`
  - workbench par route: `clients`, `admin`, `staff`, `vendors`, `ai`
- `admin.smajor.org`
  - backoffice
  - gestion utilisateurs
  - regles agents
  - supervision
- `clients.smajor.org`
  - portail clients
  - demandes de service
  - facturation
  - suivi des contrats
- `staff.smajor.org`
  - portail employes / sous-traitants
  - horaires
  - taches
  - rapports terrain
- `vendors.smajor.org`
  - fournisseurs
  - bons de commande
  - documents

### 3. Backend / Agents

- `api.smajor.org`
  - API centrale business
  - entree app / clients / automation
- `s25.smajor.org`
  - cockpit public S25
  - etat mesh
  - status
  - missions
- `merlin.smajor.org`
  - point d'entree MCP MERLIN
- `ai.smajor.org`
  - surface future pour outils IA exposes a l'entreprise

## Repartition fonctionnelle

### S25

S25 doit tenir:
- etat du systeme
- mission queue
- feed intel
- orchestration inter-agents
- logique de gouvernance
- coeur des automatisations business

### Site public

Le site public ne doit pas porter la logique metier critique.
Il doit appeler `api.smajor.org` et `s25.smajor.org`, jamais dupliquer la logique.

### Portails

Les portails doivent devenir des facades specialisees:
- `clients` = relation client
- `staff` = execution terrain
- `vendors` = chaine d'approvisionnement
- `admin` = pilotage

## MVP reel

### Etape 1

- `www.smajor.org`
- `app.smajor.org`
- `api.smajor.org`
- `s25.smajor.org`
- `merlin.smajor.org`

### Etape 2

- `clients.smajor.org`
- `admin.smajor.org`
- `majorai.smajor.org`

### Etape 3

- `excavation.smajor.org`
- `deneigement.smajor.org`
- `staff.smajor.org`
- `vendors.smajor.org`

## Regles de construction

1. Toute logique critique reste dans le backend S25, pas dans les facades.
2. Une facade web peut etre remplacee sans toucher au mesh.
3. Toute action critique doit pouvoir etre retracee dans `missions` ou `intel`.
4. Toute connexion externe doit idealement passer par un domaine `smajor.org` stable.
5. Une integration nouvelle doit d'abord se brancher sur `api.smajor.org` ou `s25.smajor.org`, pas directement sur un ingress Akash brut.

## Ce que Gemini Orchestrator doit comprendre

- le WebUI MERLIN n'est pas la source de verite
- le mesh S25 est la source de verite operationnelle
- `smajor.org` est la facade produit / business
- les agents deviennent des responsables de domaines fonctionnels, pas juste des bots de test

## Ce que TRINITY doit comprendre

- quand elle parle de "serveur MERLIN", elle doit raisonner `mesh + MCP`, pas `webui vide`
- quand elle parle du business, elle doit mapper les demandes vers:
  - public
  - operations
  - backend
  - agents
