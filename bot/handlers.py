"""Bot handlers"""
import logging
import sys

from pathlib import Path
from typing import Optional

# extract exif
import exiftool

# work with json
import orjson

# telegram core bot api
from telegram import Animation, Audio, Document, Update, Video

# telegram exceptions
from telegram.error import BadRequest

# telegram core bot api extension
from telegram.ext import Application, CallbackContext

# telegram helpers
from telegram.helpers import escape_markdown

log = logging.getLogger(__name__)

ROOT_FOLDER: str = ".cache"


class UpdateAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return "[%d] %s" % (self.extra["update_id"], msg), kwargs


def check_root_folder():
    log.debug("Checking a root folder...")
    if not Path(ROOT_FOLDER).exists():
        try:
            log.debug("The root folder does not exist, creating it...")
            Path(ROOT_FOLDER).mkdir()
        except IOError:
            log.critical("Couldn't create a root folder!")
            log.info("Exiting...")
            sys.exit(1)


async def on_bot_start(_: Application) -> None:
    log.info("Starting the bot...")
    check_root_folder()


async def on_bot_shutdown(_: Application) -> None:
    log.info("Shutting down the bot...")


class EXIFExtractor:
    def __init__(
        self,
        update: Update,
        context: CallbackContext,
        kind: str,
        document: Audio | Animation | Document | Video,
        root_folder: str = ROOT_FOLDER,
    ) -> None:
        self.update = update
        self.context = context
        self.kind = kind
        self.document = document
        self.log = UpdateAdapter(log, {"update_id": update.update_id})
        self.root_folder = Path(root_folder)

    async def extract_exif(self, file: Path) -> Optional[bytes]:
        with exiftool.ExifToolHelper() as helper:
            if metadata := helper.get_metadata(str(file.resolve())):
                return orjson.dumps(
                    metadata[0],
                    option=orjson.OPT_APPEND_NEWLINE | orjson.OPT_INDENT_2,
                )

    async def run(self) -> None:
        self.log.info("Extracting file...")
        file_name = self.document.file_name or self.document.file_id
        file_folder = self.root_folder / str(self.update.update_id)
        file_path = file_folder / file_name
        try:
            file = await self.document.get_file()
            self.log.debug("Extracted file!")
            file_folder.mkdir()
            await file.download_to_drive(file_path)
            self.log.info("Saved file %r to drive.", file_name)
            if metadata := await self.extract_exif(file_path):
                self.log.info("Successfully extracted metadata.")
                escaped_metadata = escape_markdown(metadata.decode(), version=2)
                await self.update.effective_message.reply_markdown_v2(
                    text=f"```json\n{escaped_metadata}```",
                    quote=True,
                )
        except IOError:
            self.log.exception("Couldn't create folder or write file.")
        except BadRequest as ex:
            self.log.exception("Bad request: %s.", ex.message)
        except Exception as ex:
            self.log.exception("Exception occured: %s.", ex)
        finally:
            self.log.info("Done. Removing file and folder...")
            file_path.unlink(missing_ok=True)
            if file_folder.exists():
                file_folder.rmdir()
            self.log.info("Removed file and folder.")


async def create_extract_job(
    update: Update,
    context: CallbackContext,
    kind: str,
    document: Audio | Animation | Document | Video,
) -> None:
    await EXIFExtractor(update, context, kind, document).run()


async def extract_from_audio(update: Update, context: CallbackContext):
    if audio := update.effective_message.audio:
        await create_extract_job(update, context, "audio", audio)


async def extract_from_animation(update: Update, context: CallbackContext):
    if animation := update.effective_message.animation:
        await create_extract_job(update, context, "animation", animation)


async def extract_from_video(update: Update, context: CallbackContext):
    if video := update.effective_message.video:
        await create_extract_job(update, context, "video", video)


async def extract_from_document(update: Update, context: CallbackContext):
    if document := update.effective_message.document:
        await create_extract_job(update, context, "document", document)
