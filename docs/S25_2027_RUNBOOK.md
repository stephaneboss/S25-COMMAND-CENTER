# S25 2027 — Runbook opérationnel

## Démarrage

1. Vérifier le service cockpit.
2. Vérifier le tunnel et l’API.
3. Vérifier les crons critiques.
4. Vérifier le mesh et les heartbeats.
5. Vérifier GPU et Ollama.
6. Vérifier kill switch et mode du pipeline.

## Contrôles santé minimaux

- Cockpit: actif, sans boucle de redémarrage
- Mesh: agents attendus avec heartbeat frais
- Missions: aucune file bloquée
- Backpressure: niveau normal
- Breakers: aucun ouvert sans incident associé
- DLQ: entrées classées et propriétaires identifiés
- GPU: température, VRAM et processus connus
- Git: aucun secret ou fichier runtime accidentel

## GPU et Ollama

Contrôler:

- modèle GPU détecté
- utilisation GPU
- VRAM utilisée / totale
- température
- processus actifs
- disponibilité du service Ollama

Une VRAM faible au repos est normale. Une température élevée au repos, un processus inconnu ou une saturation persistante doit ouvrir un incident.

## Mesh et missions

Pour une mission critique:

1. créer la mission
2. confirmer `claimed`
3. confirmer `acknowledged`
4. suivre `running`
5. valider `completed` avec résultat
6. vérifier qu’aucun retry ou doublon n’a été créé

Toute mission expirée doit devenir `timed_out` puis être rejouée au maximum selon `max_retries`.

## Incidents

Chaque incident doit avoir:

- titre clair
- sévérité
- propriétaire
- preuve
- impact
- action recommandée
- état de résolution

Fermer les incidents obsolètes seulement après vérification de l’état réel.

## DLQ

- Ne jamais rejouer aveuglément.
- Classer test, erreur transitoire ou erreur permanente.
- Rejouer seulement les entrées valides et idempotentes.
