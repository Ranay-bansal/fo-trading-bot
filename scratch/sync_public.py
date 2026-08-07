import os
import shutil

def sync_public():
    base_dir = r"c:\Users\RANAY\Desktop\FO TRADING BOT"
    dash_dir = os.path.join(base_dir, "dashboard")
    public_dir = os.path.join(base_dir, "public")

    for f in os.listdir(dash_dir):
        src = os.path.join(dash_dir, f)
        dst = os.path.join(public_dir, f)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"Synced {f} to public/")

if __name__ == "__main__":
    sync_public()
