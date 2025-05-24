from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler , filters ,CommandHandler
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime
import logging
from database.db_handler import get_db
from database.db_operations import (
    get_items_by_type, get_item, get_comments_by_item, get_comment_replies,
    create_item_rating, 
    get_user, create_item, create_comment, create_comment_reply,
    create_item_rating , count_direct_replies_to_comment, count_sub_replies,get_reply_replies
)
from database.models import ItemType, ContentStatus, TargetType , CommentReply , Comment

from utils.buttons import (
    create_main_menu_buttons,
    create_cancel_button,
)
from utils.items.item_buttons import (
    create_device_category_buttons,create_liquid_category_buttons,
    create_item_list_buttons,create_item_detail_buttons,
    create_comment_buttons
)
from utils.callback_handlers import (
    cancel_callback
)
NAME,DESCRIPTION,COMMENT, REPLY ,REPLY_AWAITING_CONTENT = range(5)

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
        # Save total comments count to user data
        context.user_data["total_comments"] = i
        # اگر نظرات بیشتر از ۵ تا بود
        
        if len(comments) > 5:
            final_keyboard.append([InlineKeyboardButton(f"👁️ نمایش {(len(comments) - context.user_data['total_comments'])%5} نظر دیگر",
                                                        callback_data=f"more_comments_{item_id}")])
        
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
        _,_, item_id = query.data.split("_", 2)
        
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
        if not comments or context.user_data['total_comments'] >= len(comments):
            await query.edit_message_text(
                "نظر بیشتری وجود ندارد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_category', 'unknown')}_{item_id}")]
                ])
            )
            return
        
        # تعداد نظرات باقیمانده
        remaining_comments = (len(comments) - context.user_data['total_comments']) % 5
        remaining_comments += context.user_data['total_comments']
        
        # ابتدا پیام اصلی را به‌روزرسانی می‌کنیم
        await query.edit_message_text(
            f"💬 نظرات بیشتر برای {item.name}:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات محصول", callback_data=f"item_{context.user_data.get('current_category', 'unknown')}_{item_id}")]
            ])
        )
        
        # نمایش هر نظر در یک پیام جداگانه
        for i, comment in enumerate(comments[context.user_data['total_comments']:remaining_comments], context.user_data['total_comments']):
            remaining_comments += 1
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
        context.user_data['total_comments'] = remaining_comments
        # اگر نظرات بیشتری باقی مانده بود

        if remaining_comments < len(comments):
            final_keyboard.append([InlineKeyboardButton(f"👁️ نمایش {(len(comments) - context.user_data['total_comments'])%5} نظر دیگر",
                                                        callback_data=f"more_comments_{item_id}")])
        
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

###########################################################

# Reply to comment callback handler - start conversation

