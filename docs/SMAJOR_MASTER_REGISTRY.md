# Smajor Master Registry

## But

Donner a `Smajor` une colonne vertebrale de donnees unique pour:
- plusieurs entreprises
- plusieurs clients
- plusieurs equipes
- plusieurs fournisseurs
- plusieurs services
- plusieurs agents

## Registres maitres

### 1. Organization registry

Contient:
- entite legale
- marque
- division
- site principal
- statut

Exemples:
- `smajor_holding`
- `excavation_ops`
- `snow_ops`
- `major_ai_services`

### 2. Identity registry

Contient:
- personne
- organisation rattachee
- type d'identite
- role
- statut d'acces

Types:
- client_contact
- employee
- contractor
- vendor_contact
- admin_operator

### 3. Service registry

Contient:
- service offert
- code service
- categorie
- entite operatrice
- conditions d'activation

Exemples:
- snow_contract
- excavation_job
- exterior_maintenance
- ai_consulting
- ai_automation

### 4. Asset registry

Contient:
- camion
- pelle
- equipement
- outil critique
- disponibilite
- affectation

### 5. Job registry

Contient:
- job
- client
- site
- service
- equipe
- statut
- documents

### 6. Quote and invoice registry

Contient:
- devis
- facture
- montant
- statut
- rattachement job / client / organisation

### 7. Vendor registry

Contient:
- fournisseur
- contacts
- categories d'achat
- delais
- statut

### 8. AI registry

Contient:
- agent
- role
- surface publique
- permissions
- cout
- criticite

## Regle

1. Chaque registre a un identifiant stable.
2. Un enregistrement ne doit pas vivre seulement dans le front.
3. L'admin doit pouvoir voir les liens entre registres.
4. Les agents lisent et enrichissent; ils ne doivent pas casser la structure.
5. `api.smajor.org` devra servir ces registres plus tard comme facade stable.
