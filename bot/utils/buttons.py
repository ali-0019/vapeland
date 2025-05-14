from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional

def create_main_menu_buttons():
    """Create main menu buttons."""
    keyboard = [
        [InlineKeyboardButton("🛠️ دستگاه‌ها", callback_data="devices")],
        [InlineKeyboardButton("💧 لیکوئیدها", callback_data="liquids")],
        [InlineKeyboardButton("❓ سوالات فنی", callback_data="tech")],
        [InlineKeyboardButton("🔍 جستجوی محصولات", callback_data="search")],
        [InlineKeyboardButton("📞 تماس با ما", callback_data="contact_us")]
    ]
    return InlineKeyboardMarkup(keyboard)

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
        [InlineKeyboardButton("سالت نیکوتین", callback_data="liquids_salt")],
        [InlineKeyboardButton("جویس", callback_data="liquids_juice")],
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
    if category.startswith("devices"):
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به دسته‌بندی دستگاه‌ها", callback_data="devices")])
    elif category.startswith("liquids"):
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به دسته‌بندی لیکوئیدها", callback_data="liquids")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

def create_item_detail_buttons(item_id: str, target_type: str) -> InlineKeyboardMarkup:
    """Create buttons for item detail view."""
    keyboard = [
        [
            InlineKeyboardButton("⭐ امتیاز 1", callback_data=f"rate_{target_type}_{item_id}_1"),
            InlineKeyboardButton("⭐⭐ امتیاز 2", callback_data=f"rate_{target_type}_{item_id}_2"),
        ],
        [
            InlineKeyboardButton("⭐⭐⭐ امتیاز 3", callback_data=f"rate_{target_type}_{item_id}_3"),
            InlineKeyboardButton("⭐⭐⭐⭐ امتیاز 4", callback_data=f"rate_{target_type}_{item_id}_4"),
            InlineKeyboardButton("⭐⭐⭐⭐⭐ امتیاز 5", callback_data=f"rate_{target_type}_{item_id}_5"),
        ],
        [InlineKeyboardButton("💬 افزودن کامنت", callback_data=f"comment_{target_type}_{item_id}")],
        [InlineKeyboardButton("📄 نمایش بیشتر کامنت‌ها", callback_data=f"more_comments_{target_type}_{item_id}")],
    ]
    
    # Back button based on target type
    if target_type == "item":
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به لیست محصولات", callback_data="back_to_items")])
    elif target_type == "question":
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به سوالات فنی", callback_data="tech")])
    
    return InlineKeyboardMarkup(keyboard)

def create_comment_buttons(comment_id: str, has_replies: bool = False) -> InlineKeyboardMarkup:
    """Create buttons for comment interaction."""
    keyboard = [
        [InlineKeyboardButton("💬 پاسخ به این نظر", callback_data=f"reply_comment_{comment_id}")]
    ]
    
    if has_replies:
        keyboard.append([InlineKeyboardButton("👁️ نمایش پاسخ‌ها", callback_data=f"show_replies_{comment_id}")])
    
    return InlineKeyboardMarkup(keyboard)

def create_tech_question_buttons(questions: List[Dict[str, Any]], page: int = 0, questions_per_page: int = 5) -> InlineKeyboardMarkup:
    """Create buttons for technical questions with pagination."""
    start_idx = page * questions_per_page
    end_idx = min(start_idx + questions_per_page, len(questions))
    current_questions = questions[start_idx:end_idx]
    
    keyboard = []
    for question in current_questions:
        question_id = question.get("question_id")
        text = question.get("text")
        # Truncate text if too long
        if len(text) > 30:
            text = text[:27] + "..."
        keyboard.append([InlineKeyboardButton(text, callback_data=f"question_{question_id}")])
    
    # Pagination buttons
    pagination = []
    if page > 0:
        pagination.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"tech_page_{page-1}"))
    if end_idx < len(questions):
        pagination.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"tech_page_{page+1}"))
    
    if pagination:
        keyboard.append(pagination)
    
    # Add new question button
    keyboard.append([InlineKeyboardButton("❓ افزودن سوال جدید", callback_data="add_question")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
    
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