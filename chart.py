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
print("[*] Đang cào trang chủ để trích xuất khóa giải mã...")
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
# 3. GỌI API ĐỂ LẤY DỮ LIỆU BIỂU ĐỒ (GOLD-CHART)
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
    'product': 'Vàng nhẫn 9999',  # Thử đổi thành 'Vàng miếng SJC' tiêu đề sẽ tự đổi theo
}

chart_response = requests.post(
    'https://giavang.pro/services/v1/dashboard/gold-chart', 
    cookies=cookies, 
    headers=api_headers, 
    json=json_data
)

# ==============================================================================
# 4. GIẢI MÃ VÀ ĐỊNH DẠNG DỮ LIỆU ĐỂ IN RA TERMINAL
# ==============================================================================
if chart_response.status_code == 200:
    result = chart_response.json()
    if result.get("success"):
        data_payload = result["data"]
        
        # SỬA ĐỔI TẠI ĐÂY: Lấy trực tiếp tên sản phẩm từ json_data
        product_name = json_data['product'].upper()
        print(f"\n=== DỮ LIỆU BIỂU ĐỒ {product_name} ===")
        
        chart_list = data_payload.get("list", [])
        
        for chart_item in chart_list:
            date_label = chart_item.get("date_update", "")
            
            raw_buy = decrypt_field(chart_item.get("buy"), secret_key, secret_iv)
            raw_sell = decrypt_field(chart_item.get("sell"), secret_key, secret_iv)
            
            try:
                formatted_buy = "{:,.0f}".format(float(raw_buy)).replace(",", ".")
                formatted_sell = "{:,.0f}".format(float(raw_sell)).replace(",", ".")
            except ValueError:
                formatted_buy, formatted_sell = raw_buy, raw_sell
                
            print(f"Thời gian: {date_label} | Mua vào: {formatted_buy} ₫ | Bán ra: {formatted_sell} ₫")
    else:
        print("API lỗi xử lý nội bộ:", result.get("message"))
else:
    print("Lỗi kết nối HTTP:", chart_response.status_code)