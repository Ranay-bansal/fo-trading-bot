import os
import shutil
import base64

def process_background():
    base_dir = r"c:\Users\RANAY\Desktop\FO TRADING BOT"
    bg_file = os.path.join(base_dir, "dashboard background.jpg")
    
    if os.path.exists(bg_file):
        # Copy to dashboard and public
        shutil.copy2(bg_file, os.path.join(base_dir, "dashboard", "background.jpg"))
        shutil.copy2(bg_file, os.path.join(base_dir, "public", "background.jpg"))
        print("Copied dashboard background.jpg to dashboard/ and public/")
        
        with open(bg_file, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            print(f"Background base64 length: {len(b64)}")
            with open(os.path.join(base_dir, "scratch", "bg_b64.txt"), "w") as out:
                out.write(f"data:image/jpeg;base64,{b64}")

if __name__ == "__main__":
    process_background()
