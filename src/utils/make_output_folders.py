"""Utility to create output folder structure."""

import logging
from pathlib import Path

outputs_folder = Path(__file__).parent.parent / "outputs"


logger = logging.getLogger(__name__)


def create_output_folders(output_path=outputs_folder):
    """Create output folder structure and log actions."""

    structured_output_folder = output_path / "structured_data"
    structured_queries_folder = structured_output_folder / "queries"
    structured_data_folder = structured_output_folder / "data"
    structured_charts_folder = structured_output_folder / "charts"

    for folder in [
        output_path,
        structured_output_folder,
        structured_queries_folder,
        structured_data_folder,
        structured_charts_folder,
    ]:
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            logger.info("Created folder: %s", folder)
        else:
            logger.info("Folder already exists: %s", folder)
