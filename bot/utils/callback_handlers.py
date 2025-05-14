from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler , filters
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
import logging
from database.db_handler import get_db
from database.db_operations import (
    get_items_by_type, get_item, get_comments_by_item, get_comment_replies,
    get_top_tech_questions, get_tech_question, get_question_replies, create_item_rating, create_question_rating,
    get_user, create_item, create_comment, create_tech_question, create_comment_reply,
    create_question_reply
)
from database.models import ItemType, ContentStatus, TargetType
from utils.buttons import (
    create_main_menu_buttons, create_device_category_buttons, create_liquid_category_buttons,
    create_item_list_buttons, create_item_detail_buttons, create_comment_buttons,
    create_tech_question_buttons, create_search_buttons, create_contact_buttons,
    create_cancel_button, create_back_to_main_button
)

# States for conversation handlers
COMMENT, REPLY, QUESTION, SEARCH, CONTACT = range(5)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Main menu callback handler
async def main_menu_callback(update: Update, context: CallbackContext) -> None:
    """Handle main menu callback."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "به ویپلند خوش آمدید! 🌬️\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=create_main_menu_buttons()
    )

# Devices menu callback handler
async def devices_callback(update: Update, context: CallbackContext) -> None:
    """Handle devices menu callback."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً نوع دستگاه را انتخاب کنید:",
        reply_markup=create_device_category_buttons()
    )

