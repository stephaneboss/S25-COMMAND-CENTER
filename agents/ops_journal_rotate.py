#!/usr/bin/env python3
"""
S25 Ops Journal Rotation
========================
Le journal du mesh, memory/command_mesh/ops_journal.jsonl, est append-only et
n'a jamais eu de rotation : il a atteint 496 Mo, au-dela de la limite de 100 Mo
par fichier de GitHub. Un seul fichier trop gros fait rejeter le push complet,
ce qui bloque aussi la sauvegarde de l'etat de trading.

Ce script archive le journal courant et repart d'un fichier vide, sans jamais
rien supprimer. Les archives sont compressees et restent sur le disque, hors du
depot.

Strategie : copy-truncate. Le contenu est copie dans l'archive, puis le fichier
courant est tronque en place, ce qui preserve son inode. Les processus qui le
tiennent ouvert continuent d'ecrire dans le meme fichier au lieu d'alimenter un
fichier orphelin. La contrepartie connue est qu'une ligne ecrite entre la copie
et la troncature peut etre perdue ; c'est un journal d'observabilite, pas un
registre comptable, et le compromis est volontaire.

Declenchement : taille au-dela du seuil, ou changement de mois.

Cron suggere (une fois par jour, 04:10) :
    10 4 * * * cd /home/alienstef/S25-COMMAND-CENTER && .venv/bin/python -m agents.ops_journal_rotate >> /tmp/ops_journal_rotate.log 2>&1
"""
from __future__ import annotations

import gzip
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("s25.ops_journal_rotate")

REPO = Path(__file__).resolve().parent.parent
JOURNAL = REPO / "memory" / "command_mesh" / "ops_journal.jsonl"
ARCHIVE_DIR = REPO / "memory" / "command_mesh" / "archive"

# Seuil de declenchement. Tres en dessous de la limite de 100 Mo de GitHub, pour
# qu'un journal en croissance rapide ne puisse pas franchir la limite entre deux
# passages du cron.
MAX_BYTES = 32 * 1024 * 1024


def month_tag(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m")


def archive_path(tag: str) -> Path:
    """Nom d'archive libre, suffixe numerique si le mois a deja une archive."""
    base = ARCHIVE_DIR / ("ops_journal-%s.jsonl.gz" % tag)
    if not base.exists():
        return base
    n = 2
    while True:
        candidate = ARCHIVE_DIR / ("ops_journal-%s.%d.jsonl.gz" % (tag, n))
        if not candidate.exists():
            return candidate
        n += 1


def should_rotate(size: int, mtime: float) -> tuple[bool, str]:
    if size >= MAX_BYTES:
        return True, "taille %.1f Mo >= seuil %.1f Mo" % (
            size / 1048576, MAX_BYTES / 1048576)
    now_tag = month_tag(datetime.now(timezone.utc).timestamp())
    file_tag = month_tag(mtime)
    if file_tag != now_tag:
        return True, "changement de mois (%s -> %s)" % (file_tag, now_tag)
    return False, ""


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    if not JOURNAL.exists():
        logger.info("pas de journal a %s, rien a faire", JOURNAL)
        return 0

    stat = JOURNAL.stat()
    rotate, reason = should_rotate(stat.st_size, stat.st_mtime)
    if not rotate:
        logger.info("journal a %.1f Mo, sous le seuil, pas de rotation",
                    stat.st_size / 1048576)
        return 0

    logger.info("rotation declenchee : %s", reason)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    target = archive_path(month_tag(stat.st_mtime))
    partial = target.with_suffix(target.suffix + ".partial")

    # Copie compressee d'abord. Tant qu'elle n'est pas terminee et renommee,
    # le journal courant reste intact : une interruption ne perd rien.
    try:
        with open(JOURNAL, "rb") as src, gzip.open(partial, "wb") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        os.replace(partial, target)
    except Exception:
        logger.exception("archivage echoue, journal laisse intact")
        if partial.exists():
            try:
                partial.unlink()
            except OSError:
                pass
        return 1

    archived = target.stat().st_size
    logger.info("archive ecrite : %s (%.1f Mo compresses)",
                target.name, archived / 1048576)

    # Troncature en place seulement apres une archive confirmee sur le disque.
    try:
        with open(JOURNAL, "r+b") as fh:
            fh.truncate(0)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:
        logger.exception("troncature echouee, l'archive est conservee")
        return 2

    logger.info("journal remis a zero, %.1f Mo liberes", stat.st_size / 1048576)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
