import re
import base64
import binascii
import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ==============================================================================
# 1. DECRYPTION UTILITIES
# ==============================================================================
def hex_to_bytes(hex_str):
    """Turns a hexadecimal string configuration into a list of bytes numbers."""
    return list(binascii.unhexlify(hex_str))

def xor_bytes_to_str(a, b):
    """Replicates the client-side JavaScript _u(a, b) bitwise XOR string generator."""
    return "".join(chr(a_byte ^ b_byte) for a_byte, b_byte in zip(a, b))

def decrypt_gold_field(encrypted_text, key_str, iv_str):
    """Applies AES-CBC decryption with PKCS7 padding using extracted parameters."""
    if not encrypted_text:
        return ""
    try:
        key = key_str.encode("utf-8")
        iv = iv_str.encode("utf-8")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Base64 decode raw text payload string
        encrypted_bytes = base64.b64decode(encrypted_text)
        decrypted_padded = cipher.decrypt(encrypted_bytes)
        
        # Unpad PKCS7 block bytes safely
        return unpad(decrypted_padded, AES.block_size, style="pkcs7").decode("utf-8")
    except Exception as e:
        return f"Decryption Error: {e}"

# ==============================================================================
# 2. TOKEN EXTRACTOR & DE-OBFUSCATION
# ==============================================================================
print("[*] Fetching encryption layers from landing page...")
url = "https://giavang.pro/"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

try:
    # Capture standard tags properties
    p0 = soup.find("meta", {"name": "x-locale-seg"})["data-cfg"]
    
    font_metric_tag = soup.find("link", {"rel": "x-font-metric"})
    p1 = font_metric_tag.get("data-woff") or font_metric_tag.get("data-hint")
    
    p2 = soup.find("meta", {"name": "x-sw-scope"})["data-path"]

    # Capture dynamic variable layout selectors using prefix regex matching
    div_ab = soup.find("div", id=re.compile(r"^ab-"))
    if not div_ab:
        raise ValueError("Target obfuscated div tracking node has changed layout parameters.")
    p3 = div_ab["data-variant"]

    template_perf = soup.find("template", id=re.compile(r"^perf-"))
    if not template_perf:
        raise ValueError("Target template crypto configuration node was not found.")
    p4 = template_perf.string.strip()

    p5 = soup.find("style", {"data-cls-budget": True})["data-cls-budget"]

except TypeError:
    print("[!] Error: The script structure of giavang.pro changed or data-tags were stripped.")
    exit(1)

# Re-evaluate array bitwise calculations
mk = hex_to_bytes(p0 + p1)
mm = hex_to_bytes(p2 + p3)
vi = hex_to_bytes(p4)
vm = hex_to_bytes(p5)

# Derive dynamic secrets keys arrays
secret_key = xor_bytes_to_str(mk, mm)
secret_iv = xor_bytes_to_str(vi, vm)

print(f"[+] Found Active AES Key: {secret_key}")
print(f"[+] Found Active AES IV:  {secret_iv}\n")

# ==============================================================================
# 3. BACKGROUND API REQUEST
# ==============================================================================
print("[*] Fetching encrypted pricing matrices from endpoint...")
api_url = "https://giavang.pro/services/v1/dashboard/gold-price"
json_payload = {
    "branch": "SJC",
    "city": "Hồ Chí Minh",
    "product": "Vàng miếng SJC"
}

# Clone configuration header tags layout context rules
api_headers = headers.copy()
api_headers["Content-Type"] = "application/json"
api_headers["Origin"] = "https://giavang.pro"

api_res = requests.post(api_url, json=json_payload, headers=api_headers)

# ==============================================================================
# 4. DATA PARSING & OUTPUT PRODUCTION
# ==============================================================================
if api_res.status_code == 200:
    api_data = api_res.json()
    if api_data.get("success"):
        payload_data = api_data["data"]
        
        # Read raw background crypt strings
        enc_buy = payload_data.get("buy_display")
        enc_sell = payload_data.get("sell_display")
        
        # Mirror decrypt routines natively
        real_buy_price = decrypt_gold_field(enc_buy, secret_key, secret_iv)
        real_sell_price = decrypt_gold_field(enc_sell, secret_key, secret_iv)
        
        # Print output results mapping cleanly
        print("=" * 40)
        print("        DECRYPTED MARKET VALUES")
        print("=" * 40)
        print(f"Product:      {payload_data.get('product')}")
        print(f"City:         {payload_data.get('city')}")
        print(f"Buy (Mua):    {real_buy_price} ₫")
        print(f"Sell (Bán):   {real_sell_price} ₫")
        print(f"Last Server Update: {payload_data.get('date_update')}")
        print("=" * 40)
    else:
        print(f"[!] Server processing error messaging fallback: {api_data.get('message')}")
else:
    print(f"[!] Target server failure validation status code: {api_res.status_code}")