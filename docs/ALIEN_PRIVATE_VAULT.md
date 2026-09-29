# Alien : coffre privé et Drive partagé

Google Drive (`GOUV4`) transporte les missions, notes et rapports partageables entre agents. Le coffre de secrets du runtime Alien reste sur son disque privé, hors dépôt et hors synchronisation Drive. Une connexion Drive ne donne pas accès aux clés.

`S25Vault` lit dans cet ordre effectif : `.env` local, keyring, paquet chiffré, puis variables d'environnement (qui ont la priorité finale). Son paquet chiffré par défaut est désormais `~/.local/share/s25/secrets.bundle`. `S25_SECRETS_BUNDLE_PATH` permet un chemin local explicite. La clé maître doit provenir de l'environnement privé ou du keyring, jamais du même paquet ni de Drive.

## Migration de l'hôte existant

1. Sur Alien, relever seulement la présence et la source des clés via le diagnostic expurgé du coffre, le chemin effectivement configuré et les permissions. Ne jamais afficher de valeur.
2. Si un ancien `~/Google Drive/S25/secrets.bundle` est utilisé, préparer un chemin privé sur le disque Alien et une sauvegarde locale chiffrée. Installer le paquet avec propriétaire du service et permissions restrictives. Garder les clés maîtres dans le gestionnaire de secrets de l'hôte.
3. Définir `S25_SECRETS_BUNDLE_PATH` dans l'environnement privé du service si son chemin diffère du défaut. Redémarrer seulement le service ciblé, vérifier que les clés requises sont disponibles sans les afficher, puis faire une mission de lecture et un reçu.
4. Après preuve de fonctionnement et sauvegarde, retirer l'ancien paquet de la synchronisation Drive et vérifier les accès existants. Ne jamais faire cette migration automatiquement par `git pull`.

La mémoire et les missions Drive utilisent un répertoire distinct, en lecture seule pour les workers, avec index et empreintes. Aucune facture, courriel ou transaction ne découle du seul accès à Drive.
