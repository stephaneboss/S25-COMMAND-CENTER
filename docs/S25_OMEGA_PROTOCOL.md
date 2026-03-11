# S25 OMEGA PROTOCOL

## Directive

- Contexte: le maillage S25 Lumiere est actif.
- Mission: construire le Front-End souverain et consolider l'API Gateway pour Major.
- Regle de livraison: code de production uniquement, zero placeholder, zero commentaire inutile.
- Style: cyberpunk militaire, dark mode, accents neon, structure modulaire.

## Phase 1: Back-End

Le noyau gateway doit exposer et stabiliser les routes suivantes:

1. `/api/mesh/status`
   - Agreger le statut des 15 agents.
   - Calculer readiness, ratio online, signaux de degradation, posture d'ensemble.
   - Publier la chaine de commandement agentique.

2. `/api/vault/mexc`
   - Consolider le statut du vault MEXC.
   - Afficher la boucle arbitrage `$BTC/$USDT/$AKT`.
   - Distinguer les metriques live, les protections et le mode de marche.

3. `/api/akash/infra`
   - Publier l'etat des clusters CPU/GPU S25.
   - Lister les deploiements critiques Akash.
   - Suivre uptime, provider, role runtime et route publique.

## Phase 2: Front-End

Le dashboard souverain doit afficher:

1. Header global
   - uptime S25
   - statut HA / Nabu Casa
   - solde vault et posture runtime

2. Panneau gauche
   - liste dynamique des 15 agents
   - statut par agent
   - role, badge, surface d'action

3. Panneau central
   - feed live Comet / Merlin / Trinity
   - journal de commandes
   - priorites du hub

4. Panneau droit
   - rentabilite MEXC
   - couts Akash
   - balance profit / infra

## Doctrine d'orchestration

- Le mesh S25 reste la source de verite operationnelle.
- `smajor.org` sert de facade souveraine.
- La loi du systeme reste:
  - `identity_id -> role_id -> badge_id -> scope_id -> service_entitlements`
- Aucune fonction critique n'est attachee a une identite fixe.
- Le systeme doit survivre a la rotation humaine.

## Chaine de commandement

- `TRINITY`: orchestration, missions, commandement du hub
- `MERLIN`: validation, memoire, coherence
- `COMET`: veille, suivi operatoire, relais externe
- `GOUV4`: arbitrage, policy, couts
- `KIMI`: data pump Web3
- `ORACLE`: confirmation market
- `ONCHAIN_GUARDIAN`: risque on-chain
- `ARKON`: runtime, build, raccordement

## Agents cibles pour diffusion

- `CODE_VALIDATOR`
- `SMART_REFACTOR`
- `AUTO_DOCUMENTER`
- `COMET`
- `MERLIN`
- `TRINITY`

## Resultat attendu

- un hub qui ressemble a un organisme vivant
- un gateway qui expose une image claire de l'empire
- une base industrialisable pour les portails clients, staff, vendors, admin et AI
