# TRINITY Stable Endpoint

## Etat actuel

- Backend corrige actif sur `kfhsi5oko9dbt3abob51g4s9q0.ingress.cap-test-compute.com`
- GPT live depannee via un `trycloudflare`
- Ce mode n'est pas acceptable en production car l'URL est ephemere

## Architecture recommandee

Utiliser un tunnel Cloudflare nomme devant le backend Akash corrige.

Flux cible:

`TRINITY GPT -> https://trinity.s25lumiere.net -> Cloudflare Tunnel -> backend Akash -> /api/status|/api/memory|/api/mesh/status|/api/router/report`

## Pourquoi c'est la meilleure option

- URL stable pour la GPT
- HTTPS valide et gere par Cloudflare
- Aucun besoin d'attendre un provider Akash avec certificat correct
- Possibilite de faire tourner le tunnel comme service Windows ou Linux
- Permet ensuite de brancher un domaine officiel S25

## Mise en place conseillee

1. Authentifier `cloudflared` avec le compte Cloudflare
2. Creer un tunnel nomme `trinity-s25`
3. Creer un DNS `trinity.s25lumiere.net` vers ce tunnel
4. Utiliser `cloudflare/trinity-tunnel-config.yml.example` comme base
5. Installer le tunnel comme service
6. Repointer la GPT vers `https://trinity.s25lumiere.net`

## Commandes de reference

```powershell
cloudflared login
cloudflared tunnel create trinity-s25
cloudflared tunnel route dns trinity-s25 trinity.s25lumiere.net
cloudflared service install
cloudflared tunnel run trinity-s25
```

## Variante service Windows

Mettre les fichiers ici:

- `C:\cloudflared\config.yml`
- `C:\cloudflared\trinity-s25.json`

Puis:

```powershell
cloudflared service install
Start-Service cloudflared
```

## Garde-fous

- garder le `httpHostHeader` vers l'ingress Akash reel
- ne pas utiliser `trycloudflare` en prod
- si l'ingress Akash change, mettre a jour uniquement le `service` et le `httpHostHeader`
- garder la GPT sur un domaine stable, jamais sur une URL ephemere

## Alternative secondaire

Si Cloudflare n'est pas disponible, la seconde meilleure option est:

- redeployer sur un provider Akash avec HTTPS sain
- verifier `/api/version` et `/api/mesh/status`
- seulement ensuite repointer la GPT

Cette option est moins fiable car depend du provider Akash choisi.
