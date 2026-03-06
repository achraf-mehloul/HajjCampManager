#!/usr/bin/env python3
"""
إنشاء صور بانورامية تجريبية للمواقع التفاعلية
"""

from PIL import Image, ImageDraw, ImageFont
import os
import math

def create_panorama_image(width=2048, height=1024, title="موقع تجريبي", color_scheme="blue"):
    """إنشاء صورة بانورامية تجريبية"""
    
    # إنشاء صورة جديدة
    img = Image.new('RGB', (width, height), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # ألوان مختلفة حسب نوع الموقع
    color_schemes = {
        'blue': ['#87CEEB', '#4682B4', '#1E90FF'],      # للمساجد
        'green': ['#90EE90', '#32CD32', '#228B22'],     # للمطاعم
        'red': ['#FFB6C1', '#FF69B4', '#DC143C'],       # للخدمات الطبية
        'purple': ['#DDA0DD', '#9370DB', '#8A2BE2'],    # للفنادق
        'orange': ['#FFE4B5', '#FFA500', '#FF8C00'],    # للمواصلات
        'gold': ['#F0E68C', '#DAA520', '#B8860B']       # للتسوق
    }
    
    colors = color_schemes.get(color_scheme, color_schemes['blue'])
    
    # رسم السماء (الجزء العلوي)
    for y in range(height // 2):
        color_ratio = y / (height // 2)
        r = int(colors[0][1:3], 16) + int((int(colors[1][1:3], 16) - int(colors[0][1:3], 16)) * color_ratio)
        g = int(colors[0][3:5], 16) + int((int(colors[1][3:5], 16) - int(colors[0][3:5], 16)) * color_ratio)
        b = int(colors[0][5:7], 16) + int((int(colors[1][5:7], 16) - int(colors[0][5:7], 16)) * color_ratio)
        
        draw.rectangle([(0, y), (width, y+1)], fill=(r, g, b))
    
    # رسم الأرض (الجزء السفلي)
    for y in range(height // 2, height):
        color_ratio = (y - height // 2) / (height // 2)
        r = int(colors[1][1:3], 16) + int((int(colors[2][1:3], 16) - int(colors[1][1:3], 16)) * color_ratio)
        g = int(colors[1][3:5], 16) + int((int(colors[2][3:5], 16) - int(colors[1][3:5], 16)) * color_ratio)
        b = int(colors[1][5:7], 16) + int((int(colors[2][5:7], 16) - int(colors[1][5:7], 16)) * color_ratio)
        
        draw.rectangle([(0, y), (width, y+1)], fill=(r, g, b))
    
    # إضافة بعض العناصر البصرية
    # رسم مباني بسيطة
    for i in range(8):
        x = (width // 8) * i
        building_width = width // 10
        building_height = height // 4 + (i % 3) * 50
        
        # رسم المبنى
        draw.rectangle([
            (x + 20, height - building_height),
            (x + building_width, height)
        ], fill='#696969', outline='#2F4F4F', width=2)
        
        # رسم نوافذ
        for row in range(building_height // 40):
            for col in range(building_width // 30):
                window_x = x + 30 + col * 30
                window_y = height - building_height + 20 + row * 40
                if window_x < x + building_width - 10:
                    draw.rectangle([
                        (window_x, window_y),
                        (window_x + 15, window_y + 20)
                    ], fill='#FFFF99' if (row + col) % 2 == 0 else '#87CEEB')
    
    # إضافة بعض السحب
    for i in range(5):
        cloud_x = (width // 5) * i + 50
        cloud_y = height // 6 + (i % 2) * 30
        
        # رسم سحابة بسيطة
        for j in range(3):
            draw.ellipse([
                (cloud_x + j * 30, cloud_y),
                (cloud_x + j * 30 + 60, cloud_y + 40)
            ], fill='white', outline='lightgray')
    
    # إضافة النص
    try:
        # محاولة استخدام خط عربي إذا كان متوفراً
        font_size = 48
        font = ImageFont.load_default()
        
        # حساب موضع النص
        text_bbox = draw.textbbox((0, 0), title, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        text_x = (width - text_width) // 2
        text_y = height // 2 - text_height // 2
        
        # رسم خلفية للنص
        draw.rectangle([
            (text_x - 20, text_y - 10),
            (text_x + text_width + 20, text_y + text_height + 10)
        ], fill='rgba(0,0,0,128)')
        
        # رسم النص
        draw.text((text_x, text_y), title, fill='white', font=font)
        
    except Exception as e:
        print(f"خطأ في إضافة النص: {e}")
    
    return img

def create_all_demo_panoramas():
    """إنشاء جميع الصور البانورامية التجريبية"""
    
    # التأكد من وجود المجلد
    output_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(output_dir, exist_ok=True)
    
    # قائمة المواقع مع ألوانها
    locations = [
        ("kaaba_360.jpg", "المسجد الحرام", "blue"),
        ("restaurant_360.jpg", "مطعم الحرمين", "green"),
        ("hospital_360.jpg", "مستشفى الملك فيصل", "red"),
        ("hotel_360.jpg", "فندق دار التوحيد", "purple"),
        ("mall_360.jpg", "مول الحرمين", "gold"),
        ("bus_station_360.jpg", "محطة الحافلات", "orange"),
        ("masjid_nabawi_360.jpg", "المسجد النبوي", "blue"),
        ("arafat_360.jpg", "جبل عرفات", "green"),
        ("mina_360.jpg", "مشعر منى", "orange"),
        ("muzdalifah_360.jpg", "المزدلفة", "purple")
    ]
    
    print("بدء إنشاء الصور البانورامية...")
    
    for filename, title, color_scheme in locations:
        print(f"إنشاء {filename}...")
        
        # إنشاء الصورة
        img = create_panorama_image(
            width=2048, 
            height=1024, 
            title=title, 
            color_scheme=color_scheme
        )
        
        # حفظ الصورة
        output_path = os.path.join(output_dir, filename)
        img.save(output_path, 'JPEG', quality=85)
        print(f"تم حفظ {filename}")
    
    print("تم إنشاء جميع الصور البانورامية بنجاح!")

if __name__ == "__main__":
    create_all_demo_panoramas()
