import logging

from .handlers import build_application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    application = build_application()
    logger.info("GGBH Speed2Lead bot starting (long polling)...")
    application.run_polling()


if __name__ == "__main__":
    main()
