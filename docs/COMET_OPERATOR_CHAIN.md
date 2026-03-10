# COMET Operator Chain

## But

Donner a COMET un rail simple pour piloter le deploiement `merlin-mesh` sans rebricoler le setup a chaque fois.

## Doctrine

- COMET prepare et suit le deploiement web
- Gemini / MERLIN valide via MCP
- le createur ne clique que sur le wallet
- le laptop sert d'orchestrateur et de coffre, pas de dependance runtime

## Rail operateur

### 1. Verifier les secrets core

```powershell
python scripts/manage_secrets.py doctor
```

Minimum:
- `GEMINI_API_KEY`
- `S25_SHARED_SECRET`

### 2. Rendre le manifest Akash pret a uploader

```powershell
pwsh -File scripts/prepare_merlin_mesh_deploy.ps1
```

Sortie attendue:
- un YAML rendu hors repo avec les secrets injectes
- un `COCKPIT_URL` deja pointe vers le front stable

### 3. Lancer le deploiement Akash

COMET ou l'operateur:
- ouvre `New Deployment`
- charge le manifest rendu
- verifie le prix
- laisse le createur signer dans Keplr

### 4. Valider le handshake MCP public

Quand Akash donne l'ingress:

```powershell
pwsh -File scripts/test_merlin_mcp_handshake.ps1 -Endpoint "http://<ingress>/mcp"
```

Sortie attendue:
- `ok: true`
- `server: S25 Merlin MCP Bridge`
- liste des tools exposees

## Contrat COMET

COMET doit toujours remonter:
- `dseq`
- `ingress`
- `deploy_status`
- `wallet_signature_needed`
- `handshake_status`
- `next_action`

## Contrat Gemini / MERLIN

MERLIN prend ensuite le relais sur le bridge pour:
- lire `status`
- lire `mesh`
- lire `missions`
- ecrire un verdict via `write_feedback`

## Definition de done

Le setup est considere propre quand:
- le manifest Akash est rendu automatiquement depuis le vault
- le createur ne clique que pour signer
- le handshake MCP public passe
- COMET peut rapporter l'etat du deploiement sans ressaisir les details
