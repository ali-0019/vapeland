from unicodedata import category
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional
from database.db_operations import count_direct_replies_to_comment ,count_sub_replies
from database.db_handler import get_db
from uuid import UUID

def create_device_category_buttons() -> InlineKeyboardMarkup:
    """Create device category buttons."""
    keyboard = [
        [InlineKeyboardButton("دستگاه‌های دائمی", callback_data="devices_permanent")],
        [InlineKeyboardButton("دستگاه‌های یکبارمصرف", callback_data="devices_disposable")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_liquid_category_buttons() -> InlineKeyboardMarkup:
    """Create liquid category buttons."""
    keyboard = [
        [InlineKeyboardButton("سالت نیکوتین", callback_data="liquid_salt")],
        [InlineKeyboardButton("جویس", callback_data="liquid_juice")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_item_list_buttons(items: List[Dict[str, Any]], category: str, page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Create buttons for item list with pagination."""
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(items))
    current_items = items[start_idx:end_idx]
    
    keyboard = []
    for item in current_items:
        item_id = item.get("item_id")
        name = item.get("name")
        rating = item.get("average_rating", 0)
        stars = "★" * int(rating) + "☆" * (5 - int(rating))
        keyboard.append([InlineKeyboardButton(f"{name} ({stars})", callback_data=f"item_{category}_{item_id}")])
    
    # Pagination buttons
    pagination = []
    if page > 0:
        pagination.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"page_{category}_{page-1}"))
    if end_idx < len(items):
        pagination.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"page_{category}_{page+1}"))
    
    if pagination:
        keyboard.append(pagination)
    # Back button
    if category == "devices_permanent":
        keyboard.append([InlineKeyboardButton("افزودن دستگاه دائمی", callback_data="add_item_DEVICE_PERMANENT")])
    elif category == "devices_disposable":
        keyboard.append([InlineKeyboardButton("افزودن دستگاه یکبار مصرف", callback_data="add_item_DEVICE_DISPOSABLE")])
    elif category == "liquid_salt":
        keyboard.append([InlineKeyboardButton("افزودن سالت نیکوتین", callback_data="add_item_LIQUID_SALT")])
    elif category == "liquid_juice":
        keyboard.append([InlineKeyboardButton("افزودن جویس", callback_data="add_item_LIQUID_JUICE")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به دسته‌بندی دستگاه‌ها", callback_data="devices")])
 
    return InlineKeyboardMarkup(keyboard)

def create_item_detail_buttons(item_id: str, target_type: str,category) -> InlineKeyboardMarkup:
    """Create buttons for item detail view."""
    keyboard = [
        [
            InlineKeyboardButton("⭐ امتیاز 1", callback_data=f"rate_item_{target_type}_{item_id}_1"),
            InlineKeyboardButton("⭐⭐ امتیاز 2", callback_data=f"rate_item_{target_type}_{item_id}_2"),
        ],
        [
            InlineKeyboardButton("⭐⭐⭐ امتیاز 3", callback_data=f"rate_item_{target_type}_{item_id}_3"),
            InlineKeyboardButton("⭐⭐⭐⭐ امتیاز 4", callback_data=f"rate_item_{target_type}_{item_id}_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐ امتیاز 5", callback_data=f"rate_item_{target_type}_{item_id}_5"),
        ],
        [InlineKeyboardButton("💬 مشاهده نظرات", callback_data=f"comments_{item_id}")],
        [InlineKeyboardButton("🔙 بازگشت به لیست محصولات", callback_data=f"{target_type}_{category}")]
    ]
    
    return InlineKeyboardMarkup(keyboard)
 
def create_item_comment_buttons(item_id: str, target_type: str):
    keyboards = [
        [InlineKeyboardButton("💬 افزودن کامنت", callback_data=f"comment_{target_type}_{item_id}")],
        [InlineKeyboardButton("📄 نمایش بیشتر کامنت‌ها", callback_data=f"more_comments_{target_type}_{item_id}")]
        [InlineKeyboardButton("بستن", callback_data="close_menu")]
    ] 

def create_comment_buttons(comment_id: str, has_replies: bool = False) -> InlineKeyboardMarkup:
    """Create buttons for comment interaction."""
    keyboard = [
        [InlineKeyboardButton("💬 پاسخ به این نظر", callback_data=f"reply_comment_{comment_id}")]
    ]
    
    if has_replies:
        keyboard.append([InlineKeyboardButton("👁️ نمایش پاسخ‌ها", callback_data=f"show_replies_{comment_id}_ROOT_0")])
    
    return InlineKeyboardMarkup(keyboard)
