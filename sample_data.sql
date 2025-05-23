-- اضافه کردن داده‌های نمونه برای محصولات
-- دستگاه‌های دائمی
INSERT INTO items (item_id, type, name, description, average_rating, rating_count, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'DEVICE_PERMANENT', 'ویپ جیک', 'دستگاه ویپ دائمی با باتری قابل شارژ و قابلیت تنظیم وات', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'DEVICE_PERMANENT', 'اسموک نورد', 'دستگاه ویپ دائمی با طراحی کوچک و قابل حمل', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'DEVICE_PERMANENT', 'ووپو دراگ', 'دستگاه ویپ دائمی با باتری قوی و عملکرد بالا', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- دستگاه‌های یکبار مصرف
INSERT INTO items (item_id, type, name, description, average_rating, rating_count, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'DEVICE_DISPOSABLE', 'الف بار', 'دستگاه ویپ یکبار مصرف با طعم‌های متنوع', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'DEVICE_DISPOSABLE', 'هایلو بار', 'دستگاه ویپ یکبار مصرف با ظرفیت بالا', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'DEVICE_DISPOSABLE', 'ویپ استیکس', 'دستگاه ویپ یکبار مصرف با طراحی باریک', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- سالت نیکوتین
INSERT INTO items (item_id, type, name, description, average_rating, rating_count, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'LIQUID_SALT', 'نسل سالت', 'سالت نیکوتین با طعم میوه‌های استوایی', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'LIQUID_SALT', 'نمک نیکوتین فروتی', 'سالت نیکوتین با طعم میوه‌های مختلف', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'LIQUID_SALT', 'سالت آیس', 'سالت نیکوتین با طعم خنک و یخی', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- جویس
INSERT INTO items (item_id, type, name, description, average_rating, rating_count, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 'LIQUID_JUICE', 'جویس کلاسیک', 'جویس با طعم توتون کلاسیک', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'LIQUID_JUICE', 'جویس میوه‌ای', 'جویس با ترکیب طعم‌های میوه‌ای', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    (gen_random_uuid(), 'LIQUID_JUICE', 'جویس دسری', 'جویس با طعم‌های شیرین و دسری', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
    