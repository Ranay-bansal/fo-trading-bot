import os

def embed_logo():
    html_path = r"c:\Users\RANAY\Desktop\FO TRADING BOT\dashboard\index.html"
    b64_path = r"c:\Users\RANAY\Desktop\FO TRADING BOT\scratch\logo_b64.txt"
    
    with open(b64_path, "r") as f:
        b64_str = f.read().strip()
        
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace logo.jpg src with base64 data URI while preserving logo.jpg fallback
    new_html = html.replace('src="logo.jpg"', f'src="{b64_str}"')
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_html)
    print("Embedded logo base64 string into index.html successfully.")

if __name__ == "__main__":
    embed_logo()
