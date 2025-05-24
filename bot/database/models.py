import uuid
from datetime import datetime
from sqlalchemy import (
    BigInteger, String, Text, Float, Integer, ForeignKey, CheckConstraint, Enum, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from enum import Enum as PyEnum
from sqlalchemy import func
# کلاس پایه برای مدل‌های SQLAlchemy
# این کلاس به عنوان کلاس پایه برای تمام مدل‌های دیگر استفاده می‌شود
class Base(DeclarativeBase):
    pass

# شمارشگر برای وضعیت کاربر
# وضعیت‌های ممکن: در انتظار تأیید، تأیید شده
class UserStatus(PyEnum):
    PENDING = "pending"    # در انتظار تأیید
    VERIFIED = "verified"  # تأیید شده

# شمارشگر برای انواع محصولات
# انواع محصولات: دستگاه دائمی، دستگاه یکبار مصرف، سالت نیکوتین، جویس
class ItemType(PyEnum):
    DEVICE_PERMANENT = "devices_permanent"          # دستگاه دائمی
    DEVICE_DISPOSABLE = "devices_disposable"        # دستگاه یکبار مصرف
    LIQUID_SALT = "liquid_salt"  # سالت نیکوتین
    LIQUID_JUICE = "liquid_juice"    # جویس

# شمارشگر برای وضعیت محتوا (نظرات، پاسخ‌ها، سوالات، پیشنهادات)
# وضعیت‌های ممکن: در انتظار بررسی، تأیید شده، رد شده
class ContentStatus(PyEnum):
    PENDING = "pending"    # در انتظار بررسی
    APPROVED = "approved"  # تأیید شده
    REJECTED = "rejected"  # رد شده

# شمارشگر برای وضعیت پیام‌های تماس با ما
# وضعیت‌های ممکن: در انتظار پاسخ، پاسخ داده شده، رد شده
class MessageStatus(PyEnum):
    PENDING = "pending"      # در انتظار پاسخ
    ANSWERED = "answered"    # پاسخ داده شده
    REJECTED = "rejected"    # رد شده

# شمارشگر برای انواع هدف امتیازدهی
# انواع هدف: محصول، سوال فنی
class TargetType(PyEnum):
    ITEM = "item"          # محصول
    QUESTION = "question"  # سوال فنی

# جدول کاربران
# این جدول اطلاعات کاربران ربات را ذخیره می‌کند
class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # شناسه کاربر تلگرام (کلید اصلی)
    username: Mapped[str] = mapped_column(String(30), nullable=True)  # نام کاربری (اختیاری)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)  # شماره تلفن کاربر (اختیاری)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.PENDING)  # وضعیت کاربر (پیش‌فرض: در انتظار)
    rank_score: Mapped[int] = mapped_column(Integer, default=0)  # امتیاز رتبه کاربر (پیش‌فرض: 0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # زمان ایجاد
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)  # زمان بروزرسانی
    
    # روابط با سایر جدول‌ها
    comments: Mapped[list["Comment"]] = relationship(back_populates="user")  # رابطه با نظرات
    comment_replies: Mapped[list["CommentReply"]] = relationship(back_populates="user")  # رابطه با پاسخ‌های نظرات
    tech_questions: Mapped[list["TechQuestion"]] = relationship(back_populates="user")  # رابطه با سوالات فنی
    question_replies: Mapped[list["QuestionReply"]] = relationship(back_populates="user")  # رابطه با پاسخ‌های سوالات
    item_ratings: Mapped[list["ItemRating"]] = relationship(back_populates="user")  # رابطه با امتیازدهی‌های محصول
    question_ratings: Mapped[list["QuestionRating"]] = relationship(back_populates="user")  # رابطه با امتیازدهی‌های سوال
    product_suggestions: Mapped[list["ProductSuggestion"]] = relationship(back_populates="user")  # رابطه با پیشنهادات محصول
    contact_messages: Mapped[list["ContactMessage"]] = relationship(back_populates="user")  # رابطه با پیام‌های تماس
    
    # محدودیت‌های جدول
    __table_args__ = (
        CheckConstraint("rank_score >= 0", name="check_rank_score_non_negative"),  # امتیاز رتبه نمی‌تواند منفی باشد
    )

# جدول محصولات (دستگاه‌ها: دائمی/یکبار مصرف، لیکوئیدها: سالت نیکوتین/جویس)
# این جدول اطلاعات محصولات مختلف را ذخیره می‌کند
class Item(Base):
    __tablename__ = "items"
    
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # شناسه محصول (کلید اصلی)
    type: Mapped[ItemType] = mapped_column(Enum(ItemType), nullable=False)  # نوع محصول (الزامی)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # نام محصول (الزامی)
    description: Mapped[str] = mapped_column(Text, nullable=True)  # توضیحات محصول (اختیاری)
    average_rating: Mapped[float] = mapped_column(Float, default=0)  # میانگین امتیاز (پیش‌فرض: 0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)  # تعداد امتیازدهی (پیش‌فرض: 0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # زمان ایجاد
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)  # زمان بروزرسانی
    
    # روابط با سایر جدول‌ها
    comments: Mapped[list["Comment"]] = relationship(back_populates="item")  # رابطه با نظرات
    ratings: Mapped[list["ItemRating"]] = relationship(back_populates="item")  # رابطه با امتیازدهی‌ها
    
    # محدودیت‌های جدول
    __table_args__ = (
        CheckConstraint("average_rating >= 0 AND average_rating <= 5", name="check_average_rating_range"),  # میانگین امتیاز باید بین 0 تا 5 باشد
        CheckConstraint("rating_count >= 0", name="check_rating_count_non_negative"),  # تعداد امتیازدهی نمی‌تواند منفی باشد
    )

