"""Bot application"""
import logging
import os

# telegram core bot api extension
from telegram.ext import ApplicationBuilder, MessageHandler, filters

# get bot modes
from . import BotMode

# get bot handlers
from .handlers import (
    extract_from_animation,
    extract_from_audio,
    extract_from_document,
    extract_from_video,
    on_bot_shutdown,
    on_bot_start,
)

log = logging.getLogger(__name__)


def start_bot(mode: int = BotMode.WEBHOOK) -> None:
    """Starts the bot

    Args:
        mode (int, optional): bot mode. Defaults to BotMode.POLLING.
    """
    application = (
        ApplicationBuilder()
        .token(os.environ["TOKEN"])
        .post_init(on_bot_start)
        .post_shutdown(on_bot_shutdown)
        .build()
    )

    # handle documents
    application.add_handler(
        MessageHandler(
            filters=filters.Document.ALL,
            callback=extract_from_document,
            block=False,
        )
    )

    # handle animation
    application.add_handler(
        MessageHandler(
            filters=filters.ANIMATION,
            callback=extract_from_animation,
            block=False,
        )
    )

    # handle audio
    application.add_handler(
        MessageHandler(
            filters=filters.AUDIO,
            callback=extract_from_audio,
            block=False,
        )
    )

    # handle video
    application.add_handler(
        MessageHandler(
            filters=filters.VIDEO,
            callback=extract_from_video,
            block=False,
        )
    )

    if os.environ.get("HOOK_URL") and mode == BotMode.WEBHOOK:
        log.info("Running in webhook mode!")
        webhook_url = f'https://{os.environ["HOOK_URL"]}/{os.environ["TOKEN"]}'
        webhook_port = int(os.environ.get("PORT", "8443"))
        log.info("Webhook URL: %s.", webhook_url)
        log.info("Webhook port: %s.", webhook_port)
        application.run_webhook(
            listen="0.0.0.0",
            port=webhook_port,
            url_path=os.environ["TOKEN"],
            webhook_url=webhook_url,
        )
    else:
        log.info("Running in polling mode!")
        application.run_polling()
