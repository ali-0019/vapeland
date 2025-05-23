from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
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
    create_main_menu_buttons, 
    create_cancel_button, create_back_to_main_button
)
from utils.questions.question_buttons import (
    create_tech_question_buttons,
    create_question_detail_buttons,
    create_question_reply_buttons,
    create_more_questions_buttons,
    create_question_replies_buttons
)

# حالت‌های مکالمه برای ثبت سوال یا ریپلای
ADD_QUESTION_TEXT, ADD_QUESTION_MEDIA, ADD_REPLY_TEXT, ADD_REPLY_MEDIA = range(4)

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
    
    # Save question ID in user data for future use
    context.user_data["current_question_id"] = str(question.question_id)
    
    await query.edit_message_text(
        question_details,
        reply_markup=create_question_detail_buttons(str(question.question_id))
    )

#################################

#add tech question callback

###################################
async def add_tech_question_callback(update: Update, context: CallbackContext) -> int:
    """Handle callback for adding a new technical question."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً متن سوال فنی خود را وارد کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
        ])
    )
    
    return ADD_QUESTION_TEXT


async def add_question_text_callback(update: Update, context: CallbackContext) -> int:
    """Handle receiving text for new technical question."""
    message = update.message
    context.user_data['question_text'] = message.text
    
    # Save the question to the database
    db = next(get_db())
    user_id = update.effective_user.id
    
    try:
        # Create the tech question in the database
        question = create_tech_question(
            db=db,
            user_id=user_id,
            text=context.user_data['question_text'],
        )
        db.commit()
        
        # Store question ID in user data
        context.user_data['current_question_id'] = str(question.question_id)
        
        # Ask if user wants to add media
        await message.reply_text(
            "سوال شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد.\n"
            "آیا می‌خواهید تصویر یا ویدیویی به سوال خود اضافه کنید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📷 افزودن رسانه", callback_data="add_question_media")],
                [InlineKeyboardButton("✅ اتمام", callback_data="finish_question")],
                [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
            ])
        )
        return ADD_QUESTION_MEDIA
        
    except Exception as e:
        db.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error in add_question_text_callback: {str(e)}")
        
        await message.reply_text(
            "خطا در ثبت سوال. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
        )
        return ConversationHandler.END
    
async def add_question_media_callback(update: Update, context: CallbackContext) -> int:
    """Handle adding media to a question."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً تصویر یا ویدیوی مورد نظر خود را ارسال کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
        ])
    )
    
    return ADD_QUESTION_MEDIA

async def add_question_media_handler(update: Update, context: CallbackContext) -> int:
    """Process the media file sent by user for a question."""
    message = update.message
    question_id = context.user_data.get('current_question_id')
    
    if not question_id:
        await message.reply_text(
            "خطا در پردازش درخواست. لطفاً دوباره تلاش کنید.",
            reply_markup=create_back_to_main_button()
        )
        return ConversationHandler.END
    
    # Get the file
    file = None
    media_type = None
    
    if message.photo:
        file = message.photo[-1].file_id
        media_type = "photo"
    elif message.video:
        file = message.video.file_id
        media_type = "video"
    elif message.document:
        file = message.document.file_id
        media_type = "document"
    else:
        await message.reply_text(
            "لطفاً یک تصویر یا ویدیو ارسال کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
            ])
        )
        return ADD_QUESTION_MEDIA
    
    # Save file_id to database
    db = next(get_db())
    try:
        # Update the question with media information
        question = get_tech_question(db, UUID(question_id))
        if question:
            question.media_url = file
            question.media_type = media_type
            db.commit()
            
            await message.reply_text(
                "رسانه با موفقیت به سوال شما اضافه شد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ اتمام", callback_data="finish_question")],
                    [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
                ])
            )
        else:
            await message.reply_text(
                "خطا در یافتن سوال. لطفاً دوباره تلاش کنید.",
                reply_markup=create_back_to_main_button()
            )
            return ConversationHandler.END
            
    except Exception as e:
        db.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error in add_question_media_handler: {str(e)}")
        
        await message.reply_text(
            "خطا در ذخیره رسانه. لطفاً دوباره تلاش کنید.",
            reply_markup=create_back_to_main_button()
        )
        return ConversationHandler.END
    
    return ADD_QUESTION_MEDIA

