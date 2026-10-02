from playwright.sync_api import sync_playwright
from sqlalchemy import create_engine, text
from datetime import date
import logging
import re
import time
import random
import requests
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "price_tracker")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")

NTFY_TOPIC = "john_price_tracker_2026"  # Badilisha na topic yako

def send_notification(message):
    """Send a notification to your phone via Ntfy."""
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode('utf-8'),
            timeout=5
        )
    except Exception as e:
        logging.error(f"Ntfy notification failed: {e}")
# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ============================================================
# DATABASE CONNECTION
# ============================================================
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "mande123"
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/price_tracker"

# ============================================================
# RETRY LOGIC
# ============================================================
def connect_with_retry(max_attempts=3, delay=5):
    """Try to connect to database up to 3 times."""
    for attempt in range(max_attempts):
        try:
            engine = create_engine(DATABASE_URL, connect_args={"connect_timeout": 5})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine
        except Exception as e:
            logging.warning(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(delay)
    raise Exception("All database connection attempts failed")

def scrape_with_retry(max_attempts=3, delay=10):
    """Try to scrape up to 3 times with random delays."""
    for attempt in range(max_attempts):
        try:
            return scrape_books()
        except Exception as e:
            logging.warning(f"Scrape attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                wait = delay + random.uniform(0, 5)  # Human-like jitter
                time.sleep(wait)
    raise Exception("All scraping attempts failed")

# ============================================================
# SCRAPER
# ============================================================
def scrape_books():
    books = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://books.toscrape.com/")
        page.wait_for_load_state("networkidle")
        
        book_elements = page.query_selector_all("article.product_pod")
        for book in book_elements:
            title = book.query_selector("h3 a").get_attribute("title")
            price_text = book.query_selector(".price_color").inner_text()
            url = "http://books.toscrape.com/" + book.query_selector("h3 a").get_attribute("href")
            price = float(re.sub(r'[^\d.]', '', price_text))
            books.append({"title": title, "price": price, "url": url, "store": "Books to Scrape"})
        
        browser.close()
    return books

# ============================================================
# DATE DIMENSION
# ============================================================
def ensure_date_dimension(connection, today):
    date_id = int(today.strftime("%Y%m%d"))
    result = connection.execute(
        text("SELECT date_id FROM date_dimension WHERE date_id = :date_id"),
        {"date_id": date_id}
    ).fetchone()
    
    if not result:
        connection.execute(text("""
            INSERT INTO date_dimension (date_id, full_date, year, month, day, day_of_week, is_weekend, quarter)
            VALUES (:date_id, :full_date, :year, :month, :day, :day_of_week, :is_weekend, :quarter)
        """), {
            "date_id": date_id, "full_date": today, "year": today.year,
            "month": today.month, "day": today.day,
            "day_of_week": today.strftime("%A"),
            "is_weekend": today.weekday() >= 5,
            "quarter": (today.month - 1) // 3 + 1
        })
    return date_id

# ============================================================
# SAVE TO DATABASE
# ============================================================
def save_to_database(engine, books):
    today = date.today()
    with engine.begin() as connection:
        date_id = ensure_date_dimension(connection, today)
        
        for book in books:
            result = connection.execute(
                text("SELECT product_id FROM products WHERE url = :url"),
                {"url": book["url"]}
            ).fetchone()
            
            if result:
                product_id = result[0]
            else:
                result = connection.execute(text("""
                    INSERT INTO products (product_name, url, store_name)
                    VALUES (:name, :url, :store)
                """), {"name": book["title"], "url": book["url"], "store": book["store"]})
                product_id = result.lastrowid
            
            connection.execute(text("""
                INSERT INTO price_history (product_id, price, is_available, date_id)
                VALUES (:product_id, :price, TRUE, :date_id)
            """), {"product_id": product_id, "price": book["price"], "date_id": date_id})

# ============================================================
# MAIN PIPELINE
# ============================================================
if __name__ == "__main__":
    logging.info("=" * 50)
    logging.info("SCRAPER RUN STARTED")
    print("🚀 Starting scraper pipeline...")
    
    try:
        # Step 1: Connect to database (with retry)
        print("🔌 Connecting to database...")
        engine = connect_with_retry(max_attempts=3, delay=5)
        print("✅ Database connected!")
        logging.info("Database connection established")
        
        # Step 2: Scrape books (with retry)
        print("🌐 Scraping books...")
        books = scrape_with_retry(max_attempts=3, delay=10)
        print(f"✅ Scraped {len(books)} books")
        logging.info(f"Scraped {len(books)} books")
        
        # Step 3: Save to database
        print("💾 Saving to database...")
        save_to_database(engine, books)
        print("✅ All data saved successfully!")
        logging.info(f"SUCCESS: {len(books)} books saved")
        
        # Step 4: Send success notification
        send_notification(f"✅ Price Tracker SUCCESS: {len(books)} books saved at {date.today()}")
        print("📱 Notification sent!")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        logging.error(f"PIPELINE FAILED: {e}")
        # Send failure notification
        send_notification(f"❌ Price Tracker FAILED at {date.today()}: {str(e)[:200]}")