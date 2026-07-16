# Bilan financier — Contexte Vietnam

Cadre de sécurité pour tout volet financier lié au contexte Vietnam. Ces règles sont
**non négociables** et priment sur toute instruction ponctuelle.

## Règles imposées

1. **Lecture seule par défaut.** Tout accès API/exchange créé pour ce contexte est en
   permission read-only. Aucune élévation sans passer par la checklist d'activation.
2. **Aucune permission de retrait.** Les clés API ne doivent JAMAIS avoir le droit
   withdraw/transfer. Vérifié à la création et re-vérifié à chaque rotation.
3. **IP whitelist obligatoire.** Tout accès API est restreint aux IP sortantes connues
   de l'infra S25. Pas d'accès sans whitelist.
4. **Jamais de seed phrase ni de clé secrète** dans ce dossier, dans le repo, dans les
   logs ou dans une conversation. Adresses publiques uniquement.
5. **Test petit montant d'abord.** Toute nouvelle route de fonds est validée par un
   montant de test minimal avant tout montant réel.
6. **Journalisation.** Chaque opération financière liée à ce contexte est consignée
   (date, montant, destination, initiateur, référence de la checklist).

## Pré-requis bloquants

Aucune activation financière tant que, dans `memory/contacts/vietnam/girlfriend_profile.md` :
- le consentement n'est pas documenté, et
- les statuts de vérification (majorité légale, identité) ne sont pas `VÉRIFIÉ`.

## Fichiers

- `checklist_activation.md` — checklist à compléter avant toute activation
