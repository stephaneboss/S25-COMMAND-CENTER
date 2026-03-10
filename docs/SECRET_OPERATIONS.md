# Secret Operations

## But

Arreter de courir apres les cles.

## Regle simple

- laptop operateur: OS keyring
- Google Drive: bundle chiffre synchronise entre machines
- Akash et GitHub: env vars injectees au runtime
- `.env`: fallback local seulement

## Priorite des sources

1. environment variables
2. OS keyring
3. bundle chiffre Google Drive
4. `.env`

## Commandes

Audit:

```powershell
python scripts/manage_secrets.py audit
```

Doctor:

```powershell
python scripts/manage_secrets.py doctor
```

Stocker une cle locale:

```powershell
python scripts/manage_secrets.py set GEMINI_API_KEY
```

Definir la cle maitre du bundle synchronise:

```powershell
python scripts/manage_secrets.py set-bundle-key
```

Verifier une cle sans l'afficher:

```powershell
python scripts/manage_secrets.py status GEMINI_API_KEY
```

Supprimer une cle locale:

```powershell
python scripts/manage_secrets.py delete GEMINI_API_KEY
```

Exporter les secrets a injecter en prod:

```powershell
python scripts/manage_secrets.py export --include-optional
```

Verifier le bundle:

```powershell
python scripts/manage_secrets.py bundle-status
```

Ecrire le bundle chiffre:

```powershell
python scripts/manage_secrets.py write-bundle --include-optional
```

## Mode production

Quand tu dis "ok vrai production":

1. rotation des cles critiques
2. injection dans Akash et GitHub
3. audit du vault
4. restart du runtime

## Minimum core

- `GEMINI_API_KEY`
- `HA_TOKEN`
- `S25_SHARED_SECRET`

## Minimum IA complet

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `PERPLEXITY_API_KEY`
- `KIMI_API_KEY`

## Minimum finance

- `MEXC_API_KEY`
- `MEXC_SECRET_KEY`

## Google Drive

Mode recommande:
- le fichier chiffre vit dans Google Drive
- la cle maitre reste dans le keyring Windows
- les machines autorisees lisent le meme bundle sans stocker les secrets en clair
