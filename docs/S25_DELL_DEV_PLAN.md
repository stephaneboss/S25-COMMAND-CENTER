# S25 Major - poste dev Dell
Etat verifie le 2026-09-30 a 01:35 America/Toronto.

## Perimetre
Dell Windows DESKTOP-R67NPMP, Alien, Claude, Home Assistant, cockpit-alien.smajor.org et Cloudflare.
Gemini hors ligne volontairement : exclu de ce chantier.

## Acces prouves
- Remote Desktop Commander : terminal Dell, utilisateur Steph.
- Node 24.19.0, Git 2.55.0.windows.3, Python 3.14.3.
- GitHub CLI authentifie pour stephaneboss; PR #10 fusionnee.
- GitHub -> Alien -> redemarrage cockpit : SHA 9056c473 confirme.
- HA : HTTP 200 via cockpit; tunnel Cloudflare actif.
- WSL Ubuntu : utilisateur steph, Python 3.12.3, Git 2.43.0, OpenSSH 9.6.
- VS Code et extension Claude Code disponibles.
- Claude desktop/code tourne sur Dell; CLAUDE mesh reste relay_only_no_execution.

## Poste de travail
Copie dediee : C:\Users\Steph\Documents\Playground\S25-GPT-tuneup-20260930
L'ancienne copie S25-COMMAND-CENTER-git contient du travail local : ne pas la remplacer.
Environnement de tests : .venv (local, non versionne).
Branche de travail : fix/ha-kill-switch-status-evidence.

## Reprise de session
1. Identifier le device avec list_devices, confirmer hostname et whoami.
2. Lire ce plan et git status; conserver les modifications existantes.
3. Lancer python -X utf8 scripts/s25_dev_doctor.py.
4. Comparer SHA du depot et SHA runtime; un HEAD modifie n'est pas une preuve de deploiement.
5. Verifier les capacites et les recus de mission avant d'annoncer un agent operationnel.

## Ordre des chantiers
1. Affichage HA/local : correctif prepare, 18 tests passent; publication et fusion autorisees par Stef le 30 septembre.
2. Terminal Alien : SSH direct non confirme; ancienne IP 10.0.0.97 obsolete.
   Dell Wi-Fi 192.168.1.44; hote connu 192.168.1.45 teste, sans connexion confirmee.
   Obtenir la cible actuelle via une voie d'administration authentifiee deja configuree.
3. Administration cockpit : reutiliser le secret local via le coffre, sans l'afficher.
   Pas de contournement d'authentification ni d'ouverture SSH publique.
4. Claude : verifier le worker executant, ses permissions et un recu reel d'une mission infra.
   Le relais qui emet un heartbeat ne suffit pas.
5. Cloudflare : verifier configuration et routage; conserver le tunnel qui fonctionne.
6. HA : verifier les entites infra, leur fraicheur et les doublons avant tout nettoyage.

## Livraison
Branche isolee -> tests -> PR -> fusion autorisee -> auto-pull -> SHA runtime -> sante/recus.
Le correctif HA ajoute des preuves au statut; il conserve la politique d'execution.
Le doctor ne fait que des lectures, ne journalise aucun secret et n'execute aucun ordre.
Rollback d'un correctif deploye : revert via PR, puis verification du SHA runtime.

