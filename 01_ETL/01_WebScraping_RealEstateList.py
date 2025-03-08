
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

import pandas as pd  # 📌 Library to save data
from datetime import datetime  # 📌 To track execution date

# Get current date for logs and data
today = datetime.today().strftime("%Y-%m-%d")
log_filename = f"log_{today}.txt"

# Function to write logs
def write_log(message):
    """Writes logs to a file and prints them in the console."""
    with open(log_filename, "a", encoding="utf-8") as log_file:
        log_file.write(message + "\n")
    print(message)

# 🔹 Configure WebDriver
def setup_driver():
    """Configures and returns the Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (optional)
    driver = webdriver.Chrome(options=options)
    return driver

# Load the webpage
def load_page(driver, url):
    """Loads the given URL in the browser and waits for the page to render."""
    driver.get(url)
    time.sleep(3)  # Allow some time for elements to load

# Scroll down to load all elements
def scroll_page(driver):
    """Scrolls to the bottom of the page to load dynamically loaded elements."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            break
        last_height = new_height

# Extract data from the current page
def extract_data(driver, properties):
    """Extracts data from the current page and stores it in a list."""
    wait = WebDriverWait(driver, 10)
    
    try:
        scroll_page(driver)
        
        # Find all property cards
        property_cards = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "property-card__content")))
        elements_on_page = len(property_cards)
        write_log(f"📌 Elements found on this page: {elements_on_page}")
        
        for card in property_cards:
            try:
                # Extract link
                link_element = card.find_element(By.TAG_NAME, "a")
                link = link_element.get_attribute("href") if link_element else None

                # Extract location
                location_element = card.find_element(By.CLASS_NAME, "property-card__detail-top__left")
                location = location_element.text.strip() if location_element else None

                # Extract price
                price_element = card.find_element(By.CLASS_NAME, "property-card__detail-price")
                price = price_element.text.strip() if price_element else None

                # Extract title (not required but kept for reference)
                title_element = card.find_element(By.CLASS_NAME, "property-card__detail-title")
                title = title_element.text.strip() if title_element else None

                # Extract property attributes (area, bedrooms, bathrooms, parking)
                
                specs = card.find_element(By.TAG_NAME, "pt-main-specs")
                area = specs.get_attribute("squaremeter")
                bedrooms = specs.get_attribute("bedrooms")
                bathrooms = specs.get_attribute("toilets")
                parking = specs.get_attribute("parking")
                
                # Append extracted data to the list
                properties.append({
                    "id": link.split("/")[-1] if link else None,
                    "price": price,
                    "location": location, #.split("|")[0].strip() if location else None,
                    #"city": "Bogotá D.C.",
                    "area": area,
                    "bedrooms": bedrooms,
                    "bathrooms": bathrooms,
                    "parking": parking,
                    "link": link,
                    "fecha": today  # Add extraction date
                })

            except Exception as e:
                write_log("⚠ Error extracting data from a card")
    
    except Exception as e:
        write_log(f"⚠ Error in extract_data(): {e}")

# 🔹 Navigate to the next page
def next_page(driver):
    """Attempts to click the 'Next' button to go to the next page."""
    try:
        next_button = driver.find_element(By.CLASS_NAME, "rc-pagination-next")
        
        if next_button.get_attribute("aria-disabled") == "true":
            write_log("✅ No more pages available. Finishing...")
            return False

        driver.execute_script("arguments[0].scrollIntoView();", next_button)
        time.sleep(1)
        next_button.click()
        time.sleep(3)
        return True

    except Exception as e:
        write_log(f"⚠ Error in next_page(): {e}")
        return False

# 🔹 Main function (SCRAPES DATA ONLY)
def scrape_pages(url):
    """Executes scraping on all available pages and returns the data."""
    driver = setup_driver()
    
    pages_scraped = 0
    properties = []  # 📌 List to store extracted data

    try:
        load_page(driver, url)
        
        while True:
            pages_scraped += 1
            write_log(f"\n📄 Scraping Page {pages_scraped}...")

            extract_data(driver, properties)
            
            if not next_page(driver):
                break
        
    finally:
        write_log("\n✅ PROCESS COMPLETED")
        write_log(f"🔢 Total pages scraped: {pages_scraped}")
        write_log(f"📌 Total elements found: {len(properties)}")
        driver.quit()

    return properties  # ✅ Returns scraped data for later use

# 🔹 Save data function (SEPARATE STEP)
def save_data(properties, filename="real_estate_data"):
    """Saves data in Parquet, JSON, and CSV formats."""
    df = pd.DataFrame(properties)  # Convert to DataFrame
    
    df.to_json(f"{filename}.json", orient="records", indent=4)

    write_log("\n📂 Data successfully saved:")
    write_log(f"✔ JSON: {filename}.json")


# Execute Step 1: Scrape the Data
start_url = "https://www.metrocuadrado.com/apartamento-apartaestudio-casa-casalote/venta/bogota/?search=form"
properties = scrape_pages(start_url)  # Run scraping, return extracted data

# Execute Step 2: Save Data
save_data(properties, "real_estate_data")

# Log Summary
write_log(f"\n✅ Scraping Finished. Total properties extracted: {len(properties)}")