# Liquids menu callback handler
async def liquids_callback(update: Update, context: CallbackContext) -> None:
    """Handle liquids menu callback."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً نوع لیکوئید را انتخاب کنید:",
        reply_markup=create_liquid_category_buttons()
    )

# Device category callback handler
async def device_category_callback(update: Update, context: CallbackContext) -> None:
    """Handle device category selection."""
    query = update.callback_query
    await query.answer()
    
    category = query.data
    page = 0
    
    # Get items based on category
    db = next(get_db())
    if category == "devices_permanent":
        items = get_items_by_type(db, ItemType.DEVICE_PERMANENT)
        title = "دستگاه‌های دائمی"
        item_type = ItemType.DEVICE_PERMANENT
    elif category == "devices_disposable":
        items = get_items_by_type(db, ItemType.DEVICE_DISPOSABLE)
        title = "دستگاه‌های یکبارمصرف"
        item_type = ItemType.DEVICE_DISPOSABLE
    else:
        await query.edit_message_text(
            "دسته‌بندی نامعتبر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_device_category_buttons()
        )
        return
    
    if not items:
        # ایجاد دکمه برای افزودن آیتم جدید
        keyboard = [
            [InlineKeyboardButton("➕ افزودن دستگاه جدید", callback_data=f"add_item_{item_type}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="devices")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"هیچ محصولی در دسته‌بندی {title} یافت نشد.\n"
            f"می‌توانید یک دستگاه جدید اضافه کنید.",
            reply_markup=reply_markup
        )
        return
    
    # Convert SQLAlchemy objects to dictionaries
    items_dict = [
        {
            "item_id": str(item.item_id),
            "name": item.name,
            "average_rating": item.average_rating
        } for item in items
    ]
    
    context.user_data["current_category"] = category
    context.user_data["items"] = items_dict
    
    await query.edit_message_text(
        f"لیست {title}:",
        reply_markup=create_item_list_buttons(items_dict, category, page)
    )

# Liquid category callback handler
async def liquid_category_callback(update: Update, context: CallbackContext) -> None:
    """Handle liquid category selection."""
    query = update.callback_query
    await query.answer()
    
    category = query.data
    page = 0
    
    # Get items based on category
    db = next(get_db())
    if category == "liquids_salt":
        items = get_items_by_type(db, ItemType.LIQUID_SALT)
        title = "سالت نیکوتین"
        item_type = ItemType.LIQUID_SALT
    elif category == "liquids_juice":
        items = get_items_by_type(db, ItemType.LIQUID_JUICE)
        title = "جویس"
        item_type = ItemType.LIQUID_JUICE
    else:
        await query.edit_message_text(
            "دسته‌بندی نامعتبر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_liquid_category_buttons()
        )
        return
    
    if not items:
        # ایجاد دکمه برای افزودن آیتم جدید
        keyboard = [
            [InlineKeyboardButton("➕ افزودن لیکوئید جدید", callback_data=f"add_item_{item_type}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="liquids")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"هیچ محصولی در دسته‌بندی {title} یافت نشد.\n"
            f"می‌توانید یک لیکوئید جدید اضافه کنید.",
            reply_markup=reply_markup
        )
        return
    
    # Convert SQLAlchemy objects to dictionaries
    items_dict = [
        {
            "item_id": str(item.item_id),
            "name": item.name,
            "average_rating": item.average_rating
        } for item in items
    ]
    
    context.user_data["current_category"] = category
    context.user_data["items"] = items_dict
    
    await query.edit_message_text(
        f"لیست {title}:",
        reply_markup=create_item_list_buttons(items_dict, category, page)
    )

# Pagination callback handler
async def page_callback(update: Update, context: CallbackContext) -> None:
    """Handle pagination for item lists."""
    query = update.callback_query
    await query.answer()
    
    # Extract category and page from callback data
    _, category, page = query.data.split("_", 2)
    page = int(page)
    
    items = context.user_data.get("items", [])
    
    if not items:
        await query.edit_message_text(
            "خطا در بارگذاری محصولات. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return
    
    # Get category title
    if category == "devices_permanent":
        title = "دستگاه‌های دائمی"
    elif category == "devices_disposable":
        title = "دستگاه‌های یکبارمصرف"
    elif category == "liquids_salt":
        title = "سالت نیکوتین"
    elif category == "liquids_juice":
        title = "جویس"
    else:
        title = "محصولات"
    
    await query.edit_message_text(
        f"لیست {title} (صفحه {page + 1}):",
        reply_markup=create_item_list_buttons(items, category, page)
    )
    
# Item detail callback handler
async def item_detail_callback(update: Update, context: CallbackContext) -> None:
    """Handle item detail view."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract item ID from callback data
        _,_, category, item_id = query.data.split("_", 3)
        
        # Get item details
        db = next(get_db())
        
        # Try to convert item_id to UUID, handle potential errors
        try:
            item_uuid = item_id
            item = get_item(db, item_uuid)
        except ValueError:
            # Handle invalid UUID format
            await query.edit_message_text(
                f"شناسه محصول نامعتبر است. لطفاً دوباره تلاش کنید.\n{item_uuid}",
                reply_markup=create_main_menu_buttons()
            )
            return
        
        if not item:
            await query.edit_message_text(
                "محصول مورد نظر یافت نشد. لطفاً دوباره تلاش کنید.",
                reply_markup=create_main_menu_buttons()
            )
            return
        
        # Get approved comments for the item
        comments = get_comments_by_item(db, item.item_id, ContentStatus.APPROVED)
        
        # Format item details
        rating_stars = "★" * int(item.average_rating) + "☆" * (5 - int(item.average_rating))
        item_details = (
            f"🏷️ نام: {item.name}\n\n"
            f"📝 توضیحات: {item.description or 'بدون توضیحات'}\n\n"
            f"⭐ امتیاز: {rating_stars} ({item.average_rating:.1f} از 5 - {item.rating_count} رأی)"
        )
        
        # Format comments
        comments_text = "\n\n💬 نظرات کاربران:\n"
        if comments:
            for i, comment in enumerate(comments[:3], 1):
                user = get_user(db, comment.user_id)
                username = user.username if user and user.username else f"کاربر {comment.user_id}"
                comments_text += f"\n{i}. {username}: {comment.text}\n"
                
                # Check if comment has media
                if comment.media_url:
                    comments_text += "🖼️ [دارای تصویر یا ویدیو]\n"
                
                # Add reply count if any
                reply_count = len(get_comment_replies(db, comment.comment_id, ContentStatus.APPROVED))
                if reply_count > 0:
                    comments_text += f"↩️ {reply_count} پاسخ\n"
        else:
            comments_text += "\nهنوز نظری ثبت نشده است. شما می‌توانید اولین نظر را ثبت کنید."
        
        # Save item ID in user data for future use
        context.user_data["current_item_id"] = str(item.item_id)
        
        # اضافه کردن دکمه افزودن نظر در صورت خالی بودن لیست نظرات
        buttons = create_item_detail_buttons(str(item.item_id), "item")
        
        await query.edit_message_text(
            item_details + comments_text,
            reply_markup=buttons
        )
    except Exception as e:
        # Handle any other exceptions
        logger.error(f"Error in item_detail_callback: {e}")
        await query.edit_message_text(
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید.\n{e}",
            reply_markup=create_main_menu_buttons()
        )
        
        
