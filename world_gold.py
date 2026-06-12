import re
import base64
import binascii
import requests
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# ==============================================================================
# 1. HÀM UTILITIES GIẢI MÃ CHUNG
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
# 2. KHỞI TẠO LẤY KEY VÀ IV ĐỘNG TỪ TRANG CHỦ
# ==============================================================================
print("[*] Đang kết nối lấy khóa giải mã động...")
url = "https://giavang.pro/"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

p0 = soup.find("meta", {"name": "x-locale-seg"})["data-cfg"]
font_metric_tag = soup.find("link", {"rel": "x-font-metric"})
p1 = font_metric_tag.get("data-woff") or font_metric_tag.get("data-hint")
p2 = soup.find("meta", {"name": "x-sw-scope"})["data-path"]
p3 = soup.find("div", id=re.compile(r"^ab-"))["data-variant"]
p4 = soup.find("template", id=re.compile(r"^perf-")).string.strip()
p5 = soup.find("style", {"data-cls-budget": True})["data-cls-budget"]

secret_key = xor_bytes_to_str(hex_to_bytes(p0 + p1), hex_to_bytes(p2 + p3))
secret_iv = xor_bytes_to_str(hex_to_bytes(p4), hex_to_bytes(p5))

# ==============================================================================
# 3. GỌI API LẤY GIÁ VÀNG THẾ GIỚI (WORLD-GOLD-PRICE-LIST)
# ==============================================================================
cookies = {
    'cookiePrivacyPreferenceBannerProduction': 'accepted',
}

api_headers = headers.copy()
api_headers.update({
    'Content-Type': 'application/json',
    'Origin': 'https://giavang.pro',
})

json_data = {
    'symbol': 'XAU',   # Có thể đổi thành 'XAG' để lấy giá bạc
    'range': 1,        # Khoảng thời gian (1 = 24 giờ, 7 = 7 ngày, v.v.)
    'lang': 'vi',
}

world_res = requests.post(
    'https://giavang.pro/services/v1/dashboard/pro/world-gold-price-list',
    cookies=cookies,
    headers=api_headers,
    json=json_data,
)

# ==============================================================================
# 4. GIẢI MÃ VÀ IN KẾT QUẢ GIÁ THẾ GIỚI
# ==============================================================================
if world_res.status_code == 200:
    result = world_res.json()
    if result.get("success"):
        data_payload = result["data"]
        symbol_name = "Vàng (XAU)" if json_data['symbol'] == 'XAU' else "Bạc (XAG)"
        print(f"\n=== LỊCH SỬ GIÁ KHỐI {symbol_name} THẾ GIỚI ===")
        
        price_list = data_payload.get("list", [])
        
        # Lấy ra 10 mốc thời gian gần nhất để hiển thị
        for item in price_list[:10]:
            updated_at = item.get("updatedAt", "")
            
            # ĐIỂM QUAN TRỌNG: Key cần giải mã ở đây tên là 'price'
            raw_price = decrypt_field(item.get("price"), secret_key, secret_iv)
            
            try:
                # Ép kiểu về float để giữ lại 2 chữ số thập phân của USD (ví dụ: 2,345.50 USD/oz)
                formatted_price = "{:,.2f}".format(float(raw_price))
            except ValueError:
                formatted_price = raw_price
                
            print(f"Thời gian: {updated_at} | Giá thế giới: {formatted_price} USD/oz")
    else:
        print("API lỗi xử lý nội bộ:", result.get("message"))
else:
    print("Lỗi kết nối HTTP:", world_res.status_code)