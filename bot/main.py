import logging
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, filters , ApplicationBuilder
import os
from dotenv import load_dotenv

# ماژول‌های داخلی
from pages.mainpage import start
from utils.error_handlers import error_handler
from utils.callback_handlers import register_callback_handlers
from utils.items.item_handlers import register_item_callback_handlers
from utils.questions.question_handlers import register_questions_callback_handlers
from pages.create_user import register_username_handlers
from pages.search import register_search_callback_handlers
from pages.contact_us import register_contact_us_handlers


# تنظیم لاگینگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# بارگذاری متغیرهای محیطی
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

def main() -> None:
    """راه‌اندازی بات"""
    # ایجاد اپلیکیشن
    application = ApplicationBuilder().token(TOKEN).build()

    # ثبت هندلرها
    register_username_handlers(application)
    register_callback_handlers(application)
    register_item_callback_handlers(application)
    register_questions_callback_handlers(application)
    register_search_callback_handlers(application)
    register_contact_us_handlers(application)
    
    
    application.add_handler(CommandHandler("start", start))
    
    # ثبت هندلر خطا
    application.add_error_handler(error_handler)

    # شروع بات
    application.run_polling()

if __name__ == '__main__':
    main()