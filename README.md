# GiaVang.pro API Scraper & Decryptor Toolkit

A lightweight Python toolkit designed to scrape, reverse-engineer, and decrypt real-time pricing data from `giavang.pro`. 

The target website employs an obfuscation layer that conceals API response payloads using **AES-CBC encryption**. The keys and Initialization Vectors (IVs) are not static; instead, they are dynamically generated across several hidden HTML elements, CSS selectors, and font attributes. This toolkit mirrors the client-side JavaScript execution environment to dynamically compute the active `secret_key` and `secret_iv` at runtime, providing transparent, decrypted terminal readouts.

---

## 🛠️ System Features & Script Matrix

The toolkit consists of 5 modular scripts, each targeting a specific endpoint provided by the underlying API:

| Script File | Target API Endpoint | Decrypted Output Parameters |
| :--- | :--- | :--- |
| `price.py` | `/dashboard/gold-price` | Current spot price (Buy/Sell) for local gold brands (e.g., SJC). |
| `list.py` | `/dashboard/gold-list` | Historical local price logs indexed by date. |
| `chart.py` | `/dashboard/gold-chart` | Granular time-series data points tailored for graph rendering. |
| `rate.py` | `/dashboard/currency-price` | Forex exchange matrices (Cash Buy, Transfer, Sell) from VCB. |
| `world_gold.py` | `/pro/world-gold-price-list` | International precious metals tickers (`XAU`/`XAG`) in USD/oz. |

---

## 🏗️ Architecture: How the Decryption Works

1. **Token Extraction:** The script issues a handshake request to the landing page to scrape 6 scattered properties using `BeautifulSoup`:
   * `p0`: Sourced from `<meta name="x-locale-seg">`
   * `p1`: Extracted from the font metric link (`data-woff` / `data-hint`)
   * `p2`: Sourced from `<meta name="x-sw-scope">`
   * `p3`: Pulled from an obfuscated `div` matching the regex pattern `^ab-`
   * `p4`: Recovered from a `<template>` block matching `^perf-`
   * `p5`: Extracted from a specific structural utility CSS class budget tag
2. **Key Derivation:** The extracted tokens undergo hexadecimal conversion into byte arrays. The algorithm replicates the client-side string obfuscation function via sequential bitwise XOR operations:
   $$\text{Secret Key} = \text{hex\_to\_bytes}(p0 + p1) \oplus \text{hex\_to\_bytes}(p2 + p3)$$
   $$\text{Secret IV} = \text{hex\_to\_bytes}(p4) \oplus \text{hex\_to\_bytes}(p5)$$
3. **Payload Decryption:** The server yields a Base64 encoded payload. The toolkit feeds the derived parameters into an **AES-CBC** cipher instance, utilizing **PKCS7** unpadding to print the cleartext data stream.

---

## 🚀 Getting Started

### Prerequisites

Ensure you are using Python 3.8 or higher. Install the required dependencies using your system's package manager or `pip`. 

For **Fedora** systems:
```bash
sudo dnf install python3-pip python3-pycryptodome python3-beautifulsoup4 python3-requests
