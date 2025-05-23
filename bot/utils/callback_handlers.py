from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler , filters
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import logging
from database.db_handler import get_db
from database.db_operations import (
    create_user, get_items_by_type, get_item, get_comments_by_item, get_comment_replies,
    get_top_tech_questions, get_tech_question, get_question_replies, create_item_rating, create_question_rating,
    get_user, create_item, create_comment, create_tech_question, create_comment_reply,
    create_question_reply
)
from database.models import ItemType, ContentStatus, TargetType
from utils.buttons import (
    create_main_menu_buttons,  create_search_buttons, create_contact_buttons,
    create_cancel_button, create_back_to_main_button
)

# States for conversation handlers
COMMENT, REPLY, QUESTION, SEARCH, CONTACT = range(5)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Main menu callback handler
async def main_menu_callback(update: Update, context: CallbackContext) -> None:
    """Handle main menu callback."""
    query = update.callback_query
    await query.answer()
    db = next(get_db())
    # Check if user exists in database
    user = get_user(db,query.from_user.id)
    
    # If user doesn't exist, create new user
    if not user:
        try:
            await create_user(
                telegram_id=query.from_user.id,
                username=query.from_user.username,
                first_name=query.from_user.first_name,
                last_name=query.from_user.last_name
            )
            logger.info(f"Created new user: {query.from_user.id}")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await query.message.reply_text("خطا در ثبت کاربر. لطفا دوباره تلاش کنید.")
            return
    await query.edit_message_text(
    """
    🌟 به فروشگاه ویپ لند خوش آمدید! 🌟

ما ارائه دهنده انواع دستگاه‌های ویپ، لیکوئیدها و لوازم جانبی هستیم.
برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:
    """,
        reply_markup=create_main_menu_buttons()
    )



# Cancel callback handler
async def cancel_callback(update: Update, context: CallbackContext) -> int:
    """Cancel current conversation and return to main menu."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "عملیات لغو شد. به منوی اصلی بازگشتید.",
        reply_markup=create_main_menu_buttons()
    )
    
    return ConversationHandler.END



# Register all callback handlers
def register_callback_handlers(application):
    """Register all callback query handlers."""
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(cancel_callback, pattern="^cancel$"))

