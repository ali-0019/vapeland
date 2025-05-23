from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional

def create_main_menu_buttons():
    """Create main menu buttons."""
    keyboard = [
        [InlineKeyboardButton("🛠️ دستگاه‌ها", callback_data="devices")],
        [InlineKeyboardButton("💧 لیکوئیدها", callback_data="liquids")],
        [InlineKeyboardButton("❓ سوالات فنی", callback_data="tech")],
        [InlineKeyboardButton("🔍 جستجوی محصولات", callback_data="search")],
        [InlineKeyboardButton("📞 تماس با ما", callback_data="contact_us")],
        [InlineKeyboardButton("👤 نام کاربری", callback_data="user_name")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_username_buttons() -> InlineKeyboardMarkup:
    """Create buttons for username options."""
    keyboard = [
        [InlineKeyboardButton("🆔 نام کاربری", callback_data="get_username")],
        [InlineKeyboardButton("✏️ تغییر نام کاربری", callback_data="change_username")],
        [InlineKeyboardButton("🏆 امتیاز شما", callback_data="user_score")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_search_buttons() -> InlineKeyboardMarkup:
    """Create search buttons."""
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_contact_buttons() -> InlineKeyboardMarkup:
    """Create contact buttons."""
    keyboard = [
        [InlineKeyboardButton("📝 ارسال پیام", callback_data="send_message")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_cancel_button() -> InlineKeyboardMarkup:
    """Create a cancel button for multi-step operations."""
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data="cancel")]]
    return InlineKeyboardMarkup(keyboard)

def create_back_to_main_button() -> InlineKeyboardMarkup:
    """Create a back to main menu button."""
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)
