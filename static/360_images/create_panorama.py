#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
أداة إنشاء صور بانورامية وهمية للجولة الافتراضية
Tool to create dummy panoramic images for virtual tour
"""

import os
from PIL import Image, ImageDraw, ImageFont
import colorsys

def create_panoramic_image(name, width=2048, height=1024):
    """إنشاء صورة بانورامية وهمية"""
    
    # إنشاء صورة جديدة
    img = Image.new('RGB', (width, height), color='skyblue')
    draw = ImageDraw.Draw(img)
    
    # رسم تدرج للسماء
    for y in range(height // 2):
        # تدرج من الأزرق الفاتح إلى الأزرق الداكن
        blue_intensity = int(255 - (y / (height // 2)) * 100)
        color = (135, 206, blue_intensity)
        draw.line([(0, y), (width, y)], fill=color)
    
    # رسم الأرض
    for y in range(height // 2, height):
        # تدرج بني للأرض
        brown_intensity = int(139 + ((y - height // 2) / (height // 2)) * 50)
        color = (brown_intensity, 69, 19)
        draw.line([(0, y), (width, y)], fill=color)
    
    # رسم مباني بسيطة
    building_width = width // 8
    for i in range(8):
        x = i * building_width
        building_height = height // 4 + (i % 3) * 50
        y = height // 2 - building_height
        
        # لون المبنى
        if name == "kaaba":
            color = (50, 50, 50)  # رمادي داكن للكعبة
        elif name == "masjid":
            color = (200, 200, 200)  # رمادي فاتح للمسجد
        else:
            color = (160, 82, 45)  # بني للمباني العادية
        
        draw.rectangle([x, y, x + building_width - 10, height // 2], fill=color)
        
        # نوافذ
        for window_y in range(y + 20, height // 2 - 20, 40):
            for window_x in range(x + 10, x + building_width - 20, 30):
                draw.rectangle([window_x, window_y, window_x + 15, window_y + 15], 
                             fill='yellow' if (window_x + window_y) % 60 == 0 else 'black')
    
    # إضافة نص
    try:
        # محاولة استخدام خط عربي
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    text_color = 'white'
    if name == "kaaba":
        text = "الكعبة المشرفة"
    elif name == "masjid":
        text = "المسجد الحرام"
    elif name == "mina":
        text = "منى"
    elif name == "arafat":
        text = "عرفات"
    elif name == "muzdalifah":
        text = "مزدلفة"
    else:
        text = name
    
    # حساب موقع النص
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (width - text_width) // 2
    text_y = height // 4
    
    # رسم خلفية للنص
    draw.rectangle([text_x - 10, text_y - 10, text_x + text_width + 10, text_y + text_height + 10], 
                  fill='black', outline='white', width=2)
    
    # رسم النص
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    
    return img

def create_all_panoramas():
    """إنشاء جميع الصور البانورامية"""
    
    locations = [
        "kaaba",
        "masjid", 
        "mina",
        "arafat",
        "muzdalifah",
        "jamarat",
        "safa_marwa",
        "hotel",
        "transport"
    ]
    
    for location in locations:
        print(f"إنشاء صورة بانورامية لـ {location}...")
        img = create_panoramic_image(location)
        img.save(f"{location}_360.jpg", "JPEG", quality=85)
        print(f"تم حفظ {location}_360.jpg")

if __name__ == "__main__":
    print("إنشاء الصور البانورامية للجولة الافتراضية...")
    
    # تغيير المجلد الحالي
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # إنشاء الصور
    create_all_panoramas()
    
    print("تم إنشاء جميع الصور البانورامية بنجاح!")
