from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CallbackContext, CallbackQueryHandler

async def contact_us_callback(update: Update, context: CallbackContext) -> None:
    """Handle contact us callback and display shop information."""
    query = update.callback_query
    await query.answer()
    
    # Shop introduction text
    intro_text = (
        "🏪 *وِیپ لند - VapeLand*\n\n"
        "به فروشگاه وِیپ لند خوش آمدید!\n"
        "ما ارائه دهنده انواع محصولات وِیپ با کیفیت و اصل هستیم.\n"
        "برای ارتباط با ما از طریق یکی از روش‌های زیر اقدام کنید:"
    )
    
    # Create inline keyboard with contact options
    keyboard = [
        [InlineKeyboardButton("🌐 وب‌سایت", url="https://example.com")],
        [InlineKeyboardButton("📱 اینستاگرام", url="https://example.com")],
        [InlineKeyboardButton("📧 ایمیل", url="https://example.com")],
        [InlineKeyboardButton("📞 تماس", callback_data="phone_number")],
        [InlineKeyboardButton("📍 آدرس", callback_data="address")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        intro_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def phone_number_callback(update: Update, context: CallbackContext) -> None:
    """Display phone number information."""
    query = update.callback_query
    await query.answer()
    
    phone_text = (
        "📞 *شماره تماس وِیپ لند*\n\n"
        "تلفن: 021-12345678\n"
        "موبایل: 09123456789\n\n"
        "ساعات پاسخگویی: شنبه تا پنجشنبه از ساعت 10 صبح تا 8 شب"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به اطلاعات تماس", callback_data="contact_us")]
    ]
    
    await query.edit_message_text(
        phone_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def address_callback(update: Update, context: CallbackContext) -> None:
    """Display address information."""
    query = update.callback_query
    await query.answer()
    
    address_text = (
        "📍 *آدرس فروشگاه وِیپ لند*\n\n"
        "تهران، خیابان ولیعصر، نرسیده به میدان ونک، پلاک 123\n\n"
        "کد پستی: 1234567890\n\n"
        "ساعات کاری فروشگاه:\n"
        "شنبه تا پنجشنبه: 10 صبح تا 10 شب\n"
        "جمعه: 12 ظهر تا 8 شب"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به اطلاعات تماس", callback_data="contact_us")]
    ]
    
    await query.edit_message_text(
        address_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

def register_contact_us_handlers(application: Application) -> None:
    """Register contact us related handlers."""
    application.add_handler(CallbackQueryHandler(contact_us_callback, pattern="^contact_us$"))
    application.add_handler(CallbackQueryHandler(phone_number_callback, pattern="^phone_number$"))
    application.add_handler(CallbackQueryHandler(address_callback, pattern="^address$"))