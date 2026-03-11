# Smajor Industrial Stack

## But

Transformer `smajor.org` en systeme industriel pour:
- excavation
- deneigement
- gestion client
- gestion equipe
- gestion fournisseurs
- automatisation business
- vente de services IA

Le front doit rester simple.
Le backend doit rester robuste.
Le mesh S25 doit rester la source de verite.

## Noyau minimum obligatoire

### 1. CRM / clients

Le systeme doit tenir:
- fiche client
- contacts
- adresses / sites de service
- contrats
- demandes entrantes
- devis
- factures
- historique des interventions
- statut de paiement

### 2. Operations / dispatch

Le systeme doit tenir:
- calendrier d'interventions
- priorites terrain
- assignation staff / equipement
- rapports de fin de job
- photos / preuves
- incidents / escalation

### 3. Finance

Le systeme doit tenir:
- devis
- factures
- suivi paiements
- couts fournisseurs
- marge par dossier
- couts infra
- synthese cash

### 4. Vendors / supply

Le systeme doit tenir:
- fournisseurs
- prix
- pieces / materiaux / location
- bons de commande
- receptions
- cout rattache aux jobs

### 5. Staff

Le systeme doit tenir:
- fiches equipe
- roles
- disponibilites
- horaires
- taches
- rapports terrain

### 6. IA / agents

Le systeme doit tenir:
- orchestration TRINITY
- validation MERLIN
- veille COMET
- capteurs KIMI / ORACLE / ONCHAIN_GUARDIAN
- missions
- feed intel
- journal de decisions

## Architecture cible

- `www.smajor.org`
  - vitrine business
- `app.smajor.org`
  - shell central d'operations
- `clients.smajor.org`
  - portail clients
- `admin.smajor.org`
  - poste de commandement
- `staff.smajor.org`
  - execution terrain
- `vendors.smajor.org`
  - supply chain
- `api.smajor.org`
  - entree business stable
- `s25.smajor.org`
  - cockpit et etat runtime
- `merlin.smajor.org`
  - tools / MCP / validation

## Plan de construction

### Phase 1

- facade domaine stable
- shell d'operations
- panneaux live status / missions / mesh
- doctrine agents / domaine / role

### Phase 2

- portail clients MVP
- backoffice admin MVP
- modele de dossier client
- modele devis / facture
- file de jobs

### Phase 3

- portail staff
- portail vendors
- dispatch terrain
- couts / marges / approbations

### Phase 4

- services IA vendables
- suivi clients IA
- runbooks automatiques
- reporting entreprise

## Regles

1. Le front ne porte pas la logique critique.
2. Toute action importante doit etre retracable.
3. Toute integration nouvelle doit viser `api.smajor.org`.
4. Toute orchestration complexe doit remonter dans `missions` ou `intel`.
5. Le site doit rester comprenable par un humain non technique.
6. Les agents servent les operations, ils ne remplacent pas la gouvernance.