async def finish_question_callback(update: Update, context: CallbackContext) -> int:
    """Handle finishing question creation process."""
    query = update.callback_query
    await query.answer()
    
    question_id = context.user_data.get('current_question_id')
    
    if question_id:
        await query.edit_message_text(
            "سوال شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد. با تشکر از مشارکت شما!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
        )
    else:
        await query.edit_message_text(
            "خطا در پردازش درخواست. لطفاً دوباره تلاش کنید.",
            reply_markup=create_back_to_main_button()
        )
    
    # Clear user data
    if 'question_text' in context.user_data:
        del context.user_data['question_text']
    if 'current_question_id' in context.user_data:
        del context.user_data['current_question_id']
    
    return ConversationHandler.END

async def cancel_callback(update: Update, context: CallbackContext) -> int:
    """Cancel the current conversation."""
    query = update.callback_query
    await query.answer()
    
    # Clear user data
    if 'question_text' in context.user_data:
        del context.user_data['question_text']
    if 'current_question_id' in context.user_data:
        del context.user_data['current_question_id']
    
    await query.edit_message_text(
        "عملیات لغو شد.",
        reply_markup=create_main_menu_buttons()
    )
    
    return ConversationHandler.END

#############################

# امتیازدهی به سوال
async def rate_question_callback(update: Update, context: CallbackContext) -> None:
    """Handle question rating."""
    query = update.callback_query
    await query.answer()
    
    # استخراج شناسه سوال و امتیاز از داده‌های کال‌بک
    _, _, question_id, rating = query.data.split("_", 3)
    rating = int(rating)
    
    # ثبت امتیاز
    db = next(get_db())
    user_id = update.effective_user.id
    
    try:
        create_question_rating(db,user_id, UUID(question_id), rating)
        db.commit()
        
        await query.edit_message_text(
            f"امتیاز {rating} ستاره با موفقیت ثبت شد. با تشکر از شما!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات سوال", callback_data=f"question_{question_id}")]
            ])
        )
    except Exception as e:
        db.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error in rate_question_callback: {str(e)}")
        
        await query.edit_message_text(
            "خطا در ثبت امتیاز سوال. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات سوال", callback_data=f"question_{question_id}")]
            ])
        )
###############################

#add comment to question callback

###############################
async def reply_question_callback(update: Update, context: CallbackContext) -> int:
    """Handle callback for adding a reply to a question."""
    query = update.callback_query
    await query.answer()
    
    # Extract question ID from callback data
    _, _, question_id = query.data.split("_", 2)
    
    # Store question ID in user data for future use
    context.user_data["current_question_id"] = question_id
    
    await query.edit_message_text(
        "لطفاً پاسخ خود را برای این سوال وارد کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
        ])
    )
    
    return ADD_REPLY_TEXT


async def add_reply_text_callback(update: Update, context: CallbackContext) -> int:
    """Handle receiving text for a reply to a question."""
    message = update.message
    question_id = context.user_data.get("current_question_id")
    
    if not question_id:
        await message.reply_text(
            "خطا در پردازش درخواست. لطفاً دوباره تلاش کنید.",
            reply_markup=create_back_to_main_button()
        )
        return ConversationHandler.END
    
    # Save the reply text in user data
    context.user_data["reply_text"] = message.text
    
    # Save the reply to the database
    db = next(get_db())
    user_id = update.effective_user.id
    
    try:
        # Create the reply in the database
        reply = create_question_reply(
            db=db,
            user_id=user_id,
            question_id=UUID(question_id),
            text=context.user_data["reply_text"],
        )
        db.commit()
        
        # Store reply ID in user data
        context.user_data["current_reply_id"] = str(reply.reply_id)
        
        # Ask if user wants to add media
        await message.reply_text(
            "پاسخ شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد.\n"
            "آیا می‌خواهید تصویر یا ویدیویی به پاسخ خود اضافه کنید؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📷 افزودن رسانه", callback_data="add_reply_question_media_")],
                [InlineKeyboardButton("✅ اتمام", callback_data="finish_reply_question_")],
                [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
            ])
        )
        return ADD_REPLY_MEDIA
        
    except Exception as e:
        db.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error in add_reply_text_callback: {str(e)}")
        
        await message.reply_text(
            "خطا در ثبت پاسخ. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
        )
        return ConversationHandler.END

