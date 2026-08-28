"""
سكريبت سحب أسعار الذهب من موقع آي صاغة (isagha.com)
يقرأ أسعار عيار 24 و22 و21 و18 وجنيه الذهب، ويخزنها في ملف JSON
يمكن جدولته للعمل كل 15-30 دقيقة عبر cron أو GitHub Actions
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone, timedelta

URL = "https://market.isagha.com/prices"
OUTPUT_FILE = "gold_prices.json"

CAIRO_TZ = timezone(timedelta(hours=2))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def fetch_gold_prices():
    response = requests.get(URL, headers=HEADERS, timeout=15)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table")
    if not tables:
        raise ValueError("مفيش جداول اتلاقت في الصفحة - ممكن شكل الموقع اتغير")

    gold_table = None
    for t in tables:
        if "عيار 24" in t.get_text():
            gold_table = t
            break

    if gold_table is None:
        raise ValueError("مالقيتش جدول فيه 'عيار 24' - شكل الموقع اتغير، محتاج مراجعة")

    rows = gold_table.find_all("tr")[1:]

    prices = {}
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        karat_name = cells[0].get_text(strip=True)
        sell_price = cells[1].get_text(strip=True)
        buy_price = cells[3].get_text(strip=True) if len(cells) > 3 else None

        prices[karat_name] = {
            "sell": sell_price,
            "buy": buy_price,
        }

    return prices


def save_prices(prices):
    data = {
        "updated_at": datetime.now(CAIRO_TZ).strftime("%Y-%m-%d %H:%M"),
        "prices": prices,
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def format_whatsapp_message(data):
    p = data["prices"]
    lines = [f"سعر الذهب النهارده (تحديث {data['updated_at']}):"]

    order = ["عيار 24", "عيار 22", "عيار 21", "عيار 18", "جنيه ذهب"]
    for karat in order:
        if karat in p and p[karat]["sell"]:
            lines.append(f"{karat}: {p[karat]['sell']} ج.م")

    return "\n".join(lines)


if __name__ == "__main__":
    print("بيسحب الأسعار من آي صاغة...")
    prices = fetch_gold_prices()
    data = save_prices(prices)

    print(f"\nتم التحديث الساعة {data['updated_at']}")
    print(json.dumps(data["prices"], ensure_ascii=False, indent=2))

    print("\n--- رسالة الواتساب الجاهزة ---")
    print(format_whatsapp_message(data))
