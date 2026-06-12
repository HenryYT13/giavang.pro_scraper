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
# 2. TỰ ĐỘNG CÀO TRANG CHỦ ĐỂ LẤY KHÓA ĐỘNG (BẮT BUỘC PHẢI CÓ)
# ==============================================================================
url = "https://giavang.pro/"
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Trích xuất các phân đoạn crypto ẩn trong HTML
p0 = soup.find("meta", {"name": "x-locale-seg"})["data-cfg"]
font_metric_tag = soup.find("link", {"rel": "x-font-metric"})
p1 = font_metric_tag.get("data-woff") or font_metric_tag.get("data-hint")
p2 = soup.find("meta", {"name": "x-sw-scope"})["data-path"]
p3 = soup.find("div", id=re.compile(r"^ab-"))["data-variant"]
p4 = soup.find("template", id=re.compile(r"^perf-")).string.strip()
p5 = soup.find("style", {"data-cls-budget": True})["data-cls-budget"]

# Tính toán ngược phép toán XOR để sinh ra Key và IV cho AES
secret_key = xor_bytes_to_str(hex_to_bytes(p0 + p1), hex_to_bytes(p2 + p3))
secret_iv = xor_bytes_to_str(hex_to_bytes(p4), hex_to_bytes(p5))

# ==============================================================================
# 3. GỌI API LẤY BẢNG GIÁ LỊCH SỬ
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
    'branch': 'SJC',
    'city': 'Hồ Chí Minh',
    'product': 'Vàng nhẫn 9999',
}

list_response = requests.post(
    'https://giavang.pro/services/v1/dashboard/gold-list', 
    cookies=cookies, 
    headers=api_headers, 
    json=json_data
)

# ==============================================================================
# 4. GIẢI MÃ VÀ IN KẾT QUẢ RA TERMINAL
# ==============================================================================
if list_response.status_code == 200:
    result = list_response.json()
    if result.get("success"):
        data_payload = result["data"]
        print(f"=== {data_payload.get('title')} ===")
        
        # Duyệt qua mảng danh sách lịch sử trả về
        history_list = data_payload.get("list", [])
        
        for history_item in history_list:
            full_date = history_item.get("date_update", "")
            date_only = full_date.split(" ")[-1] if " " in full_date else full_date
            
            # Lúc này các biến secret_key, secret_iv đã tồn tại đầy đủ
            buy_price = decrypt_field(history_item.get("buy_display"), secret_key, secret_iv)
            sell_price = decrypt_field(history_item.get("sell_display"), secret_key, secret_iv)
            
            print(f"Ngày: {date_only} | Mua vào: {buy_price} | Bán ra: {sell_price}")
    else:
        print("API trả về thất bại:", result.get("message"))
else:
    print("Không thể kết nối API lỗi HTTP:", list_response.status_code)