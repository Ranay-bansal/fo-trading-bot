import os
import base64

def get_logo_b64():
    logo_path = r"c:\Users\RANAY\Desktop\FO TRADING BOT\dashboard\logo.jpg"
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
            print(f"Base64 string length: {len(b64_data)}")
            with open(r"c:\Users\RANAY\Desktop\FO TRADING BOT\scratch\logo_b64.txt", "w") as out:
                out.write(f"data:image/jpeg;base64,{b64_data}")

if __name__ == "__main__":
    get_logo_b64()
