#!/usr/bin/env python3
"""
Create a professional ICO icon for Expense Tracker app
"""
from PIL import Image, ImageDraw
import os

def create_icon():
    """Generate a professional Expense Tracker icon"""
    
    # Create a 256x256 image with white background
    size = 256
    icon = Image.new('RGBA', (size, size), color='white')
    draw = ImageDraw.Draw(icon)
    
    # Define colors
    purple_dark = (124, 58, 237)      # #7c3aed
    purple_light = (139, 92, 246)     # #8b5cf6
    gold = (251, 191, 36)             # #fbbf24
    white = (255, 255, 255)
    
    # Draw main background circle (gradient effect with overlapping circles)
    for i in range(50, 0, -2):
        alpha = int(255 * (1 - i/50))
        color = (*purple_dark, alpha)
        draw.ellipse(
            [size//2 - i*2.5, size//2 - i*2.5, size//2 + i*2.5, size//2 + i*2.5],
            fill=color
        )
    
    # Draw main circle
    draw.ellipse([20, 20, size-20, size-20], fill=purple_light, outline=purple_dark, width=3)
    
    # Draw wallet/purse shape
    wallet_left = 60
    wallet_top = 80
    wallet_right = 196
    wallet_bottom = 180
    
    # Wallet body (rounded rectangle)
    draw.rectangle([wallet_left, wallet_top, wallet_right, wallet_bottom], 
                   fill=white, outline=purple_dark, width=2)
    
    # Wallet flap (curved top)
    draw.arc([wallet_left-5, wallet_top-30, wallet_right+5, wallet_top+10], 
             0, 180, fill=purple_dark, width=3)
    
    # Draw coins stack
    coin_x = wallet_left + 30
    coin_y = wallet_top + 40
    coin_size = 18
    
    # Three coins
    for i in range(3):
        y = coin_y - (i * 15)
        draw.ellipse([coin_x - coin_size, y - coin_size//2, coin_x + coin_size, y + coin_size//2],
                     fill=gold, outline=(245, 158, 11), width=2)
        # Coin detail line
        draw.line([coin_x - coin_size + 5, y, coin_x + coin_size - 5, y], 
                  fill=(245, 158, 11), width=1)
    
    # Draw rupee symbol
    rupee_x = wallet_right - 40
    rupee_y = wallet_top + 50
    
    # Vertical line
    draw.line([rupee_x, rupee_y - 20, rupee_x, rupee_y + 20], 
              fill=purple_dark, width=4)
    
    # Top curve
    draw.arc([rupee_x - 25, rupee_y - 25, rupee_x + 25, rupee_y - 5],
             0, 180, fill=purple_dark, width=3)
    
    # Bottom curve
    draw.arc([rupee_x - 25, rupee_y + 5, rupee_x + 25, rupee_y + 25],
             180, 360, fill=purple_dark, width=3)
    
    # Add decorative sparkle dots
    sparkle_positions = [(80, 50), (200, 60), (70, 210), (210, 200)]
    for x, y in sparkle_positions:
        draw.ellipse([x-3, y-3, x+3, y+3], fill=gold)
    
    # Save as ICO
    output_path = os.path.expanduser("~/Desktop/expense_tracker.ico")
    
    # Convert RGBA to RGB for ICO format
    icon_rgb = Image.new('RGB', icon.size, (255, 255, 255))
    icon_rgb.paste(icon, mask=icon.split()[3])
    
    # Save in multiple sizes for ICO
    icon_rgb.save(output_path, format='ICO', sizes=[(256, 256)])
    
    print(f"✅ Icon created: {output_path}")
    print(f"📦 Size: 256x256 pixels")
    print(f"🎨 Format: ICO (Windows Icon)")
    
    return output_path

if __name__ == '__main__':
    create_icon()