# جدول نظرات
# این جدول نظرات کاربران درباره محصولات را ذخیره می‌کند
class Comment(Base):
    __tablename__ = "comments"
    
    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # شناسه نظر (کلید اصلی)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("items.item_id", ondelete="CASCADE"), nullable=False)  # شناسه محصول (کلید خارجی)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)  # شناسه کاربر (کلید خارجی)
    text: Mapped[str] = mapped_column(Text, nullable=False)  # متن نظر (الزامی)
    media_url: Mapped[str] = mapped_column(String(255), nullable=True)  # آدرس رسانه (اختیاری)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.PENDING)  # وضعیت نظر (پیش‌فرض: در انتظار)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # زمان ایجاد
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)  # زمان بروزرسانی
    
    # روابط با سایر جدول‌ها
    item: Mapped["Item"] = relationship(back_populates="comments")  # رابطه با محصول
    user: Mapped["User"] = relationship(back_populates="comments")  # رابطه با کاربر
    replies: Mapped[list["CommentReply"]] = relationship(back_populates="comment")  # رابطه با پاسخ‌های نظر

# جدول پاسخ‌های نظرات
# این جدول پاسخ‌های کاربران به نظرات را ذخیره می‌کند
class CommentReply(Base):
    __tablename__ = "comment_replies"
    
    reply_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("comments.comment_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    
    parent_reply_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("comment_replies.reply_id", ondelete="CASCADE"), 
        nullable=True
    )  # پاسخ والد (در صورت وجود)
    
    text: Mapped[str] = mapped_column(Text, nullable=False)
    media_url: Mapped[str] = mapped_column(String(255), nullable=True)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # روابط
    comment: Mapped["Comment"] = relationship(back_populates="replies")
    user: Mapped["User"] = relationship(back_populates="comment_replies")

    parent_reply: Mapped["CommentReply | None"] = relationship(
        "CommentReply", # نام کلاس به صورت رشته
        back_populates="child_replies",
        remote_side=[reply_id], # ارجاع به صفت reply_id همین کلاس
        foreign_keys=[parent_reply_id] # ارجاع به صفت parent_reply_id همین کلاس
    )
    
    child_replies: Mapped[list["CommentReply"]] = relationship(
        "CommentReply", # نام کلاس به صورت رشته
        back_populates="parent_reply",
        cascade="all, delete-orphan",
        foreign_keys=[parent_reply_id] # ارجاع به صفت parent_reply_id همین کلاس
    )

 
    
# جدول سوالات فنی
# این جدول سوالات فنی کاربران را ذخیره می‌کند
class TechQuestion(Base):
    __tablename__ = "tech_questions"
    
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # شناسه سوال (کلید اصلی)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)  # شناسه کاربر (کلید خارجی)
    text: Mapped[str] = mapped_column(Text, nullable=False)  # متن سوال (الزامی)
    media_url: Mapped[str] = mapped_column(String(255), nullable=True)  # آدرس رسانه (اختیاری)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.PENDING)  # وضعیت سوال (پیش‌فرض: در انتظار)
    average_rating: Mapped[float] = mapped_column(Float, default=0)  # میانگین امتیاز (پیش‌فرض: 0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)  # تعداد امتیازدهی (پیش‌فرض: 0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # زمان ایجاد
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)  # زمان بروزرسانی
    
    # روابط با سایر جدول‌ها
    user: Mapped["User"] = relationship(back_populates="tech_questions")  # رابطه با کاربر
    replies: Mapped[list["QuestionReply"]] = relationship(back_populates="question")  # رابطه با پاسخ‌های سوال
    ratings: Mapped[list["QuestionRating"]] = relationship(back_populates="question")  # رابطه با امتیازدهی‌ها
    
    # محدودیت‌های جدول
    __table_args__ = (
        CheckConstraint("average_rating >= 0 AND average_rating <= 5", name="check_question_average_rating_range"),  # میانگین امتیاز باید بین 0 تا 5 باشد
        CheckConstraint("rating_count >= 0", name="check_question_rating_count_non_negative"),  # تعداد امتیازدهی نمی‌تواند منفی باشد
    )

