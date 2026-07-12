# S25 2027 — Architecture cible

## Objectif

Transformer S25 Lumière en plateforme locale, observable, résiliente et évolutive, sans interrompre le pipeline actif.

## Principes

- AlienStef demeure le plan de contrôle local et l’hôte de confiance.
- Trinity orchestre les intentions, missions, validations et reprises.
- Claude agit comme ingénieur externe du mesh pour les changements complexes.
- Les agents locaux exécutent les tâches spécialisées avec contrats explicites.
- Le GPU RTX 3060 et Ollama servent les modèles locaux et les tâches de code/analyse.
- Le cockpit expose une API de contrôle, mais ne doit pas devenir un point unique opaque.
- Toute migration se fait par étapes, derrière feature flags, avec rollback documenté.

## Couches

### 1. Control plane

- Cockpit API
- Trinity
- Mission router
- Policies de sécurité
- Kill switch

### 2. Execution plane

- Claude pour infra_ops et code_generation
- Agents locaux: MERLIN, ORACLE, COMET, COINBASE et workers spécialisés
- GPU/Ollama pour inférence locale

### 3. Reliability plane

- Heartbeats horodatés
- Backpressure
- Circuit breakers
- Dead-letter queue
- Retries bornés
- Déduplication des événements

### 4. Observability plane

- État unifié des services, agents, crons et missions
- Logs structurés
- Incidents avec propriétaire, sévérité et résolution
- Métriques GPU, latence, erreurs, files et disponibilité

## Contrat de mission v1

États autorisés:

`queued -> claimed -> acknowledged -> running -> completed`

Sorties d’erreur:

`failed`, `timed_out`, `cancelled`, `dead_lettered`

Chaque mission doit contenir:

- mission_id
- target_agent
- task_type
- intent
- created_at / updated_at
- timeout_sec
- max_retries
- require_ack
- result ou error

## Source de vérité

Une seule vue doit agréger:

- services systemd
- agents réellement vivants
- crons actifs
- missions en cours
- incidents ouverts
- DLQ
- état GPU/Ollama

Les statuts périmés doivent être marqués `stale`, jamais présentés comme actifs.

## Séparation des données