# Rate item callback handler
async def rate_callback(update: Update, context: CallbackContext) -> None:
    """Handle rating for items and questions."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Extract target type, ID and score from callback data
    _, target_type, target_id, score = query.data.split("_", 3)
    score = int(score)
    
    # Create rating
    db = next(get_db())
    user = get_user(db, user_id)
    
    
    # Create rating based on target type
    if target_type == "item":
        rating = create_item_rating(db, user_id, UUID(target_id), score)
    elif target_type == "question":
        rating = create_question_rating(db, user_id, UUID(target_id), score)
    else:
        await query.answer("نوع هدف نامعتبر است.")
        return
    
    if rating:
        await query.answer(f"امتیاز {score} با موفقیت ثبت شد!")
    else:
        await query.answer("شما قبلاً به این مورد امتیاز داده‌اید.")
    
    # Refresh the item or question details
    if target_type == "item":
        await item_detail_callback(update, context)
    elif target_type == "question":
        await question_detail_callback(update, context)

# Comment callback handler - start conversation
async def comment_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation to add a comment."""
    query = update.callback_query
    await query.answer()
    
    # Extract target type and ID from callback data
    _, target_type, target_id = query.data.split("_", 2)
    
    # Save target info in user data
    context.user_data["comment_target_type"] = target_type
    context.user_data["comment_target_id"] = target_id
    
    await query.edit_message_text(
        "لطفاً نظر خود را بنویسید. می‌توانید متن، عکس یا ویدیو ارسال کنید (حداکثر حجم: 10MB).",
        reply_markup=create_cancel_button()
    )
    
    return COMMENT

