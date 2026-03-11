# Smajor Domain Plan

## Domaine principal

- domaine achete: `smajor.org`
- nameservers Cloudflare detectes:
  - `carrera.ns.cloudflare.com`
  - `cash.ns.cloudflare.com`

## Doctrine

`smajor.org` devient la base publique unique pour:
- la vitrine business
- le backoffice
- l'infra S25
- les agents IA

Le mesh Akash reste le compute.
Cloudflare devient la couche stable de presentation.

## Sous-domaines a activer d'abord

- `s25.smajor.org`
  - cockpit public S25
  - proxy Worker vers le cockpit Akash public courant
- `api.smajor.org`
  - meme backend que `s25`
  - utile pour futures integrations site/app
- `merlin.smajor.org`
  - proxy Worker vers le bridge MCP MERLIN

## Sous-domaines reserves pour la suite

- `www.smajor.org`
  - site public entreprise
- `app.smajor.org`
  - interface centrale d'operations
- `clients.smajor.org`
  - portail clients
- `admin.smajor.org`
  - backoffice interne
- `excavation.smajor.org`
  - service terrain
- `deneigement.smajor.org`
  - service terrain hiver
- `ai.smajor.org`
  - branche IA / automations

## Mappings live

- `s25.smajor.org/*` -> Worker `trinity-s25-proxy`
- `api.smajor.org/*` -> Worker `trinity-s25-proxy`
- `merlin.smajor.org/*` -> Worker `merlin-s25-proxy`
- `smajor.org` -> Worker `smajor-hub`
- `www.smajor.org` -> Worker `smajor-hub`
- `app.smajor.org` -> Worker `smajor-hub`

## Etat du 2026-03-11

- `s25.smajor.org`, `api.smajor.org`, `merlin.smajor.org`
  - custom domains Cloudflare deployes
  - DNS public vu via `1.1.1.1` pour `s25/api/merlin`
- `smajor.org`, `www.smajor.org`, `app.smajor.org`
  - hub Cloudflare deploye
  - propagation DNS encore en cours au moment du commit

## Cible

- `s25.smajor.org/api/status` doit devenir la reference publique du cockpit
- `merlin.smajor.org/mcp` doit devenir la reference publique du bridge MCP
- plus tard, `www.smajor.org` et `app.smajor.org` absorberont le front-end business
