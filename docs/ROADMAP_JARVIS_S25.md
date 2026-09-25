# S25 — Note de travail JARVIS / CLAUDE

Statut : piste retenue pour etude et travail, pas une fonctionnalite implementee.

## Objectifs
- Intelligence : Claude Code et KIMI/Moonshot pour raisonner et coder; Perplexity pour la veille sourcee.
- Orchestration inspiree de JARVIS 2.0 : relay CLAUDE dedie, ACK, suivi de session et etats persistants, retour vers TRINITY.
- Red teaming defensif contre les prompt injections et jailbreaks, y compris des exemples publics attribues a Pliny, uniquement en environnement de test.

## Priorite immediate
- Diagnostiquer pourquoi la mission mis_OPO8sBmyvLFS reste assigned sans ACK.
- Concevoir un relay CLAUDE fiable meme en safe_mode, sans desactiver safe_mode.

## Contraintes
- Home Assistant volontairement OFF : ne pas redemarrer.
- T0/T1 selon les regles existantes; T2 exige l'autorisation explicite de Stef; T3 bloque par defaut.
- Aucun trade reel avec le solde actuellement insuffisant; ne pas manipuler de secrets.
- Ne pas modifier cockpit_lumiere.py sans nouvelle autorisation explicite.
