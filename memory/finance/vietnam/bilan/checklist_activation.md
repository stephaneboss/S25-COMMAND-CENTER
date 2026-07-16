# Checklist d'activation — Volet financier Vietnam

À compléter dans l'ordre. Chaque case non cochée est bloquante pour la suite.
Journaliser la date et l'initiateur pour chaque étape complétée.

## 1. Pré-requis humains (bloquants)

- [ ] Consentement explicite documenté dans la fiche contact (date + portée)
- [ ] Majorité légale : statut `VÉRIFIÉ` (méthode + date documentées)
- [ ] Identité : statut `VÉRIFIÉ` (méthode + date documentées)

## 2. Configuration des accès

- [ ] Compte/accès exchange créé en **lecture seule uniquement**
- [ ] Confirmation que la clé API n'a AUCUNE permission de retrait/transfert
- [ ] IP whitelist activée et limitée aux IP sortantes S25 connues
- [ ] Vérification qu'aucun secret (seed, clé privée, mot de passe) n'apparaît
      dans le repo, les logs ou les fichiers de ce dossier

## 3. Validation technique

- [ ] Test de lecture (balance/status) réussi et journalisé
- [ ] Test petit montant : montant minimal envoyé, reçu et confirmé des deux côtés
- [ ] Entrée de journalisation créée (date, montant, destination, initiateur)

## 4. Revue finale

- [ ] Relecture des règles de `README.md` (lecture seule, pas de retrait, whitelist)
- [ ] Validation finale par Steph, datée : `À REMPLIR`

## Journal

| Date | Étape | Initiateur | Référence |
|------|-------|-----------|-----------|
| —    | —     | —         | —         |