###########################################################
# Reply to comment callback handler - start conversation
async def reply_comment_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation to reply to a comment."""
    query = update.callback_query
    await query.answer(show_alert=False)
    
    # Extract comment ID from callback data
    try:
        _, _, comment_id_str = query.data.split("_", 2)
        UUID(comment_id_str) # Validate UUID format
    except (ValueError, IndexError):
        logger.error(f"Invalid callback data for reply_comment_callback: {query.data}")
        await query.edit_message_text("خطا: اطلاعات نامعتبر برای پاسخ به نظر.")
        return ConversationHandler.END
        
    context.user_data["current_reply_root_comment_id"] = comment_id_str
    context.user_data["current_reply_parent_reply_id"] = None  # Replying to the main comment directly
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="لطفاً پاسخ خود را برای نظر اصلی بنویسید. (متن، عکس، ویدیو - حداکثر 10MB).",
        reply_markup=create_cancel_button()
    )
    return REPLY

# Start conversation to reply to ANOTHER REPLY
async def init_reply_to_reply_callback(update: Update, context: CallbackContext) -> int:
    """Start conversation to reply to another reply."""
    query = update.callback_query
    await query.answer(show_alert=False)
    
    # Callback data format: "init_reply_to_reply_{root_comment_id}_{parent_reply_id}"
    try:
        parts = query.data.split("_")
        # Assuming callback data: "rtr_{root_comment_id}_{parent_reply_id}"
        # This parsing needs to be robust based on your actual callback data string
        action_prefix,parent_reply_id_str = query.data.split("_", 1)
        if action_prefix != "rtr": # Reply To Reply
            raise ValueError("Invalid action prefix for reply to reply")

        UUID(parent_reply_id_str)
    except (ValueError, IndexError):
        logging.error(f"Invalid callback data for init_reply_to_reply_callback: {query.data}")
        await query.edit_message_text("خطا: اطلاعات نامعتبر برای پاسخ به پاسخ.")
        return ConversationHandler.END
        
    context.user_data["current_reply_parent_reply_id"] = parent_reply_id_str
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="شما در حال پاسخ به یک پاسخ دیگر هستید. لطفاً پاسخ خود را بنویسید. (متن، عکس، ویدیو - حداکثر 10MB).",
        reply_markup=create_cancel_button()
    )
    return REPLY

# Internal helper to process reply submission
async def _process_reply_submission(update: Update, context: CallbackContext, text: str, media_url: str | None = None) -> int:
    user_id = update.effective_user.id
    
    root_comment_id_str = context.user_data.get("current_reply_root_comment_id")
    # parent_reply_id_str can be None if replying to a main comment
    parent_reply_id_str = context.user_data.get("current_reply_parent_reply_id") 

    if not root_comment_id_str:
        await update.message.reply_text(
            "خطا در شناسایی نظر اصلی. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return ConversationHandler.END

    try:
        db = next(get_db()) # Ensure get_db() is properly managed (e.g., contextmanager)

        root_comment_id_uuid = context.user_data.get("current_reply_root_comment_id")
        parent_reply_id_uuid = context.user_data.get("current_reply_parent_reply_id")

        # Call your existing CRUD function for creating a reply
        reply = create_comment_reply(
            db=db,
            comment_id=root_comment_id_uuid,    # This is the root_comment_id
            user_id=user_id,
            text=text,
            media_url=media_url,
            parent_reply_id=parent_reply_id_uuid # This will be None or the UUID of the parent CommentReply
        )
        # The CRUD function `create_comment_reply` already sets status to APPROVED.
        success_message = "پاسخ شما با موفقیت ثبت شد و پس از تأیید نمایش داده خواهد شد."
        await update.message.reply_text(success_message, reply_markup=create_main_menu_buttons())

    except ValueError:
        logging.error(f"Invalid UUID format provided: root='{root_comment_id_str}', parent='{parent_reply_id_str}'")
        await update.message.reply_text("خطا در قالب شناسه. لطفاً دوباره تلاش کنید.", reply_markup=create_main_menu_buttons())
    except Exception as e:
        logging.exception(f"Error creating reply submission (user: {user_id}): {e}") # Use logger.exception for traceback
        await update.message.reply_text("خطا در ثبت پاسخ. لطفاً دوباره تلاش کنید.", reply_markup=create_main_menu_buttons())
    return ConversationHandler.END

# Handle text replies
async def handle_reply_text(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    return await _process_reply_submission(update, context, text=text, media_url=None)

# Handle media replies (photo)
async def handle_reply_photo(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id # For filename
    photo = update.message.photo[-1]
    text = update.message.caption or ""

    if photo.file_size > 10 * 1024 * 1024:  # 10MB
        await update.message.reply_text("حجم عکس بیشتر از 10 مگابایت است.", reply_markup=create_cancel_button())
        return REPLY # Stay in REPLY state
    try:
        photo_file = await photo.get_file()
        # TODO: Implement actual file saving logic (async if possible)
        # media_url = await save_media_file(photo_file, f"reply_photo_{user_id}_{int(datetime.now().timestamp())}.jpg")
        media_url_placeholder = f"media/replies/photos/reply_photo_{user_id}_{int(datetime.now().timestamp())}.jpg" # Placeholder
        return await _process_reply_submission(update, context, text=text, media_url=media_url_placeholder)
    except Exception as e:
        logger.exception(f"Error processing/saving photo reply for user {user_id}: {e}")
        await update.message.reply_text("خطا در پردازش عکس. لطفاً دوباره تلاش کنید.", reply_markup=create_main_menu_buttons())
        context.user_data.pop("current_reply_root_comment_id", None) # Clean up state on error too
        context.user_data.pop("current_reply_parent_reply_id", None)
        return ConversationHandler.END

# Handle media replies (video)
async def handle_reply_video(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id # For filename
    video = update.message.video
    text = update.message.caption or ""

    if video.file_size > 10 * 1024 * 1024:  # 10MB
        await update.message.reply_text("حجم ویدیو بیشتر از 10 مگابایت است.", reply_markup=create_cancel_button())
        return REPLY # Stay in REPLY state

    try:
        video_file = await video.get_file()
        # TODO: Implement actual file saving logic (async if possible)
        # media_url = await save_media_file(video_file, f"reply_video_{user_id}_{int(datetime.now().timestamp())}.mp4")
        media_url_placeholder = f"media/replies/videos/reply_video_{user_id}_{int(datetime.now().timestamp())}.mp4" # Placeholder
        return await _process_reply_submission(update, context, text=text, media_url=media_url_placeholder)
    except Exception as e:
        logger.exception(f"Error processing/saving video reply for user {user_id}: {e}")
        await update.message.reply_text("خطا در پردازش ویدیو. لطفاً دوباره تلاش کنید.", reply_markup=create_main_menu_buttons())
        context.user_data.pop("current_reply_root_comment_id", None)
        context.user_data.pop("current_reply_parent_reply_id", None)
        return ConversationHandler.END

# Cancel reply conversation handler
async def cancel_reply_conversation(update: Update, context: CallbackContext) -> int:
    """Cancels the current reply conversation."""
    # Determine if it's a callback query or a message
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("عملیات پاسخ لغو شد.", reply_markup=create_main_menu_buttons())
    elif update.message:
        await update.message.reply_text("عملیات پاسخ لغو شد.", reply_markup=create_main_menu_buttons())
    
    context.user_data.pop("current_reply_root_comment_id", None)
    context.user_data.pop("current_reply_parent_reply_id", None)
    return ConversationHandler.END

# Show replies (generalized for root comment or sub-replies)
async def show_replies_or_sub_replies_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    # Callback data format: "show_replies_{root_comment_id}_{parent_id_str}_{offset_str}"
    # parent_id_str can be "ROOT" or a UUID of the parent reply.
    try:
        parts = query.data.split("_")
        action = parts[0] + "_" + parts[1] # "show_replies"
        logging.info(f"parts: {query.data}")
        if action != "show_replies" or len(parts) < 5: #  show_replies_rootcommentid_parentid_offset
            raise ValueError("Invalid callback data format")
            
        root_comment_id_str = parts[2] # ROOT or UUID string
        context.user_data["current_reply_root_comment_id"] = root_comment_id_str
        parent_id_str = parts[3]  # "ROOT" or UUID string
        offset = int(parts[4])
        limit = 3 # Display fewer replies per message for clarity in a tree

        if root_comment_id_str != "ROOT":
            UUID(root_comment_id_str) # Validate root_comment_id
        if parent_id_str != "ROOT":
            UUID(parent_id_str) # Validate parent_id if it's not ROOT

    except (ValueError, IndexError) as e:
        logging.error(f"Invalid callback data for show_replies: {query.data}, error: {e}")
        await query.edit_message_text("خطا: اطلاعات نامعتبر برای نمایش پاسخ‌ها.")
        return

    db = next(get_db())
    current_replies_list: List[CommentReply] = []
    total_at_this_level: int = 0
    header_message = ""
    
    root_comment_uuid = UUID(root_comment_id_str) if not "ROOT" else context.user_data.get("current_reply_root_comment_id")

    # Fetching data based on whether it's for root comment or a sub-reply
    if parent_id_str == "ROOT":
        # TODO: Fetch the main comment's text to show as header if desired
        # main_comment = db.query(Comment).filter(Comment.comment_id == root_comment_uuid).first()
        # if main_comment: header_message = f"پاسخ‌ها به نظر: \"{main_comment.text[:30]}...\"\n\n"
        # else: header_message = "پاسخ‌ها به نظر اصلی:\n\n"
        header_message = "پاسخ‌ها به نظر اصلی:\n\n"
        current_replies_list = get_comment_replies(db, root_comment_uuid, ContentStatus.APPROVED)
        total_at_this_level = count_direct_replies_to_comment(db, root_comment_uuid, ContentStatus.APPROVED)
    else:
        parent_reply_uuid = UUID(parent_id_str)
        # TODO: Fetch the parent reply's text to show as header if desired
        # parent_reply_for_header = db.query(CommentReply).filter(CommentReply.reply_id == parent_reply_uuid).first()
        # if parent_reply_for_header: header_message = f"پاسخ‌های داخلی به: \"{parent_reply_for_header.text[:30]}...\"\n\n"
        # else: header_message = f"پاسخ‌های داخلی:\n\n"
        header_message = "پاسخ‌های داخلی:\n\n"
        current_replies_list = get_reply_replies(db, parent_reply_uuid, ContentStatus.APPROVED)
        total_at_this_level = count_sub_replies(db, parent_reply_uuid, ContentStatus.APPROVED)

    if not current_replies_list and offset == 0:
        no_replies_text = header_message + "هیچ پاسخی در این سطح ثبت نشده است."
        # Simplified back button logic for now
        back_button_cb = f"show_comments_for_item_{root_comment_id_str}" # Needs item_id, or back to comment
        if parent_id_str != "ROOT": # If viewing sub-replies, back goes to parent's replies (or root comment replies)
             # This needs the parent of the current parent_id_str or the root_comment_id
             # For simplicity, back to root replies of the original comment
             # Needs a way to get the original comment if we only have parent_reply_uuid
             original_comment_of_thread = db.execute(select(CommentReply.comment_id).where(CommentReply.reply_id == parent_reply_uuid)).scalar_one_or_none() if parent_id_str != "ROOT" else root_comment_uuid
             if original_comment_of_thread:
                back_button_cb = f"show_replies_{str(original_comment_of_thread)}_ROOT_0"

        await query.edit_message_text(no_replies_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=back_button_cb)]]))
        return

    # To avoid hitting message limits, send header, then each reply, then pagination.
    # Editing the original message might be too complex if many replies.
    await context.bot.send_message(chat_id=update.effective_chat.id, text=header_message)

    for reply in current_replies_list:
        user = get_user(db, reply.user_id) # Assume get_user exists
        username = user.username if user and user.username else f"کاربر گمنام ({reply.user_id % 1000})" # Avoid showing full ID
        
        reply_display_text = f"👤 {username}:\n{reply.text}"
        if reply.media_url:
            reply_display_text += f"\n🖼️ [رسانه]" # You might want to send media directly if it's just one

        buttons_for_this_reply_row = []
        # Button to reply to *this* reply (passes root_comment_id and this reply.reply_id as parent)
        buttons_for_this_reply_row.append(
            [InlineKeyboardButton(f"↪️ پاسخ به این", callback_data=f"rtr_{reply.reply_id}")]
        )
        
        num_sub_replies = count_sub_replies(db, reply.reply_id, ContentStatus.APPROVED)
        if num_sub_replies > 0:
            buttons_for_this_reply_row.append(
                [InlineKeyboardButton(f"👁️ {num_sub_replies} پاسخ داخلی", callback_data=f"show_replies_ROOT_{reply.reply_id}_0")]
            )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=reply_display_text,
            reply_markup=InlineKeyboardMarkup(buttons_for_this_reply_row) if buttons_for_this_reply_row else None,
            # Consider sending media if reply.media_url and it's a photo/video:
            # if reply.media_url and is_photo(reply.media_url): await context.bot.send_photo(...)
        )

    # Pagination and Global Actions
    final_buttons_layout = []
    pagination_row = []
    if offset > 0:
        pagination_row.append(
            InlineKeyboardButton("صفحه قبل", callback_data=f"show_replies_ROOT_{parent_id_str}_{max(0, offset - limit)}")
        )
    if offset + len(current_replies_list) < total_at_this_level:
        pagination_row.append(
            InlineKeyboardButton("صفحه بعد", callback_data=f"show_replies_ROOT_{parent_id_str}_{offset + limit}")
        )
    if pagination_row:
        final_buttons_layout.append(pagination_row)

    # Button to add a new reply at the *current viewing level*
    if parent_id_str == "ROOT":
        final_buttons_layout.append([InlineKeyboardButton("💬 افزودن پاسخ به نظر اصلی", callback_data=f"reply_comment_{root_comment_id_str}")])
    else: # We are viewing sub-replies of parent_id_str
        final_buttons_layout.append([InlineKeyboardButton(f"💬 افزودن پاسخ به این سطح", callback_data=f"rtr_{root_comment_id_str}_{parent_id_str}")])

    # Back button logic needs to be robust.
    # If viewing sub-replies (parent_id_str is a UUID), "Back" should go to the parent of these sub-replies.
    # This means finding the parent of parent_id_str or going to ROOT.
    if parent_id_str != "ROOT":
        current_parent_reply = db.execute(select(CommentReply.parent_reply_id, CommentReply.comment_id).where(CommentReply.reply_id == UUID(parent_id_str))).first()
        if current_parent_reply:
            grandparent_reply_id = current_parent_reply.parent_reply_id
            actual_root_comment_id = current_parent_reply.comment_id # Should match root_comment_id_str
            if grandparent_reply_id: # Go to grandparent's replies
                 final_buttons_layout.append([InlineKeyboardButton("🔙 بازگشت به سطح بالاتر", callback_data=f"show_replies_{str(actual_root_comment_id)}_{str(grandparent_reply_id)}_0")])
            else: # Parent was a direct reply to comment, so back to root replies
                 final_buttons_layout.append([InlineKeyboardButton("🔙 بازگشت به پاسخ های نظر اصلی", callback_data=f"show_replies_{str(actual_root_comment_id)}_ROOT_0")])
    else:
        # We are at replies for the main comment. "Back" could go to the list of comments for the item.
        # This depends on your overall bot structure.
        # Example: final_buttons_layout.append([InlineKeyboardButton("🔙 بازگشت به لیست نظرات", callback_data=f"view_item_comments_{ITEM_ID_HERE}")])
        pass # Add appropriate "back to main comments list" or "back to item" button if needed

    if final_buttons_layout:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="گزینه‌ها:",
            reply_markup=InlineKeyboardMarkup(final_buttons_layout)
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
    
    return NAME  # استفاده از حالت COMMENT برای دریافت نام محصول

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
    
    return DESCRIPTION  # استفاده از حالت REPLY برای دریافت توضیحات محصول

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
    application.add_handler(CallbackQueryHandler(show_replies_or_sub_replies_callback, pattern="^show_replies_"))
    
    # اضافه کردن هندلر مکالمه برای افزودن آیتم
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_item_callback, pattern="^add_item_")],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_item_description)],
        },
        fallbacks=[CallbackQueryHandler(cancel_callback, pattern="^cancel$")],
        per_message=False

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
        per_message=False
    )
    
    application.add_handler(comment_conv_handler)
    application.add_handler(CallbackQueryHandler(more_comments_callback, pattern="^more_comments_"))
    application.add_handler(CallbackQueryHandler(item_comments_callback, pattern="^comments_"))
    #
    comment_reply_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(reply_comment_callback, pattern="^reply_comment_"),
                      CallbackQueryHandler(init_reply_to_reply_callback, pattern=r"^rtr_")],
        states={
            REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_text),
                MessageHandler(filters.PHOTO, handle_reply_photo),
                MessageHandler(filters.VIDEO, handle_reply_video),
                CallbackQueryHandler(cancel_reply_conversation, pattern=r"^cancel_reply_conversation$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_reply_conversation),
                   CallbackQueryHandler(cancel_reply_conversation, pattern=r"^cancel_reply_conversation$"),],
        allow_reentry=True,
        per_message=False
    )
    application.add_handler(comment_reply_conv_handler)
    #

    
    