from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

LOGGER = logging.getLogger(__name__)


def run_migrations() -> None:
    project_root = Path(__file__).resolve().parents[2]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    LOGGER.info("alembic_upgrade_start target=head")
    command.upgrade(config, "head")
    LOGGER.info("alembic_upgrade_complete target=head")
