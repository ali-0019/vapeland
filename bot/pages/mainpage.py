import logging

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ContextTypes
from utils.buttons import create_main_menu_buttons
from pages.create_user import check_and_create_user

# متن خوش‌آمدگویی
WELCOME_MESSAGE = """
🌟 به فروشگاه ویپ لند خوش آمدید! 🌟

ما ارائه دهنده انواع دستگاه‌های ویپ، لیکوئیدها و لوازم جانبی هستیم.
برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:
"""

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """فرمان شروع برای معرفی بات و نمایش منوی اصلی"""

    # بررسی و ایجاد کاربر جدید
    await check_and_create_user(update, context)
    
    
    
    reply_markup=create_main_menu_buttons()
    await context.bot.send_message(chat_id=update.effective_chat.id,text=WELCOME_MESSAGE, reply_markup=reply_markup)