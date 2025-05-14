from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext ,ContextTypes
from utils.buttons import create_main_menu_buttons

# متن خوش‌آمدگویی
WELCOME_MESSAGE = """
🌟 به فروشگاه ویپ لند خوش آمدید! 🌟

ما ارائه دهنده انواع دستگاه‌های ویپ، لیکوئیدها و لوازم جانبی هستیم.
برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """فرمان شروع برای معرفی بات و نمایش منوی اصلی"""
    # Create a 2D array of buttons for InlineKeyboardMarkup
    replymarkup = create_main_menu_buttons()
    await context.bot.send_message(chat_id=update.effective_chat.id,text=WELCOME_MESSAGE, reply_markup=replymarkup)