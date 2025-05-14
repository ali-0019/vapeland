from sqlalchemy import select, update, func
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime
from .models import (
    User, Item, Comment, CommentReply, TechQuestion, QuestionReply,
    QuestionRating,ItemRating, ProductSuggestion, ContactMessage, UserStatus, ItemType,
    ContentStatus, MessageStatus, TargetType
)

# User Operations
def create_user(db: Session, user_id: int, phone_number: str) -> User:
    """Create a new user with pending status."""
    user = User(user_id=user_id, phone_number=phone_number, status=UserStatus.PENDING)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Retrieve a user by user_id."""
    return db.execute(select(User).filter_by(user_id=user_id)).scalar_one_or_none()

def update_user_status(db: Session, user_id: int, status: UserStatus) -> Optional[User]:
    """Update user authentication status."""
    db.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(status=status)
    )
    db.commit()
    return get_user(db, user_id)

def update_user_rank_score(db: Session, user_id: int, points: int) -> Optional[User]:
    """Update user's rank score."""
    db.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(rank_score=User.rank_score + points)
    )
    db.commit()
    return get_user(db, user_id)

# Item Operations
def create_item(db: Session, type: ItemType, name: str, description: str = None) -> Item:
    """Create a new item (Device or Liquid)."""
    item = Item(type=type, name=name, description=description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def get_items_by_type(db: Session, type: ItemType, limit: int = 10, offset: int = 0) -> List[Item]:
    """Retrieve items by type with pagination."""
    items = db.execute(
        select(Item)
        .filter_by(type=type)
        .order_by(Item.average_rating.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    
    return items  # اگر لیست خالی باشد، یک لیست خالی برمی‌گرداند

def search_items(db: Session, query: str, limit: int = 10, offset: int = 0) -> List[Item]:
    """Search items by name."""
    items = db.execute(
        select(Item)
        .filter(Item.name.ilike(f"%{query}%"))
        .order_by(Item.average_rating.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    
    return items  # اگر لیست خالی باشد، یک لیست خالی برمی‌گرداند

def get_item(db: Session, item_id: UUID) -> Optional[Item]:
    """Retrieve an item by item_id."""
    return db.execute(select(Item).filter_by(item_id=item_id)).scalar_one_or_none()

# Comment Operations
def create_comment(db: Session, item_id: UUID, user_id: int, text: str, media_url: str = None) -> Comment:
    """Create a new comment with pending status."""
    comment = Comment(item_id=item_id, user_id=user_id, text=text, media_url=media_url, status=ContentStatus.PENDING)
    db.add(comment)
    update_user_rank_score(db, user_id, 5)  # Add 5 points for commenting
    db.commit()
    db.refresh(comment)
    return comment

def get_comments_by_item(db: Session, item_id: UUID, status: ContentStatus = ContentStatus.APPROVED, limit: int = 5, offset: int = 0) -> List[Comment]:
    """Retrieve approved comments for an item, sorted by creation date."""
    comments = db.execute(
        select(Comment)
        .filter_by(item_id=item_id, status=status)
        .order_by(Comment.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    
    return comments  # اگر لیست خالی باشد، یک لیست خالی برمی‌گرداند

# Comment Reply Operations
def create_comment_reply(db: Session, comment_id: UUID, user_id: int, text: str, media_url: str = None) -> CommentReply:
    """Create a new reply to a comment with pending status."""
    reply = CommentReply(comment_id=comment_id, user_id=user_id, text=text, media_url=media_url, status=ContentStatus.PENDING)
    db.add(reply)
    update_user_rank_score(db, user_id, 3)  # Add 3 points for replying
    db.commit()
    db.refresh(reply)
    return reply

def get_comment_replies(db: Session, comment_id: UUID, status: ContentStatus = ContentStatus.APPROVED, limit: int = 5, offset: int = 0) -> List[CommentReply]:
    """Retrieve approved replies for a comment, sorted by creation date."""
    replies = db.execute(
        select(CommentReply)
        .filter_by(comment_id=comment_id, status=status)
        .order_by(CommentReply.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    
    return replies  # اگر لیست خالی باشد، یک لیست خالی برمی‌گرداند

# Technical Question Operations
def create_tech_question(db: Session, user_id: int, text: str, media_url: str = None) -> TechQuestion:
    """Create a new technical question with pending status."""
    question = TechQuestion(user_id=user_id, text=text, media_url=media_url, status=ContentStatus.PENDING)
    db.add(question)
    update_user_rank_score(db, user_id, 10)  # Add 10 points for question
    db.commit()
    db.refresh(question)
    return question

def get_top_tech_questions(db: Session, limit: int = 10, offset: int = 0) -> List[TechQuestion]:
    """Retrieve top 10 approved technical questions by average rating."""
    questions = db.execute(
        select(TechQuestion)
        .filter_by(status=ContentStatus.APPROVED)
        .order_by(TechQuestion.average_rating.desc(), TechQuestion.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    
    return questions  # اگر لیست خالی باشد، یک لیست خالی برمی‌گرداند

def get_tech_question(db: Session, question_id: UUID) -> Optional[TechQuestion]:
    """Retrieve a technical question by question_id."""
    return db.execute(select(TechQuestion).filter_by(question_id=question_id)).scalar_one_or_none()

# Question Reply Operations
def create_question_reply(db: Session, question_id: UUID, user_id: int, text: str, media_url: str = None) -> QuestionReply:
    """Create a new reply to a technical question with pending status."""
    reply = QuestionReply(question_id=question_id, user_id=user_id, text=text, media_url=media_url, status=ContentStatus.PENDING)
    db.add(reply)
    update_user_rank_score(db, user_id, 3)  # Add 3 points for replying
    db.commit()
    db.refresh(reply)
    return reply

def get_question_replies(db: Session, question_id: UUID, status: ContentStatus = ContentStatus.APPROVED, limit: int = 5, offset: int = 0) -> List[QuestionReply]:
    """Retrieve approved replies for a technical question, sorted by creation date."""
    replies = db.execute(
        select(QuestionReply)
        .filter_by(question_id=question_id, status=status)
        .order_by(QuestionReply.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    
    return replies  # اگر لیست خالی باشد، یک لیست خالی برمی‌گرداند
# Rating Operations
def create_item_rating(db: Session, user_id: int, item_id: UUID, score: int) -> Optional[ItemRating]:
    """Create a new rating for an item."""
    existing_rating = db.execute(
        select(ItemRating)
        .filter_by(user_id=user_id, item_id=item_id)
    ).scalar_one_or_none()
    
    if existing_rating:
        return None  # Prevent duplicate ratings
    
    rating = ItemRating(user_id=user_id, item_id=item_id, score=score)
    db.add(rating)
    update_user_rank_score(db, user_id, 1)  # Add 1 point for rating
    
    # Update average rating and count
    avg_rating, count = db.execute(
        select(func.avg(ItemRating.score), func.count(ItemRating.rating_id))
        .filter_by(item_id=item_id)
    ).first()
    
    db.execute(
        update(Item)
        .where(Item.item_id == item_id)
        .values(average_rating=avg_rating, rating_count=count)
    )
    
    db.commit()
    db.refresh(rating)
    return rating

def create_question_rating(db: Session, user_id: int, question_id: UUID, score: int) -> Optional[QuestionRating]:
    """Create a new rating for a technical question."""
    existing_rating = db.execute(
        select(QuestionRating)
        .filter_by(user_id=user_id, question_id=question_id)
    ).scalar_one_or_none()
    
    if existing_rating:
        return None  # Prevent duplicate ratings
    
    rating = QuestionRating(user_id=user_id, question_id=question_id, score=score)
    db.add(rating)
    update_user_rank_score(db, user_id, 1)  # Add 1 point for rating
    
    # Update average rating and count
    avg_rating, count = db.execute(
        select(func.avg(QuestionRating.score), func.count(QuestionRating.rating_id))
        .filter_by(question_id=question_id)
    ).first()
    
    db.execute(
        update(TechQuestion)
        .where(TechQuestion.question_id == question_id)
        .values(average_rating=avg_rating, rating_count=count)
    )
    
    db.commit()
    db.refresh(rating)
    return rating

# Product Suggestion Operations
def create_product_suggestion(db: Session, user_id: int, name: str, description: str, media_url: str = None) -> ProductSuggestion:
    """Create a new product suggestion with pending status."""
    suggestion = ProductSuggestion(user_id=user_id, name=name, description=description, media_url=media_url, status=ContentStatus.PENDING)
    db.add(suggestion)
    update_user_rank_score(db, user_id, 15)  # Add 15 points for product suggestion
    db.commit()
    db.refresh(suggestion)
    return suggestion

def get_product_suggestions(db: Session, status: ContentStatus = ContentStatus.PENDING, limit: int = 10, offset: int = 0) -> List[ProductSuggestion]:
    """Retrieve product suggestions by status with pagination."""
    suggestions = db.execute(
        select(ProductSuggestion)
        .filter_by(status=status)
        .order_by(ProductSuggestion.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    
    return suggestions  # اگر لیست خالی باشد، یک لیست خالی برمی‌گرداند

# Contact Message Operations
def create_contact_message(db: Session, user_id: int, text: str, media_url: str = None) -> ContactMessage:
    """Create a new contact message with pending status."""
    message = ContactMessage(user_id=user_id, text=text, media_url=media_url, status=MessageStatus.PENDING)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_contact_messages(db: Session, status: MessageStatus = MessageStatus.PENDING, limit: int = 10, offset: int = 0) -> List[ContactMessage]:
    """Retrieve contact messages by status with pagination."""
    messages = db.execute(
        select(ContactMessage)
        .filter_by(status=status)
        .order_by(ContactMessage.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).scalars().all()
    
    return messages  # اگر لیست خالی باشد، یک لیست خالی برمی‌گرداند

def update_message_status(db: Session, message_id: UUID, status: MessageStatus) -> Optional[ContactMessage]:
    """Update contact message status."""
    db.execute(
        update(ContactMessage)
        .where(ContactMessage.message_id == message_id)
        .values(status=status)
    )
    db.commit()
    return db.execute(select(ContactMessage).filter_by(message_id=message_id)).scalar_one_or_none()

# Content Moderation Operations
def update_content_status(db: Session, content_type: str, content_id: UUID, status: ContentStatus) -> bool:
    """Update status of any content type (comment, reply, question, suggestion)."""
    if content_type == "comment":
        table = Comment
        id_column = Comment.comment_id
    elif content_type == "comment_reply":
        table = CommentReply
        id_column = CommentReply.reply_id
    elif content_type == "question":
        table = TechQuestion
        id_column = TechQuestion.question_id
    elif content_type == "question_reply":
        table = QuestionReply
        id_column = QuestionReply.reply_id
    elif content_type == "suggestion":
        table = ProductSuggestion
        id_column = ProductSuggestion.suggestion_id
    else:
        return False
    
    db.execute(
        update(table)
        .where(id_column == content_id)
        .values(status=status)
    )
    db.commit()
    return True

# Utility Operations
def check_daily_limit(db: Session, user_id: int, action: str, limit: int = 10) -> bool:
    """Check if user has exceeded daily limit for an action (e.g., comments, messages)."""
    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if action == "comment":
        count = db.execute(
            select(func.count(Comment.comment_id))
            .filter_by(user_id=user_id)
            .filter(Comment.created_at >= start_of_day)
        ).scalar()
    elif action == "question":
        count = db.execute(
            select(func.count(TechQuestion.question_id))
            .filter_by(user_id=user_id)
            .filter(TechQuestion.created_at >= start_of_day)
        ).scalar()
    elif action == "message":
        count = db.execute(
            select(func.count(ContactMessage.message_id))
            .filter_by(user_id=user_id)
            .filter(ContactMessage.created_at >= start_of_day)
        ).scalar()
    else:
        count = 0
    return count < limit