# Show more comments callback handler
async def more_comments_callback(update: Update, context: CallbackContext) -> None:
    """Show more comments for an item or question."""
    query = update.callback_query
    await query.answer()
    
    # Extract target type and ID from callback data
    _, target_type, target_id = query.data.split("_", 2)
    
    # Get comments
    db = next(get_db())
    
    if target_type == "item":
        comments = get_comments_by_item(db, UUID(target_id), ContentStatus.APPROVED, limit=10)
        item = get_item(db, UUID(target_id))
        title = f"نظرات کاربران برای {item.name}" if item else "نظرات کاربران"
    elif target_type == "question":
        comments = get_question_replies(db, UUID(target_id), ContentStatus.APPROVED, limit=10)
        question = get_tech_question(db, UUID(target_id))
        title = "پاسخ‌های کاربران به سوال" if question else "پاسخ‌های کاربران"
    else:
        await query.edit_message_text(
            "نوع هدف نامعتبر است.",
            reply_markup=create_main_menu_buttons()
        )
        return
    
    # Format comments
    comments_text = f"{title}:\n\n"
    if comments:
        for i, comment in enumerate(comments, 1):
            user = get_user(db, comment.user_id)
            username = user.username if user and user.username else f"کاربر {comment.user_id}"
            comments_text += f"{i}. {username}: {comment.text}\n"
            
            # Check if comment has media
            if comment.media_url:
                comments_text += "🖼️ [دارای تصویر یا ویدیو]\n"
            
            # Add reply count if any
            if target_type == "item":
                reply_count = len(get_comment_replies(db, comment.comment_id, ContentStatus.APPROVED))
                if reply_count > 0:
                    comments_text += f"↩️ {reply_count} پاسخ\n"
            
            comments_text += "\n"
    else:
        comments_text += "هنوز نظری ثبت نشده است."
    
    # Create back button
    if target_type == "item":
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_category', 'unknown')}_{target_id}")]]
    else:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به جزئیات سوال", callback_data=f"question_{target_id}")]]
    
    await query.edit_message_text(
        comments_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Reply to comment callback handler - start conversation
async def reply_comment_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation to reply to a comment."""
    query = update.callback_query
    await query.answer()
    
    # Extract comment ID from callback data
    _, comment_id = query.data.split("_", 1)
    
    # Save comment ID in user data
    context.user_data["reply_comment_id"] = comment_id
    
    await query.edit_message_text(
        "لطفاً پاسخ خود را بنویسید. می‌توانید متن، عکس یا ویدیو ارسال کنید (حداکثر حجم: 10MB).",
        reply_markup=create_cancel_button()
    )
    
    return REPLY

# Show comment replies callback handler
async def show_replies_callback(update: Update, context: CallbackContext) -> None:
    """Show replies to a comment."""
    query = update.callback_query
    await query.answer()
    
    # Extract comment ID from callback data
    _, comment_id = query.data.split("_", 1)
    
    # Get replies
    db = next(get_db())
    replies = get_comment_replies(db, UUID(comment_id), ContentStatus.APPROVED)
    
    # Format replies
    replies_text = "پاسخ‌های این نظر:\n\n"
    if replies:
        for i, reply in enumerate(replies, 1):
            user = get_user(db, reply.user_id)
            username = user.username if user and user.username else f"کاربر {reply.user_id}"
            replies_text += f"{i}. {username}: {reply.text}\n"
            
            # Check if reply has media
            if reply.media_url:
                replies_text += "🖼️ [دارای تصویر یا ویدیو]\n"
            
            replies_text += "\n"
    else:
        replies_text += "هنوز پاسخی ثبت نشده است."
    
    # Create back button based on current context
    if "current_item_id" in context.user_data:
        item_id = context.user_data["current_item_id"]
        category = context.user_data.get("current_category", "unknown")
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{category}_{item_id}")]]
    elif "current_question_id" in context.user_data:
        question_id = context.user_data["current_question_id"]
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به جزئیات سوال", callback_data=f"question_{question_id}")]]
    else:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]]
    
    await query.edit_message_text(
        replies_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Technical questions callback handler
async def tech_callback(update: Update, context: CallbackContext) -> None:
    """Handle technical questions menu."""
    query = update.callback_query
    await query.answer()
    
    # Get top technical questions
    db = next(get_db())
    questions = get_top_tech_questions(db)
    
    if not questions:
        await query.edit_message_text(
            "هنوز سوال فنی ثبت نشده است. شما می‌توانید اولین سوال را ثبت کنید!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❓ افزودن سوال جدید", callback_data="add_question")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
        )
        return
    
    # Convert SQLAlchemy objects to dictionaries
    questions_dict = [
        {
            "question_id": str(q.question_id),
            "text": q.text,
            "average_rating": q.average_rating
        } for q in questions
    ]
    
    context.user_data["questions"] = questions_dict
    
    await query.edit_message_text(
        "سوالات فنی برتر:",
        reply_markup=create_tech_question_buttons(questions_dict)
    )

# Technical question pagination callback handler
async def tech_page_callback(update: Update, context: CallbackContext) -> None:
    """Handle pagination for technical questions."""
    query = update.callback_query
    await query.answer()
    
    # Extract page from callback data
    _, page = query.data.split("_", 1)
    page = int(page)
    
    questions = context.user_data.get("questions", [])
    
    if not questions:
        await query.edit_message_text(
            "خطا در بارگذاری سوالات. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return
    
    await query.edit_message_text(
        f"سوالات فنی برتر (صفحه {page + 1}):",
        reply_markup=create_tech_question_buttons(questions, page)
    )

# Question detail callback handler
async def question_detail_callback(update: Update, context: CallbackContext) -> None:
    """Handle question detail view."""
    query = update.callback_query
    await query.answer()
    
    # Extract question ID from callback data
    _, question_id = query.data.split("_", 1)
    
    # Get question details
    db = next(get_db())
    question = get_tech_question(db, UUID(question_id))
    
    if not question:
        await query.edit_message_text(
            "سوال مورد نظر یافت نشد. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return
    
    # Get approved replies for the question
    replies = get_question_replies(db, question.question_id, ContentStatus.APPROVED)
    
    # Format question details
    rating_stars = "★" * int(question.average_rating) + "☆" * (5 - int(question.average_rating))
    question_details = (
        f"❓ سوال: {question.text}\n\n"
        f"⭐ امتیاز: {rating_stars} ({question.average_rating:.1f} از 5 - {question.rating_count} رأی)"
    )
    
    # Check if question has media
    if question.media_url:
        question_details += "\n🖼️ [دارای تصویر یا ویدیو]"
    
    # Format replies
    replies_text = "\n\n💬 پاسخ‌های کاربران:\n"
    if replies:
        for i, reply in enumerate(replies[:3], 1):
            user = get_user(db, reply.user_id)
            username = user.username if user and user.username else f"کاربر {reply.user_id}"
            replies_text += f"\n{i}. {username}: {reply.text}\n"
            
            # Check if reply has media
            if reply.media_url:
                replies_text += "🖼️ [دارای تصویر یا ویدیو]\n"
    else:
        replies_text += "\nهنوز پاسخی ثبت نشده است."
    
    # Save question ID in user data for future use
    context.user_data["current_question_id"] = str(question.question_id)
    
    await query.edit_message_text(
        question_details + replies_text,
        reply_markup=create_item_detail_buttons(str(question.question_id), "question")
    )

# Add question callback handler - start conversation
async def add_question_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation to add a technical question."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً سوال فنی خود را بنویسید. می‌توانید متن، عکس یا ویدیو ارسال کنید (حداکثر حجم: 10MB).",
        reply_markup=create_cancel_button()
    )
    
    return QUESTION

# Search callback handler - start conversation
async def search_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation for product search."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً نام محصول مورد نظر خود را وارد کنید:",
        reply_markup=create_cancel_button()
    )
    
    return SEARCH

# Contact us callback handler - start conversation
async def contact_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation for contact message."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً پیام خود را بنویسید. می‌توانید متن، عکس یا ویدیو ارسال کنید (حداکثر حجم: 10MB).",
        reply_markup=create_cancel_button()
    )
    
    return CONTACT

# Cancel callback handler
async def cancel_callback(update: Update, context: CallbackContext) -> int:
    """Cancel current conversation and return to main menu."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "عملیات لغو شد. به منوی اصلی بازگشتید.",
        reply_markup=create_main_menu_buttons()
    )
    
    return ConversationHandler.END


# اضافه کردن هندلر جدید برای افزودن آیتم
async def add_item_callback(update: Update, context: CallbackContext) -> int:
    """Handle adding a new item."""
    query = update.callback_query
    await query.answer()
    
    # Extract item type from callback data
    _, item_type = query.data.split("_", 1)
    context.user_data["add_item_type"] = item_type
    
    await query.edit_message_text(
        "لطفاً نام محصول جدید را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("لغو", callback_data="cancel")]])
    )
    
    return COMMENT  # استفاده از حالت COMMENT برای دریافت نام محصول

# هندلر برای دریافت نام محصول جدید
async def add_item_name(update: Update, context: CallbackContext) -> int:
    """Process the name for a new item."""
    user_id = update.effective_user.id
    item_type = context.user_data.get("add_item_type")
    
    if not item_type:
        await update.message.reply_text(
            "خطا در فرآیند افزودن محصول. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END
    
    # ذخیره نام محصول
    context.user_data["add_item_name"] = update.message.text
    
    await update.message.reply_text(
        "لطفاً توضیحات محصول را وارد کنید (یا 'بدون توضیحات' را ارسال کنید):",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("لغو", callback_data="cancel")]])
    )
    
    return REPLY  # استفاده از حالت REPLY برای دریافت توضیحات محصول

