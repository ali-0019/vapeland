from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler , filters
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import logging
from database.db_handler import get_db
from database.db_operations import (
    get_items_by_type,get_items
)
from database.models import (
    ItemType,ContentStatus,ItemType
                             )


from utils.buttons import (
    create_main_menu_buttons,  create_search_buttons, create_contact_buttons,
    create_cancel_button, create_back_to_main_button
)
from utils.callback_handlers import (
    cancel_callback
)
SEARCH = range(1)

# Search callback handler - start conversation
async def search_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation for product search."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً نام محصول مورد نظر خود را وارد کنید:",
        reply_markup=create_cancel_button()
    )
    
    return SEARCH
# Search message handler - search for products
async def search_message(update: Update, context: CallbackContext) -> int:
    """Search for products based on user input."""
    query = update.message.text
    db = next(get_db())
    items = get_items(db)

    if not items:
        await update.message.reply_text("متاسفانه محصولی با این نام یافت نشد.")
        return ConversationHandler.END

    # Create keyboard layout with found items
    keyboard = []
    
    # Convert the SQLAlchemy result to a list of items
    items_dict = [
        {
            "item_id": str(item.item_id),
            "name": item.name,
            "type": ItemType(item.type),
        } for item in items
    ]
    logging.info(f"Items: {str(items_dict)}")
    for item in items_dict:
        logging.info(f"Item: {str(item)}")
        # Search for items containing the query in their name
        if query.lower() in item["name"].lower():
            type = item["type"].value
            item_id = item["item_id"]
            keyboard.append([
                InlineKeyboardButton(
                    f"{item['name']}",
                    callback_data=f"item_{type}_{item_id}"
                ),
            ])
    logging.info(f"Keyboard: {str(keyboard)}")
    # If no items were found, send a message and end the conversation
    if not keyboard:
        await update.message.reply_text("متاسفانه محصولی با این نام یافت نشد.")
        return ConversationHandler.END
    
    await context.bot.send_message(
        text = "لطفاً محصول مورد نظر خود را از لیست زیر انتخاب کنید:",
        chat_id=update.effective_chat.id,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    # Add a back button to the keyboard
    keyboard.append([
        InlineKeyboardButton(
            text="بازگشت",
            callback_data="main_menu"
        )
    ])
    return ConversationHandler.END

# Search cancel callback handler - cancel conversation
async def search_cancel_callback(update: Update, context: CallbackContext) -> int:
    """Cancel current conversation and return to main menu."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "عملیات لغو شد. به منوی اصلی بازگشتید.",
        reply_markup=create_main_menu_buttons()
    )
    return ConversationHandler.END
# Register search callback handlers
def register_search_callback_handlers(application: Application) -> None:
    """Register search callback handlers."""
    search_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(search_callback, pattern='^search$')],
        states={
            SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_message),
            ]
        },
        fallbacks=[
            CallbackQueryHandler(search_cancel_callback, pattern='^cancel$'),
            CallbackQueryHandler(cancel_callback, pattern='^main_menu$')
        ]
    )
    application.add_handler(search_conv_handler)
