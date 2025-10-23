"""Main entry point for generating the newsletter."""
import os
import argparse
import logging
# import ssl
# import urllib3
# import requests
from pathlib import Path
from src.agents.newsletter_crew_v1.crew import NewsletterCrew
from src.utils.make_output_folders import create_output_folders

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "newsletter.log"

# # Disable TLS verification for local runs where MITM risk is acceptable.
# ssl._create_default_https_context = ssl._create_unverified_context
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# _original_session_request = requests.Session.request


# def _unverified_request(self, method, url, *args, **kwargs):
#     """Force requests to skip certificate verification globally."""

#     kwargs.setdefault("verify", False)
#     return _original_session_request(self, method, url, *args, **kwargs)


# requests.Session.request = _unverified_request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

LANG_ALIASES = {
    "english": "en-US",
    "en": "en-US",
    "en-us": "en-US",
    "es": "es-CL",
    "spanish": "es-CL",
    "es-cl": "es-CL",
    "pt": "pt-BR",
    "portuguese": "pt-BR",
    "pt-br": "pt-BR",
}

def normalize_lang(s: str | None, default: str = "es-CL") -> str:
    if not s:
        return default
    key = s.strip().lower()
    return LANG_ALIASES.get(key, s)

if __name__ == "__main__":
    logger.info("Starting newsletter generation process.")

    # CLI flag con fallback a .env y default
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", help="Output language (e.g., en-US, es-CL, pt-BR, 'english')",
                        default=os.getenv("NEWSLETTER_LANGUAGE", "es-CL"))
    args = parser.parse_args()
    language = normalize_lang(args.language)

    crew = NewsletterCrew().crew()

    output_folder = Path("./output")
    create_output_folders(output_folder)
    logger.info("Output folders ensured at %s", output_folder)
    logger.info("Using language=%s", language)

    try:
        result = crew.kickoff(
            inputs={
                "newsletter_topic": "Inflación en Brasil y su impacto en las pequeñas empresas",
                "output_folder": str(output_folder),
                "query": "Taxa de água e esgoto no cálculo do IPCA",
                "language": language,  # <- clave
            }
        )
        html = str(result)
        with open("newsletter.html", "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("✅ Newsletter generated: newsletter.html (language=%s)", language)
    except Exception as e:
        logger.exception("Newsletter generation failed: %s", e)