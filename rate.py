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
    return list(binascii.unhexlify(hex_str))

def xor_bytes_to_str(a, b):
    return "".join(chr(a_byte ^ b_byte) for a_byte, b_byte in zip(a, b))

def decrypt_field(encrypted_text, key_str, iv_str):
    if not encrypted_text:
        return "-"
    try:
        key = key_str.encode("utf-8")
        iv = iv_str.encode("utf-8")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        encrypted_bytes = base64.b64decode(encrypted_text)
        decrypted_padded = cipher.decrypt(encrypted_bytes)
        
        return unpad(decrypted_padded, AES.block_size, style="pkcs7").decode("utf-8")
    except Exception:
        return "-"

# ==============================================================================
# 2. SEED EXTRACTION FROM LANDING PAGE
# ==============================================================================
url = "https://giavang.pro/"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Dynamically parse dynamic structures
p0 = soup.find("meta", {"name": "x-locale-seg"})["data-cfg"]
font_metric_tag = soup.find("link", {"rel": "x-font-metric"})
p1 = font_metric_tag.get("data-woff") or font_metric_tag.get("data-hint")
p2 = soup.find("meta", {"name": "x-sw-scope"})["data-path"]

div_ab = soup.find("div", id=re.compile(r"^ab-"))
p3 = div_ab["data-variant"]

template_perf = soup.find("template", id=re.compile(r"^perf-"))
p4 = template_perf.string.strip()

p5 = soup.find("style", {"data-cls-budget": True})["data-cls-budget"]

# Compute keys
secret_key = xor_bytes_to_str(hex_to_bytes(p0 + p1), hex_to_bytes(p2 + p3))
secret_iv = xor_bytes_to_str(hex_to_bytes(p4), hex_to_bytes(p5))

# ==============================================================================
# 3. CURRENCY REQUEST & DECRYPTION
# ==============================================================================
api_url = "https://giavang.pro/services/v1/dashboard/currency-price"
json_payload = {
    'branch': 'VCB',
    'code': 'USD',
}

api_headers = headers.copy()
api_headers["Content-Type"] = "application/json"
api_headers["Origin"] = "https://giavang.pro"

api_res = requests.post(api_url, json=json_payload, headers=api_headers)

if api_res.status_code == 200:
    api_data = api_res.json()
    if api_data.get("success"):
        payload_data = api_data["data"]
        
        # Pull the three encrypted parameters
        enc_buy = payload_data.get("buy_display")
        enc_transfer = payload_data.get("transfer_display")
        enc_sell = payload_data.get("sell_display")
        
        # Decrypt values
        real_buy = decrypt_field(enc_buy, secret_key, secret_iv)
        real_transfer = decrypt_field(enc_transfer, secret_key, secret_iv)
        real_sell = decrypt_field(enc_sell, secret_key, secret_iv)
        
        print("=" * 40)
        print(f"    EXCHANGE RATE: {payload_data.get('branch')} -> {payload_data.get('code')}")
        print("=" * 40)
        print(f"Cash Buy (Mua tiền mặt):     {real_buy} ₫")
        print(f"Transfer Buy (Chuyển khoản): {real_transfer} ₫")
        print(f"Sell Out (Bán ra):           {real_sell} ₫")
        print(f"Server Update Time:          {payload_data.get('date_update')}")
        print("=" * 40)
    else:
        print(f"API Error: {api_data.get('message')}")
else:
    print(f"HTTP Connection Failed: {api_res.status_code}")