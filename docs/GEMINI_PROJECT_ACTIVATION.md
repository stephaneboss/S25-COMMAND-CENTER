# Gemini Project Activation

## But

Avoir une base Google propre pour que Gemini pilote le MCP live S25 sans friction.

## Cible S25

- MCP live:
  - `https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp`
- modele cible:
  - `gemini-2.5-flash`
- mode cible:
  - `Interactions API` + `mcp_server`

## Verites officielles

- `Remote MCP` ne marche qu'avec des serveurs `streamable-http`
- `Remote MCP` ne marche pas encore avec les modeles `Gemini 3`
- `URL context` ne se combine pas encore avec le function calling classique
- `google_search` peut se combiner avec `url_context`
- les quotas sont lies au projet Google / tier, pas a une cle isolee

## Checklist projet Google

### 1. Verifier le bon projet AI Studio

Dans AI Studio:
- aller sur la page API keys
- verifier quel projet Google est relie a la cle
- garder le meme projet pour billing, quota et cle

### 2. Activer la facturation

Source officielle:
- [Billing](https://ai.google.dev/gemini-api/docs/billing/)

But:
- sortir du free tier
- rendre le projet eligible au Tier 1

### 3. Verifier le tier et les quotas

Sources officielles:
- [Rate limits](https://ai.google.dev/gemini-api/docs/quota)
- [Pricing](https://ai.google.dev/pricing)

But:
- confirmer que le projet n'est pas encore bloque en free tier
- verifier que `gemini-2.5-flash` a un quota exploitable

### 4. Garder le bon modele

Pour le MCP live:
- utiliser `gemini-2.5-flash`

Ne pas baser le MCP sur:
- `Gemini 3`

### 5. Valider l'API de base

Commande:

```bash
python scripts/gemini_project_doctor.py
```

Lecture du resultat:
- `generate_content_basic` doit etre `200`
- `interactions_basic` doit idealement etre `200`
- `interactions_mcp` doit idealement etre `200`

### 6. Si `429 too_many_requests`

Cause probable:
- billing/tier non effectif
- quota projet pas encore releve

Action:
- verifier AI Studio Billing
- verifier le projet associe a la cle
- attendre la propagation si le changement est recent

### 7. Si `500 api_error` sur `interactions_mcp`

Cause probable:
- backend Google `Interactions` instable
- projet pas completement pret pour ce mode
- ou incident Google temporaire

Action:
- retenter plus tard
- verifier avec `interactions_basic`
- garder le writeback MCP direct comme fallback

## Commandes S25

Handshake MCP:

```bash
python scripts/test_merlin_mcp_handshake.py https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp
```

Doctor projet Gemini:

```bash
python scripts/gemini_project_doctor.py
```

Test Gemini Interactions live:

```bash
python scripts/run_gemini_merlin_interaction.py --endpoint https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp
```

Fallback writeback direct:

```bash
python scripts/write_merlin_mcp_feedback.py --endpoint https://da0m4r4tu5ctn0ja9r2t9c2vho.ingress.akashprovid.com/mcp --summary "MERLIN MCP bridge live on Akash. Public handshake validated on dseq 25878071."
```

## Doctrine S25

- MCP live Akash = bon
- Gemini project = doit etre propre
- COMET = bras web
- TRINITY = orchestration
- MERLIN/Gemini = validation + retrieval + web-native tools
