# Factures S25 — noyau brouillon

État du code : raccordé au cockpit Flask, désactivé par défaut. Aucun accès à Invoice Simple ni à une boîte courriel; aucune facture réelle n'a été importée ou envoyée.

## Circuit cible

1. Stef dicte une instruction dans la voix S25. TRINITY identifie le client et la facture par identifiant stable et relit la version actuelle.
2. TRINITY propose une modification structurée de lignes en cents, conserve la transcription et montre l'ancien et le nouveau sous-total. Toute ambiguïté sur l'adresse, les taxes ou le destinataire arrête l'action.
3. Le cockpit enregistre la révision comme **brouillon** avec `request_id`, `expected_version`, acteur, date et journal. Un conflit de version impose une nouvelle lecture. La source privée du dossier (export Invoice Simple vérifié ou saisie vérifiée) est conservée par référence.
4. Une étape future relira le brouillon et demandera une confirmation de Stef liée à l'identifiant et à la version exacts. Un adaptateur d'envoi distinct produira alors PDF et courriel, avec vérification du destinataire et accusé de résultat. Ce code n'a pas encore cette étape.

## API privée disponible après activation

Routes : `POST /api/business/invoice-drafts`, `GET /api/business/invoice-drafts/<id>`, `POST /api/business/invoice-drafts/<id>/revise`. Elles exigent `X-Invoice-Secret` et les variables `S25_INVOICE_API_ENABLED=true`, `S25_INVOICE_API_SECRET`, `S25_INVOICE_DB`. Le fichier SQLite doit être sur un volume privé persistant, sauvegardé et exclu de Git. Ne pas réutiliser le secret du mesh ni mettre des données clients dans `memory/`.

Le corps de création contient `source` (`invoice_simple_export` ou `manual_verified`), `source_ref`, `client_ref`, `actor`, `request_id`, `data: {currency: "CAD", lines: [{description, quantity, unit_cents}]}`. Une révision contient `expected_version`, `actor`, `request_id`, `data` et facultativement `voice_transcript`. Les lignes sont recalculées en cents; les taxes et le destinataire restent `unverified` jusqu'à une vérification indépendante. L'API ne possède aucun endpoint d'approbation ou d'envoi.

## Vérifications nécessaires sur le runtime

- Prouver quelle instance du cockpit reçoit réellement la voix S25 et quel SHA tourne sur Alien/Akash. `build_sha=dev` ne le prouve pas.
- Tester une dictée non sensible de bout en bout avec un identifiant de corrélation, puis relire le brouillon et son journal.
- Obtenir un export autorisé d'Invoice Simple ou une fiche client vérifiée; rapprocher facture, taxes, adresse et paiement avant import. Aucun connecteur Invoice Simple n'a été trouvé dans les outils disponibles; le navigateur Comet n'est pas une preuve d'intégration.
- Définir le mécanisme d'approbation à identité vérifiée et le canal courriel avant de permettre l'envoi; le simple texte de transcription ne vaut pas autorisation.
