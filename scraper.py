import csv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

url = "https://www.ebay.com/globaldeals/tech"
output_file = "ebay_tech_deals.csv"

def get_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)


main_driver = get_driver()
main_driver.get(url)
time.sleep(5)

last_height = main_driver.execute_script("return document.body.scrollHeight")
while True:
    main_driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
    time.sleep(2)
    new_height = main_driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

products = main_driver.find_elements(By.CSS_SELECTOR, "div.dne-itemtile")
print(f"Found {len(products)} products on main page.")

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
product_data = []

for p in products:
    try:
        title = p.find_element(By.CSS_SELECTOR, ".dne-itemtile-title span").text.strip()
    except:
        title = "N/A"
    try:
        price = p.find_element(By.CSS_SELECTOR, ".dne-itemtile-price").text.strip()
    except:
        price = "N/A"
    try:
        original_price = p.find_element(By.CSS_SELECTOR, ".itemtile-price-strikethrough").text.strip()
    except:
        original_price = "N/A"
    try:
        item_url = p.find_element(By.CSS_SELECTOR, ".dne-itemtile-detail a").get_attribute("href")
    except:
        item_url = "N/A"

    product_data.append({
        "timestamp": timestamp,
        "title": title,
        "price": price,
        "original_price": original_price,
        "item_url": item_url,
    })

main_driver.quit()

def get_shipping_info(url):
    if url == "N/A" or not url.startswith("http"):
        return "Shipping info unavailable"

    try:
        driver = get_driver()
        driver.get(url)
        time.sleep(3)

        try:
            shipping = driver.find_element(
                By.XPATH,
                "//div[contains(@class,'ux-labels-values__values')]//span[contains(text(),'Shipping') or contains(text(),'shipping') or contains(text(),'International')]"
            ).text.strip()
        except:
            try:
                shipping = driver.find_element(By.XPATH, "//span[contains(text(),'Shipping')]").text.strip()
            except:
                shipping = "Shipping info unavailable"

        driver.quit()
        return shipping

    except Exception:
        return "Shipping info unavailable"

print("Fetching shipping info from individual pages...")
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(get_shipping_info, p["item_url"]): p for p in product_data}
    for future in as_completed(futures):
        product = futures[future]
        product["shipping"] = future.result()

header = ["timestamp", "title", "price", "original_price", "shipping", "item_url"]
file_exists = os.path.isfile(output_file)

with open(output_file, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    if not file_exists:
        writer.writeheader()
    writer.writerows(product_data)

print(f"✅ Scraped {len(product_data)} products (with shipping) and saved to {output_file}")