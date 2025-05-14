from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    """منوی اصلی ربات را برمی‌گرداند"""
    keyboard = [
        [InlineKeyboardButton("🛠 دستگاه‌ها", callback_data="devices")],
        [InlineKeyboardButton("💧 لیکوئیدها", callback_data="liquids")],
        [InlineKeyboardButton("❓ سوالات فنی", callback_data="tech")],
        [InlineKeyboardButton("🔍 جستجوی محصولات", callback_data="search")],
        [InlineKeyboardButton("📞 تماس با ما", callback_data="contact_us")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_devices_submenu_keyboard():
    """زیرمنوی دستگاه‌ها را برمی‌گرداند"""
    keyboard = [
        [
            InlineKeyboardButton("دائمی", callback_data="devices_permanent"),
            InlineKeyboardButton("یکبار مصرف", callback_data="devices_disposable")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_liquids_submenu_keyboard():
    """زیرمنوی لیکوئیدها را برمی‌گرداند"""
    keyboard = [
        [
            InlineKeyboardButton("سالت نیکوتین", callback_data="liquids_salt_nicotine"),
            InlineKeyboardButton("جویس", callback_data="liquids_juice")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_items_keyboard(items, item_type, page=0, items_per_page=5):
    """کیبورد لیست محصولات را برمی‌گرداند"""
    keyboard = []
    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(items))
    
    # نمایش محصولات
    for item in items[start_idx:end_idx]:
        stars = "⭐" * int(item.average_rating) + "☆" * (5 - int(item.average_rating))
        button_text = f"{item.name} ({stars} - {item.rating_count} رأی)"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"item_{item.item_id}")])
    
    # دکمه‌های پیمایش
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"{item_type}_page_{page-1}"))
    if end_idx < len(items):
        nav_buttons.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"{item_type}_page_{page+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # دکمه بازگشت
    if item_type.startswith("devices"):
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی دستگاه‌ها", callback_data="devices")])
    elif item_type.startswith("liquids"):
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی لیکوئیدها", callback_data="liquids")])
    
    return InlineKeyboardMarkup(keyboard)

def get_item_detail_keyboard(item_id):
    """کیبورد جزئیات محصول را برمی‌گرداند"""
    keyboard = [
        [
            InlineKeyboardButton("⭐1", callback_data=f"rate_{item_id}_1"),
            InlineKeyboardButton("⭐2", callback_data=f"rate_{item_id}_2"),
            InlineKeyboardButton("⭐3", callback_data=f"rate_{item_id}_3"),
            InlineKeyboardButton("⭐4", callback_data=f"rate_{item_id}_4"),
            InlineKeyboardButton("⭐5", callback_data=f"rate_{item_id}_5")
        ],
        [InlineKeyboardButton("💬 افزودن کامنت", callback_data=f"add_comment_{item_id}")],
        [InlineKeyboardButton("📜 نمایش بیشتر کامنت‌ها", callback_data=f"more_comments_{item_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"back_from_item_{item_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_comment_keyboard(comment_id):
    """کیبورد کامنت را برمی‌گرداند"""
    keyboard = [
        [
            InlineKeyboardButton("👁 نمایش پاسخ‌ها", callback_data=f"show_replies_{comment_id}"),
            InlineKeyboardButton("↩️ پاسخ", callback_data=f"reply_to_{comment_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)