import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from database.db_handler import get_db
from database.db_operations import create_user, get_user, update_user
from utils.buttons import create_username_buttons
# Define conversation states
USERNAME = range(1)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

async def check_and_create_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user exists in database and create if not. Returns True if successful."""
    db = next(get_db())
    user_id = update.effective_user.id
    user = get_user(db, user_id)
    
    # If user doesn't exist, create new user
    if not user:
        try:
            create_user(
                db,
                user_id=user_id,
            )
            logger.info(f"Created new user: {user_id}")
            await start_username_form(update, context)
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            await update.message.reply_text("خطا در ثبت کاربر. لطفا دوباره تلاش کنید.")
            return False
    return True

async def username_section(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the username section."""
    query = update.callback_query
    await query.answer()

    # Get user data from database
    db = next(get_db())
    user = get_user(db, update.effective_user.id)

    # Format user rank score if available
    # Format user information with proper formatting
    username = user.username if user and user.username else '❌ تنظیم نشده'
    rank_display = f"\n🏆 امتیاز رتبه: {user.rank_score}" if user and hasattr(user, 'rank_score') else ""

    # Create a nicely formatted message
    message = (
        f"👤 نام کاربری: {username}\n\n"
        f"🆔 شناسه کاربری: {update.effective_user.id}\n"
        f"{rank_display}"
    )

    await query.edit_message_text(
        text=message,
        reply_markup=create_username_buttons()
    )
    
# Username form handlers
async def start_username_form(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the username form conversation."""
    # Check if user already has a username
    db = next(get_db())
    user_id = update.effective_user.id
    user = get_user(db, user_id)
    
    if user and user.username:
        await context.bot.send_message(
            text = f"نام کاربری شما در حال حاضر '{user.username}' است. آیا می‌خواهید آن را تغییر دهید؟",
            chat_id=update.effective_chat.id,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("بله، تغییر دهید", callback_data="change_username")],
                [InlineKeyboardButton("خیر، بازگشت", callback_data="cancel_username")]
            ])
        )
        return USERNAME
    
    await context.bot.send_message(
        text = ("لطفاً نام کاربری خود را وارد کنید.\n"
        "این نام در نظرات و تعاملات شما نمایش داده خواهد شد."),
        chat_id=update.effective_chat.id,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("لغو", callback_data="cancel_username")]])
    )
    return USERNAME

async def change_username_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the change username callback."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً نام کاربری جدید خود را وارد کنید.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("لغو", callback_data="cancel_username")]])
    )
    return USERNAME

async def process_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the username input."""
    username = update.message.text.strip()
    
    # Validate username
    if len(username) < 3:
        await update.message.reply_text(
            "نام کاربری باید حداقل 3 کاراکتر باشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("لغو", callback_data="cancel_username")]])
        )
        return USERNAME
    
    if len(username) > 30:
        await update.message.reply_text(
            "نام کاربری نمی‌تواند بیشتر از 30 کاراکتر باشد. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("لغو", callback_data="cancel_username")]])
        )
        return USERNAME
    
    # Save username to database
    try:
        db = next(get_db())
        user_id = update.effective_user.id
        update_user(db, user_id, username=username)
        
        await update.message.reply_text(
            f"نام کاربری شما با موفقیت به '{username}' تغییر یافت.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="main_menu")]])
        )
        
        logger.info(f"User {user_id} set username to '{username}'")
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error updating username: {e}")
        await update.message.reply_text(
            "خطا در ثبت نام کاربری. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("لغو", callback_data="cancel_username")]])
        )
        return USERNAME

async def cancel_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the username form."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "تغییر نام کاربری لغو شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="main_menu")]])
        )
    else:
        await update.message.reply_text(
            "تغییر نام کاربری لغو شد.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="main_menu")]])
        )
    
    return ConversationHandler.END

async def user_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the user's score."""
    query = update.callback_query
    await query.answer()

    # Get user data from database
    db = next(get_db())
    user = get_user(db, update.effective_user.id)

    # Format user rank score if available
    rank_display = f"\n🏆 امتیاز رتبه: {user.rank_score}" if user and hasattr(user, 'rank_score') else ""

    # Create a nicely formatted message
    message = (
        f"👤 نام کاربری: {user.username}\n\n"
        f"🆔 شناسه کاربری: {update.effective_user.id}\n"
        f"💰 امتیاز شما: {user.rank_score}\n"
        f"{rank_display}"
    )

    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="main_menu")]])
    )

def register_username_handlers(application):
    """Register handlers for username conversation."""
    username_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_username_form,"get_username"),CallbackQueryHandler(change_username_callback, pattern="change_username"),],
        states={
            USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_username),
                CallbackQueryHandler(change_username_callback, pattern="change_username"),
                CallbackQueryHandler(cancel_username, pattern="cancel_username")
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_username, pattern="cancel_username")],
        per_message=False
    )
    
    application.add_handler(username_conv_handler)
    application.add_handler(CallbackQueryHandler(username_section, pattern="user_name"))
    application.add_handler(CallbackQueryHandler(user_score, pattern="user_score"))