async def add_reply_media_callback(update: Update, context: CallbackContext) -> int:
    """Handle adding media to a reply."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "لطفاً تصویر یا ویدیوی مورد نظر خود را ارسال کنید:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
        ])
    )
    
    return ADD_REPLY_MEDIA

async def add_reply_media_handler(update: Update, context: CallbackContext) -> int:
    """Process the media file sent by user for a reply."""
    message = update.message
    reply_id = context.user_data.get("current_reply_id")
    
    if not reply_id:
        await message.reply_text(
            "خطا در پردازش درخواست. لطفاً دوباره تلاش کنید.",
            reply_markup=create_back_to_main_button()
        )
        return ConversationHandler.END
    
    # Get the file
    file = None
    media_type = None
    
    if message.photo:
        file = message.photo[-1].file_id
        media_type = "photo"
    elif message.video:
        file = message.video.file_id
        media_type = "video"
    elif message.document:
        file = message.document.file_id
        media_type = "document"
    else:
        await message.reply_text(
            "لطفاً یک تصویر یا ویدیو ارسال کنید.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
            ])
        )
        return ADD_REPLY_MEDIA
    
    # Save file_id to database
    db = next(get_db())
    try:
        # Get the reply and update with media information
        reply = db.query(QuestionReply).filter(QuestionReply.reply_id == UUID(reply_id)).first()
        if reply:
            reply.media_url = file
            reply.media_type = media_type
            db.commit()
            
            await message.reply_text(
                "رسانه با موفقیت به پاسخ شما اضافه شد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ اتمام", callback_data="finish_reply_question_")],
                    [InlineKeyboardButton("🔙 انصراف", callback_data="cancel")]
                ])
            )
        else:
            await message.reply_text(
                "خطا در یافتن پاسخ. لطفاً دوباره تلاش کنید.",
                reply_markup=create_back_to_main_button()
            )
            return ConversationHandler.END
            
    except Exception as e:
        db.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error in add_reply_media_handler: {str(e)}")
        
        await message.reply_text(
            "خطا در ذخیره رسانه. لطفاً دوباره تلاش کنید.",
            reply_markup=create_back_to_main_button()
        )
        return ConversationHandler.END
    
    return ADD_REPLY_MEDIA

async def finish_reply_callback(update: Update, context: CallbackContext) -> int:
    """Handle finishing reply creation process."""
    query = update.callback_query
    await query.answer()
    
    question_id = context.user_data.get("current_question_id")
    
    if question_id:
        await query.edit_message_text(
            "پاسخ شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد. با تشکر از مشارکت شما!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به جزئیات سوال", callback_data=f"question_{question_id}")],
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
        )
    else:
        await query.edit_message_text(
            "خطا در پردازش درخواست. لطفاً دوباره تلاش کنید.",
            reply_markup=create_back_to_main_button()
        )
    
    # Clear user data
    if "reply_text" in context.user_data:
        del context.user_data["reply_text"]
    if "current_reply_id" in context.user_data:
        del context.user_data["current_reply_id"]
    if "current_question_id" in context.user_data:
        del context.user_data["current_question_id"]
    
    return ConversationHandler.END

async def cancel_callback(update: Update, context: CallbackContext) -> int:
    """Cancel the current conversation."""
    query = update.callback_query
    await query.answer()

    # Clear user data
    if "reply_text" in context.user_data:
        del context.user_data["reply_text"]
    if "current_reply_id" in context.user_data:
        del context.user_data["current_reply_id"]
    if "current_question_id" in context.user_data:
        del context.user_data["current_question_id"]

    await query.edit_message_text(
        "عملیات لغو شد.",
        reply_markup=create_main_menu_buttons()
    )

    return ConversationHandler.END
#######################################

#question comment callback

########################################

async def view_question_replies_callback(update: Update, context: CallbackContext) -> None:
    """Handle sending comments for a question."""
    query = update.callback_query
    await query.answer()
    
    # Extract question ID from callback data
    _,_, question_id = query.data.split("_", 2)
    
    # Get question details and comments
    db = next(get_db())

    try:
        question = get_tech_question(db,question_id)
    except ValueError:
        await query.edit_message_text(
            "شناسه محصول نامعتبر است. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
           )
        return
    if not question:
        await query.edit_message_text(
            "سوال مورد نظر یافت نشد.",
            reply_markup=create_main_menu_buttons()
        )
        return
    
    
    comments = get_question_replies(db, UUID(question_id), ContentStatus.APPROVED)    
        # ابتدا پیام اصلی را به عنوان هدر نمایش می‌دهیم
    header_text = f"💬 نظرات کاربران برای \n\n{question.text}:"
    await query.edit_message_text(header_text)
    try:
        #no reply
        if not comments:
            no_comments_text = "هنوز نظری ثبت نشده است. شما می‌توانید اولین نظر را ثبت کنید."
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 افزودن پاسخ",callback_data=f"reply_question_{question}")]
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
            await context.bot.send_message(chat_id=query.message.chat_id, text=no_comments_text, reply_markup=keyboard)
            return
        
        
        if comments:
            for i, comment in enumerate(comments, 1):
                user = get_user(db, comment.user_id)
                username = user.username if user and user.username else f"کاربر {comment.user_id}"
                comment_text = f"💬 نظر #{i}:\n\n"
                comment_text += f"👤 {username}:\n{comment.text}\n"
                
                # Add media indicator if comment has media
                if comment.media_url:
                    comment_text += "🖼️ [دارای تصویر یا ویدیو]\n"
                await context.bot.send_message(chat_id=query.message.chat_id, text=comment_text)
            
                
        
        
        # Create reply markup with pagination if needed
        reply_markup = create_question_replies_buttons(str(question.question_id))
        
        await query.edit_message_text(
            comment_text,
            reply_markup=reply_markup
        )

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in view_question_replies_callback: {str(e)}")
        await query.edit_message_text(
            "خطا در نمایش نظرات. لطفاً دوباره تلاش کنید.",
            reply_markup=create_main_menu_buttons()
        )
        return

#######################################

#callback register

########################################
def register_questions_callback_handlers(application):
    """Register all callback handlers related to questions functionality."""
    application.add_handler(CallbackQueryHandler(tech_callback, pattern="^tech$"))
    application.add_handler(CallbackQueryHandler(question_detail_callback, pattern="^question_[0-9a-f-]+$"))
    application.add_handler(CallbackQueryHandler(rate_question_callback, pattern="^rate_question_[0-9a-f-]+_[1-5]$"))
    add_question_conv = ConversationHandler(
    entry_points=[
            CallbackQueryHandler(add_tech_question_callback, pattern="^add_question$")
        ],
        states={
            ADD_QUESTION_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_text_callback)
            ],
            ADD_QUESTION_MEDIA: [
                CallbackQueryHandler(add_question_media_callback, pattern="^add_question_media$"),
                CallbackQueryHandler(finish_question_callback, pattern="^finish_question$"),
                MessageHandler(filters.PHOTO | filters.VIDEO , add_question_media_handler)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_callback, pattern="^cancel$"),
            CallbackQueryHandler(finish_question_callback, pattern="^finish_question$")
        ],
        name="add_question_conversation",
        persistent=False
    )
    application.add_handler(add_question_conv)
    
        # Add reply conversation handler
    add_reply_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(reply_question_callback, pattern="^reply_question_[0-9a-f-]+$")
        ],
        states={
            ADD_REPLY_TEXT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_reply_text_callback)
            ],
            ADD_REPLY_MEDIA: [
                CallbackQueryHandler(add_reply_media_callback, pattern="^add_reply_question_media_$"),
                CallbackQueryHandler(finish_reply_callback, pattern="^finish_reply_question_$"),
                MessageHandler(filters.PHOTO | filters.VIDEO, add_reply_media_handler)
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_callback, pattern="^cancel$"),
            CallbackQueryHandler(finish_reply_callback, pattern="^finish_reply_question_$")
        ],
        name="add_reply_conversation",
        persistent=False
    )
    application.add_handler(add_reply_conv)
    application.add_handler(CallbackQueryHandler(view_question_replies_callback, pattern="^question_replies_[0-9a-f-]+$"))