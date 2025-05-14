import os
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# تنظیمات بات
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))


# ساخت رشته اتصال به PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')

# تنظیمات دیگر
WEBHOOK_URL = os.getenv('WEBHOOK_URL', None)
PORT = int(os.getenv('PORT', 8443))