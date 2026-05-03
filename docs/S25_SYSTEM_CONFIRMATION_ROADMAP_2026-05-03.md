# S25 Lumiere — Roadmap de confirmation systeme

Date d'audit: 2026-05-03  
Objet: documentation de l'etat courant S25 / Smajor.org / Coinbase / Home Assistant / agents locaux.  
Mode: confirmation operationnelle sans exiger que tous les agents cloud ou legacy soient branches.

> Ce document ne contient aucun secret, jeton, cle privee, seed phrase ou identifiant sensible.

## 1. Resume executif

S25 Lumiere fonctionne actuellement comme un pipeline hybride: l'orchestration passe par TRINITY, le cockpit Smajor.org, des agents locaux sur AlienStef, Home Assistant, Coinbase et Git/GitHub. Le systeme n'a pas besoin que tous les agents historiques soient ouverts pour confirmer la chaine principale.

Etat verifie:

- Cockpit S25 actif et tunnel actif.
- Coinbase live flag actif cote cockpit.
- Home Assistant actif avec garde-fous, incluant kill switch HA active.
- Mesh multi-agent actif avec agents locaux fonctionnels.
- Plusieurs agents cloud ou legacy sont desactives, en standby ou partiels.
- Stabilite mesh saine: breakers fermes, backpressure OK, aucune mission active bloquee.

Conclusion: la chaine de base est operationnelle, mais elle doit etre presentee comme un mode hybride controle, avec certains modules avances volontairement non essentiels ou non branches.

## 2. Architecture visible actuelle

Composants visibles dans l'audit:

- TRINITY: interface voix/texte et orchestration.
- Smajor.org / Cockpit Lumiere: gateway API, command mesh, routes ops, statut systeme.
- AlienStef: machine locale Linux, host systemd/cron/mission worker/cockpit.
- Coinbase: execution et lecture de portefeuille, mode live cote cockpit.
- Home Assistant: tableau de bord, capteurs, controles, kill switch, etat des agents.
- Git/GitHub: journalisation, snapshots, documentation, preuve de chaine.
- Agents locaux: scanner, bridge, trailing stop, drawdown guardian, system health, git auto-sync.
- Agents cloud/legacy: Gemini, Kimi, ARKON5, Comet selon disponibilite et branchement.

## 3. Statut Coinbase observe

Audit Coinbase courant:

- Mode cockpit Coinbase: LIVE flag actif.
- Valeur totale observee: environ 41.69 USD.
- USD disponible: 8.61 USD.
- Reserve en ordres ouverts: 20.54 USD.
- DOGE: 152.39749398, dont 152.3 en hold.
- BTC: 0.00018197, dont 0.00005034 en hold.
- AKT: 3.21.

Positions ouvertes observees:

- DOGE-USD: position ouverte, PnL non realise positif.
- BTC-USD: position ouverte, PnL non realise positif.
- SOL-USD: position ouverte, PnL non realise positif.
- AKT-USD: position ouverte, PnL non realise positif.

PnL observe:

- PnL realise: -2.8251 USD.
- PnL non realise: environ +6.36 USD.
- PnL total: environ +3.53 USD.
- Trades realises visibles: 28 trades historiques.

Observation importante:

- Des signaux SELL DOGE/USDT recents sont recus environ aux deux minutes avec verdict EXECUTE.
- Les donnees disponibles ne confirment pas de nouveaux fills Coinbase recents via la couche missions/PnL realise.
- Des holds importants sur DOGE et BTC indiquent des ordres ouverts ou fonds reserves.

## 4. Home Assistant

Etat Home Assistant observe:

- Agents actifs: analyste, conversation, coordinateur/coordinator, devops, recherche, trading.
- Agents standby ou indisponibles: analyst, research, bridge selon capteurs.
- Multi-agent enabled: ON.
- Debug mode: ON.
- lambda_bridge_active: OFF.
- s25_coinbase_live_trading: OFF cote HA.
- s25_kill_switch: ON cote HA.

Point de controle:

Le cockpit indique Coinbase live actif, pendant que Home Assistant indique Coinbase live trading OFF et kill switch ON. Cette divergence doit etre documentee comme un etat hybride avec garde-fou: la lecture et certains controles cockpit sont actifs, mais HA conserve un verrou de securite.

## 5. Mesh et pipeline multi-agent

Agents et services locaux observes comme actifs ou recents:

- COCKPIT_LUMIERE: online.
- COINBASE: online.
- ALIENSTEF: online.
- HOME_ASSISTANT: online.
- coinbase_ha_publisher: online.
- mesh_signal_bridge: online.
- trailing_stop_manager: online.
- auto_signal_scanner: online.
- comet_sentiment: online.
- drawdown_guardian: online.
- dca_scheduler: online.
- quant_brain: online.
- system_health: online.
- git_auto_sync: online.

Agents principaux:

- MERLIN: online.
- ORACLE: online.
- ONCHAIN_GUARDIAN: standby.
- TRINITY: controle voix/texte.

Agents cloud ou legacy partiels:

- GEMINI legacy: desactive selon registre historique.
- ARKON5: desactive dans la liste agents historique, mais le statut systeme montre encore un etat ARKON5_SELL. A clarifier dans le prochain audit.
- KIMI: legacy/desactive dans le registre, mais des fonctions cloud peuvent etre appelees separement selon configuration.

## 6. Stabilite et resilience

Etat stabilite observe:

- Backpressure: OK.
- Missions en queue: 0.
- Retries dus: 0.
- Signal rate 60s: 0 au moment du check stabilite.
- Breakers ouverts: 0.
- Breakers fermes: 5/5.
- DLQ: 4 items historiques du 2026-04-22, dont plusieurs tests forces.

Conclusion stabilite: aucun blocage actif detecte dans la couche resilience. Les DLQ doivent rester dans la documentation comme dette technique historique, pas comme incident actif.

## 7. Roadmap de confirmation sans tous les agents

Etape 1 — Audit lecture seule:

- Verifier cockpit, mode pipeline, portefeuille Coinbase, PnL, positions, HA, mesh, stabilite.
- Ne pas executer de trade.

Etape 2 — Test preuve Git:
