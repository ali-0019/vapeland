from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler , filters
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime
import logging
from database.db_handler import get_db
from database.db_operations import (
    get_items_by_type, get_item, get_comments_by_item, get_comment_replies,
    create_item_rating, 
    get_user, create_item, create_comment, create_comment_reply,
    create_item_rating
)
from database.models import ItemType, ContentStatus, TargetType
from utils.buttons import (
    create_main_menu_buttons,
    create_cancel_button,
)
from utils.items.item_buttons import (
    create_device_category_buttons,create_liquid_category_buttons,
    create_item_list_buttons,create_item_detail_buttons,
    create_comment_buttons,create_reply_comment_buttons
)
from utils.callback_handlers import (
    cancel_callback
)
COMMENT, REPLY = range(2)

####################################

# Item callback

###################################
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

##################################

#category callback

##################################
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
        keyboard = []
        if category.endswith("permanent"):
            keyboard.append([InlineKeyboardButton("افزودن دستگاه دائمی", callback_data="add_item_DEVICE_PERMANENT")])
        elif category.endswith("disposable"):
            keyboard.append([InlineKeyboardButton("افزودن دستگاه یکبار مصرف", callback_data="add_item_DEVICE_DISPOSABLE")])
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
    if category == "liquid_salt":
        items = get_items_by_type(db, ItemType.LIQUID_SALT)
        title = "سالت نیکوتین"
        item_type = ItemType.LIQUID_SALT
    elif category == "liquid_juice":
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
        keyboard = []
        if category == "liquid_salt":
            keyboard.append([InlineKeyboardButton("افزودن سالت نیکوتین", callback_data="add_LIQUID_SALT")])
        elif category == "liquid_juice":
            keyboard.append([InlineKeyboardButton("افزودن جویس", callback_data="add_LIQUID_JUICE")])
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

##################################

#items list callback

###################################
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

##################################

#item detail callback

############################
# Item detail callback handler
async def item_detail_callback(update: Update, context: CallbackContext) -> None:
    """Handle item detail view."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract item ID from callback data
        _,itemtype, category, item_id = query.data.split("_", 3)
        context.user_data["current_itemtype"] = itemtype
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
        
        # Format item details
        rating_stars = "★" * int(item.average_rating) + "☆" * (5 - int(item.average_rating))
        item_details = (
            f"🏷️ نام: {item.name}\n\n"
            f"📝 توضیحات: {item.description or 'بدون توضیحات'}\n\n"
            f"⭐ امتیاز: {rating_stars} ({item.average_rating:.1f} از 5 - {item.rating_count} رأی)"
        )
        
        # Save item ID in user data for future use
        context.user_data["current_item_id"] = str(item.item_id)
        context.user_data["current_category"] = category
        
        # Create buttons for item details with rating and comment options
        buttons = create_item_detail_buttons(str(item.item_id), context.user_data["current_itemtype"], category)
        
        await query.edit_message_text(
            item_details,
            reply_markup=buttons
        )
    except Exception as e:
        # Handle any other exceptions
        logging.error(f"Error in item_detail_callback: {e}")
        await query.edit_message_text(
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید.\n{e}",
            reply_markup=create_main_menu_buttons()
        )

###################################

#item comment callback

####################################
# Item comments callback handler
async def item_comments_callback(update: Update, context: CallbackContext) -> None:
    """Handle item comments view."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract item ID from callback data
        _, item_id = query.data.split("_", 1)
        
        # Get item details
        db = next(get_db())
        
        try:
            item = get_item(db, item_id)
        except ValueError:
            await query.edit_message_text(
                "شناسه محصول نامعتبر است. لطفاً دوباره تلاش کنید.",
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
        
        # ابتدا پیام اصلی را به عنوان هدر نمایش می‌دهیم
        header_text = f"💬 نظرات کاربران برای {item.name}:"
        await query.edit_message_text(header_text)
        
        # اگر نظری وجود نداشت
        if not comments:
            no_comments_text = "هنوز نظری ثبت نشده است. شما می‌توانید اولین نظر را ثبت کنید."
            keyboard = [
                [InlineKeyboardButton("💬 افزودن نظر", callback_data=f"comment_item_{item_id}")],
                [InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_category', 'unknown')}_{item_id}")]
            ]
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=no_comments_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # نمایش هر نظر در یک پیام جداگانه (حداکثر ۵ نظر)
        for i, comment in enumerate(comments[:5], 1):
            user = get_user(db, comment.user_id)
            username = user.username if user and user.username else f"کاربر {comment.user_id}"
            # متن نظر
            comment_text = f"💬 نظر #{i}:\n\n"
            comment_text += f"👤 {username}:\n{comment.text}\n"
            
            # اگر رسانه داشت
            if comment.media_url:
                comment_text += "\n🖼️ [دارای تصویر یا ویدیو]\n"
            
            # تعداد پاسخ‌ها
            reply_count = len(get_comment_replies(db, comment.comment_id, ContentStatus.APPROVED))
            if reply_count > 0:
                comment_text += f"\n↩️ {reply_count} پاسخ\n"
            
            # دکمه‌های هر نظر
            comment_keyboard = create_comment_buttons(str(comment.comment_id), has_replies=bool(reply_count))
            
            # ارسال پیام نظر
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=comment_text,
                reply_markup=comment_keyboard
            )
        
        # پیام نهایی با دکمه‌های اصلی
        final_keyboard = []
        
        # اگر نظرات بیشتر از ۵ تا بود
        if len(comments) > 5:
            final_keyboard.append([InlineKeyboardButton(f"👁️ نمایش {len(comments) - 5} نظر دیگر", callback_data=f"more_comments_{item_id}_5")])
        
        # دکمه‌های اصلی
        final_keyboard.append([InlineKeyboardButton("💬 افزودن نظر", callback_data=f"comment_item_{item_id}")])
        final_keyboard.append([InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_itemtype', 'unknown')}_{context.user_data.get('current_category', 'unknown')}_{item_id}")])
        
        # ارسال پیام نهایی
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="برای ادامه یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(final_keyboard)
            
        )
        
    except Exception as e:
        # Handle any other exceptions
        logger = logging.getLogger(__name__)
        logger.error(f"Error in item_comments_callback: {str(e)}")
        logger.exception("Full traceback:")
        await query.edit_message_text(
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید.\n{e}",
            reply_markup=create_main_menu_buttons()
        )

# Show more comments callback handler
async def more_comments_callback(update: Update, context: CallbackContext) -> None:
    """Handle showing more comments."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract item ID and offset from callback data
        _, item_id, offset = query.data.split("_", 2)
        offset = int(offset)
        
        # Get item details
        db = next(get_db())
        
        try:
            item = get_item(db, item_id)
        except ValueError:
            await query.edit_message_text(
                "شناسه محصول نامعتبر است. لطفاً دوباره تلاش کنید.",
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
        
        # اگر نظری وجود نداشت یا آفست بیشتر از تعداد نظرات بود
        if not comments or offset >= len(comments):
            await query.edit_message_text(
                "نظر بیشتری وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_category', 'unknown')}_{item_id}")]
                ])
            )
            return
        
        # تعداد نظرات باقیمانده
        remaining_comments = comments[offset:]
        
        # تعداد نظراتی که نمایش داده می‌شوند (حداکثر ۵ نظر)
        display_count = min(5, len(remaining_comments))
        
        # ابتدا پیام اصلی را به‌روزرسانی می‌کنیم
        await query.edit_message_text(
            f"💬 نظرات بیشتر برای {item.name}:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_category', 'unknown')}_{item_id}")]
            ])
        )
        
        # نمایش هر نظر در یک پیام جداگانه
        for i, comment in enumerate(remaining_comments[:display_count], offset + 1):
            user = get_user(db, comment.user_id)
            username = user.username if user and user.username else f"کاربر {comment.user_id}"
            
            # متن نظر
            comment_text = f"💬 نظر #{i}:\n\n"
            comment_text += f"👤 {username}:\n{comment.text}\n"
            
            # اگر رسانه داشت
            if comment.media_url:
                comment_text += "\n🖼️ [دارای تصویر یا ویدیو]\n"
            
            # تعداد پاسخ‌ها
            reply_count = len(get_comment_replies(db, comment.comment_id, ContentStatus.APPROVED))
            if reply_count > 0:
                comment_text += f"\n↩️ {reply_count} پاسخ\n"
            
            # دکمه‌های هر نظر
            comment_keyboard = [
                [InlineKeyboardButton("↩️ پاسخ به این نظر", callback_data=f"reply_{comment.comment_id}")]
            ]
            
            # ارسال پیام نظر
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=comment_text,
                reply_markup=InlineKeyboardMarkup(comment_keyboard)
            )
        
        # پیام نهایی با دکمه‌های اصلی
        final_keyboard = []
        
        # اگر نظرات بیشتری باقی مانده بود
        new_offset = offset + display_count
        if new_offset < len(comments):
            final_keyboard.append([InlineKeyboardButton(f"👁️ نمایش {len(comments) - new_offset} نظر دیگر", callback_data=f"more_comments_{item_id}_{new_offset}")])
        
        # دکمه‌های اصلی
        final_keyboard.append([InlineKeyboardButton("💬 افزودن نظر", callback_data=f"comment_item_{item_id}")])
        final_keyboard.append([InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_category', 'unknown')}_{item_id}")])
        
        # ارسال پیام نهایی
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="برای ادامه یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(final_keyboard)
        )
        
    except Exception as e:
        # Handle any other exceptions
        logger = logging.getLogger(__name__)
        logger.error(f"Error in more_comments_callback: {str(e)}")
        logger.exception("Full traceback:")
        await query.edit_message_text(
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید.\n{e}",
            reply_markup=create_main_menu_buttons()
        )

# View single comment callback handler
async def view_comment_callback(update: Update, context: CallbackContext) -> None:
    """Handle viewing a single comment."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract item ID and comment index from callback data
        _, item_id, comment_index = query.data.split("_", 2)
        comment_index = int(comment_index)
        
        # Get item details
        db = next(get_db())
        
        try:
            item = get_item(db, item_id)
        except ValueError:
            await query.edit_message_text(
                "شناسه محصول نامعتبر است. لطفاً دوباره تلاش کنید.",
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
        
        if not comments:
            await query.edit_message_text(
                f"هنوز نظری برای {item.name} ثبت نشده است.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 افزودن نظر", callback_data=f"comment_item_{item_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_category', 'unknown')}_{item_id}")]
                ])
            )
            return
        
        # Check if comment index is valid
        if comment_index < 0 or comment_index >= len(comments):
            comment_index = 0
        
        # Get the current comment
        comment = comments[comment_index]
        # Get user details
        user = get_user(db, comment.user_id)
        username = user.username if user and user.username else f"کاربر {comment.user_id}"  
        # Format comment details
        comment_text = f"💬 نظر {comment_index + 1} از {len(comments)} برای {item.name}:\n\n"
        comment_text += f"👤{username}:\n{comment.text}\n"
        
        # Check if comment has media
        if comment.media_url:
            comment_text += "\n🖼️ [دارای تصویر یا ویدیو]\n"
        
        # Get replies for this comment
        replies = get_comment_replies(db, comment.comment_id, ContentStatus.APPROVED)
        if replies:
            comment_text += f"\n↩️ پاسخ‌ها ({len(replies)}):\n"
            for i, reply in enumerate(replies[:3], 1):
                reply_user = get_user(db, reply.user_id)
                comment_text += f"{i}. {reply.text}\n"
        
            if len(replies) > 3:
                comment_text += f"... و {len(replies) - 3} پاسخ دیگر\n"
        
        # Create navigation buttons
        keyboard = []
        
        # Navigation row
        nav_row = []
        if comment_index > 0:
            nav_row.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"viewcomment_{item_id}_{comment_index - 1}"))
        
        if comment_index < len(comments) - 1:
            nav_row.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"viewcomment_{item_id}_{comment_index + 1}"))
        
        if nav_row:
            keyboard.append(nav_row)
        
        # Action buttons
        keyboard.append([InlineKeyboardButton("↩️ پاسخ به این نظر", callback_data=f"reply_comment_{comment.comment_id}")])
        keyboard.append([InlineKeyboardButton("💬 همه نظرات", callback_data=f"comments_{item_id}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_category', 'unknown')}_{item_id}")])
        
        await query.edit_message_text(
            comment_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        # Handle any other exceptions
        logger = logging.getLogger(__name__)
        logger.error(f"Error in view_comment_callback: {str(e)}")
        logger.exception("Full traceback:")
        await query.edit_message_text(
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید.\n{e}",
            reply_markup=create_main_menu_buttons()
        ) 


###################################

# Comment callback handler - start conversation

##################################
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

# Handle text comments
async def handle_comment_text(update: Update, context: CallbackContext) -> int:
    """Handle text comments."""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Get target info from user data
    target_type = context.user_data.get("comment_target_type")
    target_id = context.user_data.get("comment_target_id")
    
    if not target_type or not target_id:
        await update.message.reply_text(
            "خطا در ثبت نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END
    
    try:
        db = next(get_db())
        
        if target_type == "item":
            # Create comment for item
            comment = create_comment(db, UUID(target_id), user_id, text)
            success_message = "نظر شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."
        else:
            # Handle other target types if needed
            await update.message.reply_text(
                "نوع هدف نامعتبر است.",
                reply_markup=create_main_menu_buttons()
            )
            return ConversationHandler.END
        
        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=create_main_menu_buttons()
        )
        
    except Exception as e:
        # Log the error
        logger.error(f"Error creating comment: {e}")
        await update.message.reply_text(
            "خطا در ثبت نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
    
    # End the conversation
    return ConversationHandler.END

# Handle media comments (photo)
async def handle_comment_photo(update: Update, context: CallbackContext) -> int:
    """Handle photo comments."""
    user_id = update.effective_user.id
    photo = update.message.photo[-1]  # Get the largest photo
    text = update.message.caption or ""
    
    # Get target info from user data
    target_type = context.user_data.get("comment_target_type")
    target_id = context.user_data.get("comment_target_id")
    
    if not target_type or not target_id:
        await update.message.reply_text(
            "خطا در ثبت نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END
    
    try:
        # Get photo file
        photo_file = await photo.get_file()
        
        # Generate a unique filename
        file_extension = "jpg"
        filename = f"comment_{user_id}_{int(datetime.now().timestamp())}.{file_extension}"
        
        # Save the photo to a directory (you need to implement this)
        # For example: media_url = await save_media_file(photo_file, filename)
        media_url = f"media/comments/{filename}"  # This is just a placeholder
        
        db = next(get_db())
        
        if target_type == "item":
            # Create comment for item with media
            comment = create_comment(db, UUID(target_id), user_id, text, media_url)
            success_message = "نظر شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."
        else:
            # Handle other target types if needed
            await update.message.reply_text(
                "نوع هدف نامعتبر است.",
                reply_markup=create_main_menu_buttons()
            )
            return ConversationHandler.END
        
        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=create_main_menu_buttons()
        )
        
    except Exception as e:
        # Log the error
        logger.error(f"Error creating comment with photo: {e}")
        await update.message.reply_text(
            "خطا در ثبت نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
    
    # End the conversation
    return ConversationHandler.END

# Handle media comments (video)
async def handle_comment_video(update: Update, context: CallbackContext) -> int:
    """Handle video comments."""
    user_id = update.effective_user.id
    video = update.message.video
    text = update.message.caption or ""
    
    # Get target info from user data
    target_type = context.user_data.get("comment_target_type")
    target_id = context.user_data.get("comment_target_id")
    
    if not target_type or not target_id:
        await update.message.reply_text(
            "خطا در ثبت نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END
    
    # Check video size (10MB limit)
    if video.file_size > 10 * 1024 * 1024:  # 10MB in bytes
        await update.message.reply_text(
            "حجم ویدیو بیشتر از 10 مگابایت است. لطفاً ویدیو کوچکتری ارسال کنید.",
            reply_markup=create_cancel_button()
        )
        return COMMENT
    
    try:
        # Get video file
        video_file = await video.get_file()
        
        # Generate a unique filename
        file_extension = "mp4"
        filename = f"comment_{user_id}_{int(datetime.now().timestamp())}.{file_extension}"
        
        # Save the video to a directory (you need to implement this)
        # For example: media_url = await save_media_file(video_file, filename)
        media_url = f"media/comments/{filename}"  # This is just a placeholder
        
        db = next(get_db())
        
        if target_type == "item":
            # Create comment for item with media
            comment = create_comment(db, UUID(target_id), user_id, text, media_url)
            success_message = "نظر شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."
        else:
            # Handle other target types if needed
            await update.message.reply_text(
                "نوع هدف نامعتبر است.",
                reply_markup=create_main_menu_buttons()
            )
            return ConversationHandler.END
        
        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=create_main_menu_buttons()
        )
        
    except Exception as e:
        # Log the error
        logger.error(f"Error creating comment with video: {e}")
        await update.message.reply_text(
            "خطا در ثبت نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
    
    # End the conversation
    return ConversationHandler.END

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

###########################################################

# Reply to comment callback handler - start conversation

###########################################################
# Reply to comment callback handler - start conversation
async def reply_comment_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation to reply to a comment."""
    query = update.callback_query
    await query.answer(show_alert=False)
    
    # Extract comment ID from callback data
    _,_, comment_id = query.data.split("_", 2)
    
    # Save comment ID in user data
    context.user_data["reply_comment_id"] = comment_id
    
    await context.bot.send_message(
        text= "لطفاً پاسخ خود را بنویسید. می‌توانید متن، عکس یا ویدیو ارسال کنید (حداکثر حجم: 10MB).",
        chat_id=update.effective_chat.id,
        reply_markup=create_cancel_button()
    )
    
    return REPLY

# Handle text replies
async def handle_reply_text(update: Update, context: CallbackContext) -> int:
    """Handle text replies."""
    user_id = update.effective_user.id
    text = update.message.text

    # Get comment ID from user data
    comment_id = context.user_data.get("reply_comment_id")

    if not comment_id:
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END

    try:
        db = next(get_db())

        # Create reply
        reply = create_comment_reply(db, UUID(comment_id), user_id, text)
        success_message = "پاسخ شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."

        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=create_main_menu_buttons() 
        )

    except Exception as e:
        # Log the error
        logger.error(f"Error creating reply: {e}")
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )

    # End the conversation
    return ConversationHandler.END

# Handle media replies (photo)
async def handle_reply_photo(update: Update, context: CallbackContext) -> int:
    """Handle photo replies."""
    user_id = update.effective_user.id
    photo = update.message.photo[-1]  # Get the largest photo
    text = update.message.caption or ""

    # Get comment ID from user data
    comment_id = context.user_data.get("reply_comment_id")

    if not comment_id:
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END

    # Check photo size (10MB limit)
    if photo.file_size > 10 * 1024 * 1024:  # 10MB in bytes
        await update.message.reply_text(
            "حجم عکس بیشتر از 10 مگابایت است. لطفاً عکس کوچکتری ارسال کنید.",
            reply_markup=create_cancel_button()
        )
        return REPLY

    try:
        # Get photo file
        photo_file = await photo.get_file()

        # Generate a unique filename
        file_extension = "jpg"
        filename = f"reply_{user_id}_{int(datetime.now().timestamp())}.{file_extension}"
        # Save the photo to a directory (you need to implement this)
        # For example: media_url = await save_media_file(photo_file, filename)
        media_url = f"media/replies/{filename}"  # This is just a placeholder

        db = next(get_db())

        # Create reply with media
        reply = create_comment_reply(db, UUID(comment_id), user_id, text, media_url)
        success_message = "پاسخ شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."

        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=create_main_menu_buttons()
        )

    except Exception as e:
        # Log the error
        logger.error(f"Error creating reply with photo: {e}")
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )

    # End the conversation
    return ConversationHandler.END

# Handle media replies (video)
async def handle_reply_video(update: Update, context: CallbackContext) -> int:
    """Handle video replies."""
    user_id = update.effective_user.id
    video = update.message.video
    text = update.message.caption or ""

    # Get comment ID from user data
    comment_id = context.user_data.get("reply_comment_id")

    if not comment_id:
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END

    # Check video size (10MB limit)
    if video.file_size > 10 * 1024 * 1024:  # 10MB in bytes
        await update.message.reply_text(
            "حجم ویدیو بیشتر از 10 مگابایت است. لطفاً ویدیو کوچکتری ارسال کنید.",
            reply_markup=create_cancel_button()
        )
        return REPLY

    try:
        # Get video file
        video_file = await video.get_file()

        # Generate a unique filename
        file_extension = "mp4"
        filename = f"reply_{user_id}_{int(datetime.now().timestamp())}.{file_extension}"
        # Save the video to a directory (you need to implement this)
        # For example: media_url = await save_media_file(video_file, filename)
        media_url = f"media/replies/{filename}"  # This is just a placeholder

        db = next(get_db())

        # Create reply with media
        reply = create_comment_reply(db, UUID(comment_id), user_id, text, media_url)
        success_message = "پاسخ شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."

        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=create_main_menu_buttons()
        )

    except Exception as e:
        # Log the error
        logger.error(f"Error creating reply with video: {e}")
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )

    # End the conversation
    return ConversationHandler.END

# Cancel reply conversation handler
async def cancel_reply(update: Update, context: CallbackContext) -> int:
    """Cancel reply conversation."""
    await update.message.reply_text(
        "پاسخ به نظر لغو شد.",
        reply_markup=create_main_menu_buttons()
    )
    return ConversationHandler.END

# Show replies callback handler
async def show_replies_callback(update: Update, context: CallbackContext) -> None:
    """Handle showing replies to a comment."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract comment ID and offset from callback data
        _,_, comment_id = query.data.split("_", 2)
        
        # Get comment details
        db = next(get_db())
        
        # Get approved replies for the comment
        replies = get_comment_replies(db, comment_id, ContentStatus.APPROVED)
        
        # اگر پاسخی وجود نداشت یا آفست بیشتر از تعداد پاسخ‌ها بود
        if not replies :
            await query.edit_message_text(
                "پاسخ بیشتری وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_comments")]
                ])
            )
            return
    
        # ابتدا پیام اصلی را به‌روزرسانی می‌کنیم
        await context.bot.send_message(
            text = f"پاسخ‌های نظر:",
            chat_id=update.effective_chat.id,
        )
        
        # نمایش هر نظر در یک پیام جداگانه (حداکثر ۵ نظر)
        for i, reply in enumerate(replies[:5], 1):
            user = get_user(db, reply.user_id)
            username = user.username if user and user.username else f"کاربر {reply.user_id}"
            # متن نظر
            comment_text = f"💬 نظر #{i}:\n\n"
            comment_text += f"👤 {username}:\n{reply.text}\n"
            
            # اگر رسانه داشت
            if reply.media_url:
                comment_text += "\n🖼️ [دارای تصویر یا ویدیو]\n"
            
            # تعداد پاسخ‌ها
            reply_count = len(get_comment_replies(db, reply.reply_id, ContentStatus.APPROVED))
            if reply_count > 0:
                comment_text += f"\n↩️ {reply_count} پاسخ\n"
            
            # دکمه‌های هر نظر
            comment_keyboard = create_reply_comment_buttons(str(reply.reply_id), has_replies=bool(reply_count))
            
            # ارسال پیام نظر
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=comment_text,
                reply_markup=comment_keyboard
            )
        
        # پیام نهایی با دکمه‌های اصلی
        final_keyboard = []
        
        if 5 < len(replies):
            final_keyboard.append([InlineKeyboardButton(f"👁️ نمایش {len(replies) - 5} پاسخ دیگر", callback_data=f"show_replies_{comment_id}_{5}")])
        
        # دکمه‌های اصلی
        final_keyboard.append([InlineKeyboardButton("💬 افزودن پاسخ", callback_data=f"reply_{comment_id}")])
        final_keyboard.append([InlineKeyboardButton("🔙 بازگشت به نظرات", callback_data="back_to_comments")])
        
        # ارسال پیام نهایی
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="برای ادامه یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(final_keyboard)
        )
        
    except Exception as e:
        # Handle any other exceptions
        logger = logging.getLogger(__name__)
        logger.error(f"Error in show_replies_callback: {str(e)}")
        logger.exception("Full traceback:")
        await query.edit_message_text(
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید.\n{e}",
            reply_markup=create_main_menu_buttons()
        )
#########################################
#
########################################
async def reply_to_reply_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation to reply to a reply."""
    query = update.callback_query
    await query.answer(show_alert=False)

    # Extract reply ID from callback data
    _,_,_, reply_id = query.data.split("_", 3)

    # Save reply ID in user data
    context.user_data["reply_to_reply_id"] = reply_id

    await context.bot.send_message(
        text="لطفاً پاسخ خود را بنویسید. می‌توانید متن، عکس یا ویدیو ارسال کنید (حداکثر حجم: 10MB).",
        chat_id=update.effective_chat.id,
        reply_markup=create_cancel_button()
    )
    return REPLY

# Handle text replies to a reply
async def handle_reply_to_reply_text(update: Update, context: CallbackContext) -> int:
    """Handle text replies to a reply."""
    user_id = update.effective_user.id
    text = update.message.text

    # Get reply ID from user data
    reply_id = context.user_data.get("reply_to_reply_id")

    if not reply_id:
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END

    try:
        db = next(get_db())
        
        # دریافت اطلاعات پاسخ والد
        parent_reply = db.query(CommentReply).filter(CommentReply.reply_id == UUID(reply_id)).first()
        if not parent_reply:
            await update.message.reply_text(
                "پاسخ مورد نظر یافت نشد. لطفاً دوباره تلاش کنید.",
                reply_markup=create_main_menu_buttons()
            )
            return ConversationHandler.END
            
        # Create reply
        reply = create_comment_reply(
            db=db, 
            comment_id=parent_reply.comment_id,  # استفاده از comment_id پاسخ والد
            user_id=user_id, 
            text=text,
            parent_reply_id=UUID(reply_id)  # تنظیم parent_reply_id
        )
        success_message = "پاسخ شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."

        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=create_main_menu_buttons()
        )

    except Exception as e: 
        # Log the error
        logger.error(f"Error creating reply to reply: {e}")
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )

    # End the conversation
    return ConversationHandler.END

# Handle photo replies to a reply
async def handle_reply_to_reply_photo(update: Update, context: CallbackContext) -> int:
    """Handle photo replies to a reply."""
    user_id = update.effective_user.id
    photo = update.message.photo[-1]  # Get the largest photo
    text = update.message.caption or ""

    # Get reply ID from user data
    reply_id = context.user_data.get("reply_to_reply_id")

    if not reply_id:
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END

    # Check photo size (10MB limit)
    if photo.file_size > 10 * 1024 * 1024:  # 10MB in bytes
        await update.message.reply_text(
            "حجم عکس بیشتر از 10 مگابایت است. لطفاً عکس کوچکتری ارسال کنید.",
            reply_markup=create_cancel_button()
        )
        return REPLY
    try:
        # Get photo file
        photo_file = await photo.get_file()

        # Generate a unique filename
        file_extension = "jpg"
        filename = f"reply_{user_id}_{int(datetime.now().timestamp())}.{file_extension}"
        # Save the photo to a directory (you need to implement this)
        # For example: media_url = await save_media_file(photo_file, filename)
        media_url = f"media/replies/{filename}"  # This is just a placeholder

        db = next(get_db())
        
        # دریافت اطلاعات پاسخ والد
        parent_reply = db.query(CommentReply).filter(CommentReply.reply_id == UUID(reply_id)).first()
        if not parent_reply:
            await update.message.reply_text(
                "پاسخ مورد نظر یافت نشد. لطفاً دوباره تلاش کنید.",
                reply_markup=create_main_menu_buttons()
            )
            return ConversationHandler.END

        # Create reply with media
        reply = create_comment_reply(
            db=db, 
            comment_id=parent_reply.comment_id,
            user_id=user_id, 
            text=text, 
            media_url=media_url,
            parent_reply_id=UUID(reply_id)
        )
        success_message = "پاسخ شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."

        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=create_main_menu_buttons()
        )

    except Exception as e:
        # Log the error
        logger.error(f"Error creating reply to reply with photo: {e}")
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )

    # End the conversation
    return ConversationHandler.END

# Handle video replies to a reply
async def handle_reply_to_reply_video(update: Update, context: CallbackContext) -> int:
    """Handle video replies to a reply."""
    user_id = update.effective_user.id
    video = update.message.video
    text = update.message.caption or ""

    # Get reply ID from user data
    reply_id = context.user_data.get("reply_to_reply_id")

    if not reply_id:
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END

    # Check video size (10MB limit)
    if video.file_size > 10 * 1024 * 1024:  # 10MB in bytes
        await update.message.reply_text(
            "حجم ویدیو بیشتر از 10 مگابایت است. لطفاً ویدیو کوچکتری ارسال کنید.",
            reply_markup=create_cancel_button()
        )
        return REPLY

    try:
        # Get video file
        video_file = await video.get_file()

        # Generate a unique filename
        file_extension = "mp4"
        filename = f"reply_{user_id}_{int(datetime.now().timestamp())}.{file_extension}"
        # Save the video to a directory (you need to implement this)
        # For example: media_url = await save_media_file(video_file, filename)
        media_url = f"media/replies/{filename}"  # This is just a placeholder

        db = next(get_db())
        
        # دریافت اطلاعات پاسخ والد
        parent_reply = db.query(CommentReply).filter(CommentReply.reply_id == UUID(reply_id)).first()
        if not parent_reply:
            await update.message.reply_text(
                "پاسخ مورد نظر یافت نشد. لطفاً دوباره تلاش کنید.",
                reply_markup=create_main_menu_buttons()
            )
            return ConversationHandler.END

        # Create reply with media
        reply = create_comment_reply(
            db=db, 
            comment_id=parent_reply.comment_id,
            user_id=user_id, 
            text=text, 
            media_url=media_url,
            parent_reply_id=UUID(reply_id)
        )
        success_message = "پاسخ شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."

        # Send success message
        await update.message.reply_text(
            success_message,
            reply_markup=create_main_menu_buttons()
        )

    except Exception as e:
        # Log the error
        logger.error(f"Error creating reply to reply with video: {e}")
        await update.message.reply_text(
            "خطا در پاسخ به نظر. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )

    # End the conversation
    return ConversationHandler.END

# Cancel reply conversation handler
async def cancel_reply_to_reply(update: Update, context: CallbackContext) -> int:
    """Cancel reply conversation."""
    await update.message.reply_text(
        "پاسخ به نظر لغو شد.",
        reply_markup=create_main_menu_buttons()
    )
    return ConversationHandler.END

# Show replies to a reply callback handler
async def show_replies_to_reply_callback(update: Update, context: CallbackContext) -> None:
    """Handle showing replies to a reply."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract reply ID and offset from callback data
        _,_,_, reply_id = query.data.split("_", 3)
        
        # Get reply details
        db = next(get_db())
        parent_reply = db.query(CommentReply).filter(CommentReply.reply_id == UUID(reply_id)).first()
        
        if not parent_reply:
            await query.edit_message_text(
                "پاسخ مورد نظر یافت نشد. لطفاً دوباره تلاش کنید.",
                reply_markup=create_main_menu_buttons()
            )
            return
        
        # Get approved replies for the reply
        replies = get_reply_replies(db, UUID(reply_id), ContentStatus.APPROVED)
        
        # اگر پاسخی وجود نداشت
        if not replies:
            await query.edit_message_text(
                "پاسخ بیشتری وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_comments")]
                ])
            )
            return
    
        # ابتدا پیام اصلی را به‌روزرسانی می‌کنیم
        parent_user = get_user(db, parent_reply.user_id)
        parent_username = parent_user.username if parent_user and parent_user.username else f"کاربر {parent_reply.user_id}"
        
        await context.bot.send_message(
            text = f"↩️ پاسخ‌های {parent_username}:\n\n{parent_reply.text}",
            chat_id=update.effective_chat.id,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به نظرات", callback_data="back_to_comments")]
            ])
        )
        
        # نمایش هر پاسخ در یک پیام جداگانه (حداکثر ۵ پاسخ)
        for i, reply in enumerate(replies[:5], 1):
            user = get_user(db, reply.user_id)
            username = user.username if user and user.username else f"کاربر {reply.user_id}"
            # متن پاسخ
            reply_text = f"↩️ پاسخ #{i}:\n\n"
            reply_text += f"👤 {username}:\n{reply.text}\n"
            
            # اگر رسانه داشت
            if reply.media_url:
                reply_text += "\n🖼️ [دارای تصویر یا ویدیو]\n"
            
            # تعداد پاسخ‌های این پاسخ
            nested_replies_count = len(get_reply_replies(db, reply.reply_id, ContentStatus.APPROVED))
            if nested_replies_count > 0:
                reply_text += f"\n↩️ {nested_replies_count} پاسخ\n"
            
            # دکمه‌های هر پاسخ
            reply_keyboard = create_reply_to_reply_buttons(str(reply.reply_id), has_replies=bool(nested_replies_count))
            
            # ارسال پیام پاسخ
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=reply_text,
                reply_markup=reply_keyboard
            )
        
        # پیام نهایی با دکمه‌های اصلی
        final_keyboard = []
        
        if len(replies) > 5:
            final_keyboard.append([InlineKeyboardButton(f"👁️ نمایش {len(replies) - 5} پاسخ دیگر", callback_data=f"show_more_replies_{reply_id}_5")])
        
        # دکمه‌های اصلی
        final_keyboard.append([InlineKeyboardButton("💬 افزودن پاسخ", callback_data=f"reply_to_reply_{reply_id}")])
        final_keyboard.append([InlineKeyboardButton("🔙 بازگشت به نظرات", callback_data="back_to_comments")])
        
        # ارسال پیام نهایی
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="برای ادامه یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(final_keyboard)
        )
        
    except Exception as e:
        # Handle any other exceptions
        logger = logging.getLogger(__name__)
        logger.error(f"Error in show_replies_to_reply_callback: {str(e)}")
        logger.exception("Full traceback:")
        await query.edit_message_text(
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید.\n{e}",
            reply_markup=create_main_menu_buttons()
        )

async def create_reply_to_reply_buttons(reply_id: str, has_replies: bool = False) -> InlineKeyboardMarkup:
    """Create buttons for replying to a reply."""
    buttons = []
    
    # دکمه پاسخ به این پاسخ
    buttons.append([InlineKeyboardButton("↩️ پاسخ به این پاسخ", callback_data=f"reply_to_reply_{reply_id}")])
    
    # اگر پاسخ‌هایی وجود داشت، دکمه نمایش پاسخ‌ها را اضافه می‌کنیم
    if has_replies:
        buttons.append([InlineKeyboardButton("👁️ مشاهده پاسخ‌ها", callback_data=f"show_replies_to_reply_{reply_id}")])
    
    # دکمه بازگشت
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_comments")])
    
    return InlineKeyboardMarkup(buttons)

# Show more replies to a reply callback handler
async def show_more_replies_callback(update: Update, context: CallbackContext) -> None:
    """Handle showing more replies to a reply."""
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract reply ID and offset from callback data
        _,_,_, reply_id, offset = query.data.split("_", 4)
        offset = int(offset)
        
        # Get reply details
        db = next(get_db())
        parent_reply = db.query(CommentReply).filter(CommentReply.reply_id == UUID(reply_id)).first()
        
        if not parent_reply:
            await query.edit_message_text(
                "پاسخ مورد نظر یافت نشد. لطفاً دوباره تلاش کنید.",
                reply_markup=create_main_menu_buttons()
            )
            return
        
        # Get approved replies for the reply
        replies = get_reply_replies(db, UUID(reply_id), ContentStatus.APPROVED)
        
        # اگر پاسخی وجود نداشت یا آفست بیشتر از تعداد پاسخ‌ها بود
        if not replies or offset >= len(replies):
            await query.edit_message_text(
                "پاسخ بیشتری وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_comments")]
                ])
            )
            return
        
        # تعداد پاسخ‌های باقیمانده
        remaining_replies = replies[offset:]
        
        # تعداد پاسخ‌هایی که نمایش داده می‌شوند (حداکثر ۵ پاسخ)
        display_count = min(5, len(remaining_replies))
        
        # ابتدا پیام اصلی را به‌روزرسانی می‌کنیم
        parent_user = get_user(db, parent_reply.user_id)
        parent_username = parent_user.username if parent_user and parent_user.username else f"کاربر {parent_reply.user_id}"
        
        await query.edit_message_text(
            f"↩️ پاسخ‌های بیشتر به {parent_username}:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به نظرات", callback_data="back_to_comments")]
            ])
        )
        
        # نمایش هر پاسخ در یک پیام جداگانه
        for i, reply in enumerate(remaining_replies[:display_count], offset + 1):
            user = get_user(db, reply.user_id)
            username = user.username if user and user.username else f"کاربر {reply.user_id}"
            
            # متن پاسخ
            reply_text = f"↩️ پاسخ #{i}:\n\n"
            reply_text += f"👤 {username}:\n{reply.text}\n"
            
            # اگر رسانه داشت
            if reply.media_url:
                reply_text += "\n🖼️ [دارای تصویر یا ویدیو]\n"
            
            # تعداد پاسخ‌های این پاسخ
            nested_replies_count = len(get_reply_replies(db, reply.reply_id, ContentStatus.APPROVED))
            if nested_replies_count > 0:
                reply_text += f"\n↩️ {nested_replies_count} پاسخ\n"
            
            # دکمه‌های هر پاسخ
            reply_keyboard = create_reply_to_reply_buttons(str(reply.reply_id), has_replies=bool(nested_replies_count))
            
            # ارسال پیام پاسخ
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=reply_text,
                reply_markup=reply_keyboard
            )
        
        # پیام نهایی با دکمه‌های اصلی
        final_keyboard = []
        
        # اگر پاسخ‌های بیشتری باقی مانده بود
        new_offset = offset + display_count
        if new_offset < len(replies):
            final_keyboard.append([InlineKeyboardButton(f"👁️ نمایش {len(replies) - new_offset} پاسخ دیگر", callback_data=f"show_more_replies_{reply_id}_{new_offset}")])
        
        # دکمه‌های اصلی
        final_keyboard.append([InlineKeyboardButton("💬 افزودن پاسخ", callback_data=f"reply_to_reply_{reply_id}")])
        final_keyboard.append([InlineKeyboardButton("🔙 بازگشت به نظرات", callback_data="back_to_comments")])
        
        # ارسال پیام نهایی
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="برای ادامه یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(final_keyboard)
        )
        
    except Exception as e:
        # Handle any other exceptions
        logger = logging.getLogger(__name__)
        logger.error(f"Error in show_more_replies_callback: {str(e)}")
        logger.exception("Full traceback:")
        await query.edit_message_text(
            f"خطایی رخ داد. لطفاً دوباره تلاش کنید.\n{e}",
            reply_markup=create_main_menu_buttons()
        )
############################################

# اضافه کردن هندلر جدید برای افزودن آیتم

############################################
async def add_item_callback(update: Update, context: CallbackContext) -> int:
    """Handle adding a new item."""
    query = update.callback_query
    await query.answer()
    
    # Extract item type from callback data
    _,_, item_type = query.data.split("_", 2)
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

################################

# rate item callback handler

###############################
async def rate_item_callback(update: Update, context: CallbackContext):
    """Handle rating for items and questions."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    try:
        # Extract target type, ID and score from callback data
        _,_, target_type, target_id, score = query.data.split("_", 4)
        score = int(score)
        
        # Create rating
        db = next(get_db())
        logging.info(f"Rating item {target_type} {target_id} with score {score}")
        # Create rating based on target type
        if target_type in ["devices", "liquid"]:
            
            rating = create_item_rating(db, user_id, UUID(target_id), score)
            if rating:
                await query.answer(f"امتیاز {score} با موفقیت ثبت شد!")
            else:
                await query.answer("شما قبلاً به این مورد امتیاز داده‌اید.")
            
            # Store the clean item_id in context.user_data
            context.user_data["current_item_id"] = target_id
            
            # Create a new callback query object with the correct item_id for the refresh
            # Format should be: item_[type]_[category]_[id]
            category = context.user_data.get("current_category", "unknown")
            new_callback_data = f"item_{context.user_data.get('current_itemtype', 'unknown')}_{category}_{target_id}"
            
            # Update the callback data
            query.data = new_callback_data
            
            # Refresh the item details
            await item_detail_callback(update, context)
            
        else:
            await query.answer("نوع هدف نامعتبر است.")
            return
            
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in rate_callback: {e}")
        await query.answer("خطایی رخ داد. لطفاً دوباره تلاش کنید.")

#############################

# register item callback handlers

#############################
def register_item_callback_handlers(application):
    """Register callback handlers for items."""
    application.add_handler(CallbackQueryHandler(devices_callback, pattern="^devices$"))
    application.add_handler(CallbackQueryHandler(liquids_callback, pattern="^liquids$"))
    application.add_handler(CallbackQueryHandler(device_category_callback, pattern="^devices_(permanent|disposable)$"))
    application.add_handler(CallbackQueryHandler(liquid_category_callback, pattern="^liquid_(salt|juice)$"))
    application.add_handler(CallbackQueryHandler(page_callback, pattern="^page_"))
    application.add_handler(CallbackQueryHandler(item_detail_callback, pattern="^item_"))
    application.add_handler(CallbackQueryHandler(show_replies_callback, pattern="^show_replies_"))
    
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
    
    application.add_handler(CallbackQueryHandler(rate_item_callback,pattern="^rate_item_"))  
    
    #
    comment_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(comment_callback, pattern="^comment_")],
        states={
            COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_comment_text),
                MessageHandler(filters.PHOTO, handle_comment_photo),
                MessageHandler(filters.VIDEO, handle_comment_video),
                CallbackQueryHandler(cancel_callback, pattern="^cancel$")
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^cancel$")],
    )
    
    application.add_handler(comment_conv_handler)
    application.add_handler(CallbackQueryHandler(more_comments_callback, pattern="^more_comments_"))
    application.add_handler(CallbackQueryHandler(item_comments_callback, pattern="^comments_"))
    application.add_handler(CallbackQueryHandler(view_comment_callback, pattern="^viewcomment_"))
    application.add_handler(CallbackQueryHandler(more_comments_callback, pattern="^more_comments_"))
    #
    comment_reply_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(reply_comment_callback, pattern="^reply_comment_")],
        states={
            REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_text),
                MessageHandler(filters.PHOTO, handle_reply_photo),
                MessageHandler(filters.VIDEO, handle_reply_video),
                CallbackQueryHandler(cancel_reply, pattern="^cancel$")
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_reply, pattern="^cancel$")],

    )
    application.add_handler(comment_reply_conv_handler)
    #
    reply_to_reply_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(reply_to_reply_callback,pattern="^reply_to_reply_")],
        states={
        REPLY:[
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_to_reply_text),
            MessageHandler(filters.PHOTO, handle_reply_to_reply_photo),
            MessageHandler(filters.VIDEO, handle_reply_to_reply_video),
            CallbackQueryHandler(cancel_reply_to_reply, pattern="^cancel$")
        ],
        },
        fallbacks=[CallbackQueryHandler(cancel_reply_to_reply, pattern="^cancel$")],

    )
    application.add_handler(reply_to_reply_conv_handler)
    application.add_handler(CallbackQueryHandler(show_replies_to_reply_callback,pattern="^replies_to_reply_"))
    
    
    