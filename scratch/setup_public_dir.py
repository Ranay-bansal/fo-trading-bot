import os
import shutil

def setup_public():
    base_dir = r"c:\Users\RANAY\Desktop\FO TRADING BOT"
    dash_dir = os.path.join(base_dir, "dashboard")
    public_dir = os.path.join(base_dir, "public")

    os.makedirs(public_dir, exist_ok=True)

    files = ["index.html", "manifest.json", "sw.js", "logo.jpg", "icon-192.png", "icon-512.png"]
    for f in files:
        src = os.path.join(dash_dir, f)
        dst = os.path.join(public_dir, f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {f} to public/")

if __name__ == "__main__":
    setup_public()