# جدول پاسخ‌های سوالات
# این جدول پاسخ‌های کاربران به سوالات فنی را ذخیره می‌کند
class QuestionReply(Base):
    __tablename__ = "question_replies"
    
    reply_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # شناسه پاسخ (کلید اصلی)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tech_questions.question_id", ondelete="CASCADE"), nullable=False)  # شناسه سوال (کلید خارجی)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)  # شناسه کاربر (کلید خارجی)
    text: Mapped[str] = mapped_column(Text, nullable=False)  # متن پاسخ (الزامی)
    media_url: Mapped[str] = mapped_column(String(255), nullable=True)  # آدرس رسانه (اختیاری)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.PENDING)  # وضعیت پاسخ (پیش‌فرض: در انتظار)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # زمان ایجاد
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)  # زمان بروزرسانی
    
    # روابط با سایر جدول‌ها
    question: Mapped["TechQuestion"] = relationship(back_populates="replies")  # رابطه با سوال
    user: Mapped["User"] = relationship(back_populates="question_replies")  # رابطه با کاربر

# جدول امتیازدهی به محصولات
# این جدول امتیازهای کاربران به محصولات را ذخیره می‌کند
class ItemRating(Base):
    __tablename__ = "item_ratings"
    
    rating_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # شناسه امتیاز (کلید اصلی)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)  # شناسه کاربر (کلید خارجی)
    item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("items.item_id", ondelete="CASCADE"), nullable=False)  # شناسه محصول (کلید خارجی)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # امتیاز (1 تا 5)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # زمان ایجاد
    
    # روابط با سایر جدول‌ها
    user: Mapped["User"] = relationship(back_populates="item_ratings")  # رابطه با کاربر
    item: Mapped["Item"] = relationship(back_populates="ratings")  # رابطه با محصول
    
    # محدودیت‌های جدول
    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 5", name="check_item_score_range"),  # امتیاز باید بین 1 تا 5 باشد
        UniqueConstraint("user_id", "item_id", name="unique_user_item_rating"),  # هر کاربر فقط یک بار می‌تواند به هر محصول امتیاز دهد
    )

# جدول امتیازدهی به سوالات فنی
# این جدول امتیازهای کاربران به سوالات فنی را ذخیره می‌کند
class QuestionRating(Base):
    __tablename__ = "question_ratings"
    
    rating_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # شناسه امتیاز (کلید اصلی)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)  # شناسه کاربر (کلید خارجی)
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tech_questions.question_id", ondelete="CASCADE"), nullable=False)  # شناسه سوال (کلید خارجی)
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # امتیاز (1 تا 5)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # زمان ایجاد
    
    # روابط با سایر جدول‌ها
    user: Mapped["User"] = relationship(back_populates="question_ratings")  # رابطه با کاربر
    question: Mapped["TechQuestion"] = relationship(back_populates="ratings")  # رابطه با سوال
    
    # محدودیت‌های جدول
    __table_args__ = (
        CheckConstraint("score >= 1 AND score <= 5", name="check_question_score_range"),  # امتیاز باید بین 1 تا 5 باشد
        UniqueConstraint("user_id", "question_id", name="unique_user_question_rating"),  # هر کاربر فقط یک بار می‌تواند به هر سوال امتیاز دهد
    )
# جدول پیشنهادات محصول
# این جدول پیشنهادات کاربران برای محصولات جدید را ذخیره می‌کند
class ProductSuggestion(Base):
    __tablename__ = "product_suggestions"
    
    suggestion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # شناسه پیشنهاد (کلید اصلی)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)  # شناسه کاربر (کلید خارجی)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # نام محصول پیشنهادی (الزامی)
    description: Mapped[str] = mapped_column(Text, nullable=True)  # توضیحات محصول پیشنهادی (اختیاری)
    status: Mapped[ContentStatus] = mapped_column(Enum(ContentStatus), default=ContentStatus.PENDING)  # وضعیت پیشنهاد (پیش‌فرض: در انتظار)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # زمان ایجاد
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)  # زمان بروزرسانی
    
    # روابط با سایر جدول‌ها
    user: Mapped["User"] = relationship(back_populates="product_suggestions")  # رابطه با کاربر

# جدول پیام‌های تماس
# این جدول پیام‌های تماس کاربران را ذخیره می‌کند
class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # شناسه پیام (کلید اصلی)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)  # شناسه کاربر (کلید خارجی)
    text: Mapped[str] = mapped_column(Text, nullable=False)  # متن پیام (الزامی)
    media_url: Mapped[str] = mapped_column(String(255), nullable=True)  # آدرس رسانه (اختیاری)
    status: Mapped[MessageStatus] = mapped_column(Enum(MessageStatus), default=MessageStatus.PENDING)  # وضعیت پیام (پیش‌فرض: در انتظار)
    response: Mapped[str] = mapped_column(Text, nullable=True)  # پاسخ به پیام (اختیاری)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)  # زمان ایجاد
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)  # زمان بروزرسانی
    
    # روابط با سایر جدول‌ها
    user: Mapped["User"] = relationship(back_populates="contact_messages")  # رابطه با کاربر
