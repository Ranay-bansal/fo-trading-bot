import os
from PIL import Image

def generate_icons():
    logo_path = r"c:\Users\RANAY\Desktop\FO TRADING BOT\dashboard\logo.jpg"
    dashboard_dir = r"c:\Users\RANAY\Desktop\FO TRADING BOT\dashboard"

    if os.path.exists(logo_path):
        img = Image.open(logo_path).convert("RGBA")
        
        # Resize for 192x192 and 512x512
        icon_192 = img.resize((192, 192), Image.Resampling.LANCZOS)
        icon_512 = img.resize((512, 512), Image.Resampling.LANCZOS)
        
        icon_192.save(os.path.join(dashboard_dir, "icon-192.png"), "PNG")
        icon_512.save(os.path.join(dashboard_dir, "icon-512.png"), "PNG")
        print("Generated icon-192.png and icon-512.png successfully.")

if __name__ == "__main__":
    generate_icons()
