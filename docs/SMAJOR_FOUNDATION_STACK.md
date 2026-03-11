# Smajor Foundation Stack

## Decision

Pour une vraie entreprise multi-service avec IA:

- **Backbone business**: ERPNext / Frappe
- **HR**: Frappe HRMS
- **Customer-facing self-service**: Smajor custom facade sur Cloudflare
- **AI orchestration**: S25 Lumiere + MERLIN MCP + TRINITY
- **Optional modern sales CRM layer later**: Twenty

## Pourquoi ce choix

### ERPNext / Frappe

Meilleur backbone pour:
- clients
- devis
- factures
- achats
- projets / jobs
- assets
- compta de base
- workflow entreprise

Ca colle mieux a une vraie entreprise terrain qu'un simple CRM.

### HRMS

Meilleur bloc RH libre pour:
- employes
- onboarding
- presence
- shifts
- paie / RH selon besoin

### Smajor custom facade

On garde `smajor.org` comme facade:
- experience sur mesure
- administration stricte
- portail client/employe/fournisseur
- control plane unique

Donc:
- Frappe sert la logique business
- S25 sert l'orchestration IA
- Smajor sert l'experience et la gouvernance produit

### Twenty

A garder comme couche optionnelle plus tard si on veut:
- pipeline ventes moderne
- experience CRM slick
- objets custom sales

Mais pas comme centre de gravite principal pour excavation / deneigement / operations.

## Regle de construction

1. Ne pas empiler des stacks concurrentes pour le meme besoin.
2. Un seul backbone business.
3. S25 reste la source de verite IA / orchestration.
4. Smajor reste la facade visible.
5. Toute nouvelle brique doit s'inserer dans cette ligne.

## Candidats retenus

- ERPNext: business backbone
- HRMS: workforce backbone
- Twenty: sales CRM optionnel
- Frappe Assistant Core / MCP: piste d'integration IA a surveiller
