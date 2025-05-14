import logging
from telegram import Update
from telegram.ext import CallbackContext

# تنظیم لاگینگ
logger = logging.getLogger(__name__)

async def error_handler(update: Update, context: CallbackContext) -> None:
    """مدیریت خطاها"""
    await logger.warning(f'Update {update} caused error {context.error}')