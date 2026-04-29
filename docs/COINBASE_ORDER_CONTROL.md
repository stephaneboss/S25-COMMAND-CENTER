# Coinbase Order Control Documentation

TRINITY can already execute trades using `trade_execute`, but it lacks the ability to cancel or replace orders due to missing order IDs and endpoints.

## Protocole de Test Réel

- **Snapshot**: Capture l'état actuel des ordres ouverts.
- **List Open DOGE Orders**: Liste tous les ordres ouverts pour la paire DOGE.
- **Cancel Order ID Explicite**: Annule un ordre spécifique en utilisant son ID.
- **Vérifier Hold Libéré**: Vérifie que le hold associé à l'ordre a été libéré après annulation.
- **Remplacer Petit Ordre Vocalement**: Remplace un petit ordre en vocalisant les nouvelles paramètres de l'ordre.
- **Vérifier Hold Recréé**: Vérifie que le hold a été recréé pour l'ordre remplacement.
- **Journaliser Attribution**: Enregistre l'attribution des modifications d'ordres.

## Exigences Sécurité

- Audit avant et après les opérations de contrôle d'ordres.
- Vérification obligatoire de l'ID de l'ordre avant annulation.
- Confirmation opérateur requise pour annuler tous les ordres d'une paire spécifique avec `cancel_all_for_symbol`.
- Vérification de la cancellation avant remplacement de l'ordre.

## Fonctions à Implémenter

- `list_open_orders(symbol)`: Liste tous les ordres ouverts pour une paire spécifique.
- `cancel_order(order_id)`: Annule un ordre en utilisant son ID.
- `cancel_all_for_symbol(symbol)`: Annule tous les ordres d'une paire spécifique avec confirmation opérateur.
- `replace_order(order_id, new_params)`: Remplace un ordre existant en utilisant son ID et de nouveaux paramètres.