# هندلر برای دریافت توضیحات محصول جدید
async def add_item_description(update: Update, context: CallbackContext) -> int:
    """Process the description for a new item."""
    user_id = update.effective_user.id
    item_type_str = context.user_data.get("add_item_type")
    item_name = context.user_data.get("add_item_name")
    
    if not item_type_str or not item_name:
        await update.message.reply_text(
            "خطا در فرآیند افزودن محصول. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END
    
    # تبدیل رشته نوع آیتم به نوع شمارشی
    if item_type_str == "DEVICE_PERMANENT":
        item_type = ItemType.DEVICE_PERMANENT
        category = "devices_permanent"
    elif item_type_str == "DEVICE_DISPOSABLE":
        item_type = ItemType.DEVICE_DISPOSABLE
        category = "devices_disposable"
    elif item_type_str == "LIQUID_SALT":
        item_type = ItemType.LIQUID_SALT
        category = "liquids_salt"
    elif item_type_str == "LIQUID_JUICE":
        item_type = ItemType.LIQUID_JUICE
        category = "liquids_juice"
    else:
        await update.message.reply_text(
            "نوع محصول نامعتبر است. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END
    
    # دریافت توضیحات
    description = update.message.text
    if description.lower() == "بدون توضیحات":
        description = None
    
    # ایجاد آیتم جدید در دیتابیس
    db = next(get_db())
    try:
        new_item = create_item(db, item_type, item_name, description)
        
        # پاک کردن داده‌های موقت
        context.user_data.pop("add_item_type", None)
        context.user_data.pop("add_item_name", None)
        
        await update.message.reply_text(
            f"محصول '{item_name}' با موفقیت اضافه شد!",
            reply_markup=create_main_menu_buttons()
        )
        
        # نمایش جزئیات محصول جدید
        keyboard = [
            [InlineKeyboardButton("مشاهده جزئیات محصول", callback_data=f"item_{category}_{new_item.item_id}")],
            [InlineKeyboardButton("بازگشت به منوی اصلی", callback_data="main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "می‌خواهید چه کاری انجام دهید؟",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        await update.message.reply_text(
            "خطا در ایجاد محصول. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
    
    return ConversationHandler.END


# Register all callback handlers
def register_callback_handlers(application):
    """Register all callback query handlers."""
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(devices_callback, pattern="^devices$"))
    application.add_handler(CallbackQueryHandler(liquids_callback, pattern="^liquids$"))
    application.add_handler(CallbackQueryHandler(device_category_callback, pattern="^devices_(permanent|disposable)$"))
    application.add_handler(CallbackQueryHandler(liquid_category_callback, pattern="^liquids_(salt|juice)$"))
    application.add_handler(CallbackQueryHandler(page_callback, pattern="^page_"))
    application.add_handler(CallbackQueryHandler(item_detail_callback, pattern="^item_"))
    application.add_handler(CallbackQueryHandler(rate_callback, pattern="^rate_"))
    application.add_handler(CallbackQueryHandler(more_comments_callback, pattern="^more_comments_"))
    application.add_handler(CallbackQueryHandler(reply_comment_callback, pattern="^reply_comment_"))
    application.add_handler(CallbackQueryHandler(show_replies_callback, pattern="^show_replies_"))
    application.add_handler(CallbackQueryHandler(tech_callback, pattern="^tech$"))
    application.add_handler(CallbackQueryHandler(tech_page_callback, pattern="^tech_page_"))
    application.add_handler(CallbackQueryHandler(question_detail_callback, pattern="^question_"))
    application.add_handler(CallbackQueryHandler(add_question_callback, pattern="^add_question$"))
    application.add_handler(CallbackQueryHandler(search_callback, pattern="^search$"))
    application.add_handler(CallbackQueryHandler(contact_callback, pattern="^contact_us$"))
    application.add_handler(CallbackQueryHandler(cancel_callback, pattern="^cancel$"))
    # اضافه کردن هندلر برای افزودن آیتم جدید
    application.add_handler(CallbackQueryHandler(add_item_callback, pattern="^add_item_"))
    
    # اضافه کردن هندلر مکالمه برای افزودن آیتم
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_item_callback, pattern="^add_item_")],
        states={
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_name)],
            REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_description)],
        },
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^cancel$")],
    )
    application.add_handler(conv_handler)
