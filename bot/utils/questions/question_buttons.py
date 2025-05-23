from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional

def create_tech_question_buttons(questions: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های مربوط به سوالات فنی
    
    Args:
        questions: لیست سوالات فنی (حداکثر 10 سوال)
        
    Returns:
        دکمه‌های اینلاین برای نمایش سوالات
    """
    keyboard = []
    
    # نمایش سوالات به صورت دکمه
    for question in questions[:10]:  # حداکثر 10 سوال
        # نمایش متن سوال و امتیاز آن
        rating_stars = "★" * int(question["average_rating"]) + "☆" * (5 - int(question["average_rating"]))
        button_text = f"{question['text'][:30]}... ({rating_stars})"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text, 
                callback_data=f"question_{question['question_id']}"
            )
        ])
    
    # دکمه‌های اضافی
    extra_buttons = []
    
    # دکمه نمایش سوالات بیشتر (اگر بیش از 10 سوال وجود داشته باشد)
    if len(questions) > 10:
        extra_buttons.append(
            InlineKeyboardButton("📄 نمایش سوالات بیشتر", callback_data="more_questions_10")
        )
    
    # دکمه افزودن سوال جدید
    extra_buttons.append(
        InlineKeyboardButton("❓ افزودن سوال جدید", callback_data="add_question")
    )
    
    # اضافه کردن دکمه‌های اضافی به کیبورد
    if extra_buttons:
        keyboard.append(extra_buttons)
    
    # دکمه بازگشت به منوی اصلی
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_question_detail_buttons(question_id: str) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های مربوط به جزئیات سوال
    
    Args:
        question_id: شناسه سوال
        
    Returns:
        دکمه‌های اینلاین برای نمایش جزئیات سوال
    """
    keyboard = []
    
    # دکمه‌های امتیازدهی (1 تا 5)
    rating_buttons = []
    for i in range(1, 6):
        rating_buttons.append(
            InlineKeyboardButton(f"{i} ⭐", callback_data=f"rate_question_{question_id}_{i}")
        )
    keyboard.append(rating_buttons)
    
    # دکمه نمایش ریپلای‌ها
    keyboard.append([
        InlineKeyboardButton("💬 نمایش پاسخ‌ها", callback_data=f"question_replies_{question_id}")
    ])
    
    # دکمه ریپلای به سوال
    keyboard.append([
        InlineKeyboardButton("↩️ پاسخ به سوال", callback_data=f"reply_question_{question_id}")
    ])
    
    # دکمه بازگشت به لیست سوالات
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به لیست سوالات", callback_data="tech")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_question_reply_buttons(reply_id: str, question_id: str, has_replies: bool = False) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های مربوط به ریپلای‌های سوال
    
    Args:
        reply_id: شناسه ریپلای
        question_id: شناسه سوال
        has_replies: آیا این ریپلای، ریپلای‌های دیگری دارد؟
        
    Returns:
        دکمه‌های اینلاین برای ریپلای‌ها
    """
    keyboard = []
    
    # اگر ریپلای دارای ریپلای‌های دیگری باشد
    if has_replies:
        keyboard.append([
            InlineKeyboardButton("👁️ نمایش پاسخ‌های بیشتر", callback_data=f"more_replies_{reply_id}")
        ])
    
    # دکمه ریپلای به این ریپلای
    keyboard.append([
        InlineKeyboardButton("↩️ پاسخ", callback_data=f"reply_to_reply_{reply_id}_{question_id}")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_more_questions_buttons(questions: List[Dict[str, Any]], start_index: int) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های نمایش سوالات بیشتر
    
    Args:
        questions: لیست سوالات
        start_index: شاخص شروع برای نمایش سوالات
        
    Returns:
        دکمه‌های اینلاین برای نمایش سوالات بیشتر
    """
    keyboard = []
    
    # نمایش 10 سوال بعدی
    for question in questions[start_index:start_index+10]:
        rating_stars = "★" * int(question["average_rating"]) + "☆" * (5 - int(question["average_rating"]))
        button_text = f"{question['text'][:30]}... ({rating_stars})"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text, 
                callback_data=f"question_{question['question_id']}"
            )
        ])
    
    # دکمه‌های ناوبری
    navigation_buttons = []
    
    # دکمه صفحه قبل (اگر در صفحه اول نباشیم)
    if start_index > 0:
        prev_index = max(0, start_index - 10)
        navigation_buttons.append(
            InlineKeyboardButton("◀️ قبلی", callback_data=f"more_questions_{prev_index}")
        )
    
    # دکمه صفحه بعد (اگر سوالات بیشتری وجود داشته باشد)
    if start_index + 10 < len(questions):
        next_index = start_index + 10
        navigation_buttons.append(
            InlineKeyboardButton("بعدی ▶️", callback_data=f"more_questions_{next_index}")
        )
    
    # اضافه کردن دکمه‌های ناوبری به کیبورد
    if navigation_buttons:
        keyboard.append(navigation_buttons)
    
    # دکمه افزودن سوال جدید
    keyboard.append([
        InlineKeyboardButton("❓ افزودن سوال جدید", callback_data="add_question")
    ])
    
    # دکمه بازگشت به منوی اصلی
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_question_replies_buttons(question_id: str, has_more_replies: bool = False, offset: int = 0) -> InlineKeyboardMarkup:
    """
    ایجاد دکمه‌های مربوط به نمایش ریپلای‌های سوال
    
    Args:
        question_id: شناسه سوال
        has_more_replies: آیا ریپلای‌های بیشتری وجود دارد؟
        offset: تعداد ریپلای‌هایی که تا کنون نمایش داده شده‌اند
        
    Returns:
        دکمه‌های اینلاین برای نمایش ریپلای‌ها
    """
    keyboard = []
    
    # اگر ریپلای‌های بیشتری وجود داشته باشد
    if has_more_replies:
        keyboard.append([
            InlineKeyboardButton("👁️ نمایش پاسخ‌های بیشتر", callback_data=f"more_question_replies_{question_id}_{offset}")
        ])
    
    # دکمه ریپلای به سوال
    keyboard.append([
        InlineKeyboardButton("↩️ پاسخ به سوال", callback_data=f"reply_question_{question_id}")
    ])
    
    # دکمه بازگشت به جزئیات سوال
    keyboard.append([
        InlineKeyboardButton("🔙 بازگشت به جزئیات سوال", callback_data=f"question_{question_id}")
    ])
    
    return InlineKeyboardMarkup(keyboard)