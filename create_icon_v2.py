#!/usr/bin/env python3
"""
Create a high-quality ICO icon from scratch
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_professional_icon():
    """Generate a professional icon with better colors and design"""
    
    size = 256
    icon = Image.new('RGBA', (size, size), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(icon)
    
    # Color palette
    purple_main = (124, 58, 237)      # #7c3aed - Main purple
    purple_dark = (109, 40, 217)      # #6d28d9 - Dark purple
    gold = (251, 191, 36)             # #fbbf24 - Gold
    gold_dark = (217, 119, 6)         # #d97706 - Dark gold
    white = (255, 255, 255)
    
    # Draw background circle gradient (multiple circles)
    for radius in range(128, 0, -5):
        color_val = int(124 + (109 - 124) * (1 - radius/128))
        color_val2 = int(58 + (40 - 58) * (1 - radius/128))
        color_val3 = int(237 + (217 - 237) * (1 - radius/128))
        
        alpha = int(255 * (radius / 128))
        draw.ellipse(
            [size//2 - radius, size//2 - radius, size//2 + radius, size//2 + radius],
            fill=(color_val, color_val2, color_val3, alpha)
        )
    
    # Draw main circle with border
    draw.ellipse([15, 15, size-15, size-15], fill=purple_main, outline=purple_dark, width=4)
    
    # Draw wallet shape (main body)
    wallet_x1, wallet_y1 = 50, 90
    wallet_x2, wallet_y2 = 206, 190
    
    # Wallet rectangle with rounded corners effect
    draw.rectangle([wallet_x1+10, wallet_y1, wallet_x2-10, wallet_y2], fill=white, outline=purple_dark, width=3)
    draw.rectangle([wallet_x1, wallet_y1+10, wallet_x2, wallet_y2-10], fill=white, outline=purple_dark, width=3)
    
    # Wallet flap (top part)
    flap_points = [
        (wallet_x1+20, wallet_y1),
        (wallet_x2-20, wallet_y1),
        (wallet_x2-10, wallet_y1-30),
        (wallet_x1+10, wallet_y1-30)
    ]
    draw.polygon(flap_points, fill=purple_main, outline=purple_dark)
    
    # Draw coins (stack of 3)
    coin_x = wallet_x1 + 40
    coin_y = wallet_y1 + 50
    coin_width = 22
    coin_height = 12
    
    # Bottom coin (darkest)
    draw.ellipse([coin_x - coin_width, coin_y + 25 - coin_height//2, 
                  coin_x + coin_width, coin_y + 25 + coin_height//2],
                 fill=gold_dark, outline=gold_dark, width=2)
    draw.line([coin_x - coin_width + 5, coin_y + 25, coin_x + coin_width - 5, coin_y + 25],
              fill=white, width=1)
    
    # Middle coin
    draw.ellipse([coin_x - coin_width, coin_y + 10 - coin_height//2, 
                  coin_x + coin_width, coin_y + 10 + coin_height//2],
                 fill=gold, outline=gold_dark, width=2)
    draw.line([coin_x - coin_width + 5, coin_y + 10, coin_x + coin_width - 5, coin_y + 10],
              fill=gold_dark, width=1)
    
    # Top coin (lightest)
    draw.ellipse([coin_x - coin_width, coin_y - 5 - coin_height//2, 
                  coin_x + coin_width, coin_y - 5 + coin_height//2],
                 fill=(255, 224, 130), outline=gold, width=2)
    draw.line([coin_x - coin_width + 5, coin_y - 5, coin_x + coin_width - 5, coin_y - 5],
              fill=gold_dark, width=1)
    
    # Draw rupee symbol on right side
    rupee_x = wallet_x2 - 45
    rupee_y = wallet_y1 + 45
    
    # Vertical line of rupee
    draw.line([rupee_x, rupee_y - 25, rupee_x, rupee_y + 25], fill=purple_dark, width=5)
    
    # Top horizontal line
    draw.line([rupee_x - 20, rupee_y - 20, rupee_x + 20, rupee_y - 20], fill=purple_dark, width=4)
    
    # Top curve
    draw.arc([rupee_x - 20, rupee_y - 28, rupee_x + 20, rupee_y - 12], 0, 180, fill=purple_dark, width=4)
    
    # Bottom curve
    draw.arc([rupee_x - 18, rupee_y + 8, rupee_x + 18, rupee_y + 24], 180, 360, fill=purple_dark, width=4)
    
    # Decorative sparkles
    sparkles = [(70, 40), (220, 50), (60, 230), (210, 220)]
    for sx, sy in sparkles:
        draw.ellipse([sx-4, sy-4, sx+4, sy+4], fill=gold)
        draw.ellipse([sx-2, sy-2, sx+2, sy+2], fill=white)
    
    # Save as ICO (multiple sizes for quality)
    icon_path = os.path.expanduser("~/Desktop/expense_tracker.ico")
    
    # Create versions at different sizes
    sizes_to_create = [(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
    
    # Save main 256x256 version
    icon.save(icon_path, format='ICO', sizes=sizes_to_create)
    
    print(f"✅ Professional icon created successfully!")
    print(f"📍 Location: {icon_path}")
    print(f"📦 Sizes: {sizes_to_create}")
    
    return icon_path

if __name__ == '__main__':
    create_professional_icon()
