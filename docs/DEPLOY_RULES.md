# S25 LUMIERE — MAJOR DEPLOY RULES
# INDESTRUCTIBLE — Ne jamais bypasser ces regles
# Valide pour: ARKON, TRINITY, MERLIN, COMET, tout le monde

---

## REGLE #1 — DEUX CONTENEURS, JAMAIS UN SEUL

| Conteneur | DSEQ     | Image Tag | Toucher? |
|-----------|----------|-----------|----------|
| PROD      | 25838342 | :latest   | JAMAIS sans sandbox OK |
| SANDBOX   | a deployer | :main   | Oui — c'est fait pour ca |

- PROD = intouchable jusqu'a validation sandbox
- SANDBOX = terrain de jeu, peut exploser, c'est correct
- Jamais de deploy direct en prod depuis un commit non teste

---

## REGLE #2 — FLOW OBLIGATOIRE

```
code change
    ↓
git push → :main buildé automatiquement
    ↓
test sur SANDBOX (URL sandbox)
    ↓
[OK] → git tag vX.X.X → :latest buildé
    ↓
update PROD (akash update deployment)
```

Jamais sauter une etape. Meme si c'est urgent.

---

## REGLE #3 — TAGS IMAGE

| Tag      | Quand buildé           | Deployé sur |
|----------|------------------------|-------------|
| `:main`  | Chaque push sur main   | SANDBOX     |
| `:latest`| Release tag vX.X.X     | PROD        |
| `:sha-*` | Chaque commit (backup) | Reference   |

---

## REGLE #4 — ENV VARS SECRETS

- Jamais de token/key dans le code ou le SDL commité
- SDL commité = variables avec REPLACE_WITH_XXX comme placeholder
- Les vraies valeurs = uniquement dans Akash deployment via CLI ou dashboard
- Fichier .env.example = template, .env = jamais commité (.gitignore)

---

## REGLE #5 — MEMOIRE PERSISTANTE

- `memory/SHARED_MEMORY.md` = source de verite globale
- Modifier via PR seulement (pas de push direct sur ce fichier en prod)
- `agents_state.json` = runtime, peut changer en live via /api/memory/state
- Backup memory = toujours dans GitHub (synce apres chaque session importante)

---

## REGLE #6 — ROLLBACK

Si sandbox ou prod crash:
```bash
# Rollback image vers commit precedent
akash tx deployment update akash/deploy_sandbox.yaml --from wallet --dseq DSEQ

# Ou forcer image sha specifique dans SDL
image: ghcr.io/stephaneboss/s25-command-center:sha-COMMIT_SHA
```
Les sha- tags sont gardes = toujours possible de rollback.

---

## REGLE #7 — KILL SWITCH

En cas de probleme critique:
1. POST /api/trinity {"action": "signal", "data": {"trade_action": "HOLD"}}
2. HA input_boolean.s25_kill_switch = ON
3. Jamais detruire le deploiement Akash en premier (perdre les logs)

---

## SDL FILES

| Fichier                      | Role         |
|------------------------------|--------------|
| akash/deploy_cockpit.yaml    | PROD SDL     |
| akash/deploy_sandbox.yaml    | SANDBOX SDL  |

---
*Redige par ARKON — Mars 2026 — Ces regles protegent le capital et la stabilite S25*
