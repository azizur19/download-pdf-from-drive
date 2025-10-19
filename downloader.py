
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
from fpdf import FPDF
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

import argparse

# --- Parse command-line arguments ---
parser = argparse.ArgumentParser(description="Google Drive Image Scraper and PDF Generator")

parser.add_argument("url", help="Google Drive file view URL")
parser.add_argument("img_dir", help="Folder to save images")
parser.add_argument("pdf_dir", help="Output PDF file name")

args = parser.parse_args()

# --- Use variables from command line ---
URL = args.url
IMG_DIR = args.img_dir
PDF_DIR = args.pdf_dir

print(f"URL       : {URL}")
print(f"IMG_DIR   : {IMG_DIR}")
print(f"PDF_DIR  : {PDF_DIR}")

# # --- Configuration ---
# URL = "https://drive.google.com/file/d/1HoPxGnMhIGcyH3FB6bScTeMty_v3U139/view"
# IMG_DIR = "images"
# PDF_DIR = "diode p4.pdf"

# --- Setup Selenium ---
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
# driver = webdriver.Chrome(service=Service(r"C:\Chrome_Driver\chromedriver.exe"), options=chrome_options)
driver.get(URL)
time.sleep(5)  # wait for page to load


# --- Step 2: Find divs ---
# divs_1 = driver.find_elements(By.XPATH, "//div[@class='ndfHFb-c4YZDc-cYSp0e-DARUcf']")
divs_2 = driver.find_elements(By.XPATH, "//div[starts-with(@style, 'padding-bottom:')]")
# divs3 = driver.find_elements(By.XPATH, "//div[starts-with(@class, 'ndfHFb') and starts-with(@style, 'padding-bottom:')]")


filtered_divs = divs_2
# print(f"Found {len(filtered_divs)} divs")
# len(divs_1), len(divs_2), len(divs3)


# --- Step 3: Prepare directory ---
os.makedirs(IMG_DIR, exist_ok=True)
saved_count = 0

# --- Step 4: Process each div ---
for idx, div in enumerate(filtered_divs, start=1):
    driver.execute_script("arguments[0].scrollIntoView();", div)
    time.sleep(0.5)  # give it a moment to load
    try:
        img_tag = div.find_element("tag name", "img")
        src = img_tag.get_attribute("src")

        if src and src.startswith("blob:https://drive.google.com/"):
            img_id = src.split("/")[-1]
            print(f"[{idx}] Found blob image id: {img_id}")

            # Extract image via JavaScript blob conversion
            # Create a canvas in JS, draw image, return base64 data
            script = """
                const img = arguments[0];
                const canvas = document.createElement('canvas');
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);
                return canvas.toDataURL('image/png');
            """
            img_base64 = driver.execute_script(script, img_tag)

            # Decode base64 and save
            if img_base64.startswith("data:image"):
                import base64
                data = base64.b64decode(img_base64.split(",")[1])
                img_path = os.path.join(IMG_DIR, f"{idx:03d}.png")
                with open(img_path, "wb") as f:
                    f.write(data)
                saved_count += 1
        else:
            print(f"[{idx}] No valid blob image found.")
    except Exception as e:
        print(f"[{idx}] Error: {e}")

print(f"\n✅ {saved_count} images saved in '{IMG_DIR}' folder.\n")


# --- Cleanup ---
driver.quit()

# --- Step 5: Create PDF with actual image size ---
# saved_count = len(os.listdir(IMG_DIR))
print(f"Creating PDF from {saved_count} images...")
if saved_count > 0:
    pdf = FPDF(unit="pt")  # Use points as unit for precise sizing
    for i in range(1, saved_count + 1):
        img_path = os.path.join(IMG_DIR, f"{i:03d}.png")
        if os.path.exists(img_path):
            image = Image.open(img_path)
            w, h = image.size  # size in pixels

            # Create a page with the same size as the image
            pdf.add_page(orientation='P', format=(w, h))
            pdf.image(img_path, 0, 0, w, h)  # keep actual image size

    pdf.output(PDF_DIR)
    print(f"📄 PDF created successfully: {PDF_DIR}")
else:
    print("No images saved. PDF not created.")


